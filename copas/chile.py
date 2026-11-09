"""Copa Chile: motor de la copa (sin Streamlit). Se enchufa al registro con `CopaChile` (copas/registro.py).

Formato 2026 de la ANFP (fuente: Emol, "Este viernes arranca la Copa Chile"):
  * 32 clubes: los 16 de la Liga de Primera y los 16 de la Primera B (la Segunda División Profesional queda afuera).
  * Fase de grupos: 8 grupos de 4 (dos de Primera y dos de Primera B), armados por zonas (Norte: A a D, Sur: E a H).
    Los primeros dos de cada grupo pasan a octavos.
  * Octavos, cuartos y semifinales a ida y vuelta (si el global empata, penales). La final es un partido único en cancha neutral.
  * Cupo internacional: el campeón tiene el Chile 4 (Libertadores · Fase 2). En el reglamento real juega un partido contra el
    3° de la liga y, si pierde, va a la Sudamericana; acá se simplifica (copas/conmebol.py, `CUPOS_COPA`).

Cuenta de clubes: 32 -> 16 (dos por grupo) -> 8 -> 4 -> 2 -> 1.

Simplificaciones (ver docs/LIGAS_EXTERIOR.md):
  * Los grupos: los clubes se ordenan de norte a sur (datos/json/copa_chile.json); la mitad más norteña de Primera y la de la B
    forman la Zona Norte y el resto la Zona Sur. Dentro de cada zona se sortea quién va con quién (dos de cada división por grupo).
  * Dentro de un grupo los dos de la B se enfrentan a ida y vuelta (fechas 1 y 2, en febrero, como en el calendario real) y cada
    uno de Primera juega a ida y vuelta contra cada uno de la B (fechas 3 a 6, desde junio). Los dos de Primera no se enfrentan
    entre sí: son 10 partidos por grupo. Es una lectura del calendario publicado, no del reglamento.
  * Octavos: el 1° de un grupo contra el 2° de otro (A1-B2, C1-D2, E1-F2, G1-H2 y sus cruces espejo B1-A2, D1-C2...); en la ida
    es local el 2° y la vuelta es en la cancha del 1°. A partir de cuartos el cuadro es fijo (el ganador del cruce 2j contra el del
    2j+1) y en la ida es local el club de menor media.
  * Los días son miércoles (las ligas juegan viernes y sábado).

El estado de la copa es un diccionario común con la forma del de una liga del exterior (`ligas/exterior.py`): `rondas`, `fecha`,
`log`, `nombres`, `r` y `E`. Por eso se juega con `jugar_ronda` y se guarda en el `.afa` sin tocar nada.
"""

import numpy as np

from copas.brasil import _local_primero, _pendiente, _penales_del_global
from datos.cargador import cargar
from ligas.exterior import partidos_de_ronda, ronda, stats_vacias, tabla
from motor.fechas import desde

NOMBRE = "Copa Chile"
PAIS = "Chile"
CLAVE = "copa_cl"

CLUBES_POR_DIVISION = 16
N_GRUPOS = 8
LETRAS = "ABCDEFGH"
MIERCOLES = 2

ORDEN_NORTE_SUR = {n: i for i, n in enumerate(cargar("copa_chile")["norte_a_sur"])}

FECHAS_GRUPOS = [(2, 4), (2, 11), (6, 17), (7, 1), (7, 15), (7, 29)]
# (fase, partidos por llave, [(mes, a partir del día)] de cada partido): miércoles
FASES_KO = [
    ("Octavos de final", 2, [(8, 12), (8, 26)]),
    ("Cuartos de final", 2, [(9, 9), (9, 23)]),
    ("Semifinales", 2, [(10, 7), (10, 21)]),
    ("Final", 1, [(11, 18)]),
]
NOMBRES_KO = [f for f, _, _ in FASES_KO]
NOMBRES_FASES = ["Fase de grupos", *NOMBRES_KO]
I_FINAL = len(FASES_KO) - 1
N_RONDAS_GRUPOS = len(FECHAS_GRUPOS)
TOTAL_RONDAS = N_RONDAS_GRUPOS + sum(len(d) for _, _, d in FASES_KO)      # 13
# (grupo del 1°, grupo del 2°) de cada cruce de octavos, en el orden del cuadro: el 1° y el 2° de un grupo quedan en mitades distintas
CRUCES_OCTAVOS = [(0, 1), (6, 7), (2, 3), (4, 5), (1, 0), (7, 6), (3, 2), (5, 4)]
LIBERTADORES_PREVIA = "Libertadores · Fase 2"


def _ronda_ko(f):
    """Índice (desde 0) de la primera ronda de la fase eliminatoria f."""
    return N_RONDAS_GRUPOS + sum(len(d) for _, _, d in FASES_KO[:f])


def nueva_copa(anio):
    """Copa de la temporada, todavía sin sortear (se sortea al armar la temporada, cuando ya se sabe quién juega la Primera y la B)."""
    rondas = [ronda("Fase de grupos", f"Grupos · fecha {k + 1}", "Fase de grupos", desde(anio, mes, dia, MIERCOLES), suma="Grupos")
              for k, (mes, dia) in enumerate(FECHAS_GRUPOS)]
    for fase, piernas, dias in FASES_KO:
        for k, (mes, dia) in enumerate(dias):
            ida_vuelta = None if piernas == 1 else ("ida" if k == 0 else "vuelta")
            rotulo = fase if piernas == 1 else f"{fase} · {ida_vuelta}"
            rondas.append(ronda(fase, rotulo, fase, desde(anio, mes, dia, MIERCOLES), ko=piernas == 1,
                                neutral=fase == "Final", ida_vuelta=ida_vuelta))
    return {"formato": "copa_chile", "nombre": NOMBRE, "pais": PAIS, "clave": CLAVE, "sorteada": False,
            "nombres": [], "r": np.array([], dtype=float), "origen": [], "grupos": [], "grupo_de": [], "E": {},
            "rondas": rondas, "fecha": 0, "log": [], "globales": {}, "campeon": None, "subcampeon": None}


def _mitades(clubes):
    """(zona Norte, zona Sur): la mitad más norteña y el resto, según el orden de datos/json/copa_chile.json."""
    orden = sorted(clubes, key=lambda n: (ORDEN_NORTE_SUR.get(n, len(ORDEN_NORTE_SUR)), n))
    h = len(orden) // 2
    return orden[:h], orden[h:]


def _fixture_grupo(g):
    """Seis fechas de un grupo [P1, P2, B1, B2]: los dos de la B entre sí (fechas 1 y 2) y cada uno de Primera contra cada uno de la B."""
    p1, p2, b1, b2 = g
    return [[(b1, b2)], [(b2, b1)], [(p1, b1), (p2, b2)], [(p1, b2), (p2, b1)], [(b1, p1), (b2, p2)], [(b2, p1), (b1, p2)]]


def sortear(L, rng, primera, segunda, media):
    """Sortea los grupos con los 16 clubes de la Primera y los 16 de la Primera B y carga las seis fechas de la fase de grupos."""
    if len(primera) != CLUBES_POR_DIVISION or len(segunda) != CLUBES_POR_DIVISION:
        raise ValueError(f"{NOMBRE}: hacen falta {CLUBES_POR_DIVISION} clubes de Primera y {CLUBES_POR_DIVISION} de la Primera B; "
                         f"hay {len(primera)} y {len(segunda)}")
    nombres = list(primera) + list(segunda)
    ids = {n: i for i, n in enumerate(nombres)}
    grupos = []
    for zona_p, zona_b in zip(_mitades(primera), _mitades(segunda)):
        p = [ids[n] for n in rng.permutation(zona_p)]
        b = [ids[n] for n in rng.permutation(zona_b)]
        for j in range(len(p) // 2):
            grupos.append([p[2 * j], p[2 * j + 1], b[2 * j], b[2 * j + 1]])
    grupo_de = [0] * len(nombres)
    for j, g in enumerate(grupos):
        for i in g:
            grupo_de[i] = j
    L.update(nombres=nombres, r=np.array([media(n) for n in nombres], dtype=float), grupos=grupos, grupo_de=grupo_de,
             origen=["Primera"] * len(primera) + ["Primera B"] * len(segunda), E={"Grupos": stats_vacias(len(nombres))},
             sorteada=True)
    fixtures = [_fixture_grupo(g) for g in grupos]
    for k in range(N_RONDAS_GRUPOS):
        R = L["rondas"][k]
        R["pares"] = [par for fx in fixtures for par in fx[k]]
        R["grupo_de"] = {i: f"Grupo {LETRAS[grupo_de[i]]}" for i in range(len(nombres))}
    return L


def tablas_grupos(L):
    """[(letra, DataFrame)]: la tabla de cada grupo (misma forma que las de las ligas)."""
    return [(LETRAS[j], tabla(L, L["E"]["Grupos"], ids=g)) for j, g in enumerate(L["grupos"])]


def _poner(L, f, cruces, local_menor_media=True):
    """Carga los cruces de la fase eliminatoria f en sus rondas (ida y vuelta si es a dos partidos)."""
    i0 = _ronda_ko(f)
    ida = [_local_primero(L, a, b) for a, b in cruces] if local_menor_media else list(cruces)
    L["rondas"][i0]["pares"] = ida
    if FASES_KO[f][1] == 2:
        L["rondas"][i0 + 1]["pares"] = [(v, l) for l, v in ida]


def _armar_octavos(L):
    ids = {n: i for i, n in enumerate(L["nombres"])}
    clas = []
    for _, df in tablas_grupos(L):
        clas.append((ids[df.iloc[0]["Equipo"]], ids[df.iloc[1]["Equipo"]]))
    L["clasificados"] = [{"grupo": LETRAS[j], "primero": L["nombres"][a], "segundo": L["nombres"][b]} for j, (a, b) in enumerate(clas)]
    # en la ida es local el 2° y la vuelta se juega en la cancha del 1°
    _poner(L, 0, [(clas[g2][1], clas[g1][0]) for g1, g2 in CRUCES_OCTAVOS], local_menor_media=False)


def _ganadores(L, f, rng):
    """Ids de los que pasan la fase eliminatoria f (ya jugada), en el orden de sus cruces."""
    ids = {n: i for i, n in enumerate(L["nombres"])}
    i0 = _ronda_ko(f)
    if FASES_KO[f][1] == 1:
        return [ids[p["gana"]] for p in partidos_de_ronda(L, i0 + 1)]
    out, globales = [], []
    for p1, p2 in zip(partidos_de_ronda(L, i0 + 1), partidos_de_ronda(L, i0 + 2)):
        a, b = ids[p1["local"]], ids[p1["visita"]]                   # a abrió de local (la ida)
        ga, gb = p1["gl"] + p2["gv"], p1["gv"] + p2["gl"]
        gana = (a if ga > gb else b) if ga != gb else _penales_del_global(L, p2, a, b, rng)
        out.append(gana)
        globales.append({"a": L["nombres"][a], "b": L["nombres"][b], "ga": int(ga), "gb": int(gb),
                         "gana": L["nombres"][gana], "pen": p2.get("pen")})
    L["globales"][f] = globales
    return out


def avanzar(L, rng):
    """Se llama después de cada ronda jugada: al cerrar los grupos arma los octavos; al cerrar una fase eliminatoria arma los
    cruces de la que sigue o, al terminar la final, define al campeón."""
    n = L["fecha"]                                   # rondas jugadas
    if not L["sorteada"] or n == 0 or L["campeon"] is not None or n < N_RONDAS_GRUPOS:
        return
    if n == N_RONDAS_GRUPOS:
        if L["rondas"][n]["pares"] is None:
            _armar_octavos(L)
        return
    R = L["rondas"][n - 1]
    if R["ida_vuelta"] == "ida":                     # falta la vuelta (sus cruces ya están cargados)
        return
    f = NOMBRES_KO.index(R["etapa"])
    if f < I_FINAL and L["rondas"][min(n, TOTAL_RONDAS - 1)]["pares"] is not None:
        return                                       # la fase siguiente ya está armada
    gana = _ganadores(L, f, rng)
    if f == I_FINAL:
        p = partidos_de_ronda(L, TOTAL_RONDAS)[0]
        L["campeon"] = p["gana"]
        L["subcampeon"] = p["local"] if p["gana"] == p["visita"] else p["visita"]
        return
    _poner(L, f + 1, list(zip(gana[0::2], gana[1::2])))      # cuadro fijo: el ganador del cruce 2j contra el del 2j+1


def en_juego(L):
    """Fase en la que está la copa (la de la próxima ronda) o "Terminada"."""
    if not L["sorteada"]:
        return "Sin sortear"
    if L["campeon"] is not None:
        return "Terminada"
    return L["rondas"][min(L["fecha"], TOTAL_RONDAS - 1)]["etapa"]


def cruces_de_fase(L, f):
    """Cruces de la fase eliminatoria f: [{"ida": partido, "vuelta": partido o None, "a", "b", "gana"}]; `a` abre de local. Vacío
    si todavía no se conocen. Un partido es un dict con local, visita, gl, gv, gana, pen, neutral y dia (con gl, gv y gana
    vacíos si todavía no se jugó)."""
    piernas = FASES_KO[f][1]
    i0 = _ronda_ko(f)
    R1 = L["rondas"][i0]
    if not L["sorteada"] or R1["pares"] is None:
        return []
    out = []
    for k, (a, b) in enumerate(R1["pares"]):
        partidos = []
        for j in range(piernas):
            i = i0 + j
            if i < L["fecha"]:
                p = partidos_de_ronda(L, i + 1)[k]
                partidos.append({**p, "dia": L["rondas"][i]["dia"]})
            else:
                x, y = L["rondas"][i]["pares"][k]
                partidos.append(_pendiente(L, i, x, y))
        gana = None
        if piernas == 1:
            gana = partidos[0]["gana"]
        elif i0 + 1 < L["fecha"]:
            g = L["globales"].get(f, [])
            gana = g[k]["gana"] if k < len(g) else None
        out.append({"ida": partidos[0], "vuelta": partidos[1] if piernas == 2 else None,
                    "a": L["nombres"][a], "b": L["nombres"][b], "gana": gana})
    return out


def llaves(L):
    """Datos del cuadro de octavos a la final: [(título, [cruce o None])] con los 8, 4, 2 y 1 cruces de cada fase."""
    out = []
    for f in range(len(FASES_KO)):
        cruces = cruces_de_fase(L, f)
        out.append((FASES_KO[f][0], cruces if cruces else [None] * 2 ** (I_FINAL - f)))
    return out


def participantes(L):
    """Filas de la tabla de clubes: [{"Club", "Origen", "Grupo", "Media", "Hasta"}]; `Hasta` es la última fase que jugó (o "Campeón")."""
    ultima = {}
    for p in L["log"]:
        f = NOMBRES_FASES.index(L["rondas"][p["fecha"] - 1]["etapa"])
        for n in (p["local"], p["visita"]):
            ultima[n] = max(ultima.get(n, -1), f)
    filas = []
    for i, n in enumerate(L["nombres"]):
        f = ultima.get(n)
        hasta = "" if f is None else ("Campeón" if n == L["campeon"] else NOMBRES_FASES[f])
        filas.append({"Club": n, "Origen": L["origen"][i], "Grupo": LETRAS[L["grupo_de"][i]],
                      "Media": round(float(L["r"][i]), 1), "Hasta": hasta})
    return filas


def definicion(L, temp):
    """Resumen de la copa de la temporada `temp` para la sección Campeones: campeón, subcampeón y los partidos de las
    semifinales y la final con su día."""
    partidos = [{**p, "dia": L["rondas"][p["fecha"] - 1]["dia"]} for p in L["log"] if p["comp"] in ("Semifinales", "Final")]
    return {"temp": temp, "campeon": L["campeon"], "subcampeon": L.get("subcampeon"), "partidos": partidos}

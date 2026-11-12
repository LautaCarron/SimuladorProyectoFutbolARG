"""Copa Venezuela: motor de la copa (sin Streamlit). Se enchufa al registro con `CopaVenezuela` (copas/registro.py).

Formato 2025-26 de la FVF (fuentes: Wikipedia "2025 Copa Venezuela", economis.com.ar y NTN24 sobre la edición 2026):
  * 28 clubes: los 14 de la Liga FUTVE y los 14 de la Liga FUTVE 2 (sin filiales, que no pueden jugarla).
  * Fase de grupos: 20 clubes (los 14 de la Liga FUTVE 2 y 6 de Primera, los que no llegan a las fases finales del Apertura). Cinco
    grupos de cuatro, ida y vuelta (seis fechas). Pasan los cinco primeros y los tres mejores segundos (8 clubes).
  * Octavos de final: los 8 clasificados contra los 8 de Primera que sí llegaron a las fases finales del Apertura, que entran
    directo. Partido único (como la edición 2026), con localía del que entró directo; si empatan, penales.
  * Cuartos de final, semifinales y final: ida y vuelta (como la edición 2025). Si el global empata no hay alargue: penales.
  * Sin cupo internacional: desde 2020 el campeón ya no va a la Sudamericana (el real juega la Supercopa de Venezuela contra el
    campeón de la liga, que no se simula).

Cuenta de clubes: 28 -> 20 (grupos) + 8 (directos) -> 8 + 8 = 16 -> 8 -> 4 -> 2 -> 1.

Simplificaciones (ver docs/LIGAS_EXTERIOR.md):
  * Los 8 de Primera que entran directo son los de mayor media (el real: los ocho de las fases finales del Apertura, que acá no existe
    porque la Liga FUTVE es un solo torneo). Los otros 6 de Primera juegan los grupos.
  * Grupos: sorteo libre (un club de Primera por grupo y el sexto en el grupo A). El real los arma por zonas geográficas.
  * Octavos: los 8 clasificados contra los 8 directos, al azar; los directos van ordenados por media para que los mejores queden en
    mitades distintas del cuadro. Desde ahí el cuadro es fijo (el ganador del cruce 2j contra el del 2j+1).
  * Cuartos, semifinales y final: abre de local (la ida) el de menor media, así cierra de local el de mayor media.
  * Los días son miércoles (las ligas juegan los sábados). Los grupos van cada dos semanas desde junio.

El estado de la copa es un diccionario común con la forma del de una liga del exterior (`ligas/exterior.py`): `rondas`, `fecha`, `log`,
`nombres`, `r` y `E`. Por eso se juega con `jugar_ronda` y se guarda en el `.afa` sin tocar nada.
"""

import numpy as np

from copas.brasil import _pendiente, _penales_del_global
from ligas.exterior import espejo, partidos_de_ronda, ronda, rueda, stats_vacias, tabla
from motor.fechas import desde

NOMBRE = "Copa Venezuela"
PAIS = "Venezuela"
CLAVE = "copa_ve"
LIGA_1, LIGA_2 = "Liga FUTVE", "Liga FUTVE 2"

CLUBES_PRIMERA = 14
CLUBES_SEGUNDA = 14
N_DIRECTOS = 8                                      # clubes de Primera que entran directo a octavos
N_GRUPOS = 5
POR_GRUPO = 4
N_SEGUNDOS = 3                                      # mejores segundos que pasan
LETRAS = "ABCDE"
MIERCOLES = 2

# Seis fechas de grupos (ida y vuelta), una cada dos semanas desde junio
FECHAS_GRUPOS = [(6, 3), (6, 17), (7, 1), (7, 15), (7, 29), (8, 12)]
# (fase, partidos por llave, [(mes, a partir del día)] de cada partido): miércoles
FASES_KO = [
    ("Octavos de final", 1, [(9, 2)]),
    ("Cuartos de final", 2, [(9, 23), (9, 30)]),
    ("Semifinales", 2, [(10, 21), (10, 28)]),
    ("Final", 2, [(11, 18), (11, 25)]),
]
NOMBRES_KO = [f for f, _, _ in FASES_KO]
NOMBRES_FASES = ["Fase de grupos", *NOMBRES_KO]
I_OCTAVOS = 0
I_FINAL = len(FASES_KO) - 1
N_RONDAS_GRUPOS = len(FECHAS_GRUPOS)
TOTAL_RONDAS = N_RONDAS_GRUPOS + sum(len(d) for _, _, d in FASES_KO)      # 13
# Orden de los 8 directos (0 = el de mayor media) en el cuadro: los mejores en mitades distintas
ORDEN_DIRECTOS = [0, 7, 3, 4, 1, 6, 2, 5]
CUPO = "Sin cupo internacional"


def _ronda_ko(f):
    """Índice (desde 0) de la primera ronda de la fase eliminatoria f."""
    return N_RONDAS_GRUPOS + sum(len(d) for _, _, d in FASES_KO[:f])


def nueva_copa(anio):
    """Copa de la temporada, todavía sin sortear; la clase CopaVenezuela la sortea al armar la temporada (con los clubes de las dos ligas)."""
    rondas = [ronda("Fase de grupos", f"Grupos · fecha {k + 1}", "Fase de grupos", desde(anio, mes, dia, MIERCOLES), suma="Grupos")
              for k, (mes, dia) in enumerate(FECHAS_GRUPOS)]
    for fase, piernas, dias in FASES_KO:
        for k, (mes, dia) in enumerate(dias):
            ida_vuelta = None if piernas == 1 else ("ida" if k == 0 else "vuelta")
            rotulo = fase if piernas == 1 else f"{fase} · {ida_vuelta}"
            rondas.append(ronda(fase, rotulo, fase, desde(anio, mes, dia, MIERCOLES), ko=piernas == 1, ida_vuelta=ida_vuelta))
    return {"formato": "copa_venezuela", "nombre": NOMBRE, "pais": PAIS, "clave": CLAVE, "sorteada": False,
            "nombres": [], "r": np.array([], dtype=float), "origen": [], "entrada": [], "directos": [], "grupos": [],
            "grupo_de": [], "E": {}, "rondas": rondas, "fecha": 0, "log": [], "globales": {}, "clasificados": [],
            "campeon": None, "subcampeon": None}


def _local_ida(L, a, b):
    """(local de la ida, visita): abre de local el de menor media, así cierra de local el de mayor media."""
    return (a, b) if L["r"][a] <= L["r"][b] else (b, a)


def sortear(L, rng, primera, segunda, media):
    """Sortea la copa con los 14 clubes de la Liga FUTVE y los 14 de la Liga FUTVE 2: los 8 de Primera de mayor media entran directo a
    octavos y el resto (6 de Primera y los 14 de la segunda) arma los cinco grupos de cuatro (seis fechas)."""
    if len(primera) != CLUBES_PRIMERA or len(segunda) != CLUBES_SEGUNDA:
        raise ValueError(f"{NOMBRE}: hacen falta {CLUBES_PRIMERA} clubes de la Liga FUTVE y {CLUBES_SEGUNDA} de la Liga FUTVE 2; "
                         f"hay {len(primera)} y {len(segunda)}")
    nombres = list(primera) + list(segunda)
    ids = {n: i for i, n in enumerate(nombres)}
    orden = sorted(primera, key=lambda n: (-media(n), n))
    directos = [ids[n] for n in orden[:N_DIRECTOS]]                          # de mayor a menor media
    de_grupos = [ids[n] for n in orden[N_DIRECTOS:]]                         # los 6 restantes de Primera
    p = [int(i) for i in rng.permutation(de_grupos)]
    s = [ids[n] for n in rng.permutation(segunda)]
    # un club de Primera por grupo (el sexto en el grupo A) y los 14 de la segunda completan los cuatro lugares de cada grupo
    grupos, k = [], 0
    for j in range(N_GRUPOS):
        de_p = p[j:j + 1] + (p[N_GRUPOS:] if j == 0 else [])
        grupos.append(de_p + s[k:k + POR_GRUPO - len(de_p)])
        k += POR_GRUPO - len(de_p)
    grupo_de = [-1] * len(nombres)
    for j, g in enumerate(grupos):
        for i in g:
            grupo_de[i] = j
    entrada = ["Fase de grupos" if grupo_de[i] >= 0 else "Octavos de final" for i in range(len(nombres))]
    L.update(nombres=nombres, r=np.array([media(n) for n in nombres], dtype=float), grupos=grupos, grupo_de=grupo_de,
             origen=[LIGA_1] * len(primera) + [LIGA_2] * len(segunda), entrada=entrada, directos=directos,
             E={"Grupos": stats_vacias(len(nombres))}, sorteada=True)
    fixtures = []
    for g in grupos:
        ida = rueda(rng, g)                                                  # 3 fechas de 2 partidos por grupo
        fixtures.append(ida + espejo(ida))                                   # y la vuelta con las localías invertidas
    for k in range(N_RONDAS_GRUPOS):
        R = L["rondas"][k]
        R["pares"] = [par for fx in fixtures for par in fx[k]]
        R["grupo_de"] = {i: f"Grupo {LETRAS[grupo_de[i]]}" for i in range(len(nombres)) if grupo_de[i] >= 0}
    return L


def tablas_grupos(L):
    """[(letra, DataFrame)]: la tabla de cada grupo (misma forma que las de las ligas)."""
    return [(LETRAS[j], tabla(L, L["E"]["Grupos"], ids=g)) for j, g in enumerate(L["grupos"])]


def _poner(L, f, cruces):
    """Carga los cruces de la fase eliminatoria f en sus rondas (ida y vuelta si es a dos partidos). En un partido único el
    primero de cada cruce es el local."""
    i0 = _ronda_ko(f)
    if FASES_KO[f][1] == 1:
        L["rondas"][i0]["pares"] = [(int(a), int(b)) for a, b in cruces]
        return
    ida = [_local_ida(L, a, b) for a, b in cruces]
    L["rondas"][i0]["pares"] = ida
    L["rondas"][i0 + 1]["pares"] = [(v, l) for l, v in ida]


def _clave_orden(fila):
    """Orden para comparar a los de distintos grupos: puntos, diferencia de gol y goles a favor."""
    return (-int(fila["Pts"]), -int(fila["DG"]), -int(fila["GF"]), fila["Equipo"])


def _guardar_clasificados(L):
    """Al cerrar los grupos: los cinco primeros y los tres mejores segundos (L["clasificados"]), ordenados de mejor a peor."""
    ids = {n: i for i, n in enumerate(L["nombres"])}
    tablas = [df for _, df in tablas_grupos(L)]
    primeros = sorted(((j, df.iloc[0]) for j, df in enumerate(tablas)), key=lambda x: _clave_orden(x[1]))
    segundos = sorted(((j, df.iloc[1]) for j, df in enumerate(tablas)), key=lambda x: _clave_orden(x[1]))
    pasan = {j for j, _ in segundos[:N_SEGUNDOS]}
    L["clasificados"] = [{"grupo": LETRAS[j], "primero": df.iloc[0]["Equipo"], "segundo": df.iloc[1]["Equipo"],
                          "pasa_segundo": j in pasan} for j, df in enumerate(tablas)]
    L["_clas_ids"] = [ids[f["Equipo"]] for _, f in primeros] + [ids[f["Equipo"]] for _, f in segundos[:N_SEGUNDOS]]


def _armar_octavos(L, rng):
    """Octavos: los 8 de la fase de grupos contra los 8 que entraron directo (de local), al azar."""
    directos = [L["directos"][k] for k in ORDEN_DIRECTOS]
    rivales = [int(i) for i in rng.permutation(L["_clas_ids"])]
    _poner(L, I_OCTAVOS, list(zip(directos, rivales)))


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
    """Se llama después de cada ronda jugada: al cerrar los grupos guarda los clasificados y arma los octavos; al cerrar una fase
    eliminatoria arma los cruces de la que sigue o, al terminar la final, define al campeón."""
    n = L["fecha"]                                   # rondas jugadas
    if not L["sorteada"] or n == 0 or L["campeon"] is not None or n < N_RONDAS_GRUPOS:
        return
    if n == N_RONDAS_GRUPOS:
        if not L["clasificados"]:
            _guardar_clasificados(L)
            _armar_octavos(L, rng)
        return
    R = L["rondas"][n - 1]
    if R["ida_vuelta"] == "ida":                     # falta la vuelta (sus cruces ya están cargados)
        return
    f = NOMBRES_KO.index(R["etapa"])
    if f < I_FINAL and L["rondas"][min(n, TOTAL_RONDAS - 1)]["pares"] is not None:
        return                                       # la fase siguiente ya está armada
    gana = _ganadores(L, f, rng)
    if f == I_FINAL:
        g = L["globales"][f][0]
        L["campeon"] = g["gana"]
        L["subcampeon"] = g["a"] if g["gana"] == g["b"] else g["b"]
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
    for f in range(I_OCTAVOS, len(FASES_KO)):
        cruces = cruces_de_fase(L, f)
        out.append((FASES_KO[f][0], cruces if cruces else [None] * 2 ** (I_FINAL - f)))
    return out


def participantes(L):
    """Filas de la tabla de clubes: [{"Club", "Origen", "Grupo", "Entra en", "Media", "Hasta"}]; `Hasta` es la última fase que jugó (o "Campeón")."""
    ultima = {}
    for p in L["log"]:
        f = NOMBRES_FASES.index(L["rondas"][p["fecha"] - 1]["etapa"])
        for n in (p["local"], p["visita"]):
            ultima[n] = max(ultima.get(n, -1), f)
    filas = []
    for i, n in enumerate(L["nombres"]):
        f = ultima.get(n)
        hasta = "" if f is None else ("Campeón" if n == L["campeon"] else NOMBRES_FASES[f])
        g = L["grupo_de"][i]
        filas.append({"Club": n, "Origen": L["origen"][i], "Grupo": LETRAS[g] if g >= 0 else "—", "Entra en": L["entrada"][i],
                      "Media": round(float(L["r"][i]), 1), "Hasta": hasta})
    return filas


def definicion(L, temp):
    """Resumen de la copa de la temporada `temp` para la sección Campeones: campeón, subcampeón y los partidos de las
    semifinales y la final con su día."""
    partidos = [{**p, "dia": L["rondas"][p["fecha"] - 1]["dia"]} for p in L["log"] if p["comp"] in ("Semifinales", "Final")]
    return {"temp": temp, "campeon": L["campeon"], "subcampeon": L.get("subcampeon"), "partidos": partidos}

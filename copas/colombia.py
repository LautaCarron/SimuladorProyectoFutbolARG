"""Copa Colombia (Copa BetPlay): motor de la copa (sin Streamlit). Se enchufa al registro con `CopaColombia` (copas/registro.py).

Formato 2026 de la Dimayor (fuentes: Wikipedia "2026 Copa Colombia", RTVC, Vanguardia y Publimetro sobre el cambio de agosto):
  * 36 clubes: los 20 de la Liga BetPlay y los 16 del Torneo BetPlay.
  * Fase 1A (fase de grupos): 20 clubes (12 de Primera y 8 del Torneo), los que no llegan a las fases finales del Apertura. Cuatro
    grupos de cinco (tres de Primera y dos del Torneo), una sola rueda: cada club juega cuatro partidos (dos de local y dos de
    visita) y descansa una fecha. Pasan los dos primeros de cada grupo (8 clubes).
  * Fase 1B (series): los otros 16 clubes (8 de Primera y 8 del Torneo), los que sí llegan a las fases finales del Apertura. Ocho
    series a ida y vuelta, cada una entre uno de Primera y uno del Torneo; el del Torneo es local en la vuelta. Pasan 8.
  * Octavos de final: los 8 de la fase 1A contra los 8 de la fase 1B, a partido único (el reglamento original era ida y vuelta; la
    Dimayor lo cambió en agosto de 2026 por el terremoto). Cuartos de final, también a partido único.
  * Semifinales y final: ida y vuelta. Si el global empata no hay alargue: penales.
  * Localía: si se enfrentan uno de Primera y uno del Torneo, el del Torneo es local en el partido único (y en la vuelta de las series);
    si son de la misma división, el mejor ubicado de la tabla de reclasificación del primer semestre.
  * Cupo internacional: el campeón va a la Copa Sudamericana, siempre que juegue en Primera. Si ya clasificó por la liga, el cupo
    pasa al que sigue en la tabla (copas/conmebol.py).

Cuenta de clubes: 36 -> 20 (fase 1A) + 16 (fase 1B) -> 8 + 8 = 16 -> 8 -> 4 -> 2 -> 1.

Simplificaciones (ver docs/LIGAS_EXTERIOR.md):
  * El simulador no tiene Apertura ni Finalización, así que no se sabe quién llega a las fases finales: van a la fase 1B los 8 clubes de
    Primera y los 8 del Torneo de mayor media; los demás juegan la fase de grupos. La copa se sortea al armar la temporada.
  * Grupos: sorteo libre (tres de Primera y dos del Torneo por grupo). El real los arma por zonas geográficas.
  * Series de la fase 1B: cada club de Primera contra uno del Torneo, al azar. Octavos: los 8 de la fase 1A contra los 8 de la fase 1B,
    al azar (el 1° y el 2° de un mismo grupo quedan en mitades distintas del cuadro); desde ahí el cuadro es fijo (el ganador del cruce
    2j contra el del 2j+1).
  * Semifinales y final: si son de la misma división, es local en la vuelta el de mayor media (el real usa la tabla del Apertura).
  * Los días son miércoles (las ligas juegan viernes y sábado). Las fechas se acomodan para terminar antes de mediados de diciembre.

El estado de la copa es un diccionario común con la forma del de una liga del exterior (`ligas/exterior.py`): `rondas`, `fecha`, `log`,
`nombres`, `r` y `E`. Por eso se juega con `jugar_ronda` y se guarda en el `.afa` sin tocar nada.
"""

import numpy as np

from copas.brasil import _pendiente, _penales_del_global
from ligas.exterior import partidos_de_ronda, ronda, rueda, stats_vacias, tabla
from motor.fechas import desde

NOMBRE = "Copa Colombia"
PAIS = "Colombia"
CLAVE = "copa_co"

CLUBES_PRIMERA = 20
CLUBES_TORNEO = 16
N_GRUPOS = 4
LETRAS = "ABCD"
POR_GRUPO_PRIMERA, POR_GRUPO_TORNEO = 3, 2          # cinco por grupo
A_FASE_1B = 8                                       # de cada división: los de mayor media van a las series
MIERCOLES = 2

# Cinco fechas de grupos (una por semana desde la primera semana de mayo)
FECHAS_GRUPOS = [(5, 6), (5, 13), (5, 20), (5, 27), (6, 3)]
# (fase, partidos por llave, [(mes, a partir del día)] de cada partido): miércoles
FASES_KO = [
    ("Fase 1B", 2, [(7, 22), (8, 5)]),
    ("Octavos de final", 1, [(9, 2)]),
    ("Cuartos de final", 1, [(10, 14)]),
    ("Semifinales", 2, [(11, 11), (11, 18)]),
    ("Final", 2, [(11, 25), (12, 2)]),
]
NOMBRES_KO = [f for f, _, _ in FASES_KO]
NOMBRES_FASES = ["Fase de grupos", *NOMBRES_KO]
I_SERIES, I_OCTAVOS = 0, 1
I_FINAL = len(FASES_KO) - 1
N_RONDAS_GRUPOS = len(FECHAS_GRUPOS)
TOTAL_RONDAS = N_RONDAS_GRUPOS + sum(len(d) for _, _, d in FASES_KO)      # 13
# Orden de los 8 clasificados de la fase 1A en el cuadro: el 1° y el 2° de un grupo quedan en mitades distintas
ORDEN_CLASIFICADOS = [(0, 0), (1, 1), (2, 0), (3, 1), (1, 0), (0, 1), (3, 0), (2, 1)]      # (grupo, puesto)
SUDAMERICANA = "Sudamericana · Fase 1"


def _ronda_ko(f):
    """Índice (desde 0) de la primera ronda de la fase eliminatoria f."""
    return N_RONDAS_GRUPOS + sum(len(d) for _, _, d in FASES_KO[:f])


def nueva_copa(anio):
    """Copa de la temporada, todavía sin sortear (se sortea al armar la temporada, cuando ya se sabe quién juega la Liga y el Torneo)."""
    rondas = [ronda("Fase de grupos", f"Grupos · fecha {k + 1}", "Fase de grupos", desde(anio, mes, dia, MIERCOLES), suma="Grupos")
              for k, (mes, dia) in enumerate(FECHAS_GRUPOS)]
    for fase, piernas, dias in FASES_KO:
        for k, (mes, dia) in enumerate(dias):
            ida_vuelta = None if piernas == 1 else ("ida" if k == 0 else "vuelta")
            rotulo = fase if piernas == 1 else f"{fase} · {ida_vuelta}"
            rondas.append(ronda(fase, rotulo, fase, desde(anio, mes, dia, MIERCOLES), ko=piernas == 1, ida_vuelta=ida_vuelta))
    return {"formato": "copa_colombia", "nombre": NOMBRE, "pais": PAIS, "clave": CLAVE, "sorteada": False,
            "nombres": [], "r": np.array([], dtype=float), "origen": [], "entrada": [], "grupos": [], "grupo_de": [], "E": {},
            "rondas": rondas, "fecha": 0, "log": [], "globales": {}, "clasificados": [], "campeon": None, "subcampeon": None}


def _es_primera(L, i):
    return L["origen"][i] == "Liga BetPlay"


def _local_unico(L, a, b):
    """(local, visita) de un partido único: el del Torneo si se enfrentan las dos divisiones; si no, el de mayor media."""
    if _es_primera(L, a) != _es_primera(L, b):
        return (b, a) if _es_primera(L, a) else (a, b)
    return (a, b) if L["r"][a] >= L["r"][b] else (b, a)


def _local_ida(L, a, b):
    """(local de la ida, visita): el de Primera abre de local y el del Torneo cierra; en la misma división, el de menor media abre."""
    if _es_primera(L, a) != _es_primera(L, b):
        return (a, b) if _es_primera(L, a) else (b, a)
    return (a, b) if L["r"][a] <= L["r"][b] else (b, a)


def sortear(L, rng, primera, torneo, media):
    """Sortea la copa con los 20 clubes de la Liga BetPlay y los 16 del Torneo BetPlay: arma los cuatro grupos (fase 1A, cinco fechas) y
    las ocho series de la fase 1B."""
    if len(primera) != CLUBES_PRIMERA or len(torneo) != CLUBES_TORNEO:
        raise ValueError(f"{NOMBRE}: hacen falta {CLUBES_PRIMERA} clubes de la Liga y {CLUBES_TORNEO} del Torneo; "
                         f"hay {len(primera)} y {len(torneo)}")
    nombres = list(primera) + list(torneo)
    ids = {n: i for i, n in enumerate(nombres)}
    mejores = lambda lista: sorted(lista, key=lambda n: (-media(n), n))                   # noqa: E731
    p_orden, t_orden = mejores(primera), mejores(torneo)
    series_p, series_t = p_orden[:A_FASE_1B], t_orden[:A_FASE_1B]                        # los que llegarían a las fases finales del Apertura
    grupos_p, grupos_t = p_orden[A_FASE_1B:], t_orden[A_FASE_1B:]
    p = [ids[n] for n in rng.permutation(grupos_p)]
    t = [ids[n] for n in rng.permutation(grupos_t)]
    grupos = [p[POR_GRUPO_PRIMERA * j:POR_GRUPO_PRIMERA * (j + 1)] + t[POR_GRUPO_TORNEO * j:POR_GRUPO_TORNEO * (j + 1)]
              for j in range(N_GRUPOS)]
    grupo_de = [-1] * len(nombres)
    for j, g in enumerate(grupos):
        for i in g:
            grupo_de[i] = j
    entrada = ["Fase de grupos" if grupo_de[i] >= 0 else "Fase 1B" for i in range(len(nombres))]
    L.update(nombres=nombres, r=np.array([media(n) for n in nombres], dtype=float), grupos=grupos, grupo_de=grupo_de,
             origen=["Liga BetPlay"] * len(primera) + ["Torneo BetPlay"] * len(torneo), entrada=entrada,
             E={"Grupos": stats_vacias(len(nombres))}, sorteada=True)
    fixtures = [rueda(rng, g) for g in grupos]                                           # 5 fechas de 2 partidos por grupo
    for k in range(N_RONDAS_GRUPOS):
        R = L["rondas"][k]
        R["pares"] = [par for fx in fixtures for par in fx[k]]
        R["grupo_de"] = {i: f"Grupo {LETRAS[grupo_de[i]]}" for i in range(len(nombres)) if grupo_de[i] >= 0}
    rivales = [ids[n] for n in rng.permutation(series_t)]
    _poner(L, I_SERIES, [(ids[a], b) for a, b in zip(series_p, rivales)])
    return L


def tablas_grupos(L):
    """[(letra, DataFrame)]: la tabla de cada grupo (misma forma que las de las ligas)."""
    return [(LETRAS[j], tabla(L, L["E"]["Grupos"], ids=g)) for j, g in enumerate(L["grupos"])]


def _poner(L, f, cruces):
    """Carga los cruces de la fase eliminatoria f en sus rondas (ida y vuelta si es a dos partidos)."""
    i0 = _ronda_ko(f)
    if FASES_KO[f][1] == 1:
        L["rondas"][i0]["pares"] = [_local_unico(L, a, b) for a, b in cruces]
        return
    ida = [_local_ida(L, a, b) for a, b in cruces]
    L["rondas"][i0]["pares"] = ida
    L["rondas"][i0 + 1]["pares"] = [(v, l) for l, v in ida]


def _guardar_clasificados(L):
    """Al cerrar los grupos: los dos primeros de cada uno (L["clasificados"])."""
    ids = {n: i for i, n in enumerate(L["nombres"])}
    L["clasificados"] = [{"grupo": LETRAS[j], "primero": df.iloc[0]["Equipo"], "segundo": df.iloc[1]["Equipo"]}
                         for j, (_, df) in enumerate(tablas_grupos(L))]
    L["_clas_ids"] = [[ids[df.iloc[0]["Equipo"]], ids[df.iloc[1]["Equipo"]]] for _, df in tablas_grupos(L)]


def _armar_octavos(L, rng, ganadores_series):
    """Octavos: los 8 de la fase 1A (el 1° y el 2° de un grupo en mitades distintas del cuadro) contra los 8 de la fase 1B, al azar."""
    clas = [L["_clas_ids"][g][puesto] for g, puesto in ORDEN_CLASIFICADOS]
    rivales = [int(i) for i in rng.permutation(ganadores_series)]
    _poner(L, I_OCTAVOS, list(zip(clas, rivales)))


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
    """Se llama después de cada ronda jugada: al cerrar los grupos guarda los clasificados; al cerrar las series arma los octavos;
    al cerrar una fase eliminatoria arma los cruces de la que sigue o, al terminar la final, define al campeón."""
    n = L["fecha"]                                   # rondas jugadas
    if not L["sorteada"] or n == 0 or L["campeon"] is not None or n < N_RONDAS_GRUPOS:
        return
    if n == N_RONDAS_GRUPOS:
        if not L["clasificados"]:
            _guardar_clasificados(L)
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
    if f == I_SERIES:
        _armar_octavos(L, rng, gana)
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

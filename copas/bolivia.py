"""Copa Bolivia (torneo por series de la División Profesional): motor de la copa (sin Streamlit). Se enchufa al registro con
`CopaBolivia` (copas/registro.py).

Formato 2026 de la FBF (fuentes: Correo del Sur, Red Uno, Erbol y Los Tiempos, julio de 2026; Wikipedia "2025 Copa Bolivia"):
  * 16 clubes: los de la División Profesional. Se juega en paralelo a la liga, entre semana.
  * Fase de grupos: cuatro series de cuatro, todos contra todos a una rueda (tres fechas) más una fecha de clásicos interserie.
  * Pasan los dos primeros de cada serie (8 clubes). El reglamento prevé además un playoff de terceros "para completar el
    cuadro"; no se simula (con ocho clasificados el cuadro de cuartos ya está completo).
  * Cuartos de final, semifinales y final: ida y vuelta. Si el global empata no hay alargue: penales.
  * Cupo internacional: el campeón es el Bolivia 3 (Libertadores · Fase 2), siempre que juegue en Primera; si ya clasificó por la
    liga, el cupo pasa al que sigue en la tabla (copas/conmebol.py, `CUPOS_COPA`). El real le da al subcampeón un cupo de
    Sudamericana; acá no se simula (los cuatro de la Sudamericana salen de la tabla de la liga).

Cuenta de clubes: 16 -> 8 -> 4 -> 2 -> 1.

Simplificaciones (ver docs/LIGAS_EXTERIOR.md):
  * Series por bombos de media: un club de cada bombo (por media) en cada serie. El sorteo real es libre.
  * Clásicos interserie: la serie A juega contra la B y la C contra la D; cada club con uno al azar de la serie hermana (sus
    puntos cuentan para la tabla de su serie). El real arma los clásicos por rivalidad.
  * Cuadro fijo: 1° de A contra 2° de B, 1° de C contra 2° de D, 1° de D contra 2° de C y 1° de B contra 2° de A. El 1° y el
    2° de una serie quedan en mitades distintas. Cierra de local (la vuelta) el de mayor media (el real usa la posición en la serie).
  * Días: miércoles (la liga juega los sábados). Del 19/8 al 2/12.

El estado de la copa es un diccionario común con la forma del de una liga del exterior (`ligas/exterior.py`): `rondas`, `fecha`,
`log`, `nombres`, `r` y `E`. Por eso se juega con `jugar_ronda` y se guarda en el `.afa` sin tocar nada.
"""

import numpy as np

from copas.brasil import _pendiente, _penales_del_global
from ligas.exterior import partidos_de_ronda, ronda, rueda, stats_vacias, tabla
from motor.fechas import desde

NOMBRE = "Copa Bolivia"
PAIS = "Bolivia"
CLAVE = "copa_bo"

N_CLUBES = 16
N_GRUPOS = 4
POR_GRUPO = 4
LETRAS = "ABCD"
MIERCOLES = 2

# Cuatro fechas de la fase de grupos (la cuarta es la de clásicos interserie): una por semana desde el 19/8
FECHAS_GRUPOS = [(8, 19), (8, 26), (9, 2), (9, 9)]
# (fase, partidos por llave, [(mes, a partir del día)] de cada partido): miércoles
FASES_KO = [
    ("Cuartos de final", 2, [(10, 7), (10, 14)]),
    ("Semifinales", 2, [(11, 4), (11, 11)]),
    ("Final", 2, [(11, 25), (12, 2)]),
]
NOMBRES_KO = [f for f, _, _ in FASES_KO]
NOMBRES_FASES = ["Fase de grupos", *NOMBRES_KO]
I_CUARTOS = 0
I_FINAL = len(FASES_KO) - 1
N_RONDAS_GRUPOS = len(FECHAS_GRUPOS)
TOTAL_RONDAS = N_RONDAS_GRUPOS + sum(len(d) for _, _, d in FASES_KO)      # 10
# Cuadro de cuartos: (serie y puesto del que abre la llave, serie y puesto de su rival); (1° = 0, 2° = 1)
CUADRO_CUARTOS = [((0, 0), (1, 1)), ((2, 0), (3, 1)), ((3, 0), (2, 1)), ((1, 0), (0, 1))]
CUPO = "Libertadores · Fase 2"


def _ronda_ko(f):
    """Índice (desde 0) de la primera ronda de la fase eliminatoria f."""
    return N_RONDAS_GRUPOS + sum(len(d) for _, _, d in FASES_KO[:f])


def nueva_copa(anio):
    """Copa de la temporada, todavía sin sortear; la clase CopaBolivia la sortea al armar la temporada (con los 16 de la Primera)."""
    rondas = []
    for k, (mes, dia) in enumerate(FECHAS_GRUPOS):
        clasicos = k == N_RONDAS_GRUPOS - 1
        rondas.append(ronda("Fase de grupos", "Clásicos interserie" if clasicos else f"Grupos · fecha {k + 1}",
                            "Clásicos interserie" if clasicos else "Fase de grupos", desde(anio, mes, dia, MIERCOLES), suma="Grupos"))
    for fase, _, dias in FASES_KO:
        for k, (mes, dia) in enumerate(dias):
            ida_vuelta = "ida" if k == 0 else "vuelta"
            rondas.append(ronda(fase, f"{fase} · {ida_vuelta}", fase, desde(anio, mes, dia, MIERCOLES), ida_vuelta=ida_vuelta))
    return {"formato": "copa_bolivia", "nombre": NOMBRE, "pais": PAIS, "clave": CLAVE, "sorteada": False,
            "nombres": [], "r": np.array([], dtype=float), "grupos": [], "grupo_de": [], "E": {},
            "rondas": rondas, "fecha": 0, "log": [], "globales": {}, "clasificados": [], "campeon": None, "subcampeon": None}


def _local_ida(L, a, b):
    """(local de la ida, visita): abre de local el de menor media, así cierra de local el de mayor media."""
    return (a, b) if L["r"][a] <= L["r"][b] else (b, a)


def sortear(L, rng, clubes, media):
    """Sortea la copa con los 16 clubes de la Primera: arma las cuatro series por bombos de media (tres fechas) y los clásicos
    interserie (la cuarta fecha)."""
    if len(clubes) != N_CLUBES:
        raise ValueError(f"{NOMBRE}: hacen falta {N_CLUBES} clubes de la Primera; hay {len(clubes)}")
    nombres = list(clubes)
    ids = {n: i for i, n in enumerate(nombres)}
    orden = sorted(nombres, key=lambda n: (-media(n), n))
    bombos = [[ids[n] for n in rng.permutation(orden[POR_GRUPO * k:POR_GRUPO * (k + 1)])] for k in range(POR_GRUPO)]
    grupos = [[bombo[j] for bombo in bombos] for j in range(N_GRUPOS)]
    grupo_de = [-1] * len(nombres)
    for j, g in enumerate(grupos):
        for i in g:
            grupo_de[i] = j
    L.update(nombres=nombres, r=np.array([media(n) for n in nombres], dtype=float), grupos=grupos, grupo_de=grupo_de,
             E={"Grupos": stats_vacias(len(nombres))}, sorteada=True)
    fixtures = [rueda(rng, g) for g in grupos]                                   # 3 fechas de 2 partidos por serie
    for k in range(N_RONDAS_GRUPOS - 1):
        R = L["rondas"][k]
        R["pares"] = [par for fx in fixtures for par in fx[k]]
        R["grupo_de"] = {i: f"Grupo {LETRAS[grupo_de[i]]}" for i in range(len(nombres))}
    clasicos = []                                                                # A con B y C con D, cada uno con uno al azar
    for a, b in ((0, 1), (2, 3)):
        rivales = [int(i) for i in rng.permutation(grupos[b])]
        clasicos += [(int(x), y) if k % 2 == 0 else (y, int(x)) for k, (x, y) in enumerate(zip(grupos[a], rivales))]
    L["rondas"][N_RONDAS_GRUPOS - 1]["pares"] = clasicos
    return L


def tablas_grupos(L):
    """[(letra, DataFrame)]: la tabla de cada serie (misma forma que las de las ligas)."""
    return [(LETRAS[j], tabla(L, L["E"]["Grupos"], ids=g)) for j, g in enumerate(L["grupos"])]


def _poner(L, f, cruces):
    """Carga los cruces de la fase eliminatoria f (ida y vuelta) en sus dos rondas."""
    i0 = _ronda_ko(f)
    ida = [_local_ida(L, a, b) for a, b in cruces]
    L["rondas"][i0]["pares"] = ida
    L["rondas"][i0 + 1]["pares"] = [(v, l) for l, v in ida]


def _guardar_clasificados(L):
    """Al cerrar los grupos: los dos primeros de cada serie (L["clasificados"]) y los cruces de cuartos."""
    ids = {n: i for i, n in enumerate(L["nombres"])}
    tablas = tablas_grupos(L)
    L["clasificados"] = [{"grupo": LETRAS[j], "primero": df.iloc[0]["Equipo"], "segundo": df.iloc[1]["Equipo"]}
                         for j, (_, df) in enumerate(tablas)]
    clas = [[ids[df.iloc[0]["Equipo"]], ids[df.iloc[1]["Equipo"]]] for _, df in tablas]
    L["_clas_ids"] = clas
    _poner(L, I_CUARTOS, [(clas[g1][p1], clas[g2][p2]) for (g1, p1), (g2, p2) in CUADRO_CUARTOS])


def _ganadores(L, f, rng):
    """Ids de los que pasan la fase eliminatoria f (ya jugada), en el orden de sus cruces."""
    ids = {n: i for i, n in enumerate(L["nombres"])}
    i0 = _ronda_ko(f)
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
    """Se llama después de cada ronda jugada: al cerrar los grupos guarda los clasificados y arma los cuartos; al cerrar una fase
    eliminatoria arma los cruces de la que sigue o, al terminar la final, define al campeón."""
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
    _poner(L, f + 1, list(zip(gana[0::2], gana[1::2])))      # cuadro fijo: el ganador del cruce 2j contra el del 2j+1


def en_juego(L):
    """Fase en la que está la copa (la de la próxima ronda) o "Terminada"."""
    if not L["sorteada"]:
        return "Sin sortear"
    if L["campeon"] is not None:
        return "Terminada"
    return L["rondas"][min(L["fecha"], TOTAL_RONDAS - 1)]["etapa"]


def cruces_de_fase(L, f):
    """Cruces de la fase eliminatoria f: [{"ida": partido, "vuelta": partido, "a", "b", "gana"}]; `a` abre de local. Vacío si
    todavía no se conocen. Un partido es un dict con local, visita, gl, gv, gana, pen, neutral y dia (con gl, gv y gana
    vacíos si todavía no se jugó)."""
    i0 = _ronda_ko(f)
    R1 = L["rondas"][i0]
    if not L["sorteada"] or R1["pares"] is None:
        return []
    out = []
    for k, (a, b) in enumerate(R1["pares"]):
        partidos = []
        for j in range(2):
            i = i0 + j
            if i < L["fecha"]:
                p = partidos_de_ronda(L, i + 1)[k]
                partidos.append({**p, "dia": L["rondas"][i]["dia"]})
            else:
                x, y = L["rondas"][i]["pares"][k]
                partidos.append(_pendiente(L, i, x, y))
        gana = None
        if i0 + 1 < L["fecha"]:
            g = L["globales"].get(f, [])
            gana = g[k]["gana"] if k < len(g) else None
        out.append({"ida": partidos[0], "vuelta": partidos[1], "a": L["nombres"][a], "b": L["nombres"][b], "gana": gana})
    return out


def llaves(L):
    """Datos del cuadro de cuartos a la final: [(título, [cruce o None])] con los 4, 2 y 1 cruces de cada fase."""
    out = []
    for f in range(len(FASES_KO)):
        cruces = cruces_de_fase(L, f)
        out.append((FASES_KO[f][0], cruces if cruces else [None] * 2 ** (I_FINAL - f)))
    return out


def participantes(L):
    """Filas de la tabla de clubes: [{"Club", "Grupo", "Media", "Hasta"}]; `Hasta` es la última fase que jugó (o "Campeón")."""
    ultima = {}
    for p in L["log"]:
        f = NOMBRES_FASES.index(L["rondas"][p["fecha"] - 1]["etapa"])
        for n in (p["local"], p["visita"]):
            ultima[n] = max(ultima.get(n, -1), f)
    filas = []
    for i, n in enumerate(L["nombres"]):
        f = ultima.get(n)
        hasta = "" if f is None else ("Campeón" if n == L["campeon"] else NOMBRES_FASES[f])
        filas.append({"Club": n, "Grupo": LETRAS[L["grupo_de"][i]], "Media": round(float(L["r"][i]), 1), "Hasta": hasta})
    return filas


def definicion(L, temp):
    """Resumen de la copa de la temporada `temp` para la sección Campeones: campeón, subcampeón y los partidos de las
    semifinales y la final con su día."""
    partidos = [{**p, "dia": L["rondas"][p["fecha"] - 1]["dia"]} for p in L["log"] if p["comp"] in ("Semifinales", "Final")]
    return {"temp": temp, "campeon": L["campeon"], "subcampeon": L.get("subcampeon"), "partidos": partidos}

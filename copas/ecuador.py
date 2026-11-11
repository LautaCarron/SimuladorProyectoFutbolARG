"""Copa Ecuador: eliminación directa con clubes de Serie A, Serie B y Segunda Categoría.

El simulador incorpora los 76 clubes cargados en las tres categorías: 16 de Serie A,
12 de Serie B y 48 de Segunda Categoría. Una ronda preliminar entre 24 clubes de
Segunda Categoría reduce el cuadro a 64; los otros 24 de esa categoría y los 28
clubes profesionales entran directamente a los treintaidosavos.

Cruces: la preliminar, los treintaidosavos, los dieciseisavos y los octavos se sortean libremente entre los que pasan;
desde los octavos el cuadro es fijo (el ganador del cruce 2j juega con el del 2j+1), así que las llaves se dibujan con
sus líneas de octavos a la final. Todas las rondas son a partido único (la final, en cancha neutral).
"""
import numpy as np

from ligas.exterior import partidos_de_ronda, ronda
from motor.fechas import desde

NOMBRE = "Copa Ecuador"
PAIS = "Ecuador"
CLAVE = "copa_ec"
MIERCOLES = 2
ETAPAS = [
    ("Preliminar", "Fase preliminar", False, (5, 20)),
    ("Treintaidosavos", "Treintaidosavos de final", False, (6, 17)),
    ("Dieciseisavos", "Dieciseisavos de final", False, (7, 22)),
    ("Octavos", "Octavos de final", False, (8, 19)),
    ("Cuartos", "Cuartos de final", False, (9, 23)),
    ("Semifinales", "Semifinales", False, (10, 21)),
    ("Final", "Final", True, (11, 18)),
]
TOTAL_RONDAS = len(ETAPAS)
NOMBRES_FASES = [rotulo for _, rotulo, _, _ in ETAPAS]
I_OCTAVOS = 3                         # desde acá el cuadro es fijo y se dibuja con líneas
I_FINAL = TOTAL_RONDAS - 1


def nueva_copa(anio):
    rondas = [ronda(etapa, rotulo, rotulo, desde(anio, *dia, MIERCOLES), ko=True, neutral=neutral)
              for etapa, rotulo, neutral, dia in ETAPAS]
    return {"formato": "copa_ecuador", "nombre": NOMBRE, "pais": PAIS, "clave": CLAVE,
            "sorteada": False, "nombres": [], "r": np.array([], dtype=float), "origen": [],
            "byes": [], "rondas": rondas, "fecha": 0, "log": [], "campeon": None, "subcampeon": None}


def _de(L, origen):
    return [i for i, o in enumerate(L["origen"]) if o == origen]


def _local(L, a, b):
    nivel = {"Serie A": 0, "Serie B": 1, "Segunda Categoría": 2}
    na, nb = nivel[L["origen"][a]], nivel[L["origen"][b]]
    if na != nb:
        return (a, b) if na > nb else (b, a)
    return (a, b) if L["r"][a] <= L["r"][b] else (b, a)


def sortear(L, rng, primera, segunda, tercera, media):
    if len(primera) != 16 or len(segunda) != 12 or len(tercera) < 24:
        raise ValueError(f"{NOMBRE}: se necesitan 16 de Serie A, 12 de Serie B y al menos 24 de Segunda Categoría")
    origenes = [("Serie A", primera), ("Serie B", segunda), ("Segunda Categoría", tercera)]
    L["nombres"] = [n for _, clubes in origenes for n in clubes]
    L["origen"] = [o for o, clubes in origenes for _ in clubes]
    L["r"] = np.array([media(n) for n in L["nombres"]], dtype=float)
    L["sorteada"] = True
    tercera_ids = [int(i) for i in rng.permutation(_de(L, "Segunda Categoría"))]
    juegan = tercera_ids[:24]
    L["byes"] = tercera_ids[24:] + _de(L, "Serie A") + _de(L, "Serie B")
    L["rondas"][0]["pares"] = [(_local(L, int(a), int(b))) for a, b in zip(juegan[::2], juegan[1::2])]
    return L


def _ganadores(L, n):
    return [L["nombres"].index(p["gana"]) for p in partidos_de_ronda(L, n)]


def avanzar(L, rng):
    if not L["sorteada"] or L["campeon"] is not None or L["fecha"] == 0:
        return
    n = L["fecha"]
    if n >= TOTAL_RONDAS:
        p = partidos_de_ronda(L, TOTAL_RONDAS)[0]
        L["campeon"] = p["gana"]
        L["subcampeon"] = p["visita"] if p["gana"] == p["local"] else p["local"]
        return
    if L["rondas"][n]["pares"] is not None:
        return
    gana = [int(i) for i in _ganadores(L, n)]
    if n <= I_OCTAVOS:                               # sorteo libre hasta armar los octavos; después el cuadro es fijo
        gana = [int(i) for i in rng.permutation(gana)]
    if n == 1:
        ids = [int(i) for i in rng.permutation(gana + L["byes"])]
        pares = [_local(L, a, b) for a, b in zip(ids[::2], ids[1::2])]
    else:
        pares = [_local(L, a, b) for a, b in zip(gana[::2], gana[1::2])]
    L["rondas"][n]["pares"] = pares


def en_juego(L):
    """Fase en la que está la copa (la de la próxima ronda) o "Terminada"."""
    if not L["sorteada"]:
        return "Sin sortear"
    if L["campeon"] is not None:
        return "Terminada"
    return L["rondas"][min(L["fecha"], TOTAL_RONDAS - 1)]["etapa"]


def _pendiente(L, i, a, b):
    R = L["rondas"][i]
    return {"local": L["nombres"][a], "visita": L["nombres"][b], "gl": "", "gv": "", "gana": None, "pen": None,
            "neutral": R["neutral"], "dia": R["dia"]}


def cruces_de_fase(L, f):
    """Cruces de la fase f (0 = preliminar ... 6 = final): [{"ida": partido, "vuelta": None, "a", "b", "gana"}]; `a` es el
    local. Vacío si todavía no se conocen. Un partido es un dict con local, visita, gl, gv, gana, pen, neutral y dia (con gl,
    gv y gana vacíos si todavía no se jugó). Todas las fases son a partido único."""
    R = L["rondas"][f]
    if not L["sorteada"] or R["pares"] is None:
        return []
    out = []
    for k, (a, b) in enumerate(R["pares"]):
        if f < L["fecha"]:
            p = {**partidos_de_ronda(L, f + 1)[k], "dia": R["dia"]}
        else:
            p = _pendiente(L, f, a, b)
        out.append({"ida": p, "vuelta": None, "a": L["nombres"][a], "b": L["nombres"][b], "gana": p["gana"]})
    return out


def llaves(L):
    """Datos del cuadro de octavos a la final: [(título, [cruce o None])] con los 8, 4, 2 y 1 cruces de cada fase (None si
    todavía no se conocen)."""
    out = []
    for f in range(I_OCTAVOS, TOTAL_RONDAS):
        cruces = cruces_de_fase(L, f)
        out.append((ETAPAS[f][0], cruces if cruces else [None] * 2 ** (I_FINAL - f)))
    return out


def participantes(L):
    """Filas de la tabla de clubes: [{"Club", "Origen", "Entra en", "Media", "Hasta"}]; `Hasta` es la última fase que jugó
    (o "Campeón"). Entran en la preliminar los 24 clubes de Segunda Categoría del primer sorteo; el resto, en los
    treintaidosavos."""
    ultima = {}
    for p in L["log"]:
        f = L["rondas"][p["fecha"] - 1]["etapa"]
        f = [e for e, _, _, _ in ETAPAS].index(f)
        for n in (p["local"], p["visita"]):
            ultima[n] = max(ultima.get(n, -1), f)
    preliminar = {i for par in (L["rondas"][0]["pares"] or []) for i in par}
    filas = []
    for i, n in enumerate(L["nombres"]):
        f = ultima.get(n)
        hasta = "" if f is None else ("Campeón" if n == L["campeon"] else NOMBRES_FASES[f])
        filas.append({"Club": n, "Origen": L["origen"][i],
                      "Entra en": NOMBRES_FASES[0] if i in preliminar else NOMBRES_FASES[1],
                      "Media": round(float(L["r"][i]), 1), "Hasta": hasta})
    return filas


def definicion(L, temp):
    partidos = [{**p, "dia": L["rondas"][p["fecha"] - 1]["dia"]} for p in L["log"]
                if p["comp"] in ("Semifinales", "Final")]
    return {"temp": temp, "campeon": L["campeon"], "subcampeon": L.get("subcampeon"), "partidos": partidos}

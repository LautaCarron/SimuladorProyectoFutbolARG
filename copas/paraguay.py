"""Copa Paraguay: motor de la copa (sin Streamlit). Se enchufa al registro con `CopaParaguay` (copas/registro.py).

Formato real 2026 (APF, "La Copa de Todos"; fuente: Wikipedia y ABC Color): 74 clubes entran por etapas según su categoría,
todo a eliminación directa y partido único (si empatan, penales):
  * Primera fase: Primera B, Primera C y los 17 campeones departamentales de la UFI (46 clubes): 20 cruces y dos triangulares,
    pasan 24.
  * Segunda fase: a esos 24 se suman los 16 de la División Intermedia: 40 clubes, 20 cruces.
  * Tercera fase: entran los 12 de Primera contra los 20 que pasaron: 16 cruces.
  * Octavos, cuartos, semifinales y final.
  * El campeón juega la Libertadores del año siguiente (Fase 1) y la Supercopa Paraguay. Si ya clasificó por la liga, el cupo
    pasa al que sigue (en el simulador: copas/conmebol.py, `_sortear_pais`).

Formato del simulador (58 clubes: los 12 de la Primera, los 16 de la Intermedia, los 17 de la Primera B Metropolitana y los 13 de
la B Nacional). Simplificaciones (ver docs/LIGAS_EXTERIOR.md):
  * No están la Primera C ni los campeones departamentales de la UFI (16 + 17 clubes): la B Nacional, que es del interior, hace
    de UFI. Para que sigan pasando 24 en la primera fase, sólo juegan los cruces necesarios entre los clubes de las dos B (6 con 30 clubes, 7 con 31) y el resto
    pasa directo (en la realidad no hay clubes libres).
  * Segunda fase: los 24 de la primera y los 16 de la Intermedia se sortean libremente (20 cruces). Tercera fase: cada uno de
    los 12 de Primera juega contra uno de los 20 que pasaron y los 8 restantes se cruzan entre sí (16 cruces).
  * Desde octavos el cuadro es fijo: el ganador del cruce 2j contra el del 2j+1 (la tercera fase se sortea mezclada, así que
    es como un sorteo). Es local el club de la categoría más baja (si son de la misma, el de menor media); la final es en
    cancha neutral.
  * Los días son miércoles. En la realidad la copa arranca en junio y termina en noviembre.

El estado de la copa es un diccionario común con la forma del de una liga del exterior (`ligas/exterior.py`): `rondas`, `fecha`,
`log`, `nombres`, `r` y `E`. Por eso se juega con `jugar_ronda` y se guarda en el `.afa` sin tocar nada.
"""

import numpy as np

from ligas.exterior import partidos_de_ronda, ronda
from motor.fechas import desde

NOMBRE = "Copa Paraguay"
PAIS = "Paraguay"
CLAVE = "copa_py"
LIBERTADORES = "Paraguay · Libertadores (Fase 1)"

MIERCOLES = 2
ORIGENES = ("Primera", "Intermedia", "B Metropolitana", "B Nacional")
NIVEL = {"Primera": 0, "Intermedia": 1, "B Metropolitana": 2, "B Nacional": 2}       # la categoría más baja es local
EQUIPOS = {"Primera": 12, "Intermedia": 16}                   # las dos B pueden tener cualquier cantidad (hoy 17 + 14)
PASAN_PRIMERA_FASE = 24                                       # a la segunda fase llegan siempre 24 de las dos B (6 de 30, 7 de 31, ...)

# (etapa, rótulo, neutral, (mes, a partir del día)): miércoles
ETAPAS = [("Primera fase", "Primera fase", False, (6, 3)),
          ("Segunda fase", "Segunda fase", False, (7, 15)),
          ("Tercera fase", "Tercera fase", False, (8, 12)),
          ("Octavos de final", "Octavos de final", False, (9, 16)),
          ("Cuartos de final", "Cuartos de final", False, (10, 14)),
          ("Semifinales", "Semifinales", False, (11, 4)),
          ("Final", "Final", True, (11, 25))]
NOMBRES_FASES = [e for e, _, _, _ in ETAPAS]
TOTAL_RONDAS = len(ETAPAS)                                    # 7
I_OCTAVOS = NOMBRES_FASES.index("Octavos de final")


def nueva_copa(anio):
    """Copa de la temporada, todavía sin sortear (se sortea al armar la temporada, cuando ya se sabe quién juega en cada categoría)."""
    rondas = [ronda(etapa, rotulo, rotulo, desde(anio, *dia, MIERCOLES), ko=True, neutral=neutral)
              for etapa, rotulo, neutral, dia in ETAPAS]
    return {"formato": "copa_paraguay", "nombre": NOMBRE, "pais": PAIS, "clave": CLAVE, "sorteada": False,
            "nombres": [], "r": np.array([], dtype=float), "origen": [], "byes": [], "E": {},
            "rondas": rondas, "fecha": 0, "log": [], "campeon": None, "subcampeon": None}


def _local(L, a, b):
    """(local, visitante): abre de local el de la categoría más baja; si son de la misma, el de menor media."""
    na, nb = NIVEL[L["origen"][a]], NIVEL[L["origen"][b]]
    if na != nb:
        return (a, b) if na > nb else (b, a)
    return (a, b) if L["r"][a] <= L["r"][b] else (b, a)


def _de(L, *origenes):
    return [i for i, o in enumerate(L["origen"]) if o in origenes]


def _parejas(L, ids):
    return [_local(L, a, b) for a, b in zip(ids[0::2], ids[1::2])]


def sortear(L, rng, por_origen, media):
    """Arma la copa con los clubes de cada categoría (`por_origen`: {origen: [clubes]}) y sortea la primera fase: los cruces necesarios entre
    clubes de las dos B para que pasen 24 (el resto pasa directo a la segunda fase). `media(club)` da la media de cada uno."""
    cont = {o: len(por_origen.get(o, [])) for o in ORIGENES}
    b = cont["B Metropolitana"] + cont["B Nacional"]
    if cont["Primera"] != EQUIPOS["Primera"] or cont["Intermedia"] != EQUIPOS["Intermedia"] or not PASAN_PRIMERA_FASE < b <= 2 * PASAN_PRIMERA_FASE:
        raise ValueError(f"{NOMBRE}: hacen falta {EQUIPOS['Primera']} clubes de Primera, {EQUIPOS['Intermedia']} de la Intermedia y entre "
                         f"{PASAN_PRIMERA_FASE + 1} y {2 * PASAN_PRIMERA_FASE} de las dos Primera B; hay {cont['Primera']}, {cont['Intermedia']} y {b}")
    cruces = b - PASAN_PRIMERA_FASE                                  # cada cruce elimina a uno: quedan 24
    nombres = [n for o in ORIGENES for n in por_origen[o]]
    L.update(nombres=nombres, r=np.array([media(n) for n in nombres], dtype=float),
             origen=[o for o in ORIGENES for _ in por_origen[o]], sorteada=True)
    pool = [int(i) for i in rng.permutation(_de(L, "B Metropolitana", "B Nacional"))]
    juegan = pool[:2 * cruces]
    L["byes"] = pool[2 * cruces:]                       # pasan directo a la segunda fase
    L["rondas"][0]["pares"] = _parejas(L, juegan)
    return L


def _ganadores(L, n):
    """Ids de los ganadores de la ronda n (1, 2, ...), en el orden de los cruces."""
    return [L["nombres"].index(p["gana"]) for p in partidos_de_ronda(L, n)]


def avanzar(L, rng):
    """Se llama después de cada ronda jugada: arma los cruces de la que sigue o, al terminar la final, define al campeón."""
    if not L["sorteada"] or L["campeon"] is not None or L["fecha"] == 0:
        return
    n = L["fecha"]                                                   # rondas jugadas
    if n >= TOTAL_RONDAS:
        p = partidos_de_ronda(L, TOTAL_RONDAS)[0]
        L["campeon"] = p["gana"]
        L["subcampeon"] = p["local"] if p["gana"] == p["visita"] else p["visita"]
        return
    if L["rondas"][n]["pares"] is not None:
        return
    gana = _ganadores(L, n)
    if n == 1:                                                       # segunda fase: los que pasaron + los 16 de la Intermedia
        ids = [int(i) for i in rng.permutation(gana + L["byes"] + _de(L, "Intermedia"))]
        pares = _parejas(L, ids)
    elif n == 2:                                                     # tercera fase: cada uno de Primera contra uno de los 20
        primera = [int(i) for i in rng.permutation(_de(L, "Primera"))]
        gana = [int(i) for i in rng.permutation(gana)]
        pares = [_local(L, a, b) for a, b in zip(primera, gana)]
        pares += _parejas(L, gana[len(primera):])
        pares = [pares[int(i)] for i in rng.permutation(len(pares))]   # el orden del cuadro (quién se cruza después) es libre
    else:                                                            # cuadro fijo: el ganador del cruce 2j contra el del 2j+1
        pares = _parejas(L, gana)
    L["rondas"][n]["pares"] = pares


def en_juego(L):
    """Fase en la que está la copa (la de la próxima ronda), \"Sin sortear\" o \"Terminada\"."""
    if not L["sorteada"]:
        return "Sin sortear"
    if L["campeon"] is not None:
        return "Terminada"
    return L["rondas"][min(L["fecha"], TOTAL_RONDAS - 1)]["etapa"]


def llaves(L, desde_etapa=I_OCTAVOS):
    """Datos del cuadro de eliminación: [(rótulo de la ronda, [partido o None])], de la etapa `desde_etapa` (2 = tercera fase,
    3 = octavos) a la final. Un partido es un dict con local, visita, gl, gv, gana, pen, neutral y dia (con gl, gv y gana
    vacíos si todavía no se jugó); None si el cruce no se conoce."""
    out = []
    for k in range(max(desde_etapa, 2), TOTAL_RONDAS):
        _, rotulo, neutral, _ = ETAPAS[k]
        R = L["rondas"][k]
        n = 2 ** (TOTAL_RONDAS - 1 - k)
        if not L["sorteada"] or R["pares"] is None:
            ms = [None] * n
        elif k < L["fecha"]:
            ms = [{**p, "dia": R["dia"]} for p in partidos_de_ronda(L, k + 1)]
        else:
            ms = [{"local": L["nombres"][a], "visita": L["nombres"][b], "gl": "", "gv": "", "gana": None, "pen": None,
                   "neutral": R["neutral"], "dia": R["dia"]} for a, b in R["pares"]]
        out.append((rotulo, ms))
    return out


def participantes(L):
    """Filas de la tabla de clubes: [{"Club", "Origen", "Media", "Hasta"}]; `Hasta` es la última fase que jugó (o \"Campeón\")."""
    ultima = {}
    for p in L["log"]:
        f = NOMBRES_FASES.index(L["rondas"][p["fecha"] - 1]["etapa"])
        for n in (p["local"], p["visita"]):
            ultima[n] = max(ultima.get(n, -1), f)
    filas = []
    for i, n in enumerate(L["nombres"]):
        f = ultima.get(n)
        hasta = "" if f is None else ("Campeón" if n == L["campeon"] else NOMBRES_FASES[f])
        filas.append({"Club": n, "Origen": L["origen"][i], "Media": round(float(L["r"][i]), 1), "Hasta": hasta})
    return filas


def definicion(L, temp):
    """Resumen de la copa de la temporada `temp` para la sección Campeones: campeón, subcampeón y los partidos de las
    semifinales y la final con su día."""
    partidos = [{**p, "dia": L["rondas"][p["fecha"] - 1]["dia"]} for p in L["log"] if p["comp"] in ("Semifinales", "Final")]
    return {"temp": temp, "campeon": L["campeon"], "subcampeon": L.get("subcampeon"), "partidos": partidos}

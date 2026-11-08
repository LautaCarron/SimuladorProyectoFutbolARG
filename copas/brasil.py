"""Copa do Brasil: motor de la copa (sin Streamlit). Se enchufa al registro con `CopaBrasil` (copas/registro.py).

Formato 2026 de la CBF (126 clubes, nueve fases eliminatorias; fuentes: Lance!, Trivela y NetVasco sobre el formato nuevo):
  * Primera fase: los 28 clubes peor ubicados en el ranking, a partido único. Pasan 14.
  * Segunda fase: los 14 que pasaron + 74 que entran directo (88 clubes, 44 cruces).
  * Tercera fase: los 44 que pasaron + 4 que entran directo (los campeones de la Série C y de la Série D del año
    anterior y los cupos de la Copa Verde y de la Copa do Nordeste). 48 clubes, pasan 24.
  * Cuarta fase: los 24 que pasaron la tercera, a partido único (12 cruces). Pasan 12.
  * Quinta fase: los 20 de la Série A entran acá y se cruzan con los 12 sobrevivientes. Desde acá todo es a ida y vuelta.
  * Octavos de final, cuartos de final y semifinales a ida y vuelta (si el global empata, penales).
  * Final: partido único en cancha neutral (novedad de 2026).
  * Cupos internacionales: el campeón va a la fase de grupos de la Libertadores y el subcampeón a su fase previa
    (Fase 2). Si ya habían clasificado por el Brasileirão, el cupo pasa a la Série A (copas/conmebol.py, `_sortear_pais`).

Cuenta de clubes: 28 -> 14 | 14 + 74 = 88 -> 44 | 44 + 4 = 48 -> 24 | 24 -> 12 | 12 + 20 = 32 -> 16 | 16 -> 8 -> 4 -> 2 -> 1.

Simplificaciones (a revisar contra el reglamento de la CBF; ver docs/LIGAS_EXTERIOR.md):
  * No hay estaduales ni Copa Verde ni Copa do Nordeste: los 106 clubes que no son de la Série A salen de la Série B, la C
    y la D del simulador. Los mejores 102 por media (menos los 4 de la tercera fase) juegan; los 28 de peor media
    arrancan en la primera fase y los otros 74 en la segunda (el real usa el ranking de la CBF).
  * Los cuatro de la tercera fase son el campeón de la Série C y el de la Série D de la temporada anterior y los dos
    clubes de mejor media que quedaron afuera (en el lugar de los campeones de la Copa Verde y de la Copa do Nordeste).
  * Los cruces de las cuatro primeras fases son al azar (el real los arma por regiones). En la quinta fase, 12 clubes de la
    Série A (al azar) se cruzan con los 12 sobrevivientes y los otros 8 entre sí. Octavos: sorteo libre entre los 16
    que pasan; desde ahí el cuadro es fijo.
  * Localía: en los partidos únicos es local el club de menor media; en las series, la ida es del de menor media y la vuelta
    del de mayor media.

El estado de la copa es un diccionario común y corriente con la forma del de una liga del exterior (`ligas/exterior.py`):
`rondas`, `fecha`, `log`, `nombres` y `r`. Por eso se juega con `jugar_ronda` y se guarda en el `.afa` sin tocar nada.
"""

import numpy as np

from ligas.exterior import partidos_de_ronda, ronda
from motor.fechas import desde
from motor.nucleo import tanda_penales

NOMBRE = "Copa do Brasil"
PAIS = "Brasil"
CLAVE = "copa_br"

EQUIPOS_A = 20                 # Série A: entran en la quinta fase
N_PRIMERA = 28                 # los 28 de peor ranking juegan la primera fase
N_SEGUNDA = 74                 # entran directo a la segunda fase
N_TERCERA = 4                  # entran directo a la tercera fase
TOTAL_CLUBES = EQUIPOS_A + N_PRIMERA + N_SEGUNDA + N_TERCERA      # 126

MIERCOLES = 2
# (fase, partidos por llave, [(mes, a partir del día)] de cada partido): miércoles
FASES = [
    ("Primera fase", 1, [(2, 11)]),
    ("Segunda fase", 1, [(2, 25)]),
    ("Tercera fase", 1, [(3, 18)]),
    ("Cuarta fase", 1, [(4, 8)]),
    ("Quinta fase", 2, [(4, 22), (5, 6)]),
    ("Octavos de final", 2, [(8, 5), (8, 19)]),
    ("Cuartos de final", 2, [(9, 2), (9, 16)]),
    ("Semifinales", 2, [(10, 7), (10, 21)]),
    ("Final", 1, [(11, 18)]),
]
NOMBRES_FASES = [f for f, _, _ in FASES]
I_SEGUNDA, I_TERCERA, I_CUARTA, I_QUINTA, I_OCTAVOS = 1, 2, 3, 4, 5
I_FINAL = len(FASES) - 1
FASES_LLAVES = NOMBRES_FASES[I_OCTAVOS:]              # lo que dibuja el cuadro: de octavos a la final
TOTAL_RONDAS = sum(len(d) for _, _, d in FASES)       # 13 rondas (cuatro fases de ida y vuelta + cinco de partido único)
LIBERTADORES = "Libertadores · fase de grupos"
LIBERTADORES_PREVIA = "Libertadores · Fase 2"


def _primera_ronda(f):
    """Índice (desde 0) de la primera ronda de la fase f."""
    return sum(len(d) for _, _, d in FASES[:f])


def nueva_copa(anio):
    """Copa de la temporada, todavía sin sortear (se sortea al armar la temporada, cuando ya se sabe quién juega la Série A)."""
    rondas = []
    for fase, piernas, dias in FASES:
        for k, (mes, dia) in enumerate(dias):
            ida_vuelta = None if piernas == 1 else ("ida" if k == 0 else "vuelta")
            rotulo = fase if piernas == 1 else f"{fase} · {ida_vuelta}"
            rondas.append(ronda(fase, rotulo, fase, desde(anio, mes, dia, MIERCOLES), ko=piernas == 1,
                                neutral=fase == "Final", ida_vuelta=ida_vuelta))
    return {"formato": "copa_brasil", "nombre": NOMBRE, "pais": PAIS, "clave": CLAVE, "sorteada": False,
            "nombres": [], "r": np.array([], dtype=float), "origen": [], "entrada": [], "entran": {}, "rondas": rondas,
            "fecha": 0, "log": [], "globales": {}, "campeon": None, "subcampeon": None}


def elegir_tercera_fase(por_division, campeones, media):
    """Los 4 clubes que entran en la tercera fase: [(club, cómo entra)].

    por_division  {"Série B": [clubes], "Série C": [...], "Série D": [...]} (todos menos los de la Série A).
    campeones     {"Série C": club, "Série D": club} de la temporada anterior (puede faltar: la primera temporada).
    media         función club -> media.
    Entran el campeón de la C, el de la D y, en el lugar de los campeones de la Copa Verde y de la Copa do Nordeste, los dos
    de mejor media que quedan."""
    elegidos = []
    validos = {n for lista in por_division.values() for n in lista}
    for div in ("Série C", "Série D"):
        club = campeones.get(div)
        if club in validos and club not in {c for c, _ in elegidos}:
            elegidos.append((club, f"Campeón de la {div} anterior"))
        elif por_division.get(div):                      # sin campeón anterior (primera temporada): el mejor de la división
            mejor = max(por_division[div], key=lambda n: (media(n), n))
            elegidos.append((mejor, f"Mejor de la {div} (todavía no hay campeón anterior)"))
    ya = {c for c, _ in elegidos}
    resto = sorted((n for lista in por_division.values() for n in lista if n not in ya), key=lambda n: (-media(n), n))
    for n in resto[:N_TERCERA - len(elegidos)]:
        elegidos.append((n, "Cupo regional (Copa Verde / Copa do Nordeste)"))
    return elegidos[:N_TERCERA]


def sortear(L, rng, serie_a, por_division, tercera, media):
    """Sortea la copa: `serie_a` (20 clubes), `por_division` = {división: [clubes]} con todos los demás y `tercera` = los
    4 que entran en la tercera fase ([(club, cómo entra)]). Arma las listas de cada fase y los cruces de la primera."""
    entran3 = [n for n, _ in tercera]
    origen_de = {n: div for div, lista in por_division.items() for n in lista}
    resto = sorted((n for n in origen_de if n not in set(entran3)), key=lambda n: (-media(n), n))
    if len(serie_a) != EQUIPOS_A or len(entran3) != N_TERCERA or len(resto) < N_PRIMERA + N_SEGUNDA:
        raise ValueError(f"{NOMBRE}: hacen falta {EQUIPOS_A} de la Série A, {N_TERCERA} para la tercera fase y al menos "
                         f"{N_PRIMERA + N_SEGUNDA} más; hay {len(serie_a)}, {len(entran3)} y {len(resto)}")
    resto = resto[:N_PRIMERA + N_SEGUNDA]
    segunda, primera = resto[:N_SEGUNDA], resto[N_SEGUNDA:]
    nombres = list(serie_a) + entran3 + segunda + primera
    L["nombres"] = nombres
    L["r"] = np.array([media(n) for n in nombres], dtype=float)
    L["origen"] = ["Série A"] * EQUIPOS_A + [origen_de[n] for n in entran3 + segunda + primera]
    entra = ["Quinta fase"] * EQUIPOS_A + ["Tercera fase"] * N_TERCERA + ["Segunda fase"] * N_SEGUNDA \
        + ["Primera fase"] * N_PRIMERA
    L["entrada"] = entra
    via = {n: v for n, v in tercera}
    L["via"] = [via.get(n, "") for n in nombres]
    ids = {n: i for i, n in enumerate(nombres)}
    L["entran"] = {I_SEGUNDA: [ids[n] for n in segunda], I_TERCERA: [ids[n] for n in entran3],
                   I_QUINTA: [ids[n] for n in serie_a]}
    L["sorteada"] = True
    _poner(L, 0, _parejas(rng, [ids[n] for n in primera]))
    return L
def _local_primero(L, a, b):
    """(local, visita): el de menor media hace de local (en la ida, si es a dos partidos)."""
    return (a, b) if L["r"][a] <= L["r"][b] else (b, a)


def _parejas(rng, ids):
    ids = [int(i) for i in rng.permutation(list(ids))]
    return list(zip(ids[0::2], ids[1::2]))


def _poner(L, f, cruces):
    """Carga los cruces de la fase f en sus rondas (ida y vuelta si la fase es a dos partidos)."""
    _, piernas, _ = FASES[f]
    i0 = _primera_ronda(f)
    ida = [_local_primero(L, a, b) for a, b in cruces]
    L["rondas"][i0]["pares"] = ida
    if piernas == 2:
        L["rondas"][i0 + 1]["pares"] = [(v, l) for l, v in ida]


def _cruces_quinta(rng, serie_a, sobrevivientes):
    """Quinta fase: 12 clubes de la Série A (al azar) contra los 12 sobrevivientes y los otros 8 entre sí."""
    a = [int(i) for i in rng.permutation(list(serie_a))]
    n = len(sobrevivientes)
    return list(zip(sobrevivientes, a[:n])) + list(zip(a[n::2], a[n + 1::2]))
def _penales_del_global(L, p_vuelta, a, b, rng):
    """Global empatado: gana `a` o `b` por penales (algo más probable el de mejor media). Se anota en el partido de vuelta."""
    p_a = float(np.clip(0.5 + (L["r"][a] - L["r"][b]) / 400, 0.35, 0.65))
    gana_a = bool(rng.random() < p_a)
    gana_local = (L["nombres"][a] == p_vuelta["local"]) == gana_a
    tanda = tanda_penales(rng, gana_local)
    p_vuelta["tanda"], p_vuelta["pen"] = tanda, (sum(tanda[0]), sum(tanda[1]))
    p_vuelta["gana"] = L["nombres"][a] if gana_a else L["nombres"][b]
    return a if gana_a else b


def _ganadores(L, f, rng):
    """Ids de los que pasan la fase f (ya jugada), en el orden de sus cruces."""
    ids = {n: i for i, n in enumerate(L["nombres"])}
    i0 = _primera_ronda(f)
    if FASES[f][1] == 1:
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
    """Se llama después de cada ronda jugada: al cerrar una fase arma los cruces de la que sigue o, al terminar la final,
    define al campeón."""
    n = L["fecha"]                                   # rondas jugadas
    if not L["sorteada"] or n == 0 or L["campeon"] is not None:
        return
    R = L["rondas"][n - 1]
    if R["ida_vuelta"] == "ida":                     # falta la vuelta (sus cruces ya están cargados)
        return
    f = NOMBRES_FASES.index(R["etapa"])
    if L["rondas"][min(n, TOTAL_RONDAS - 1)]["pares"] is not None and f < I_FINAL:
        return                                       # la fase siguiente ya está armada
    gana = _ganadores(L, f, rng)
    if f == I_FINAL:
        p = partidos_de_ronda(L, TOTAL_RONDAS)[0]
        L["campeon"] = p["gana"]
        L["subcampeon"] = p["local"] if p["gana"] == p["visita"] else p["visita"]
        return
    s = f + 1
    if s in (I_SEGUNDA, I_TERCERA):                  # se suman los que entran directo en esa fase
        cruces = _parejas(rng, gana + L["entran"][s])
    elif s == I_CUARTA or s == I_OCTAVOS:            # sorteo libre
        cruces = _parejas(rng, gana)
    elif s == I_QUINTA:
        cruces = _cruces_quinta(rng, L["entran"][I_QUINTA], gana)
    else:                                            # cuadro fijo: el ganador del cruce 2j contra el del 2j+1
        cruces = list(zip(gana[0::2], gana[1::2]))
    _poner(L, s, cruces)
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
    """Cruces de la fase f: [{"ida": partido o None, "vuelta": partido o None, "a", "b", "gana"}]; `a` abre de local. Vacío
    si todavía no se conocen. Un partido es un dict con local, visita, gl, gv, gana, pen, neutral y dia (con gl, gv y gana
    vacíos si todavía no se jugó)."""
    piernas = FASES[f][1]
    i0 = _primera_ronda(f)
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
    """Datos del cuadro de octavos a la final: [(título, [cruce o None])] con los 8, 4, 2 y 1 cruces de cada fase (None si
    todavía no se conocen)."""
    out = []
    for k, f in enumerate(range(I_OCTAVOS, len(FASES))):
        n = 2 ** (len(FASES) - 1 - f)
        cruces = cruces_de_fase(L, f)
        out.append((FASES[f][0], cruces if cruces else [None] * n))
    return out


def participantes(L):
    """Filas de la tabla de clubes: [{"Club", "Origen", "Entra en", "Media", "Cómo", "Hasta"}]; `Hasta` es la última
    fase que jugó (o "Campeón")."""
    ids = {n: i for i, n in enumerate(L["nombres"])}
    ultima = {}
    for p in L["log"]:
        f = NOMBRES_FASES.index(L["rondas"][p["fecha"] - 1]["etapa"])
        for n in (p["local"], p["visita"]):
            ultima[n] = max(ultima.get(n, -1), f)
    filas = []
    for n in L["nombres"]:
        f = ultima.get(n)
        hasta = "" if f is None else ("Campeón" if n == L["campeon"] else NOMBRES_FASES[f])
        filas.append({"Club": n, "Origen": L["origen"][ids[n]], "Entra en": L["entrada"][ids[n]],
                      "Media": round(float(L["r"][ids[n]]), 1), "Cómo": L["via"][ids[n]], "Hasta": hasta})
    return filas


def definicion(L, temp):
    """Resumen de la copa de la temporada `temp` para la sección Campeones: campeón, subcampeón y los partidos de las
    semifinales y la final con su día."""
    partidos = [{**p, "dia": L["rondas"][p["fecha"] - 1]["dia"]} for p in L["log"]
                if p["comp"] in ("Semifinales", "Final")]
    return {"temp": temp, "campeon": L["campeon"], "subcampeon": L.get("subcampeon"), "partidos": partidos}

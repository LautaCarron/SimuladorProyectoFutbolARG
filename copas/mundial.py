"""Mundial de Clubes: clasificación y torneo (se juega cada 4 temporadas: 2029 = temporada 4).

Clasificación (ciclo de 4 años, como el formato 2025-2028 de la FIFA): los campeones continentales de
los 4 años anteriores clasifican directo y el resto de cada cupo sale del ranking, con máximo de 2
clubes por país (salvo campeones). Cupos: UEFA 12, CONMEBOL 6, AFC 4, CAF 4, Concacaf 4, OFC 1 y el
anfitrión (ver clubes_mundial.py).

  * CONMEBOL: campeones de la Libertadores simulada de cada temporada. El ranking suma los puntos de
    partidos (victoria 3, empate 1) de la Libertadores y la mitad de los de la Sudamericana de los 4 años.
    El año 2025 arranca con los campeones y el ranking reales.
  * UEFA, AFC, CAF, Concacaf y OFC no se simulan como torneo: al terminar cada temporada se sortea su
    campeón continental entre los clubes de clubes_mundial.py (los de mayor media tienen más chances).
    El "ranking" de esas confederaciones se aproxima con la media del club. 2025: campeones reales.

Formato (como 2025): 8 grupos de 4 a una rueda (3 fechas) y eliminación directa: octavos, cuartos,
semifinales y final. Todo en cancha neutral; en las eliminatorias, si empatan, penales.
"""

from collections import Counter

import numpy as np

from datos.clubes_mundial import CUPOS_2029, MEDIA_MUNDIAL, PAIS_MUNDIAL, clubes_de
from copas.conmebol import PAIS_EXT, _medias, pais_de
from motor.nucleo import MAX_R, MIN_R, jugar, jugar_ko, nuevo_partido, tanda_penales

MUNDIAL = "Mundial de Clubes"
CADA = 4                      # se juega cada 4 temporadas (temporada 4 = 2029)
ANIO_BASE = 2025              # la temporada 1 del simulador es 2026
GRUPOS = "ABCDEFGH"
RONDAS = ["Fase de grupos · fecha 1", "Fase de grupos · fecha 2", "Fase de grupos · fecha 3",
          "Octavos de final", "Cuartos de final", "Semifinales", "Final"]
CONFS = ["UEFA", "CONMEBOL", "AFC", "CAF", "CONCACAF", "OFC"]
ANFITRION = "CONCACAF"        # confederación del anfitrión (la sede 2029 todavía no está definida)
TORNEO_CONF = {"UEFA": "Champions League", "CONMEBOL": "Copa Libertadores", "AFC": "Champions League de Asia",
               "CAF": "Champions League de África", "CONCACAF": "Concacaf Champions Cup",
               "OFC": "Champions League de Oceanía"}
_FIX3 = [[(0, 1), (2, 3)], [(3, 0), (1, 2)], [(0, 2), (3, 1)]]       # una rueda de un grupo de 4
_TEMP_SORTEO = 5.0            # cuánto pesa la media al sortear un campeón continental

# Campeones continentales reales de 2025 y ranking CONMEBOL real de 2025 (puntos para el Mundial 2029)
CAMPEONES_2025 = {"UEFA": "Paris Saint-Germain", "CONMEBOL": "Flamengo", "AFC": "Al-Ahli",
                  "CAF": "Pyramids", "CONCACAF": "Cruz Azul", "OFC": "Auckland City"}
PUNTOS_2025 = {"Palmeiras": 57, "Flamengo": 55, "Liga de Quito": 44, "Estudiantes (LP)": 37, "Racing": 35,
               "São Paulo": 25, "Peñarol": 25, "Vélez": 24, "Cerro Porteño": 24, "River Plate": 23,
               "Universitario": 22, "Independiente del Valle": 21, "Universidad de Chile": 13}


# ---------------------------------------------------------------- calendario de ediciones
def es_temporada_mundial(temp):
    return temp % CADA == 0


def anio_de(temp):
    return ANIO_BASE + temp


def proxima_temporada(temp):
    """Temporada (la actual o una posterior) en la que se juega el Mundial."""
    return temp if es_temporada_mundial(temp) else (temp // CADA + 1) * CADA


def pais_club(nombre):
    return PAIS_MUNDIAL.get(nombre) or pais_de(nombre)


# ---------------------------------------------------------------- estado
def nuevo_mundial():
    """Mundial de la temporada, todavía sin sortear (solo se sortea en temporadas múltiplo de 4)."""
    return {"sorteado": False, "anio": None, "temp": None, "nombres": [], "conf": {}, "via": {}, "r": {},
            "grupos": [], "gstats": {}, "ronda": 0, "total": len(RONDAS), "log": [], "cuadro": [],
            "campeon": None, "subcampeon": None}


def hay_mundial(S):
    return bool(S.get("mundial", {}).get("sorteado"))


def mundial_terminado(S):
    """Cierto si esta temporada no hay Mundial o ya se jugó la final."""
    M = S.get("mundial")
    return (not M) or (not M["sorteado"]) or M["ronda"] >= M["total"]


def ciclo(S):
    """Campeones continentales y puntos del ranking CONMEBOL por año (arranca con los de 2025)."""
    c = S.get("mundial_ciclo")
    if c is None:
        c = {"campeones": {ANIO_BASE: dict(CAMPEONES_2025)}, "puntos": {ANIO_BASE: dict(PUNTOS_2025)}}
        S["mundial_ciclo"] = c
    return c


def medias(S):
    """Media actual de todos los clubes que pueden jugar el Mundial."""
    out = dict(_medias(S))
    out.update(S.setdefault("rating_mundial", dict(MEDIA_MUNDIAL)))
    return out


def actualizar_ratings(S, rng):
    """Clubes de otros continentes: su media cambia un poco cada año (vuelve hacia la de su club)."""
    rm = S.setdefault("rating_mundial", dict(MEDIA_MUNDIAL))
    for n, base in MEDIA_MUNDIAL.items():
        x = rm.get(n, base)
        rm[n] = float(np.clip(x + 0.3 * (base - x) + rng.normal(0, 1.5), MIN_R, MAX_R))


# ---------------------------------------------------------------- cierre de temporada
def _sortear_campeon(rng, conf, rm):
    clubes = clubes_de(conf)
    if not clubes:
        return None
    x = np.array([rm.get(n, MEDIA_MUNDIAL[n]) for n in clubes], dtype=float)
    p = np.exp((x - x.max()) / _TEMP_SORTEO)
    return clubes[int(rng.choice(len(clubes), p=p / p.sum()))]


def _puntos_conmebol(S):
    """Puntos del ranking de la temporada que termina: victoria 3, empate 1 (Sudamericana, la mitad)."""
    pts = {}
    for clave, peso in (("lib", 1.0), ("sud", 0.5)):
        for p in S.get("int", {}).get(clave, {}).get("log", []):
            for n, f, c in ((p["local"], p["gl"], p["gv"]), (p["visita"], p["gv"], p["gl"])):
                pts[n] = pts.get(n, 0.0) + peso * (3 if f > c else 1 if f == c else 0)
    return {n: round(v, 1) for n, v in pts.items()}


def cerrar_temporada(S, rng):
    """Al terminar la temporada: registra los campeones continentales del año y los puntos del
    ranking CONMEBOL (hay que llamarla antes de armar las copas internacionales siguientes)."""
    c = ciclo(S)
    y = anio_de(S["temp"])
    rm = S.setdefault("rating_mundial", dict(MEDIA_MUNDIAL))
    camp = {"CONMEBOL": S.get("int", {}).get("lib", {}).get("campeon")}
    for conf in ("UEFA", "AFC", "CAF", "CONCACAF", "OFC"):
        camp[conf] = _sortear_campeon(rng, conf, rm)
    c["campeones"][y] = camp
    c["puntos"][y] = _puntos_conmebol(S)


# ---------------------------------------------------------------- clasificación
def _puntos_ciclo(S, anios):
    tot = {}
    for y in anios:
        for n, v in ciclo(S)["puntos"].get(y, {}).items():
            tot[n] = tot.get(n, 0.0) + v
    return tot


def calcular_clasificados(S, temp):
    """Los 32 clasificados de la edición de la temporada `temp`, según lo registrado hasta ahora:
    lista de dicts {club, conf, via}. Antes de que termine el ciclo es una proyección."""
    C = ciclo(S)
    y0 = anio_de(temp)
    anios = list(range(y0 - CADA, y0))
    med = medias(S)
    usados, out = set(), []
    puntos = _puntos_ciclo(S, anios)
    pool_conmebol = set(puntos) | set(S["nombres"])
    pool_conmebol |= set(PAIS_EXT)

    def llenar(conf, cupo, candidatos, via_directo, via_rank):
        lista, cuenta = [], Counter()
        for y in anios:                                           # campeones del ciclo
            club = C["campeones"].get(y, {}).get(conf)
            if club and club not in usados and len(lista) < cupo:
                lista.append((club, f"Campeón {TORNEO_CONF[conf]} {y}"))
                usados.add(club)
                cuenta[pais_club(club)] += 1
        for tope in (2, 99):                                      # ranking: máx. 2 por país (si no alcanza, sin tope)
            for club in candidatos:
                if len(lista) >= cupo:
                    break
                if club in usados or cuenta[pais_club(club)] >= tope:
                    continue
                lista.append((club, via_rank))
                usados.add(club)
                cuenta[pais_club(club)] += 1
        out.extend({"club": n, "conf": conf, "via": v} for n, v in lista)

    for conf in CONFS:
        if conf == "CONMEBOL":
            cand = sorted(pool_conmebol, key=lambda n: (-puntos.get(n, 0.0), -med.get(n, 0.0)))
            via = "Ranking CONMEBOL"
        else:
            cand = sorted(clubes_de(conf), key=lambda n: -med.get(n, 0.0))
            via = f"Ranking {conf}"
        llenar(conf, CUPOS_2029[conf], cand, "", via)
    # anfitrión: el mejor club de su confederación que todavía no clasificó
    for club in sorted(clubes_de(ANFITRION), key=lambda n: -med.get(n, 0.0)):
        if club not in usados:
            out.append({"club": club, "conf": ANFITRION, "via": "Anfitrión"})
            usados.add(club)
            break
    return out


# ---------------------------------------------------------------- sorteo
def _valido(M, grupo):
    cont = Counter(M["conf"][n] for n in grupo)
    return all(v <= (2 if c == "UEFA" else 1) for c, v in cont.items())


def _sorteo_grupos(rng, M):
    """8 grupos de 4: 4 bombos por media, un club de cada bombo por grupo; misma confederación no
    comparte grupo (UEFA puede tener 2)."""
    orden = sorted(M["nombres"], key=lambda n: -M["r"][n])
    bombos = [orden[i * 8:(i + 1) * 8] for i in range(4)]
    for _ in range(3000):
        grupos = [[] for _ in range(8)]
        ok = True
        for b in bombos:
            libres = list(range(8))
            for n in [str(x) for x in rng.permutation(b)]:
                posibles = [g for g in libres if _valido(M, grupos[g] + [n])]
                if not posibles:
                    ok = False
                    break
                g = int(rng.choice(posibles))
                grupos[g].append(n)
                libres.remove(g)
            if not ok:
                break
        if ok:
            return grupos
    return [[str(x) for x in rng.permutation(b)] for b in zip(*bombos)]      # sin restricciones


def sortear_mundial(S, rng):
    """Arma el Mundial de la temporada en curso: clasificados y grupos."""
    cl = calcular_clasificados(S, S["temp"])
    med = medias(S)
    M = nuevo_mundial()
    M["sorteado"], M["temp"], M["anio"] = True, S["temp"], anio_de(S["temp"])
    M["nombres"] = [x["club"] for x in cl]
    M["conf"] = {x["club"]: x["conf"] for x in cl}
    M["via"] = {x["club"]: x["via"] for x in cl}
    M["r"] = {n: float(med.get(n, 60.0)) for n in M["nombres"]}
    M["grupos"] = _sorteo_grupos(rng, M)
    M["gstats"] = {n: {"pj": 0, "g": 0, "e": 0, "p": 0, "gf": 0, "gc": 0} for n in M["nombres"]}
    return M


# ---------------------------------------------------------------- juego
def tabla_grupo(M, g):
    """Tabla del grupo g (lista de dicts ordenada por Pts, DG, GF y, a igualdad, la media)."""
    filas = []
    for n in M["grupos"][g]:
        s = M["gstats"][n]
        filas.append({"Equipo": n, "PJ": s["pj"], "G": s["g"], "E": s["e"], "P": s["p"], "GF": s["gf"],
                      "GC": s["gc"], "DG": s["gf"] - s["gc"], "Pts": 3 * s["g"] + s["e"]})
    filas.sort(key=lambda x: (x["Pts"], x["DG"], x["GF"], M["r"][x["Equipo"]]), reverse=True)
    return filas


def _sumar(M, n, gf, gc):
    s = M["gstats"][n]
    s["pj"] += 1
    s["gf"] += gf
    s["gc"] += gc
    s["g"] += gf > gc
    s["e"] += gf == gc
    s["p"] += gf < gc


def _armar_octavos(M):
    """1° vs 2° de otro grupo (A-B, C-D, E-F, G-H y las revanchas B-A, D-C, F-E, H-G); los cruces van de
    a pares, así que cuartos y semis quedan como en el Mundial real."""
    t = [[x["Equipo"] for x in tabla_grupo(M, g)] for g in range(8)]
    pares = [(0, 1), (2, 3), (4, 5), (6, 7), (1, 0), (3, 2), (5, 4), (7, 6)]
    M["cuadro"] = [[{"a": t[ga][0], "b": t[gb][1], "p": None, "gana": None} for ga, gb in pares]]


def simular_ronda_mundial(S, P, rng):
    """Juega la ronda que sigue: una fecha de grupos o una ronda de eliminación directa."""
    M = S["mundial"]
    if not M["sorteado"] or M["ronda"] >= M["total"]:
        return
    k = M["ronda"]
    r = M["r"]
    if k < 3:
        pares = [(g, M["grupos"][g][i], M["grupos"][g][j]) for g in range(8) for i, j in _FIX3[k]]
        gl, gv = jugar(rng, np.array([r[a] for _, a, _ in pares]), np.array([r[b] for _, _, b in pares]),
                       P["sorpresa"], localia=0.0)
        for (g, a, b), x, y in zip(pares, gl, gv):
            x, y = int(x), int(y)
            M["log"].append(nuevo_partido(MUNDIAL, k + 1, RONDAS[k], f"Grupo {GRUPOS[g]}", a, b, x, y,
                                          neutral=True))
            _sumar(M, a, x, y)
            _sumar(M, b, y, x)
        if k == 2:
            _armar_octavos(M)
    else:
        llaves = M["cuadro"][k - 3]
        gl, gv, gana_l, pen = jugar_ko(rng, np.array([r[m["a"]] for m in llaves]),
                                       np.array([r[m["b"]] for m in llaves]), P["sorpresa"], localia=0.0)
        for m, g1, g2, gl_, pe in zip(llaves, gl, gv, gana_l, pen):
            tanda = tanda_penales(rng, bool(gl_)) if pe else None
            m["gana"] = m["a"] if gl_ else m["b"]
            m["p"] = nuevo_partido(MUNDIAL, k + 1, RONDAS[k], RONDAS[k], m["a"], m["b"], g1, g2, tanda=tanda,
                                   gana=m["gana"], neutral=True)
            M["log"].append(m["p"])
        if k < M["total"] - 1:
            M["cuadro"].append([{"a": llaves[2 * j]["gana"], "b": llaves[2 * j + 1]["gana"], "p": None,
                                 "gana": None} for j in range(len(llaves) // 2)])
        else:
            M["campeon"] = llaves[0]["gana"]
            M["subcampeon"] = llaves[0]["b"] if llaves[0]["gana"] == llaves[0]["a"] else llaves[0]["a"]
    M["ronda"] += 1


def fase_actual(M):
    return "Terminado" if M["ronda"] >= M["total"] else RONDAS[M["ronda"]]


def partidos_ronda(M, n):
    """Cruces de la ronda n (1-7) como (local, visita, rotulo, comp), para el calendario."""
    if not M["sorteado"]:
        return []
    if n <= 3:
        return [(M["grupos"][g][i], M["grupos"][g][j], RONDAS[n - 1], f"Grupo {GRUPOS[g]}")
                for g in range(8) for i, j in _FIX3[n - 1]]
    if len(M["cuadro"]) >= n - 3:
        return [(m["a"], m["b"], RONDAS[n - 1], RONDAS[n - 1]) for m in M["cuadro"][n - 4]]
    return []

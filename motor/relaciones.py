"""Relaciones del manager (va en motor/relaciones.py). Sin Streamlit.

Cada relación va de 0 a 100 %:
  Globales (te siguen de club en club):  tapia, beligoy, toviggino, karma
  Del club que dirigís:                  hinchada, dirigencia, plantel, economia

Consecuencias (por ahora sólo estas dos; el resto se muestra pero todavía no cambia nada):
  * DIRIGENCIA baja de un umbral (según la dificultad): cada día jugado hay chance de que te echen.
  * PLANTEL por debajo de UMBRAL_CAMA: "te hacen la cama": el equipo rinde peor (menos goles a favor,
    más en contra y menos control del mediocampo), y eso empeora los resultados y la relación.

Cómo se mueven (sólo mientras sos DT del primer equipo): después de cada partido de tu club se compara
el resultado con el esperable según las medias de los dos equipos y la localía. Ganar un partido
difícil sube mucho; perder uno que parecía ganado baja mucho; los resultados esperables casi no
mueven nada. La hinchada y la dirigencia castigan un poco más las derrotas (tolerancia baja).
Las decisiones también cuentan: renunciar, dejar un club por otra oferta o que te echen bajan el karma.
"""

import hashlib

from motor.ofertas import medias_por_categoria, renunciar

ETIQUETAS = {"tapia": "Tapia", "beligoy": "Beligoy", "toviggino": "Toviggino", "karma": "Karma",
             "hinchada": "Hinchada", "dirigencia": "Dirigencia", "plantel": "Plantel", "economia": "Economía"}
GLOBALES = ("tapia", "beligoy", "toviggino", "karma")
DE_CLUB = ("hinchada", "dirigencia", "plantel", "economia")

# Relación inicial con Tapia, Beligoy y Toviggino según la reputación
INICIAL_AFA = {"Desconocido": 30, "Ex jugador de ascenso": 40, "Ex jugador profesional": 50, "Ex estrella": 65}
KARMA_INICIAL = 50

UMBRAL_DESPIDO = {"Fácil": 22, "Normal": 30, "Difícil": 40}   # dirigencia por debajo de esto: te pueden echar
MIN_DIAS_DT = 8            # días jugados como DT del primer equipo antes de que puedan echarte
UMBRAL_CAMA = 35           # plantel por debajo de esto: te hacen la cama (más fuerte cuanto más abajo)
CAMA_ATAQUE, CAMA_DEFENSA, CAMA_CONTROL = 0.18, 0.18, 4.0   # efecto máximo (plantel en 0 %)
LOCALIA = 4.5              # misma ventaja de local que el motor de partidos

REVERSION = 0.012          # por partido, cuánto vuelven hinchada/dirigencia/plantel hacia su valor normal
BASE = {"hinchada": 50.0, "dirigencia": 55.0, "plantel": 50.0}

KARMA_RENUNCIAR = -5
KARMA_DEJAR_CLUB = -6      # aceptar otra oferta estando en un club
KARMA_DESPIDO = -3


def _tope(x):
    return max(0.0, min(100.0, float(x)))


def descripcion(valor):
    if valor is None:
        return "—"
    return ("Pésima" if valor < 15 else "Mala" if valor < 35 else "Regular" if valor < 55
            else "Buena" if valor < 75 else "Excelente")


# ---- Estado ---------------------------------------------------------------------------------------
def relaciones_iniciales(reputacion):
    base = INICIAL_AFA.get(reputacion, 40)
    return {"tapia": float(base), "beligoy": float(base), "toviggino": float(base), "karma": float(KARMA_INICIAL),
            "hinchada": None, "dirigencia": None, "plantel": None, "economia": None}


def asegurar(M):
    """Sesiones viejas (sin relaciones) se completan con los valores iniciales."""
    if "rel" not in M:
        M["rel"] = relaciones_iniciales(M.get("reputacion"))
    M.setdefault("rel_log", [])
    M.setdefault("partidos_vistos", set())
    M.setdefault("dias_dt", 0)
    return M["rel"]


def media_de(S, club):
    """Media del club (ligas argentinas, copas CONMEBOL o Mundial); None si no se encuentra."""
    for meds in medias_por_categoria(S).values():
        if club in meds:
            return meds[club]
    for C in (S.get("int") or {}).values():
        if club in (C.get("r") or {}):
            return float(C["r"][club])
    M = S.get("mundial") or {}
    if club in (M.get("r") or {}):
        return float(M["r"][club])
    return None


def economia_inicial(media, club):
    """Clubes más grandes, más plata; con una variación fija por club."""
    ruido = int(hashlib.md5(club.encode("utf-8")).hexdigest()[:4], 16) % 21 - 10
    return _tope(15 + (media - 20) * 1.1 + ruido)


def entrar_club(S, M, club):
    """Relaciones del club al que llegás: arrancás neutral (la dirigencia te contrata, así que un poco mejor)."""
    rel = asegurar(M)
    media = media_de(S, club)
    rel.update(hinchada=50.0, dirigencia=60.0, plantel=50.0,
               economia=economia_inicial(media if media is not None else 50.0, club))
    M["dias_dt"] = 0


def salir_club(M):
    rel = asegurar(M)
    rel.update(hinchada=None, dirigencia=None, plantel=None, economia=None)
    M["dias_dt"] = 0


def cambiar(M, clave, delta):
    rel = asegurar(M)
    if rel.get(clave) is not None:
        rel[clave] = _tope(rel[clave] + delta)


# ---- Partidos -------------------------------------------------------------------------------------
def clave_partido(p):
    return (p["liga"], p["fecha"], p["comp"], p["rotulo"], p["local"], p["visita"])


# Puntos esperables por partido según la diferencia de media (localía incluida), medidos con el propio
# motor de partidos (nivel de sorpresas 6, el valor por defecto): (diferencia, puntos).
_PUNTOS_ESPERADOS = [(-40, 0.50), (-35, 0.54), (-30, 0.59), (-25, 0.66), (-20, 0.75), (-15, 0.87), (-10, 1.01),
                     (-5, 1.17), (0, 1.35), (5, 1.53), (10, 1.71), (15, 1.87), (20, 2.00), (25, 2.10),
                     (30, 2.19), (35, 2.25), (40, 2.29)]


def _esperado(dif):
    """Puntos esperables (0 a 3) de un partido según la diferencia de media (con la localía incluida)."""
    t = _PUNTOS_ESPERADOS
    if dif <= t[0][0]:
        return t[0][1]
    if dif >= t[-1][0]:
        return t[-1][1]
    for (x0, y0), (x1, y1) in zip(t, t[1:]):
        if x0 <= dif <= x1:
            return y0 + (y1 - y0) * (dif - x0) / (x1 - x0)


def aplicar_partido(S, M, p):
    """Mueve las relaciones según un partido jugado por el club (sólo como DT del primer equipo).
    Devuelve el texto del cambio (para el registro)."""
    rel = asegurar(M)
    club = M["club"]
    local = p["local"] == club
    rival = p["visita"] if local else p["local"]
    gf, gc = (p["gl"], p["gv"]) if local else (p["gv"], p["gl"])
    if gf > gc:
        pts, res = 3.0, "Ganaste"
    elif gf < gc:
        pts, res = 0.0, "Perdiste"
    elif p.get("pen"):                                   # empate definido por penales
        gano = p.get("gana") == club
        pts, res = (2.0, "Ganaste por penales") if gano else (1.0, "Perdiste por penales")
    else:
        pts, res = 1.0, "Empataste"
    ma, mr = media_de(S, club), media_de(S, rival)
    dif = (50.0 if ma is None else ma) - (50.0 if mr is None else mr)
    dif += 0 if p.get("neutral") else (LOCALIA if local else -LOCALIA)
    sorpresa = (pts - _esperado(dif)) / 3.0              # -1 (lo peor) a +1 (lo mejor)
    neg = 1.10 if sorpresa < 0 else 1.0                  # castigan un poco más las derrotas
    d = {"plantel": 3.5 * sorpresa,
         "hinchada": 6.0 * sorpresa * neg,
         "dirigencia": 5.5 * sorpresa * neg * (1.25 if (sorpresa < 0 and (rel["economia"] or 50) < 30) else 1.0),
         "economia": 0.6 * sorpresa}
    for k in ("hinchada", "dirigencia", "plantel"):      # con el tiempo todo vuelve de a poco a lo normal
        cambiar(M, k, REVERSION * (BASE[k] - rel[k]))
    for k, v in d.items():
        cambiar(M, k, v)
    for k in ("tapia", "beligoy", "toviggino"):
        cambiar(M, k, 0.4 * sorpresa * (1.0 if sorpresa > 0 else 0.5))
    return (f"{res} {gf}-{gc} vs {rival}: Plantel {d['plantel']:+.0f}, Hinchada {d['hinchada']:+.0f}, "
            f"Dirigencia {d['dirigencia']:+.0f}")


# ---- Consecuencias --------------------------------------------------------------------------------
def efecto_cama(M):
    """0 (el plantel te banca) a 1 (todos en contra): cuánto te hacen la cama. Sólo como DT del primer equipo."""
    rel = M.get("rel") or {}
    if not M.get("club") or M.get("rol") != "primer_equipo" or rel.get("plantel") is None:
        return 0.0
    return _tope((UMBRAL_CAMA - rel["plantel"]) / UMBRAL_CAMA * 100.0) / 100.0


def con_cama(tactica, k):
    """Táctica (ataque, defensa, control) ya afectada por el plantel: la cama resta ataque y control y suma
    goles en contra."""
    atk, dfn, ctl = tactica[:3]
    return (atk * (1 - CAMA_ATAQUE * k), dfn * (1 + CAMA_DEFENSA * k), ctl - CAMA_CONTROL * k)


def umbral_despido(M):
    return UMBRAL_DESPIDO.get(M.get("dificultad"), UMBRAL_DESPIDO["Normal"])


def despedir(S, M):
    """La dirigencia te echa: quedás libre, el club no te vuelve a llamar por un tiempo y baja el karma."""
    club, rel = M["club"], asegurar(M)
    valor = rel["dirigencia"]
    renunciar(M)
    for h in reversed(M["historial_clubes"]):
        if h["club"] == club and h["hasta"] == M["hoy"]:
            h["despedido"] = True
            break
    salir_club(M)
    cambiar(M, "karma", KARMA_DESPIDO)
    return f"La dirigencia de {club} te echó: la relación con los dirigentes cayó a {valor:.0f}%."


def revisar_despido(S, M, rng):
    """Una vez por día jugado: con la dirigencia por debajo del umbral hay chance de que te echen.
    Devuelve el texto si te echaron, o None."""
    rel = asegurar(M)
    if not M.get("club") or M.get("rol") != "primer_equipo" or rel["dirigencia"] is None:
        return None
    u = umbral_despido(M)
    if M["dias_dt"] < MIN_DIAS_DT or rel["dirigencia"] >= u:
        return None
    p = min(0.6, 0.06 + 0.40 * (u - rel["dirigencia"]) / u)
    return despedir(S, M) if rng.random() < p else None

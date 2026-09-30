"""Motor: piezas genéricas de la simulación (no dependen de ninguna liga).

Generación de goles, penales, fixtures todos contra todos, tablas de posiciones
y cruces de eliminatorias. Solo usa numpy y pandas (nada de Streamlit).
"""

import numpy as np
import pandas as pd

ESCALA = 20.0        # cuánto pesa la diferencia de medias en los goles esperados
LOCALIA = 4.5        # ventaja fija de local (en puntos de media)
GOLES_BASE = 1.16    # goles esperados por equipo en un partido parejo (~2.2 por partido)
DISPERSION = 16.0    # menor valor = más partidos "raros" (0-0 seguidos de goleadas)
RHO_DC = -0.05       # corrección Dixon-Coles: un poco más de 0-0 y 1-1 (fútbol argentino)
TOPE_GOLES = 10      # marcadores posibles por equipo: 0..9
_TOT = np.add.outer(np.arange(TOPE_GOLES), np.arange(TOPE_GOLES))
# Los marcadores muy abultados quedan como rareza (6+ goles ≈ 0,8% de los partidos)
AMORTIGUAR = np.where(_TOT >= 8, 0.06, np.where(_TOT >= 6, 0.16, np.where(_TOT == 5, 0.75, 1.0)))
_LOG_FACT = np.concatenate([[0.0], np.cumsum(np.log(np.arange(1, TOPE_GOLES)))])
P_GOL_PENAL = 0.76   # probabilidad de convertir cada penal de la tanda
REVERSION = 0.10     # cuánto vuelven las medias hacia el promedio de su liga cada temporada
MIN_R, MAX_R = 20.0, 90.0
STATS = ("pj", "g", "e", "p", "gf", "gc")


# ----------------------------------------------------------------------------
# MOTOR COMÚN
# ----------------------------------------------------------------------------
def generar_fixture(n):
    """Todos contra todos, una vuelta (método de Berger). Lista de fechas.

    Las localías quedan balanceadas: cada equipo es local en la mitad de sus
    partidos (±1) y nunca juega más de 2 fechas seguidas de local o de visitante.
    """
    impar = n % 2 == 1
    m = n + 1 if impar else n
    fechas = []
    for r in range(m - 1):
        pares = [(r, m - 1) if r % 2 == 0 else (m - 1, r)]
        for k in range(1, m // 2):
            x, y = (r + k) % (m - 1), (r - k) % (m - 1)
            pares.append((x, y) if k % 2 == 1 else (y, x))
        if impar:
            pares = [p for p in pares if m - 1 not in p]
        fechas.append(pares)
    return fechas


def generar_fixture_interzonal(rng, za, zb, rondas):
    """`rondas` fechas cruzando las zonas A y B: cada equipo enfrenta a `rondas`
    rivales distintos de la otra zona (rotación tipo Latin square, sin repetir
    cruces) y es local en exactamente la mitad de esas fechas: la zona local
    alterna fecha a fecha, así que con `rondas` par cada equipo termina 50/50."""
    n = len(za)
    orden_b = rng.permutation(n)
    fechas = []
    for r in range(rondas):
        a_local = r % 2 == 0
        pares = []
        for i in range(n):
            x, y = int(za[i]), int(zb[int(orden_b[(i + r) % n])])
            pares.append((x, y) if a_local else (y, x))
        fechas.append(pares)
    return fechas


def ultimas_localias(fechas, cuantas=2):
    """Condición (1 local, 0 visitante) de las últimas fechas de cada equipo."""
    prev = {}
    for pares in fechas[-cuantas:]:
        for a, b in pares:
            prev.setdefault(a, []).append(1)
            prev.setdefault(b, []).append(0)
    return prev


def puntaje_localias(fechas, previas, balance=None):
    """Penaliza rachas de 3+ fechas con la misma condición y desbalances local/visitante."""
    seq = {t: list(v) for t, v in previas.items()}
    ini = {t: len(v) for t, v in previas.items()}
    for pares in fechas:
        for a, b in pares:
            seq.setdefault(a, []).append(1)
            seq.setdefault(b, []).append(0)
    s = 0
    for t, q in seq.items():
        run = 1
        for i in range(1, len(q)):
            run = run + 1 if q[i] == q[i - 1] else 1
            if run > 2:
                s += 10 * (run - 2)
        nuevo = q[ini.get(t, 0):]
        total = (balance or {}).get(t, 0) + 2 * sum(nuevo) - len(nuevo)
        s += 3 * max(0, abs(total) - 1)
    return s


def balance_localias(fechas):
    """Partidos de local menos partidos de visitante de cada equipo."""
    bal = {}
    for pares in fechas:
        for a, b in pares:
            bal[a] = bal.get(a, 0) + 1
            bal[b] = bal.get(b, 0) - 1
    return bal


def fixture_revancha(rng, ids, H, previas, balance=None, intentos=300):
    """Una rueda entre `ids` respetando la revancha: si x fue local contra y antes,
    ahora es local y. Los cruces nuevos le dan la localía al que viene jugando menos
    de local. Entre los órdenes posibles elige el de localías más parejas."""
    base = generar_fixture(len(ids))
    mejor = None
    for t in range(intentos):
        perm = np.asarray(ids) if t == 0 else rng.permutation(ids)
        bal = dict(balance or {})
        fechas = []
        for pares in base:
            fecha = []
            for a, b in pares:
                x, y = int(perm[a]), int(perm[b])
                if H[x, y]:
                    x, y = y, x                                  # localía invertida
                elif not H[y, x] and bal.get(y, 0) < bal.get(x, 0):
                    x, y = y, x                                  # cruce nuevo: equilibra
                bal[x] = bal.get(x, 0) + 1
                bal[y] = bal.get(y, 0) - 1
                fecha.append((x, y))
            fechas.append(fecha)
        s = puntaje_localias(fechas, previas, balance)
        if mejor is None or s < mejor[0]:
            mejor = (s, fechas)
            if s == 0:
                break
    return mejor[1]


def jugar(rng, r_local, r_visita, sorpresa, escala=ESCALA, localia=LOCALIA):
    """Simula partidos (vectorizado). Devuelve goles local y visitante.

    sorpresa = desvío (en puntos de media) de la "forma del día": en cada
    partido cada equipo rinde un poco por encima o por debajo de su media.
    """
    r_local = np.asarray(r_local, float)
    r_visita = np.asarray(r_visita, float)
    forma = rng.normal(0.0, sorpresa, r_local.shape) - rng.normal(0.0, sorpresa, r_local.shape)
    d_ef = (r_local - r_visita) + forma + localia
    d_ef = 28.0 * np.tanh(d_ef / 28.0)          # las diferencias enormes no se disparan
    # "Ritmo" del partido (media 1): hay partidos cerrados (0-0, 1-0) y otros
    # abiertos (3-2). Los resultados muy abultados quedan como rareza.
    ritmo = rng.gamma(DISPERSION, 1.0 / DISPERSION, size=d_ef.shape)
    lam_l = GOLES_BASE * ritmo * np.exp(d_ef / (2 * escala))
    lam_v = GOLES_BASE * ritmo * np.exp(-d_ef / (2 * escala))
    # Matriz de probabilidades de cada marcador: Poisson + Dixon-Coles + amortiguación
    k = np.arange(TOPE_GOLES)
    pl = np.exp(k * np.log(lam_l[..., None]) - lam_l[..., None] - _LOG_FACT)
    pv = np.exp(k * np.log(lam_v[..., None]) - lam_v[..., None] - _LOG_FACT)
    M = pl[..., :, None] * pv[..., None, :]
    M[..., 0, 0] *= 1 - lam_l * lam_v * RHO_DC
    M[..., 0, 1] *= 1 + lam_l * RHO_DC
    M[..., 1, 0] *= 1 + lam_v * RHO_DC
    M[..., 1, 1] *= 1 - RHO_DC
    M = np.clip(M, 0.0, None) * AMORTIGUAR
    acum = np.cumsum(M.reshape(*d_ef.shape, TOPE_GOLES ** 2), axis=-1)
    u = rng.random(d_ef.shape)[..., None] * acum[..., -1:]
    idx = (acum < u).sum(axis=-1)
    return idx // TOPE_GOLES, idx % TOPE_GOLES


def tanda_penales(rng, gana_local):
    """Tanda de penales (patea primero el local) coherente con el ganador ya definido.

    Devuelve dos listas de bool (convertido / errado) para local y visitante.
    """
    while True:
        tl, tv = [], []
        for i in range(5):
            tl.append(bool(rng.random() < P_GOL_PENAL))
            if sum(tl) > sum(tv) + (5 - len(tv)) or sum(tv) > sum(tl) + (5 - len(tl)):
                break
            tv.append(bool(rng.random() < P_GOL_PENAL))
            if sum(tl) > sum(tv) + (5 - len(tv)) or sum(tv) > sum(tl) + (5 - len(tl)):
                break
        while sum(tl) == sum(tv):                   # muerte súbita
            tl.append(bool(rng.random() < P_GOL_PENAL))
            tv.append(bool(rng.random() < P_GOL_PENAL))
        if (sum(tl) > sum(tv)) == bool(gana_local):
            return tl, tv


def nuevo_partido(liga, fecha, rotulo, comp, local, visita, gl, gv,
                  tanda=None, gana=None, neutral=False):
    """Registro de un partido jugado (para resultados, fichas, buscador y cuadros)."""
    gl, gv = int(gl), int(gv)
    if gana is None:
        gana = local if gl > gv else visita if gv > gl else None
    return {
        "liga": liga, "fecha": int(fecha), "rotulo": rotulo, "comp": comp,
        "local": local, "visita": visita, "gl": gl, "gv": gv, "gana": gana,
        "tanda": tanda, "pen": (sum(tanda[0]), sum(tanda[1])) if tanda else None,
        "neutral": neutral,
    }


def jugar_ko(rng, r_loc, r_vis, sorpresa, localia=LOCALIA):
    """Partido único eliminatorio SIN alargue: si empatan, penales directos.

    Devuelve goles local, goles visitante, si ganó el local y si hubo penales.
    """
    gl, gv = jugar(rng, r_loc, r_vis, sorpresa, localia=localia)
    p_loc = np.clip(0.5 + (np.asarray(r_loc, float) - np.asarray(r_vis, float)) / 400, 0.35, 0.65)
    pen_local = rng.random(np.shape(gl)) < p_loc
    gana_local = np.where(gl != gv, gl > gv, pen_local)
    return gl, gv, gana_local, gl == gv


def jugar_ko_posicion(rng, r_loc, r_vis, sorpresa, localia=LOCALIA):
    """Partido único del reducido del Federal A (menos la final): el local ya es el
    mejor ubicado en la tabla, y si empatan gana directamente el local (sin penales;
    es decir, gana el que quedó mejor en la tabla)."""
    gl, gv = jugar(rng, r_loc, r_vis, sorpresa, localia=localia)
    gana_local = gl >= gv
    return gl, gv, gana_local, gl == gv


def jugar_reducido_federal(rng, r, A, B, sorpresa, final):
    """Cruce del reducido del Federal A: A siempre es el mejor ubicado (cruces_mejor_peor
    ya lo deja así). En cuartos y semis juega de local y el empate lo gana él; la final
    es en cancha neutral y el empate se define por penales."""
    if final:
        gl, gv, gana_local, pen = jugar_ko(rng, r[A["id"]], r[B["id"]], sorpresa, localia=0.0)
    else:
        gl, gv, gana_local, pen = jugar_ko_posicion(rng, r[A["id"]], r[B["id"]], sorpresa)
    gan = {k: np.where(gana_local, A[k], B[k]) for k in A}
    per = {k: np.where(gana_local, B[k], A[k]) for k in A}
    return A, B, gl, gv, gan, per, pen


def sumar_partidos(E, h, a, gh, ga):
    """Actualiza las estadísticas de la liga E (dict con arrays de STATS)."""
    E["pj"][h] += 1
    E["pj"][a] += 1
    E["gf"][h] += gh
    E["gc"][h] += ga
    E["gf"][a] += ga
    E["gc"][a] += gh
    E["g"][h] += (gh > ga)
    E["g"][a] += (ga > gh)
    E["p"][h] += (gh < ga)
    E["p"][a] += (ga < gh)
    E["e"][h] += (gh == ga)
    E["e"][a] += (gh == ga)


def df_stats(nombres, r, v, ids):
    """Tabla ordenada de los equipos `ids` (con columna interna 'id')."""
    ids = np.asarray(ids)
    df = pd.DataFrame({
        "id": ids,
        "Equipo": [nombres[i] for i in ids],
        "PJ": v["pj"][ids], "G": v["g"][ids], "E": v["e"][ids], "P": v["p"][ids],
        "GF": v["gf"][ids], "GC": v["gc"][ids],
    })
    df["DG"] = df["GF"] - df["GC"]
    df["Pts"] = 3 * df["G"] + df["E"]
    df["Media"] = np.asarray(r)[ids].round(1)
    return df.sort_values(["Pts", "DG", "GF"], ascending=False).reset_index(drop=True)


# ----------------------------------------------------------------------------
# MOTOR PRIMERA NACIONAL
# ----------------------------------------------------------------------------
# Un "bloque" es un dict de arrays (n, k) con las claves:
#   id (equipo), zona (0 Campeonato / 1 Intermedia), pts (puntos en su zona de la
#   fase 2) y seed (orden de mérito 1-12). Sirve tanto para un cuadro real (n=1)
#   como para miles de simulaciones a la vez.
def unir(T1, T2):
    return {k: np.concatenate([T1[k], T2[k]], axis=1) for k in T1}


def cruces_mejor_peor(T):
    """Ordena por mérito y cruza el mejor con el peor (1 vs último, 2 vs anteúltimo...)."""
    idx = np.argsort(T["seed"], axis=1)
    T = {k: np.take_along_axis(v, idx, axis=1) for k, v in T.items()}
    m = T["id"].shape[1] // 2
    A = {k: v[:, :m] for k, v in T.items()}
    B = {k: v[:, ::-1][:, :m] for k, v in T.items()}
    return A, B


def a_es_local(A, B):
    """Localía del reducido.

    1) Campeonato vs Intermedia: siempre local el de Campeonato.
    2) Misma zona: local el que sumó más puntos en esa zona (empate: mejor posición).
    """
    a_camp = A["zona"] == 0
    a_mas_pts = (A["pts"] > B["pts"]) | ((A["pts"] == B["pts"]) & (A["seed"] < B["seed"]))
    return np.where(A["zona"] != B["zona"], a_camp, a_mas_pts)


def ko_jugar(rng, r, A, B, sorpresa):
    """Juega los cruces A vs B (partido único, penales directos si empatan)."""
    a_loc = a_es_local(A, B)
    loc = {k: np.where(a_loc, A[k], B[k]) for k in A}
    vis = {k: np.where(a_loc, B[k], A[k]) for k in A}
    gl, gv, gana_local, pen = jugar_ko(rng, r[loc["id"]], r[vis["id"]], sorpresa)
    gan = {k: np.where(gana_local, loc[k], vis[k]) for k in A}
    per = {k: np.where(gana_local, vis[k], loc[k]) for k in A}
    return loc, vis, gl, gv, gan, per, pen


def _fila_historial(SB, instancia, loc, vis, gl, gv, definicion):
    nom = SB["nombres"]
    return pd.DataFrame({
        "Instancia": instancia,
        "Local": [nom[i] for i in loc], "GL": gl, "GV": gv,
        "Visitante": [nom[i] for i in vis], "Definición": definicion,
    })
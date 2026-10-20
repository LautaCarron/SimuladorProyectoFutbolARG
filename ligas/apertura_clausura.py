"""Primera División · formato APERTURA Y CLAUSURA CON LLAVES (como en la vida real). Va en ligas/apertura_clausura.py.

Dos torneos cortos, cada uno con:
  * Etapa regular (15 fechas): los 30 equipos se reparten en dos zonas de 15 (A y B). Se juega todos contra
    todos dentro de la zona (14 fechas: cada equipo descansa una vez) y, en la fecha en que descansa, juega un
    "clásico" interzonal contra el que descansa en la otra zona. Así todos juegan las 15 fechas.
  * Llaves: los 8 primeros de cada zona (16 equipos) juegan octavos, cuartos, semifinales y final a partido
    único (el mejor ubicado de local; la final, en cancha neutral; si empatan, penales).
El campeón de cada torneo es el ganador de la final. Además hay una TABLA ANUAL con los puntos de las dos
etapas regulares (las llaves no suman): sus posiciones definen la copa, la promoción y los descensos, y su
primero es el "Campeón de Liga" (el título de la temporada para la Supercopa y el historial).

Estado: S["ac"] (ver nueva()). Las fechas se agregan a S["fechas"] a medida que se conocen (las llaves, recién
cuando termina la ronda anterior), así que el fixture y el calendario funcionan igual que en los demás formatos.
"""

import numpy as np

from motor.incidentes import revisar_liga
from motor.nucleo import (
    LOCALIA,
    STATS,
    df_stats,
    generar_fixture,
    jugar,
    jugar_ko,
    mods_ids,
    nuevo_partido,
    sumar_partidos,
    tanda_penales,
)

REG = 15                       # fechas de la etapa regular de cada torneo
RONDAS = ["Octavos de final", "Cuartos de final", "Semifinales", "Final"]
POR_TORNEO = REG + len(RONDAS)  # 19
TOTAL = 2 * POR_TORNEO          # 38
NOMBRES = ["Apertura", "Clausura"]
CLASIFICAN = 8                 # por zona
LIGA = "Primera División"


# ---- Calendario del formato -----------------------------------------------------------------------
def etapa(n):
    """(torneo, k) de la fecha n (1-based): k < REG es regular; después, la ronda de llaves k - REG."""
    return divmod(n - 1, POR_TORNEO)


def rotulo(n):
    t, k = etapa(n)
    return f"{NOMBRES[t]} · Fecha {k + 1}" if k < REG else f"{NOMBRES[t]} · {RONDAS[k - REG]}"


def competencia(S, n, x, y):
    """Nombre de la competencia de un partido de la fecha n entre los equipos x e y (ids)."""
    t, k = etapa(n)
    if k >= REG:
        return f"{NOMBRES[t]} · {RONDAS[k - REG]}"
    zd = S["ac"]["zona_de"]
    return f"{NOMBRES[t]} · " + ("Interzonal" if zd[x] != zd[y] else f"Zona {'AB'[zd[x]]}")


# ---- Armado ----------------------------------------------------------------------------------------
def _fixture_regular(zA, zB):
    """15 fechas: todos contra todos dentro de cada zona y, en cada fecha, el clásico interzonal de los que descansan."""
    fa, fb = generar_fixture(len(zA)), generar_fixture(len(zB))
    fechas = []
    for r in range(len(fa)):
        pares = [(int(zA[x]), int(zA[y])) for x, y in fa[r]] + [(int(zB[x]), int(zB[y])) for x, y in fb[r]]
        libA = next(i for i in range(len(zA)) if all(i not in p for p in fa[r]))
        libB = next(i for i in range(len(zB)) if all(i not in p for p in fb[r]))
        a, b = int(zA[libA]), int(zB[libB])
        pares.append((a, b) if r % 2 == 0 else (b, a))
        fechas.append(pares)
    return fechas


def nueva(S, perm):
    """Arma el formato para la temporada (perm: orden al azar de los 30 equipos). Deja listas las fechas del Apertura."""
    n = len(S["nombres"])
    mitad = n // 2
    zA, zB = np.asarray(perm[:mitad], dtype=int), np.asarray(perm[mitad:], dtype=int)
    zona_de = np.zeros(n, dtype=int)
    zona_de[zB] = 1
    reg = _fixture_regular(zA, zB)
    S["ac"] = {
        "zonas": [zA, zB], "zona_de": zona_de, "reg": reg,
        "t_stats": [{k: np.zeros(n, dtype=int) for k in STATS} for _ in NOMBRES],
        "T": [{"nombre": nm, "cuadro": [], "campeon": None, "subcampeon": None, "clasif": None} for nm in NOMBRES],
        "campeon_liga": None,
    }
    S["fechas"] = [list(f) for f in reg]


# ---- Tablas ----------------------------------------------------------------------------------------
def tabla_zona(S, t, z):
    """Tabla de la zona z (0 = A, 1 = B) en el torneo t, con "Destino" = pasa a las llaves."""
    AC = S["ac"]
    df = df_stats(S["nombres"], S["r"], AC["t_stats"][t], AC["zonas"][z])
    df.insert(0, "Pos", df.index + 1)
    df["Destino"] = ["Pasa a las llaves" if p <= CLASIFICAN else "" for p in df["Pos"]]
    return df


def _semillas(S, t):
    """{id: puesto} de los 16 clasificados según lo hecho en la etapa regular del torneo t (para la localía)."""
    ids = [i for z in (0, 1) for i in tabla_zona(S, t, z).head(CLASIFICAN)["id"]]
    pts = {i: (3 * S["ac"]["t_stats"][t]["g"][i] + S["ac"]["t_stats"][t]["e"][i],
               S["ac"]["t_stats"][t]["gf"][i] - S["ac"]["t_stats"][t]["gc"][i]) for i in ids}
    orden = sorted(ids, key=lambda i: pts[i], reverse=True)
    return {int(i): k for k, i in enumerate(orden)}


def _armar_octavos(S, t):
    A = [int(i) for i in tabla_zona(S, t, 0).head(CLASIFICAN)["id"]]
    B = [int(i) for i in tabla_zona(S, t, 1).head(CLASIFICAN)["id"]]
    cruces = [(A[0], B[7]), (A[3], B[4]), (A[1], B[6]), (A[2], B[5]),
              (B[0], A[7]), (B[3], A[4]), (B[1], A[6]), (B[2], A[5])]       # el mejor sembrado de cada cruce, de local
    T = S["ac"]["T"][t]
    T["clasif"] = A + B
    T["cuadro"] = [[{"a": a, "b": b, "p": None, "gana": None} for a, b in cruces]]
    S["fechas"].append(list(cruces))


# ---- Cómo se juega cada fecha ------------------------------------------------------------------------
def simular(S, P, tabla_general):
    """Juega la fecha que sigue (regular o ronda de llaves). `tabla_general(S)` es la tabla anual de primera.py."""
    f = S["fecha"]
    if f >= TOTAL:
        return
    t, k = etapa(f + 1)
    AC, rng, nom, r = S["ac"], S["rng"], S["nombres"], S["r"]
    if k < REG:                                                       # ---- etapa regular
        pares = S["fechas"][f]
        h = np.array([x[0] for x in pares])
        a = np.array([x[1] for x in pares])
        gh, ga = jugar(rng, r[h], r[a], **P, **mods_ids(rng, nom, h, a))
        sumar_partidos(S, h, a, gh, ga)                               # tabla anual
        sumar_partidos(AC["t_stats"][t], h, a, gh, ga)                # tabla del torneo
        d = r[h] - r[a]
        S["sorpresas"] += int((((d >= 3) & (ga > gh)) | ((d <= -3) & (gh > ga))).sum())
        for x, y, g1, g2 in zip(h, a, gh, ga):
            S["log"].append(nuevo_partido(LIGA, f + 1, rotulo(f + 1), competencia(S, f + 1, x, y),
                                          nom[x], nom[y], g1, g2))
        revisar_liga(S, S["log"][-len(h):], rng)                      # suspensiones y sanciones (rarísimo)
        tabla = tabla_general(S)
        pos = np.zeros(len(nom), dtype=int)
        pos[tabla["id"].to_numpy()] = tabla["Pos"].to_numpy()
        S["pos_hist"].append((1, pos))
        S["fecha"] += 1
        if k == REG - 1:                                              # terminó la etapa regular: se arman las llaves
            _armar_octavos(S, t)
    else:                                                             # ---- llaves
        ronda = k - REG
        T = AC["T"][t]
        cruces = T["cuadro"][ronda]
        final = ronda == len(RONDAS) - 1
        a = np.array([m["a"] for m in cruces])
        b = np.array([m["b"] for m in cruces])
        gl, gv, gana_l, pen = jugar_ko(rng, r[a], r[b], P["sorpresa"], localia=0.0 if final else LOCALIA,
                                       **mods_ids(rng, nom, a, b))
        for m, g1, g2, gl_, pe in zip(cruces, gl, gv, gana_l, pen):
            tanda = tanda_penales(rng, bool(gl_)) if pe else None
            m["gana"] = m["a"] if gl_ else m["b"]
            m["p"] = nuevo_partido(LIGA, f + 1, rotulo(f + 1), f"{NOMBRES[t]} · {RONDAS[ronda]}",
                                   nom[m["a"]], nom[m["b"]], g1, g2, tanda=tanda, gana=nom[m["gana"]], neutral=final)
            S["log"].append(m["p"])
        S["fecha"] += 1
        if not final:
            sem = _semillas(S, t)
            sig = []
            for j in range(0, len(cruces), 2):
                x, y = cruces[j]["gana"], cruces[j + 1]["gana"]
                sig.append((x, y) if sem[x] < sem[y] else (y, x))     # de local, el mejor sembrado
            T["cuadro"].append([{"a": x, "b": y, "p": None, "gana": None} for x, y in sig])
            S["fechas"].append(list(sig))
        else:
            T["campeon"] = cruces[0]["gana"]
            T["subcampeon"] = cruces[0]["b"] if cruces[0]["gana"] == cruces[0]["a"] else cruces[0]["a"]
            if t == 0:                                                # sigue el Clausura: misma zona, localías al revés
                S["fechas"] += [[(v, l) for l, v in fecha] for fecha in AC["reg"]]
    if S["fecha"] >= TOTAL:
        AC["campeon_liga"] = nom[int(tabla_general(S)["id"].iloc[0])]

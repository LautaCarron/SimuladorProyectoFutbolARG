"""Estaduales de Brasil: los campeonatos estaduales (Paulista, Carioca, Mineiro, Gaúcho...) de los clubes de la Série A a la D.
Motor puro (sin Streamlit) derivado de los Regionales argentinos (copas/regionales.py). Se enchufa al registro con
`Estaduales` (copas/registro.py). Siempre se juegan (no hay interruptor) y arrancan el 10 de enero, una ronda cada 4 días.

Quién juega
  Cada club de la Série A, B, C y D juega el torneo de SU estado (datos/json/estaduales.json: club -> estado). Cada torneo
  tiene un tamaño (`tam`): entran primero los clubes de la división más alta y, dentro de ella, los de mayor media; si el
  estado tiene menos clubes que `tam`, se completa con clubes "complementarios" (`extras` del JSON: media fija y sin escudo,
  no juegan ninguna liga nacional). Si tiene de más (São Paulo: 19 para 16 lugares), los de peor división y media quedan afuera.

Cómo se juega (a partido único, el mejor sembrado de local, penales si empatan, final en cancha neutral)
  * Fase de grupos: `grupos` = 1 es una sola tabla todos contra todos a una rueda. Con `cruzado` (Paulista: 4 grupos de 4) cada club
    juega una vez contra los de los otros grupos (se descartan los cruces dentro del grupo).
  * Llave de `llave` clasificados (8: cuartos, semifinales y final · 4: semifinales y final): pasan los mejores de cada grupo
    (o de la tabla). Cada torneo empieza la llave cuando termina su fase de grupos.
Hay un campeón por estado; el Historial anota {torneo: campeón} en S["campeones"][-1]["Estaduales"].

Estado en S["estaduales"] (misma forma que el de los Regionales: nombres, r, cat, torneos, E, log, ronda, total, activo).
"""

import unicodedata

import numpy as np

from datos.cargador import cargar
from motor.nucleo import (LOCALIA, STATS, df_stats, generar_fixture, jugar, jugar_ko, mods_nombres, nuevo_partido,
                          sumar_partidos, tanda_penales)

NOMBRE = "Estaduales"
PAIS = "Brasil"
MIN_CLUBES = 4
LIGAS_BR = ((("ext_br"), "Série A"), ("ext_br2", "Série B"), ("ext_br3", "Série C"), ("ext_br4", "Série D"))
SIN_SERIE = "Complementario"
CORTO_CATEGORIA = {"Série A": "Série A", "Série B": "Série B", "Série C": "Série C", "Série D": "Série D",
                   SIN_SERIE: "Sin serie"}
ETAPAS_LLAVE = {2: ("Final",), 4: ("Semifinales", "Final"), 8: ("Cuartos de final", "Semifinales", "Final")}
CRUCES_LLAVE = {2: [(1, 2)], 4: [(1, 4), (2, 3)], 8: [(1, 8), (4, 5), (2, 7), (3, 6)]}

_D = cargar("estaduales")           # datos/json/estaduales.json
TORNEOS = _D["torneos"]
POR_ID = {t["id"]: t for t in TORNEOS}
NOMBRES_TORNEOS = [t["nombre"] for t in TORNEOS]
_MEDIA_EXTRA = {e["nombre"]: float(e["media"]) for lista in _D["extras"].values() for e in lista}


def torneo_de(nombre):
    """Id del estado de un club (None si no está en datos/json/estaduales.json)."""
    return _D["clubes"].get(nombre)


def participantes_por_estado(S):
    """{estado: [(club, media, categoría)]} con los clubes de las cuatro divisiones, ordenados por división y media."""
    out = {}
    for clave, cat in LIGAS_BR:
        L = S.get(clave)
        if not L:
            continue
        for n, x in zip(L["nombres"], L["r"]):
            if (e := torneo_de(n)):
                out.setdefault(e, []).append((n, float(x), cat))
    orden = {c: i for i, (_, c) in enumerate(LIGAS_BR)}
    for e in out:
        out[e].sort(key=lambda f: (orden[f[2]], -f[1], f[0]))
    return out


def plan(S):
    """Qué torneos se juegan hoy, sin sortear: [{"torneo", "clubes": [(club, media, categoría)], "grupos", "llave"}]."""
    por_estado = participantes_por_estado(S)
    out = []
    for t in TORNEOS:
        clubes = por_estado.get(t["id"], [])[:t["tam"]]
        for e in _D["extras"].get(t["id"], []):
            if len(clubes) >= t["tam"]:
                break
            clubes.append((e["nombre"], float(e["media"]), SIN_SERIE))
        if len(clubes) >= MIN_CLUBES:
            out.append({"torneo": t, "clubes": clubes, "grupos": t["grupos"], "llave": t["llave"]})
    return out


def estaduales_vacios():
    """Estado de los Estaduales cuando no hay clubes de Brasil (o antes de armar la temporada)."""
    return {"activo": False, "ronda": 0, "total": 0, "log": [], "nombres": [], "r": np.zeros(0), "cat": [],
            "torneos": [], "E": {k: np.zeros(0, dtype=int) for k in STATS}, "sin_torneo": []}


def nombre_grupo(g, k):
    return "Grupo único" if g == 1 else f"Grupo {'ABCD'[k]}"


def _armar_torneo(t, ids, r, rng):
    """Sortea los grupos (bombos por media) y arma el fixture de un torneo. `ids`: índices de sus clubes."""
    n, g = len(ids), t["grupos"]
    orden = sorted(ids, key=lambda i: -r[i])
    grupos = [[] for _ in range(g)]
    for k in range(0, n, g):                                  # bombo de a `g` clubes, repartido al azar
        bombo = orden[k:k + g]
        for i, destino in zip(bombo, rng.permutation(g)[:len(bombo)]):
            grupos[int(destino)].append(int(i))
    if t["cruzado"]:                                          # todos contra todos sin los cruces dentro del grupo
        puestos = [int(ids[i]) for i in rng.permutation(n)]
        del_grupo = {i: k for k, gr in enumerate(grupos) for i in gr}
        fechas = []
        for fecha in generar_fixture(n):
            cruces = [(puestos[a], puestos[b]) for a, b in fecha if del_grupo[puestos[a]] != del_grupo[puestos[b]]]
            if cruces:
                fechas.append(cruces)
        fixtures = [fechas]
    else:
        fixtures = []
        for grupo in grupos:
            puestos = [int(i) for i in rng.permutation(grupo)]
            fixtures.append([[(puestos[a], puestos[b]) for a, b in fecha] for fecha in generar_fixture(len(puestos))])
    rondas = max(len(f) for f in fixtures)
    llave = t["llave"]
    return {"id": t["id"], "nombre": t["nombre"], "corto": t["corto"], "color": t["color"], "zona": t["zona"],
            "cruzado": bool(t["cruzado"]), "ids": [int(i) for i in ids], "grupos": grupos, "fixtures": fixtures,
            "rondas_grupo": rondas, "llave": llave, "fin": rondas + len(ETAPAS_LLAVE[llave]), "semilla": {},
            "clasificados": [], "ko": [], "campeon": None, "subcampeon": None}


def sortear_estaduales(S, rng):
    """Arma los Estaduales de la temporada: torneos, grupos y fixtures (todavía sin jugar)."""
    R = estaduales_vacios()
    juegan = plan(S)
    nombres, medias, cats, torneos = [], [], [], []
    for p in juegan:
        ids = []
        for club, media, cat in p["clubes"]:
            ids.append(len(nombres))
            nombres.append(club)
            medias.append(media + (float(rng.normal(0, 1.5)) if cat == SIN_SERIE else 0.0))
            cats.append(cat)
        torneos.append((p["torneo"], ids))
    r = np.array(medias, dtype=float)
    R["nombres"], R["r"], R["cat"] = nombres, r, cats
    R["torneos"] = [_armar_torneo(t, ids, r, rng) for t, ids in torneos]
    R["E"] = {k: np.zeros(len(nombres), dtype=int) for k in STATS}
    R["activo"] = bool(R["torneos"])
    R["total"] = max((t["fin"] for t in R["torneos"]), default=0)
    jugando = {c for p in juegan for c, _, _ in p["clubes"]}
    todos = [n for lista in participantes_por_estado(S).values() for n, _, _ in lista]
    R["sin_torneo"] = sorted(c for c in todos if c not in jugando)
    return R


# ----------------------------------------------------------------------------
# TABLAS
# ----------------------------------------------------------------------------
def tabla_grupo(R, t, k):
    """Tabla del grupo k del torneo t (con columnas Pos, Equipo, Categoría, PJ... y la 'id' interna)."""
    df = df_stats(R["nombres"], R["r"], R["E"], t["grupos"][k])
    df.insert(0, "Pos", range(1, len(df) + 1))
    df.insert(3, "Categoría", [CORTO_CATEGORIA[R["cat"][int(i)]] for i in df["id"]])
    return df


def _clasificar(R, t):
    """Los `llave` clasificados del torneo, de mejor a peor sembrado: primero los ganadores de grupo, después los
    segundos, etc., y dentro de cada puesto por puntos por partido, diferencia de gol y goles (por partido)."""
    cand = []
    for k in range(len(t["grupos"])):
        tabla = tabla_grupo(R, t, k)
        for pos, f in enumerate(tabla.itertuples(index=False)):
            pj = max(1, int(f.PJ))
            cand.append((pos, -int(f.Pts) / pj, -int(f.DG) / pj, -int(f.GF) / pj, int(f.id)))
    cand.sort()
    return [c[-1] for c in cand[:t["llave"]]]


def destino_grupo(t, club_id, pos):
    """Destino de un puesto (pos desde 1) de la tabla de un grupo: "Clasifica", "Mejor tercero" (si todavía se puede
    colar entre los mejores terceros, mientras se juega) o "" (queda afuera). Con la fase terminada es definitivo."""
    if t["clasificados"]:
        return "Clasifica" if club_id in t["clasificados"] else ""
    g, llave = len(t["grupos"]), t["llave"]
    por_grupo = llave // g if llave % g == 0 else 2          # puestos que pasan seguro en cada grupo
    if g == 1:
        return "Clasifica" if pos <= llave else ""
    if pos <= por_grupo:
        return "Clasifica"
    return "Mejor tercero" if pos == por_grupo + 1 and llave > por_grupo * g else ""


# ----------------------------------------------------------------------------
# JUGAR
# ----------------------------------------------------------------------------
def _etapa_llave(t, k):
    """Nombre de la k-ésima ronda (1, 2, 3) de la llave del torneo t."""
    return ETAPAS_LLAVE[t["llave"]][k - 1]


def _partidos_ronda(R, n):
    """Partidos que se juegan en la ronda global n: [(torneo, "grupo" | "ko", a, b, rótulo, partido de llave)]."""
    out = []
    for t in R["torneos"]:
        if n <= t["rondas_grupo"]:
            for k, fixture in enumerate(t["fixtures"]):
                if n <= len(fixture):
                    rot = f"Fecha {n}" if t["cruzado"] or len(t["grupos"]) == 1 else f"{nombre_grupo(len(t['grupos']), k)} · Fecha {n}"
                    out += [(t, "grupo", a, b, rot, None) for a, b in fixture[n - 1]]
        else:
            k = n - t["rondas_grupo"]
            if k <= len(t["ko"]):
                ronda = t["ko"][k - 1]
                out += [(t, "ko", m["a"], m["b"], ronda["nombre"], m) for m in ronda["partidos"]]
    return out


def cruces_ronda(S, n):
    """Partidos todavía sin jugar de la ronda n: [(local, visita, rótulo, torneo)]."""
    R = S["estaduales"]
    if not R["activo"] or n <= R["ronda"]:
        return []
    nom = R["nombres"]
    return [(nom[a], nom[b], rot, t["nombre"]) for t, _, a, b, rot, _ in _partidos_ronda(R, n)]


def rotulo_ronda(S, n):
    """Rótulo de la ronda n para el calendario: las etapas que se juegan ese día ("Fecha 3", "Fecha 8 · Semifinales")."""
    etapas = []
    for t in S["estaduales"]["torneos"]:
        if n > t["fin"]:                                        # este torneo ya terminó
            continue
        e = f"Fecha {n}" if n <= t["rondas_grupo"] else _etapa_llave(t, n - t["rondas_grupo"])
        if e not in etapas:
            etapas.append(e)
    return " · ".join(etapas) or f"Ronda {n}"


def _armar_ronda_llave(R, t, ganadores):
    """Pone el cuadro de la próxima ronda con los `ganadores` en el orden de la llave (el de menor siembra, de local)."""
    k = len(t["ko"]) + 1
    if not t["ko"]:                                              # primera ronda: cruces por siembra
        pares = [(ganadores[a - 1], ganadores[b - 1]) for a, b in CRUCES_LLAVE[t["llave"]]]
    else:
        pares = [tuple(sorted(ganadores[j:j + 2], key=lambda i: t["semilla"][i])) for j in range(0, len(ganadores), 2)]
    t["ko"].append({"nombre": _etapa_llave(t, k),
                    "partidos": [{"a": int(a), "b": int(b), "p": None, "gana": None} for a, b in pares]})


def _jugar_grupo(R, t, n, partidos, P, rng):
    a = np.array([x[2] for x in partidos])
    b = np.array([x[3] for x in partidos])
    nom, r = R["nombres"], R["r"]
    gl, gv = jugar(rng, r[a], r[b], P["sorpresa"], **mods_nombres(rng, [nom[i] for i in a], [nom[i] for i in b]))
    sumar_partidos(R["E"], a, b, gl, gv)
    for (_, _, ia, ib, rot, _), g1, g2 in zip(partidos, gl, gv):
        R["log"].append(nuevo_partido(NOMBRE, n, rot, t["nombre"], nom[ia], nom[ib], g1, g2))


def _jugar_llave(R, t, n, partidos, P, rng):
    a = np.array([x[2] for x in partidos])
    b = np.array([x[3] for x in partidos])
    nom, r = R["nombres"], R["r"]
    final = len(partidos) == 1 and partidos[0][4] == "Final"
    gl, gv, gana_l, pen = jugar_ko(rng, r[a], r[b], P["sorpresa"], localia=0.0 if final else LOCALIA,
                                   **mods_nombres(rng, [nom[i] for i in a], [nom[i] for i in b]))
    for (_, _, ia, ib, rot, m), g1, g2, gl_, pe in zip(partidos, gl, gv, gana_l, pen):
        tanda = tanda_penales(rng, bool(gl_)) if pe else None
        m["gana"] = ia if gl_ else ib
        m["p"] = nuevo_partido(NOMBRE, n, rot, t["nombre"], nom[ia], nom[ib], g1, g2, tanda=tanda,
                               gana=nom[m["gana"]], neutral=final)
        R["log"].append(m["p"])


def simular_ronda_estaduales(S, P, rng):
    """Juega la próxima ronda de todos los torneos a la vez (fechas de grupo y/o llaves) y arma lo que sigue."""
    R = S["estaduales"]
    if not R["activo"] or R["ronda"] >= R["total"]:
        return
    n = R["ronda"] + 1
    todos = _partidos_ronda(R, n)
    for t in R["torneos"]:
        grupo = [x for x in todos if x[0] is t and x[1] == "grupo"]
        llave = [x for x in todos if x[0] is t and x[1] == "ko"]
        if grupo:
            _jugar_grupo(R, t, n, grupo, P, rng)
        if llave:
            _jugar_llave(R, t, n, llave, P, rng)
    R["ronda"] = n
    for t in R["torneos"]:
        if n == t["rondas_grupo"]:                              # terminó la fase de grupos: se arma la llave
            t["clasificados"] = _clasificar(R, t)
            t["semilla"] = {i: s for s, i in enumerate(t["clasificados"])}
            _armar_ronda_llave(R, t, t["clasificados"])
        elif n > t["rondas_grupo"] and n <= t["fin"]:
            ronda = t["ko"][n - t["rondas_grupo"] - 1]
            ganadores = [m["gana"] for m in ronda["partidos"]]
            if len(ganadores) == 1:                             # la final
                m = ronda["partidos"][0]
                t["campeon"] = int(m["gana"])
                t["subcampeon"] = int(m["b"] if m["gana"] == m["a"] else m["a"])
            else:
                _armar_ronda_llave(R, t, ganadores)


def campeones(S):
    """{nombre del torneo: club campeón} de los torneos que ya terminaron."""
    R = S["estaduales"]
    return {t["nombre"]: R["nombres"][t["campeon"]] for t in R["torneos"] if t["campeon"] is not None}


def torneo_del_club(S, club):
    """Torneo de los Regionales donde juega el club esta temporada (None si no juega)."""
    R = S.get("estaduales") or {}
    if not R.get("activo") or club not in R.get("nombres", []):
        return None
    i = R["nombres"].index(club)
    return next((t for t in R["torneos"] if i in t["ids"]), None)


def fase_torneo(t, ronda):
    """Texto de en qué etapa está el torneo después de `ronda` rondas jugadas."""
    if t["campeon"] is not None:
        return "Terminado"
    if ronda < t["rondas_grupo"]:
        return f"Fase de grupos · fecha {min(ronda + 1, t['rondas_grupo'])} de {t['rondas_grupo']}"
    return _etapa_llave(t, ronda - t["rondas_grupo"] + 1)

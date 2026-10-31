"""Regionales: los torneos regionales del fútbol argentino, al estilo de los campeonatos estaduales de Brasil
(Carioca, Paulista, Gaúcho...). Es una copa OPCIONAL: se activa y se desactiva desde la pestaña Copas > Regionales.

Quién juega
  Los clubes de Primera División, Primera Nacional, Federal A, Federal B (si existe) y Primera B y Primera C.
  No juegan el Promocional Amateur ni el Regional Amateur. Cada club juega el torneo de SU zona, que sale de
  datos/json/regionales.json (club -> torneo, y si no está, por provincia):

      Porteño · Sur y La Plata · Norte y Oeste · Bonaerense · Cordobés · Cuyano · Litoral · Nordeste ·
      Noroeste · Patagónico

  Un torneo con menos de 4 clubes no se juega (sus clubes se quedan sin Regionales esa temporada).

Cómo se juega cada torneo (todos a la vez, una ronda cada 3 días desde el 7 de enero: ver Regionales.dia)
  * Fase de grupos: una sola rueda dentro de cada grupo (sorteados con bombos por media). La cantidad de grupos
    depende del tamaño del torneo:
        4 a 8 clubes        1 grupo         9 a 16 clubes      2 grupos
        17 a 24 clubes      3 grupos        25 o más           4 grupos
  * Llaves, a partido único (el mejor sembrado de local, empate por penales; la final en cancha neutral):
        1 grupo con 4-5 clubes: final entre los 2 primeros.
        1 grupo con 6-8, o 2 grupos con hasta 13 clubes: semifinales con 4 clasificados.
        el resto: cuartos de final con 8 clasificados.
    Pasan los 2 primeros de cada grupo; si faltan lugares los completan los mejores terceros (o cuartos) según
    puntos por partido. El campeón de cada torneo es el ganador de la final.
  * Cada torneo empieza su llave apenas termina su propia fase de grupos.

Sin Streamlit: es motor puro. Se registra en copas/registro.py (clase Regionales).
Estado en S["regionales"] (siempre existe; "activo" dice si se juega esta temporada) y la elección de la persona
en S["regionales_on"] (cambia desde la pestaña; rige ahora si la temporada no empezó, o desde la que viene).
"""

import unicodedata

import numpy as np

from datos.cargador import cargar
from motor.nucleo import (LOCALIA, STATS, df_stats, generar_fixture, jugar, jugar_ko, mods_nombres, nuevo_partido,
                          sumar_partidos, tanda_penales)

NOMBRE = "Regionales"
MIN_CLUBES = 4                      # un torneo con menos clubes no se juega
CATEGORIAS = ("Primera División", "Primera Nacional", "Federal A", "Federal B", "Primera B", "Primera C")
CORTO_CATEGORIA = {"Primera División": "Primera", "Primera Nacional": "B Nacional", "Federal A": "Federal A",
                   "Federal B": "Federal B", "Primera B": "Primera B", "Primera C": "Primera C"}
ETAPAS_LLAVE = {2: ("Final",), 4: ("Semifinales", "Final"), 8: ("Cuartos de final", "Semifinales", "Final")}
# Cruces de la llave por siembra (1 = mejor sembrado): el ganador del cruce 2k juega contra el del 2k+1
CRUCES_LLAVE = {2: [(1, 2)], 4: [(1, 4), (2, 3)], 8: [(1, 8), (4, 5), (2, 7), (3, 6)]}

_D = cargar("regionales")           # datos/json/regionales.json
TORNEOS = _D["torneos"]
POR_ID = {t["id"]: t for t in TORNEOS}
NOMBRES_TORNEOS = [t["nombre"] for t in TORNEOS]


def _norm(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s.lower()) if not unicodedata.combining(c)).strip()


_PROVINCIAS = {_norm(k): v for k, v in _D["provincias"].items()}


# ----------------------------------------------------------------------------
# A QUÉ TORNEO VA CADA CLUB
# ----------------------------------------------------------------------------
def torneo_de(nombre):
    """Id del torneo regional de un club: la lista a mano (datos/json/regionales.json), si no su provincia, si es
    metropolitano sin datos el de Norte y Oeste y, si no, el de la región de su grupo del Federal A."""
    from datos.clubes_interior import datos_club
    from datos.equipos import origen, region_de
    if (t := _D["clubes"].get(nombre)):
        return t
    datos = datos_club(nombre)
    if datos and (t := _PROVINCIAS.get(_norm(datos.get("provincia", "")))):
        return t
    if origen(nombre) == "Metropolitana":
        return _D["metropolitano_por_defecto"]
    return _D["grupo_federal"].get(region_de(nombre), _D["metropolitano_por_defecto"])


def participantes(S):
    """[(club, media, categoría)] de todos los que juegan Regionales esta temporada (con la media de cada liga)."""
    ligas = ((S, "Primera División"), (S["b"], "Primera Nacional"), (S["f"], "Federal A"), (S.get("fb"), "Federal B"),
             (S["pb"], "Primera B"), (S["pc"], "Primera C"))
    out = []
    for L, cat in ligas:
        if L is None:
            continue
        out += [(n, float(x), cat) for n, x in zip(L["nombres"], L["r"])]
    return out


# ----------------------------------------------------------------------------
# FORMATO DE CADA TORNEO
# ----------------------------------------------------------------------------
def n_grupos(n):
    """Cantidad de grupos de un torneo de n clubes."""
    return 1 if n <= 8 else 2 if n <= 16 else 3 if n <= 24 else 4


def tam_llave(n):
    """Clasificados a la llave (2, 4 u 8) de un torneo de n clubes."""
    g = n_grupos(n)
    if g == 1:
        return 2 if n < 6 else 4
    if g == 2:
        return 4 if n <= 13 else 8
    return 8


def nombre_grupo(g, k):
    return "Grupo único" if g == 1 else f"Grupo {'ABCD'[k]}"


def plan(S):
    """Qué torneos se jugarían hoy, sin sortear: [{"torneo", "clubes": [(club, media, categoría)], "grupos", "llave"}].
    Sirve para mostrar el formato cuando los Regionales están desactivados."""
    por_torneo = {}
    for club, media, cat in participantes(S):
        por_torneo.setdefault(torneo_de(club), []).append((club, media, cat))
    out = []
    for t in TORNEOS:
        clubes = por_torneo.get(t["id"], [])
        if len(clubes) >= MIN_CLUBES:
            out.append({"torneo": t, "clubes": clubes, "grupos": n_grupos(len(clubes)),
                        "llave": tam_llave(len(clubes))})
    return out


def regionales_vacios():
    """Estado de los Regionales cuando no se juegan esta temporada."""
    return {"activo": False, "ronda": 0, "total": 0, "log": [], "nombres": [], "r": np.zeros(0), "cat": [],
            "torneos": [], "E": {k: np.zeros(0, dtype=int) for k in STATS}, "sin_torneo": []}


def _armar_torneo(t, ids, r, rng):
    """Sortea los grupos (bombos por media) y arma el fixture de un torneo. `ids`: índices de sus clubes."""
    n = len(ids)
    g = n_grupos(n)
    orden = sorted(ids, key=lambda i: -r[i])
    grupos = [[] for _ in range(g)]
    for k in range(0, n, g):                                  # bombo de a `g` clubes, repartido al azar
        bombo = orden[k:k + g]
        for i, destino in zip(bombo, rng.permutation(g)[:len(bombo)]):
            grupos[int(destino)].append(int(i))
    fixtures = []
    for grupo in grupos:
        puestos = [int(i) for i in rng.permutation(grupo)]
        fixtures.append([[(puestos[a], puestos[b]) for a, b in fecha] for fecha in generar_fixture(len(puestos))])
    rondas = max(len(f) for f in fixtures)
    llave = tam_llave(n)
    return {"id": t["id"], "nombre": t["nombre"], "corto": t["corto"], "color": t["color"], "zona": t["zona"],
            "ids": [int(i) for i in ids], "grupos": grupos, "fixtures": fixtures, "rondas_grupo": rondas,
            "llave": llave, "fin": rondas + len(ETAPAS_LLAVE[llave]), "semilla": {}, "clasificados": [],
            "ko": [], "campeon": None, "subcampeon": None}


def sortear_regionales(S, rng):
    """Arma los Regionales de la temporada: torneos, grupos y fixtures (todavía sin jugar)."""
    R = regionales_vacios()
    juegan = plan(S)
    nombres, medias, cats, torneos = [], [], [], []
    for p in juegan:
        ids = []
        for club, media, cat in p["clubes"]:
            ids.append(len(nombres))
            nombres.append(club)
            medias.append(media)
            cats.append(cat)
        torneos.append((p["torneo"], ids))
    r = np.array(medias, dtype=float)
    R["nombres"], R["r"], R["cat"] = nombres, r, cats
    R["torneos"] = [_armar_torneo(t, ids, r, rng) for t, ids in torneos]
    R["E"] = {k: np.zeros(len(nombres), dtype=int) for k in STATS}
    R["activo"] = bool(R["torneos"])
    R["total"] = max((t["fin"] for t in R["torneos"]), default=0)
    jugando = {c for p in juegan for c, _, _ in p["clubes"]}
    R["sin_torneo"] = [c for c, _, _ in participantes(S) if c not in jugando]
    return R


def cambiar_activacion(S, rng, activar, temporada_empezada):
    """Activa o desactiva los Regionales. Si la temporada todavía no empezó rige ahora (se sortean o se borran);
    si ya empezó, queda elegido para la temporada que viene y la actual sigue como estaba. Devuelve True si rige ya."""
    S["regionales_on"] = bool(activar)
    if temporada_empezada:
        return False
    S["regionales"] = sortear_regionales(S, rng) if activar else regionales_vacios()
    return True


def pendiente_de_aplicar(S):
    """True si lo elegido (S["regionales_on"]) no es lo que rige esta temporada."""
    return bool(S.get("regionales_on")) != bool(S["regionales"]["activo"])


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
                    rot = (f"{nombre_grupo(len(t['grupos']), k)} · Fecha {n}" if len(t["grupos"]) > 1 else f"Fecha {n}")
                    out += [(t, "grupo", a, b, rot, None) for a, b in fixture[n - 1]]
        else:
            k = n - t["rondas_grupo"]
            if k <= len(t["ko"]):
                ronda = t["ko"][k - 1]
                out += [(t, "ko", m["a"], m["b"], ronda["nombre"], m) for m in ronda["partidos"]]
    return out


def cruces_ronda(S, n):
    """Partidos todavía sin jugar de la ronda n: [(local, visita, rótulo, torneo)]."""
    R = S["regionales"]
    if not R["activo"] or n <= R["ronda"]:
        return []
    nom = R["nombres"]
    return [(nom[a], nom[b], rot, t["nombre"]) for t, _, a, b, rot, _ in _partidos_ronda(R, n)]


def rotulo_ronda(S, n):
    """Rótulo de la ronda n para el calendario: las etapas que se juegan ese día ("Fecha 3", "Fecha 8 · Semifinales")."""
    etapas = []
    for t in S["regionales"]["torneos"]:
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


def simular_ronda_regionales(S, P, rng):
    """Juega la próxima ronda de todos los torneos a la vez (fechas de grupo y/o llaves) y arma lo que sigue."""
    R = S["regionales"]
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
    R = S["regionales"]
    return {t["nombre"]: R["nombres"][t["campeon"]] for t in R["torneos"] if t["campeon"] is not None}


def torneo_del_club(S, club):
    """Torneo de los Regionales donde juega el club esta temporada (None si no juega)."""
    R = S.get("regionales") or {}
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

"""Copas internacionales de la CONMEBOL: Libertadores, Sudamericana y Recopa.

Clasifican por la temporada anterior (como en la vida real):
  * Argentina, por la tabla final de Primera: 1°-5° a la fase de grupos de la Libertadores,
    11° a la fase previa de la Libertadores, 6°-8° y 12°-13° a la Sudamericana. El campeón de
    la Copa Argentina también va a los grupos de la Libertadores (si ya estaba clasificado, el
    lugar pasa al mejor ubicado que todavía no entró). Los campeones de la Libertadores y la
    Sudamericana van a los grupos de la Libertadores siguiente.
  * Los otros 9 países: cupos fijos por país (Brasil tiene más); qué club ocupa cada cupo se
    sortea cada temporada entre los de primera división de ese país (los más fuertes entran
    más seguido). Todos con licencia (ver clubes_int.py).
  * Temporada 1: la tabla de Primera se toma por media; campeones 2025: Flamengo
    (Libertadores), Lanús (Sudamericana) e Independiente Rivadavia (Copa Argentina).

Formato:
  * Libertadores: fase previa (Fase 2: 16 equipos; Fase 3: 8) a ida y vuelta; los 4 que ganan
    la Fase 3 van a los grupos y los 4 que pierden, a los grupos de la Sudamericana. Grupos:
    8 de 4, ida y vuelta; 1° y 2° a octavos, 3° a los playoffs de la Sudamericana. Octavos,
    cuartos y semis a ida y vuelta (si el global empata, penales); final única en cancha neutral.
  * Sudamericana: 8 grupos de 4 (28 clasificados + 4 de la Libertadores); 1° a octavos, 2°
    a los playoffs contra los 3° de la Libertadores; después igual que la Libertadores.
  * Recopa: campeón de la Libertadores vs. campeón de la Sudamericana, ida y vuelta.
"""

import numpy as np

from clubes_int import CLUBES_INT, PAISES
from motor import jugar, jugar_ko, nuevo_partido, tanda_penales

LIB, SUD, REC = "Copa Libertadores", "Copa Sudamericana", "Recopa Sudamericana"

LIB_RONDAS = (["Fase 2 · ida", "Fase 2 · vuelta", "Fase 3 · ida", "Fase 3 · vuelta"]
              + [f"Grupos · fecha {k}" for k in range(1, 7)]
              + ["Octavos · ida", "Octavos · vuelta", "Cuartos · ida", "Cuartos · vuelta",
                 "Semifinal · ida", "Semifinal · vuelta", "Final"])
SUD_RONDAS = ([f"Grupos · fecha {k}" for k in range(1, 7)]
              + ["Playoffs · ida", "Playoffs · vuelta", "Octavos · ida", "Octavos · vuelta",
                 "Cuartos · ida", "Cuartos · vuelta", "Semifinal · ida", "Semifinal · vuelta", "Final"])
REC_RONDAS = ["Ida", "Vuelta"]

# Cupos de los otros países (Argentina sale de la tabla de Primera). Brasil absorbe la diferencia
# para que siempre sean 28 en los grupos, 16 en la fase previa y 28 en la Sudamericana.
CUPOS_LIB_GRUPOS = {"Brasil": 6, "Colombia": 2, "Paraguay": 2, "Perú": 2, "Chile": 2, "Uruguay": 2,
                    "Ecuador": 2, "Bolivia": 2, "Venezuela": 2}
CUPOS_LIB_PREVIA = {"Brasil": 1, "Colombia": 2, "Paraguay": 2, "Perú": 2, "Chile": 2, "Uruguay": 2,
                    "Ecuador": 2, "Bolivia": 1, "Venezuela": 1}
CUPOS_SUD = {"Brasil": 6, "Colombia": 3, "Paraguay": 2, "Perú": 2, "Chile": 2, "Uruguay": 2,
             "Ecuador": 2, "Bolivia": 2, "Venezuela": 2}
GRUPOS = "ABCDEFGH"
# fixture de un grupo de 4 (ida y vuelta)
_FIX4 = [[(0, 1), (2, 3)], [(3, 0), (1, 2)], [(0, 2), (3, 1)],
         [(1, 0), (3, 2)], [(0, 3), (2, 1)], [(2, 0), (1, 3)]]
PAIS_EXT = {n: p for n, p, _, _ in CLUBES_INT}
MEDIA_EXT = {n: float(m) for n, p, m, _ in CLUBES_INT}


def pais_de(nombre):
    return PAIS_EXT.get(nombre, "Argentina")


# ---------------------------------------------------------------- clasificación
def clasif_argentina(S):
    """Clasificados argentinos por la temporada que termina: {grupos, previa, sud} con
    (club, cómo clasificó), más los campeones para la Recopa y la Libertadores siguiente."""
    from torneos import tabla_final
    tabla = tabla_final(S).sort_values("Pos")
    orden = list(tabla["Equipo"])
    SC = S.get("copa", {})
    copa = SC["nombres"][SC["campeon"]] if SC.get("campeon") is not None else None
    return _reparto_argentino(orden, copa, S["temp"])


def _reparto_argentino(orden, copa, temp):
    pos = {n: k + 1 for k, n in enumerate(orden)}
    grupos = [(n, f"Primera {temp}: {pos[n]}°") for n in orden[:5]]
    ya = {n for n, _ in grupos}
    if copa and copa not in ya:
        grupos.append((copa, "Campeón Copa Argentina"))
    else:                                            # el lugar pasa al mejor que no entró
        n = next(x for x in orden if x not in ya)
        grupos.append((n, f"Primera {temp}: {pos[n]}° (cupo de la Copa Argentina)"))
    ya |= {n for n, _ in grupos}
    previa = [(n, f"Primera {temp}: {pos[n]}°") for n in orden[10:11] if n not in ya]
    ya |= {n for n, _ in previa}
    sud = []
    for k in (5, 6, 7, 11, 12, 8, 9, 13, 14, 15):   # 6°-8° y 12°-13° (si alguno ya entró, el que sigue)
        if len(sud) == 5:
            break
        n = orden[k]
        if n not in ya:
            sud.append((n, f"Primera {temp}: {pos[n]}°"))
            ya.add(n)
    return {"grupos": grupos, "previa": previa, "sud": sud, "orden": orden, "temp_tabla": temp}


def clasif_inicial(S):
    """Temporada 1 (2026): la tabla de Primera por media y los campeones reales de 2025."""
    orden = [S["nombres"][i] for i in np.argsort(-np.asarray(S["r"]))]
    c = _reparto_argentino(orden, "Independiente Rivadavia", 2025)
    for lista in (c["grupos"], c["previa"], c["sud"]):
        for k, (n, via) in enumerate(lista):
            lista[k] = (n, via.replace("Primera 2025", "Primera 2025 (por media)"))
    c["campeon_lib"], c["campeon_sud"] = "Flamengo", "Lanús"
    return c


def fin_de_temporada(S):
    """Al terminar la temporada: quiénes van a las copas de la que viene."""
    c = clasif_argentina(S)
    I = S["int"]
    c["campeon_lib"] = I["lib"].get("campeon")
    c["campeon_sud"] = I["sud"].get("campeon")
    S["int_clasif"] = c


def _medias(S):
    from copas import categoria_actual
    out = {n: m for n, (_, m) in categoria_actual(S).items()}
    out.update(S.setdefault("rating_int", dict(MEDIA_EXT)))
    return out


def _sortear_pais(rng, S, pais, k, excluir):
    pool = [n for n, p, _, _ in CLUBES_INT if p == pais and n not in excluir]
    if k <= 0 or not pool:
        return []
    m = np.array([S["rating_int"].get(n, MEDIA_EXT[n]) for n in pool])
    w = np.exp((m - m.max()) / 4.0)
    idx = rng.choice(len(pool), size=min(k, len(pool)), replace=False, p=w / w.sum())
    return [pool[int(i)] for i in idx]


def _ajustar_cupos(cupos, total):
    c = dict(cupos)
    c["Brasil"] = max(0, c["Brasil"] + total - sum(cupos.values()))
    return c


# ---------------------------------------------------------------- estado de cada copa
def _copa(nombre, rondas, medias, participantes):
    """participantes: [(club, cómo clasificó)]."""
    return {"nombre": nombre, "rondas": rondas, "ronda": 0, "total": len(rondas), "log": [],
            "r": {n: medias.get(n, 60.0) for n, _ in participantes},
            "via": dict(participantes), "grupos": None, "gstats": {}, "llaves": {}, "campeon": None,
            "subcampeon": None, "terceros": [], "a_sud": []}


def nuevas_internacionales(S, rng):
    """Arma la Libertadores, la Sudamericana y la Recopa de la temporada que empieza."""
    c = S.get("int_clasif") or clasif_inicial(S)
    medias = _medias(S)
    arg_g, arg_p, arg_s = c["grupos"], c["previa"], c["sud"]
    ya = {n for n, _ in arg_g + arg_p + arg_s}
    lib_g = list(arg_g)
    for cl, via in ((c.get("campeon_lib"), "Campeón de la Libertadores"),
                    (c.get("campeon_sud"), "Campeón de la Sudamericana")):
        if cl and cl not in {n for n, _ in lib_g}:
            lib_g = [(n, v) for n, v in lib_g]
            if cl in ya:                               # si ya estaba en otra lista, sube a grupos
                arg_p = [(n, v) for n, v in arg_p if n != cl]
                arg_s = [(n, v) for n, v in arg_s if n != cl]
            lib_g.append((cl, via))
            ya.add(cl)
    # si un campeón vigente subió a los grupos, su lugar en la previa / Sudamericana pasa al que sigue
    orden = c.get("orden", [])
    for lista, cant in ((arg_p, len(c["previa"])), (arg_s, len(c["sud"]))):
        for n in orden[5:]:
            if len(lista) >= cant:
                break
            if n not in ya:
                lista.append((n, f"Primera {c.get('temp_tabla', '')}: {orden.index(n) + 1}° (reemplazo)"))
                ya.add(n)
    ext_g = _ajustar_cupos(CUPOS_LIB_GRUPOS, 28 - len(lib_g))
    for pais in PAISES:
        for n in _sortear_pais(rng, S, pais, ext_g[pais], ya):
            lib_g.append((n, f"{pais} · grupos"))
            ya.add(n)
    lib_p = list(arg_p)
    ext_p = _ajustar_cupos(CUPOS_LIB_PREVIA, 16 - len(lib_p))
    for pais in PAISES:
        for n in _sortear_pais(rng, S, pais, ext_p[pais], ya):
            lib_p.append((n, f"{pais} · fase previa"))
            ya.add(n)
    sud = list(arg_s)
    ext_s = _ajustar_cupos(CUPOS_SUD, 28 - len(sud))
    for pais in PAISES:
        for n in _sortear_pais(rng, S, pais, ext_s[pais], ya):
            sud.append((n, f"{pais} · Sudamericana"))
            ya.add(n)

    L = _copa(LIB, LIB_RONDAS, medias, lib_g + lib_p)
    L["directos"] = [n for n, _ in lib_g]
    L["cabeza"] = c.get("campeon_lib")
    L["llaves"]["Fase 2"] = _cruces_bombos(rng, [n for n, _ in lib_p], L["r"])
    U = _copa(SUD, SUD_RONDAS, medias, sud)
    U["directos"] = [n for n, _ in sud]
    rec = [(c.get("campeon_lib"), "Campeón de la Libertadores"), (c.get("campeon_sud"), "Campeón de la Sudamericana")]
    rec = [(n, v) for n, v in rec if n]
    R = _copa(REC, REC_RONDAS if len(rec) == 2 else [], medias, rec)
    if len(rec) == 2:
        R["llaves"]["Final"] = [_serie(rec[0][0], rec[1][0])]
    S["int"] = {"lib": L, "sud": U, "rec": R}


# ---------------------------------------------------------------- series, grupos y cruces
def _serie(a, b):
    """Serie a ida y vuelta: `a` cierra de local."""
    return {"a": a, "b": b, "ida": None, "vuelta": None, "ga": 0, "gb": 0, "pen": None, "gana": None}


def _cruces_bombos(rng, equipos, r):
    """Bombo 1 (los mejores por media) contra bombo 2; el del bombo 1 cierra de local."""
    orden = sorted(equipos, key=lambda n: -r[n])
    mitad = len(orden) // 2
    b1, b2 = list(rng.permutation(orden[:mitad])), list(rng.permutation(orden[mitad:]))
    return [_serie(str(a), str(b)) for a, b in zip(b1, b2)]


def _sorteo_grupos(rng, equipos, r, primero=None):
    """8 grupos de 4 por bombos (por media); se evita que dos del mismo país compartan grupo."""
    orden = sorted(equipos, key=lambda n: (n != primero, -r[n]))
    bombos = [orden[8 * k:8 * k + 8] for k in range(4)]
    mejor, menos = None, 99
    for _ in range(400):
        grupos = [[b] for b in rng.permutation(bombos[0])]
        choques = 0
        for bombo in bombos[1:]:
            libres = list(range(8))
            for n in rng.permutation(bombo):
                ok = [g for g in libres if pais_de(str(n)) not in {pais_de(x) for x in grupos[g]}]
                g = ok[int(rng.integers(len(ok)))] if ok else libres[int(rng.integers(len(libres)))]
                choques += not ok
                grupos[g].append(str(n))
                libres.remove(g)
        if choques < menos:
            mejor, menos = grupos, choques
        if choques == 0:
            break
    return [[str(x) for x in g] for g in mejor]


def tabla_grupo(C, g):
    """Tabla del grupo g: lista de dicts ordenada (Pts, DG, GF)."""
    filas = []
    for n in C["grupos"][g]:
        s = C["gstats"][n]
        filas.append({"Equipo": n, "PJ": s["pj"], "G": s["g"], "E": s["e"], "P": s["p"], "GF": s["gf"],
                      "GC": s["gc"], "DG": s["gf"] - s["gc"], "Pts": 3 * s["g"] + s["e"]})
    filas.sort(key=lambda x: (x["Pts"], x["DG"], x["GF"], C["r"][x["Equipo"]]), reverse=True)
    return filas


def _sumar(C, n, gf, gc):
    s = C["gstats"][n]
    s["pj"] += 1
    s["gf"] += gf
    s["gc"] += gc
    s["g"] += gf > gc
    s["e"] += gf == gc
    s["p"] += gf < gc


def _partido(C, k, rng, P, local, visita, comp, neutral=False):
    rl, rv = np.array([C["r"][local]]), np.array([C["r"][visita]])
    if neutral:
        gl, gv, gana_l, pen = jugar_ko(rng, rl, rv, P["sorpresa"], localia=0.0)
        tanda = tanda_penales(rng, bool(gana_l[0])) if pen[0] else None
        p = nuevo_partido(C["nombre"], k + 1, C["rondas"][k], comp, local, visita, gl[0], gv[0],
                          tanda=tanda, gana=local if gana_l[0] else visita, neutral=True)
    else:
        gl, gv = jugar(rng, rl, rv, **P)
        p = nuevo_partido(C["nombre"], k + 1, C["rondas"][k], comp, local, visita, gl[0], gv[0])
    C["log"].append(p)
    return p


def _jugar_series(C, k, rng, P, series, vuelta, comp):
    for x in series:
        if not vuelta:
            x["ida"] = _partido(C, k, rng, P, x["b"], x["a"], comp)
            x["ga"], x["gb"] = x["ida"]["gv"], x["ida"]["gl"]
        else:
            p = _partido(C, k, rng, P, x["a"], x["b"], comp)
            x["ga"] += p["gl"]
            x["gb"] += p["gv"]
            if x["ga"] != x["gb"]:
                x["gana"] = x["a"] if x["ga"] > x["gb"] else x["b"]
            else:                                      # global empatado: penales
                pa = float(np.clip(0.5 + (C["r"][x["a"]] - C["r"][x["b"]]) / 400, 0.35, 0.65))
                gana_a = bool(rng.random() < pa)
                p["tanda"] = tanda_penales(rng, gana_a)
                p["pen"] = (sum(p["tanda"][0]), sum(p["tanda"][1]))
                x["pen"] = p["pen"]
                x["gana"] = x["a"] if gana_a else x["b"]
                p["gana"] = x["gana"]
            x["vuelta"] = p


def _campana(C, n):
    """Para ordenar cruces: el de mejor campaña en grupos cierra de local."""
    s = C["gstats"].get(n)
    if not s:
        return (0, 0, 0, C["r"][n])
    return (3 * s["g"] + s["e"], s["gf"] - s["gc"], s["gf"], C["r"][n])


def _siguiente(C, anteriores):
    """Cruces de la ronda siguiente: ganador de la serie 2j contra el de la 2j+1."""
    out = []
    for j in range(0, len(anteriores), 2):
        a, b = anteriores[j]["gana"], anteriores[j + 1]["gana"]
        if _campana(C, b) > _campana(C, a):
            a, b = b, a
        out.append(_serie(a, b))
    return out


def _octavos(rng, C, primeros, rivales, grupo_de):
    """Primeros (cierran de local) contra `rivales`, sin repetir grupo."""
    for _ in range(300):
        perm = [str(x) for x in rng.permutation(rivales)]
        if all(grupo_de.get(a) != grupo_de.get(b) for a, b in zip(primeros, perm)):
            break
    orden = [str(x) for x in rng.permutation(primeros)]
    emparejado = dict(zip(primeros, perm))
    return [_serie(a, emparejado[a]) for a in orden]


# ---------------------------------------------------------------- simulación por ronda
def listo(S, clave):
    """¿Puede jugarse la próxima ronda de esta copa? (la Sudamericana espera a la Libertadores)."""
    C = S["int"][clave]
    if C["ronda"] >= C["total"]:
        return False
    if clave == "sud":
        L = S["int"]["lib"]
        if C["ronda"] == 0 and L["ronda"] < 4:          # necesita los que pierden la Fase 3
            return False
        if C["ronda"] >= 5 and L["ronda"] < 10:         # necesita los 3° de los grupos
            return False
    return True


def simular_ronda_int(S, clave, P, rng):
    if not listo(S, clave):
        return
    C = S["int"][clave]
    k = C["ronda"]
    etapa = C["rondas"][k]
    if clave == "rec":
        _jugar_series(C, k, rng, P, C["llaves"]["Final"], k == 1, "Recopa")
        if k == 1:
            x = C["llaves"]["Final"][0]
            C["campeon"], C["subcampeon"] = x["gana"], (x["b"] if x["gana"] == x["a"] else x["a"])
    elif etapa.startswith("Grupos"):
        if C["grupos"] is None:
            _armar_grupos(S, C, rng)
        f = int(etapa.split()[-1]) - 1
        for g, eq in enumerate(C["grupos"]):
            for i, j in _FIX4[f]:
                p = _partido(C, k, rng, P, eq[i], eq[j], f"Grupo {GRUPOS[g]}")
                _sumar(C, eq[i], p["gl"], p["gv"])
                _sumar(C, eq[j], p["gv"], p["gl"])
        if f == 5:
            _cierre_grupos(S, C, rng)
    elif etapa == "Final":
        x = C["llaves"]["Final"][0]
        p = _partido(C, k, rng, P, x["a"], x["b"], "Final", neutral=True)
        x["ida"], x["gana"] = p, p["gana"]
        C["campeon"] = p["gana"]
        C["subcampeon"] = x["b"] if p["gana"] == x["a"] else x["a"]
    else:
        fase, pierna = etapa.split(" · ")
        series = C["llaves"][fase]
        _jugar_series(C, k, rng, P, series, pierna == "vuelta", fase)
        if pierna == "vuelta":
            _cierre_serie(S, C, fase, rng)
    C["ronda"] += 1


def _armar_grupos(S, C, rng):
    if C["nombre"] == LIB:
        equipos = C["directos"] + [x["gana"] for x in C["llaves"]["Fase 3"]]
        primero = C.get("cabeza")                     # el campeón vigente, cabeza del grupo A
    else:
        L = S["int"]["lib"]
        perd = [x["b"] if x["gana"] == x["a"] else x["a"] for x in L["llaves"]["Fase 3"]]
        for n in perd:
            C["r"][n] = L["r"][n]
            C["via"][n] = "Perdió la Fase 3 de la Libertadores"
        equipos = C["directos"] + perd
        primero = None
    C["grupos"] = _sorteo_grupos(rng, equipos, C["r"], primero)
    C["gstats"] = {n: {"pj": 0, "g": 0, "e": 0, "p": 0, "gf": 0, "gc": 0} for g in C["grupos"] for n in g}


def _cierre_grupos(S, C, rng):
    tablas = [tabla_grupo(C, g) for g in range(8)]
    grupo_de = {n: g for g, eq in enumerate(C["grupos"]) for n in eq}
    primeros = [t[0]["Equipo"] for t in tablas]
    segundos = [t[1]["Equipo"] for t in tablas]
    if C["nombre"] == LIB:
        C["terceros"] = [t[2]["Equipo"] for t in tablas]
        C["llaves"]["Octavos"] = _octavos(rng, C, primeros, segundos, grupo_de)
    else:
        L = S["int"]["lib"]
        terceros = L["terceros"]
        for n in terceros:
            C["r"][n] = L["r"][n]
            C["via"][n] = "3° de grupo en la Libertadores"
        # los 3° de la Libertadores cierran de local contra los 2° de la Sudamericana
        C["llaves"]["Playoffs"] = [_serie(a, str(b)) for a, b in zip(terceros, rng.permutation(segundos))]
        C["primeros"] = primeros
        C["grupo_de"] = grupo_de


def _cierre_serie(S, C, fase, rng):
    series = C["llaves"][fase]
    if fase == "Fase 2":
        ganadores = [x["gana"] for x in series]
        C["llaves"]["Fase 3"] = [_serie(*sorted(par, key=lambda n: -C["r"][n]))
                                 for par in zip(*[iter([str(x) for x in rng.permutation(ganadores)])] * 2)]
    elif fase == "Playoffs":
        ganadores = [x["gana"] for x in series]
        C["llaves"]["Octavos"] = _octavos(rng, C, C["primeros"], ganadores, C["grupo_de"])
    elif fase in ("Octavos", "Cuartos", "Semifinal"):
        sig = {"Octavos": "Cuartos", "Cuartos": "Semifinal", "Semifinal": "Final"}[fase]
        C["llaves"][sig] = _siguiente(C, series)


def terminadas(S):
    return all(C["ronda"] >= C["total"] for C in S["int"].values())


def fase_actual(C):
    if C["ronda"] >= C["total"]:
        return "Terminada"
    return C["rondas"][C["ronda"]]

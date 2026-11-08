"""Copa AUF Uruguay: motor de la copa (sin Streamlit). Se enchufa al registro con `CopaUruguay` (copas/registro.py).

Formato 2026 (nuevo formato anunciado por la AUF; fuente: Montevideo Portal, lanzamiento de la Copa AUF Uruguay 2026):
  * 40 clubes: los 16 de la Liga AUF Uruguaya, los 8 mejores de la Segunda División (tabla del Torneo Competencia, la
    primera fase de su Tabla Anual) y 16 amateurs (en la realidad, 10 de la OFI, 4 de la Divisional C y 2 de la D).
  * Fase de grupos entre los 24 profesionales: 6 grupos de 4, una rueda (3 fechas). Pasan los 2 primeros de cada grupo y
    los 4 mejores terceros (16 en total).
  * Dieciseisavos: los profesionales juegan entre sí y los amateurs entre sí (8 + 8 cruces). Desde octavos todos
    se mezclan en un mismo cuadro. Semifinales y final, a partido único en cancha neutral.
  * El campeón obtiene el cupo Uruguay 4 de la Libertadores (Fase 1). Si ya clasificó por la liga, el cupo vuelve a la Tabla
    Anual (copas/conmebol.py, `_sortear_pais`).

Simplificaciones (a revisar contra el reglamento de la AUF; ver docs/LIGAS_EXTERIOR.md):
  * Los amateurs son 16 clubes de la Primera Amateur (la tercera división, ligas/uruguay_amateur.py; sus clubes salen de
    datos/json/liga_uruguay.json, `tercera`): se sortean al arrancar la copa, con un poco más de chances los de mejor
    media. No se juega la clasificatoria del interior ni de la C.
  * Grupos: sorteo por 4 bombos según la media. El real puede tener otras reglas (por ejemplo, separar a los del interior).
  * Todas las rondas son a partido único (con penales si empatan); el local es el mejor sembrado en dieciseisavos
    de los profesionales y el primero que sale en el sorteo en octavos y cuartos. El real puede prever otra cosa.
  * Los cruces de dieciseisavos de los profesionales siguen la siembra de la fase de grupos: el mejor contra el peor.
  * Los 8 de la Segunda se toman al cerrar el Torneo Competencia (no hay que esperar al final de la fase regular).

El estado de la copa es un diccionario común y corriente con la misma forma que el de una liga del exterior
(`ligas/exterior.py`): `rondas`, `fecha`, `log`, `nombres`, `r` y `E`. Por eso se juega con `jugar_ronda` y se guarda en el
`.afa` sin tocar nada.
"""

import numpy as np

from ligas.exterior import partidos_de_ronda, ronda, rueda, stats_vacias, tabla
from motor.fechas import desde

NOMBRE = "Copa AUF Uruguay"
PAIS = "Uruguay"
CLAVE = "copa_uy"

GRUPOS = 6
EQUIPOS_PRO = 24                       # 16 de Primera + 8 de Segunda
EQUIPOS_AMATEUR = 16
DE_SEGUNDA = 8
FECHAS_GRUPOS = 3
PASAN_TERCEROS = 4

ETAPA_GRUPOS = "Grupos"
ETAPAS_KO = [("Dieciseisavos", "Dieciseisavos de final", False),
             ("Octavos", "Octavos de final", False),
             ("Cuartos", "Cuartos de final", False),
             ("Semifinal", "Semifinal", True),
             ("Final", "Final", True)]
# (mes, a partir del día): miércoles, cada dos semanas desde agosto (el real arranca la primera semana de agosto)
DIAS = [(8, 4), (8, 18), (9, 1), (9, 15), (9, 29), (10, 13), (10, 27), (11, 10)]
MIERCOLES = 2
TOTAL_RONDAS = FECHAS_GRUPOS + len(ETAPAS_KO)


def nueva_copa(anio):
    """Copa de la temporada, todavía sin sortear (se sortea cuando termina el Torneo Competencia de la Segunda)."""
    rondas = [ronda(ETAPA_GRUPOS, f"Fase de grupos · fecha {k + 1}", "Fase de grupos",
                    desde(anio, *DIAS[k], MIERCOLES), suma="Grupos") for k in range(FECHAS_GRUPOS)]
    for k, (etapa, rotulo, neutral) in enumerate(ETAPAS_KO):
        rondas.append(ronda(etapa, rotulo, rotulo, desde(anio, *DIAS[FECHAS_GRUPOS + k], MIERCOLES), ko=True,
                            neutral=neutral))
    return {"formato": "copa_uruguay", "nombre": NOMBRE, "pais": PAIS, "clave": CLAVE, "sorteada": False,
            "nombres": [], "r": np.array([], dtype=float), "origen": [], "rondas": rondas, "fecha": 0, "log": [],
            "E": {"Grupos": stats_vacias(0)}, "grupos": [], "campeon": None, "subcampeon": None}


def sortear_amateurs(rng, pool, r_de, k=EQUIPOS_AMATEUR):
    """k clubes de la Primera Amateur (tercera división) que juegan la copa: al azar, con un poco más de chances los de mejor media."""
    pool = list(pool)
    k = min(k, len(pool))
    m = np.array([r_de(n) for n in pool], dtype=float)
    w = np.exp((m - m.max()) / 6.0)
    return [pool[int(i)] for i in rng.choice(len(pool), size=k, replace=False, p=w / w.sum())]


def sortear(L, rng, pro, r_pro, amateurs, r_amat):
    """Sortea la copa: `pro` = los 24 profesionales, `amateurs` = los 16 amateurs (con sus medias). Arma los 6 grupos por
    bombos de media y las tres fechas de la fase de grupos."""
    n_pro = len(pro)
    if n_pro != EQUIPOS_PRO or len(amateurs) != EQUIPOS_AMATEUR:
        raise ValueError(f"{NOMBRE}: hacen falta {EQUIPOS_PRO} profesionales y {EQUIPOS_AMATEUR} amateurs "
                         f"y hay {n_pro} y {len(amateurs)}")
    L["nombres"] = list(pro) + list(amateurs)
    L["r"] = np.array(list(r_pro) + list(r_amat), dtype=float)
    L["origen"] = ["Profesional"] * n_pro + ["Amateur"] * len(amateurs)
    L["E"] = {"Grupos": stats_vacias(len(L["nombres"]))}
    orden = np.argsort(-np.asarray(r_pro, dtype=float), kind="stable")
    grupos = [[] for _ in range(GRUPOS)]
    por_bombo = n_pro // 4
    for b in range(4):
        for g, i in zip(rng.permutation(GRUPOS), orden[b * por_bombo:(b + 1) * por_bombo]):
            grupos[int(g)].append(int(i))
    L["grupos"] = [sorted(g) for g in grupos]
    ruedas = [rueda(rng, g) for g in L["grupos"]]
    grupo_de = {i: f"Grupo {'ABCDEF'[k]}" for k, g in enumerate(L["grupos"]) for i in g}
    for f in range(FECHAS_GRUPOS):
        R = L["rondas"][f]
        R["pares"] = [p for rr in ruedas for p in rr[f]]
        R["grupo_de"] = grupo_de
    L["sorteada"] = True
    return L
def _ganadores(L, n):
    """Ids de los ganadores de la ronda n (1, 2, ...), en el orden de los cruces."""
    return [L["nombres"].index(p["gana"]) for p in partidos_de_ronda(L, n)]


def tablas_grupos(L):
    """[(nombre del grupo, tabla)] con la tabla de cada grupo."""
    return [(f"Grupo {'ABCDEF'[k]}", tabla(L, L["E"]["Grupos"], g)) for k, g in enumerate(L["grupos"])]


def clasificados_grupos(L):
    """Los 16 profesionales que pasan, ordenados por siembra: primero los ganadores de grupo, después los segundos y
    después los 4 mejores terceros (cada bloque por puntos, diferencia de gol y goles a favor)."""
    tablas = [t for _, t in tablas_grupos(L)]

    def mejores(pos):
        filas = [t.iloc[pos] for t in tablas]
        filas.sort(key=lambda f: (-int(f["Pts"]), -int(f["DG"]), -int(f["GF"])))
        return [int(f["id"]) for f in filas]
    return mejores(0) + mejores(1) + mejores(2)[:PASAN_TERCEROS]


def _armar_dieciseisavos(L, rng):
    pro = clasificados_grupos(L)
    cruces = [(pro[k], pro[len(pro) - 1 - k]) for k in range(len(pro) // 2)]
    amat = [int(i) for i in rng.permutation([i for i, o in enumerate(L["origen"]) if o == "Amateur"])]
    cruces += list(zip(amat[0::2], amat[1::2]))
    L["rondas"][FECHAS_GRUPOS]["pares"] = cruces


def avanzar(L, rng):
    """Se llama después de cada ronda jugada: arma los cruces de la que sigue o, al terminar la final, define al campeón."""
    if not L["sorteada"]:
        return
    n = L["fecha"]
    if n == FECHAS_GRUPOS and L["rondas"][n]["pares"] is None:
        _armar_dieciseisavos(L, rng)
    elif FECHAS_GRUPOS < n < TOTAL_RONDAS and L["rondas"][n]["pares"] is None:
        gana = _ganadores(L, n)
        if n == FECHAS_GRUPOS + 1:
            gana = [int(i) for i in rng.permutation(gana)]
        L["rondas"][n]["pares"] = list(zip(gana[0::2], gana[1::2]))
    elif n >= TOTAL_RONDAS and L["campeon"] is None:
        p = partidos_de_ronda(L, TOTAL_RONDAS)[0]
        L["campeon"] = p["gana"]
        L["subcampeon"] = p["local"] if p["gana"] == p["visita"] else p["visita"]


def llaves(L, desde_etapa=1):
    """Datos del cuadro de eliminación: [(rótulo de la ronda, [partido o None])], de la etapa `desde_etapa` (0 =
    dieciseisavos, 1 = octavos) a la final. Un partido es un dict con local, visita, gl, gv, gana, pen, neutral y dia
    (con gl, gv y gana vacíos si todavía no se jugó); None si el cruce no se conoce."""
    out = []
    for k, (etapa, rotulo, neutral) in enumerate(ETAPAS_KO):
        if k < desde_etapa:
            continue
        i = FECHAS_GRUPOS + k
        R = L["rondas"][i]
        n = 2 ** (len(ETAPAS_KO) - 1 - k)
        if not L["sorteada"] or R["pares"] is None:
            ms = [None] * n
        elif i < L["fecha"]:
            ms = [{**p, "dia": R["dia"]} for p in partidos_de_ronda(L, i + 1)]
        else:
            ms = [{"local": L["nombres"][a], "visita": L["nombres"][b], "gl": "", "gv": "", "gana": None, "pen": None,
                   "neutral": R["neutral"], "dia": R["dia"]} for a, b in R["pares"]]
        out.append((rotulo, ms))
    return out


def definicion(L, temp):
    """Resumen de la copa de la temporada `temp` para la sección Campeones: campeón, subcampeón y los partidos de
    semifinales y final con su día."""
    partidos = [{**p, "dia": L["rondas"][p["fecha"] - 1]["dia"]} for p in L["log"] if p["comp"] in ("Semifinal", "Final")]
    return {"temp": temp, "campeon": L["campeon"], "subcampeon": L.get("subcampeon"), "partidos": partidos}

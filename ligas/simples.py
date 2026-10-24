"""Primera B, Primera C y Promocional Amateur: todos contra todos con la misma mecánica (ida y vuelta con 24 equipos
o menos, una sola vuelta con 25 o más).
"""

import math

import numpy as np

from motor.incidentes import revisar_liga
from motor.nucleo import (
    STATS,
    _fila_historial,
    df_stats,
    generar_fixture,
    jugar,
    mods_ids,
    nuevo_partido,
    sumar_partidos,
    cruces_mejor_peor,
    jugar_reducido_federal,
    tanda_penales,
    tope_descensos,
    unir,
)
from ligas.desempates import bloque_empatado, duelo_o_liguilla
from ligas.primera import definir_bloque


# ----------------------------------------------------------------------------
# MOTOR PRIMERA B, PRIMERA C y Torneo Promocional Amateur (Nueva Primera D)
# ----------------------------------------------------------------------------
# ---- Modo dios: ascensos, descensos y reducido de la Primera B y la Primera C ----------------------------
ASC_MAX, DESC_MAX, RED_MAX = 6, 8, 8        # tope de ascensos directos, descensos y equipos del reducido
CLAVES_CFG = ("pb", "pc", "pd")             # ligas configurables
CON_DESCENSOS = ("pb", "pc")                # el Promocional no tiene descensos
NOMBRE_CLAVE = {"Primera B": "pb", "Primera C": "pc", "Promocional Amateur": "pd"}


def cfg_simple(S, clave):
    """Lo elegido en el Modo dios: ascienden directo, descienden (None = automático: del 18° para abajo), si hay\n    reducido por un ascenso más y cuántos equipos lo juegan (los que siguen a los ascendidos directos)."""
    c = S.setdefault("cfg", {}).setdefault(clave, {})
    c.setdefault("directos", 2)
    c.setdefault("descensos", None)
    c.setdefault("reducido", False)
    c.setdefault("red_equipos", 4)
    return c


IDA_VUELTA_MAX_SIMPLE = 24                  # con 24 equipos o menos: ida y vuelta; con 25 o más: una sola vuelta


def hay_vuelta(n):
    """True si la liga de n equipos se juega ida y vuelta (24 o menos); con 25 o más es una sola vuelta."""
    return n <= IDA_VUELTA_MAX_SIMPLE


def formato_simple(n):
    return "Ida y vuelta" if hay_vuelta(n) else "Una sola vuelta"


def desc_auto(n):
    return max(0, n - 17) if n >= 18 else 0


def etapas_reducido(m):
    """Rondas del reducido con m equipos (los peor ubicados juegan una primera ronda y los mejores esperan)."""
    rondas = math.ceil(math.log2(m))
    juegan = 2 * (m - 2 ** (rondas - 1))
    nombres = {2: "Final del reducido", 4: "Semifinales del reducido", 8: "Cuartos de final del reducido",
               16: "Octavos de final del reducido"}
    etapas = ["Eliminatoria preliminar" if (k == 0 and juegan < 2 ** rondas and rondas > 1) else nombres[2 ** (rondas - k)]
              for k in range(rondas)]
    return rondas, juegan, etapas


def plan_simple(n, directos=2, descensos=None, reducido=False, red_equipos=4):
    """Plan de la temporada de una liga de n equipos, ya acotado para que sea posible."""
    d = max(0, min(int(directos), n - 2))
    desc = desc_auto(n) if descensos is None else int(descensos)
    desc = max(0, min(desc, n - d - 1, tope_descensos(n, DESC_MAX)))
    m = max(2, min(int(red_equipos), RED_MAX, n - d - desc))
    if not reducido or n - d - desc < 2:
        return {"directos": d, "desc": desc, "reducido": False, "equipos": 0, "rondas": 0, "juegan": 0, "etapas": []}
    rondas, juegan, etapas = etapas_reducido(m)
    return {"directos": d, "desc": desc, "reducido": True, "equipos": m, "rondas": rondas, "juegan": juegan,
            "etapas": etapas}


def plan_de(L, clave=None):
    """Plan de la liga (las partidas viejas no lo tienen: 2 ascensos y descenso del 18° para abajo, sólo PB y PC)."""
    if L.get("plan") is None:
        L["plan"] = plan_simple(len(L["nombres"]), descensos=None if clave in CON_DESCENSOS else 0)
    return L["plan"]


def destino_liga(pos, total, plan):
    if pos <= plan["directos"]: return "Ascenso directo"
    if plan["reducido"] and pos <= plan["directos"] + plan["equipos"]: return "Reducido"
    if plan["desc"] and pos > total - plan["desc"]: return "Desciende"
    return ""


def nueva_estructura_liga(S_LIGA, rng, S=None, clave=None):
    n = len(S_LIGA["nombres"])
    if S is not None and clave in CLAVES_CFG:               # Modo dios: lo elegido para esta temporada
        c = cfg_simple(S, clave)
        S_LIGA["plan"] = plan_simple(n, c["directos"], c["descensos"] if clave in CON_DESCENSOS else 0,
                                     c["reducido"], c["red_equipos"])
    else:
        S_LIGA["plan"] = plan_simple(n, descensos=None if clave in CON_DESCENSOS else 0)
    S_LIGA["red"], S_LIGA["bracket"], S_LIGA["asc_reducido"], S_LIGA["ascendidos"] = None, [], None, []
    base = generar_fixture(n)
    fechas = [[(int(a), int(b)) for a, b in pares] for pares in base]
    if hay_vuelta(n):                                          # 24 equipos o menos: ida y vuelta
        fechas += [[(v, l) for l, v in fecha] for fecha in fechas]
    S_LIGA["fechas"] = fechas
    S_LIGA["total"] = len(fechas)
    S_LIGA["fecha"] = 0
    for k in STATS:
        S_LIGA[k] = np.zeros(n, dtype=int)
    S_LIGA["historial"] = []
    S_LIGA["log"] = []
    S_LIGA["pos_hist"] = []
    S_LIGA["campeon"] = None
    S_LIGA["asc_directo"] = []
    S_LIGA["desc_directo"] = []
    S_LIGA["orden_final"] = None
    S_LIGA["desempate_pendiente"] = False
    S_LIGA["ids_desempate"] = []
    S_LIGA["motivos_desempate"] = []        # si no, la tabla nueva sigue marcando el desempate anterior


def tabla_liga(L, clave):
    """Tabla de una liga simple (clave: "pb", "pc" o "pd") con su destino y los desempates marcados."""
    df = df_stats(L["nombres"], L["r"], L, np.arange(len(L["nombres"])))
    if L.get("orden_final") is not None:
        df = df.set_index("id").loc[L["orden_final"]].reset_index()

    df.insert(0, "Pos", df.index + 1)
    df["Destino"] = [destino_liga(p, len(L["nombres"]), plan_de(L, clave)) for p in df["Pos"]]

    if L.get("motivos_desempate"):
        ids_actuales = df["id"].to_numpy()
        for motivo in L["motivos_desempate"]:
            partes = motivo.split()
            nombre_frontera = partes[1]
            inicio, fin = map(int, partes[2].split("-"))
            ids_bloque = ids_actuales[inicio:fin]
            df.loc[df["id"].isin(ids_bloque), "Destino"] = f"Desempate {nombre_frontera}"

    return df


def tabla_pb(SPB):
    return tabla_liga(SPB, "pb")


def tabla_pc(SPC):
    return tabla_liga(SPC, "pc")


def tabla_pd(SPD):
    return tabla_liga(SPD, "pd")


def simular_fecha_liga(S_LIGA, P, rng, nombre_liga, fn_tabla):
    """Juega la próxima fecha de la liga. Al llegar a la última detecta los empates que definen campeón, ascensos o
    descenso (se juegan en una fecha extra) y cierra la temporada."""
    f = S_LIGA["fecha"]
    if f >= S_LIGA["total"]:
        return
    es_desempate = S_LIGA.get("desempate_pendiente") and f == S_LIGA["total"] - 1
    if es_desempate:
        _jugar_desempates(S_LIGA, P, rng, nombre_liga, fn_tabla, f)
    else:
        _jugar_fecha_normal(S_LIGA, P, rng, nombre_liga, f)

    df = fn_tabla(S_LIGA)
    ids = df["id"].to_numpy()
    pos = np.zeros(len(S_LIGA["nombres"]), dtype=int)
    pos[ids] = np.arange(1, len(ids) + 1)
    S_LIGA["pos_hist"].append((1, pos))
    S_LIGA["fecha"] += 1

    ya_se_jugo = S_LIGA.get("orden_final") is not None
    if S_LIGA["fecha"] == S_LIGA["total"] and not ya_se_jugo:
        if _armar_desempates(S_LIGA, nombre_liga, df, ids):
            return                                   # hay empates: se agregó una fecha para definirlos
    if S_LIGA["fecha"] == S_LIGA["total"]:
        _cerrar_liga(S_LIGA, P, rng, nombre_liga, ids, ya_se_jugo)


def _jugar_fecha_normal(S_LIGA, P, rng, nombre_liga, f):
    r, nom = S_LIGA["r"], S_LIGA["nombres"]
    pares = S_LIGA["fechas"][f]
    h = np.array([x[0] for x in pares])
    a = np.array([x[1] for x in pares])
    gh, ga = jugar(rng, r[h], r[a], **P, **mods_ids(rng, nom, h, a))
    sumar_partidos(S_LIGA, h, a, gh, ga)
    S_LIGA["historial"].append(_fila_historial(S_LIGA, [nombre_liga] * len(h), h, a, gh, ga, ""))
    for x, y, g1, g2 in zip(h, a, gh, ga):
        S_LIGA["log"].append(nuevo_partido(nombre_liga, f + 1, f"Fecha {f + 1}", "Liga", nom[x], nom[y], g1, g2))
    revisar_liga(S_LIGA, S_LIGA["log"][-len(h):], rng)


def _jugar_desempates(S_LIGA, P, rng, nombre_liga, fn_tabla, f):
    """Fecha extra: juega los duelos / liguillas que desempatan los bloques detectados al terminar la liga."""
    r, nom = S_LIGA["r"], S_LIGA["nombres"]
    df_prev = fn_tabla(S_LIGA)
    ids_finales = df_prev["id"].to_numpy().copy()

    def registrar(a, b, gl, gv, tanda, gana, comp):
        partido = nuevo_partido(nombre_liga, f + 1, "Desempate", comp, nom[a], nom[b],
                                gl, gv, tanda=tanda, gana=nom[gana], neutral=True)
        S_LIGA["log"].append(partido)
        return partido

    for motivo in S_LIGA.get("motivos_desempate", []):
        partes = motivo.split()
        nombre_frontera = partes[1]
        inicio, fin = map(int, partes[2].split("-"))
        bloque = ids_finales[inicio:fin]
        # cupos: cuántos del bloque logran el objetivo (título / ascenso / permanencia)
        pl = plan_de(S_LIGA, NOMBRE_CLAVE.get(nombre_liga))
        frontera = {"Campeonato": 0, "Ascenso": max(0, pl["directos"] - 1),
                    "Permanencia": len(nom) - pl["desc"] - 1}.get(nombre_frontera, 0)
        ids_finales[inicio:fin] = definir_bloque(
            rng, r, bloque, P["sorpresa"], registrar, nombre_frontera, f"Liguilla {nombre_frontera}",
            nom, campeonato=nombre_frontera == "Campeonato", cupos=frontera + 1 - inicio)

    S_LIGA["orden_final"] = ids_finales
    S_LIGA["desempate_pendiente"] = False


def _armar_desempates(S_LIGA, nombre_liga, df, ids):
    """Busca empates en puntos justo en las fronteras que importan (campeón, último ascenso directo, última plaza de
    permanencia). Si hay, agrega una fecha para desempatar y devuelve True."""
    pts = df["Pts"].to_numpy()
    partidos_desempate = []
    ids_involucrados = []
    motivos = []

    pl = plan_de(S_LIGA, NOMBRE_CLAVE.get(nombre_liga))
    fronteras = [(0, "Campeonato")]
    if pl["directos"] >= 2:                                   # último ascenso directo contra el que sigue
        fronteras.append((pl["directos"] - 1, "Ascenso"))
    if pl["desc"] and len(ids) - pl["desc"] - 1 >= 1:         # última plaza de permanencia contra la primera que baja
        fronteras.append((len(ids) - pl["desc"] - 1, "Permanencia"))

    bloques_procesados = set()
    for idx_frontera, nombre_frontera in fronteras:
        if pts[idx_frontera] == pts[idx_frontera + 1]:
            inicio, fin = bloque_empatado(pts, idx_frontera)       # dónde empieza y termina el bloque de empatados
            if inicio not in bloques_procesados:
                bloques_procesados.add(inicio)
                ids_bloque = [int(i) for i in ids[inicio:fin]]
                ids_involucrados.extend(ids_bloque)
                tipo, partido = duelo_o_liguilla(ids_bloque)
                motivos.append(f"{tipo} {nombre_frontera} {inicio}-{fin}")
                partidos_desempate.append(partido)

    if not partidos_desempate:
        return False
    S_LIGA["desempate_pendiente"] = True
    S_LIGA["ids_desempate"] = ids_involucrados
    S_LIGA["motivos_desempate"] = motivos
    S_LIGA["total"] += 1
    S_LIGA["fechas"].append(partidos_desempate)
    return True


def _cerrar_liga(S_LIGA, P, rng, nombre_liga, ids, ya_se_jugo):
    """Última fecha jugada: campeón, ascendidos y descendidos directos y, si hay, el reducido."""
    ids_cierre = S_LIGA["orden_final"] if ya_se_jugo else ids
    pl = plan_de(S_LIGA, NOMBRE_CLAVE.get(nombre_liga))
    n_eq, d = len(ids_cierre), pl["directos"]
    S_LIGA["campeon"] = int(ids_cierre[0])
    S_LIGA["asc_directo"] = [int(i) for i in ids_cierre[:d]]
    S_LIGA["ascendidos"] = list(S_LIGA["asc_directo"])
    if nombre_liga in ("Primera B", "Primera C"):
        S_LIGA["desc_directo"] = [int(i) for i in ids_cierre[n_eq - pl["desc"]:]] if pl["desc"] else []
    if pl["reducido"]:
        _jugar_reducido(S_LIGA, rng, P, nombre_liga, ids_cierre, pl)


def _jugar_reducido(L, rng, P, nombre_liga, ids, pl):
    """Reducido por un ascenso más: eliminación directa entre los que siguen a los ascendidos directos (se juega de\n    una vez al cerrar la liga; el ganador asciende). Los mejores ubicados esperan y los peores juegan la primera ronda."""
    nom, r, d, m, juegan = L["nombres"], L["r"], pl["directos"], pl["equipos"], pl["juegan"]
    pts = 3 * L["g"] + L["e"]

    def bloque(idx, seed0):
        idx = np.asarray(idx)[None, :]
        return {"id": idx, "pts": pts[idx], "seed": np.arange(seed0, seed0 + idx.shape[1])[None, :]}

    esperan = bloque(ids[d:d + m - juegan], d + 1)
    T = bloque(ids[d + m - juegan:d + m], d + 1 + m - juegan)
    L["red"] = [(i + 1, nom[ids[d + i]]) for i in range(m)]
    L["bracket"] = []
    for etapa in range(pl["rondas"]):
        if etapa > 0:
            T = unir(esperan, T) if esperan["id"].shape[1] > 0 and etapa == 1 else T
        A, B = cruces_mejor_peor(T)
        final = etapa == pl["rondas"] - 1
        loc, vis, gl, gv, gan, per, pen = jugar_reducido_federal(rng, r, A, B, P["sorpresa"], final, nombres=nom)
        ronda = []
        for li, vi, g1, g2, wi, p in zip(loc["id"][0], vis["id"][0], gl[0], gv[0], gan["id"][0], pen[0]):
            tanda = tanda_penales(rng, wi == li) if (p and final) else None
            partido = nuevo_partido(nombre_liga, L["total"] + 1 + etapa, "Reducido", pl["etapas"][etapa],
                                    nom[li], nom[vi], g1, g2, tanda=tanda, gana=nom[wi], neutral=final)
            ronda.append(partido)
            L["log"].append(partido)
        L["bracket"].append(ronda)
        T = gan
    L["asc_reducido"] = int(T["id"][0, 0])
    L["ascendidos"] = L["asc_directo"] + [L["asc_reducido"]]

"""Federal A: grupos, zonas Campeonato y Descenso, desempates, reducido y cómo se juega cada fecha.
"""

import numpy as np
import pandas as pd

from datos.equipos import F_GRUPOS_NOMBRES, region_de
from motor.incidentes import revisar_liga
from motor.nucleo import (
    STATS,
    _fila_historial,
    cruces_mejor_peor,
    df_stats,
    generar_fixture,
    jugar,
    jugar_reducido_federal,
    nuevo_partido,
    sumar_partidos,
    tanda_penales,
    unir,
)
from ligas.primera import definir_bloque


# Federal A: la fase 1 tiene 5 grupos "por cercanía" cuyo tamaño no es fijo (el plantel
# cambia con los ascensos/descensos), así que su cantidad de fechas se calcula por
# temporada (ver nueva_estructura_f), no acá.
F_ZONA_TAM = 10                   # Campeonato y Descenso en la fase 2 (10 y 10)


F_F2_RONDAS = F_ZONA_TAM - 1       # 9 fechas, una rueda


F_RED = 3                          # eliminatoria, semifinales, final


F_ETAPAS = ["Eliminatoria preliminar", "Semifinales del reducido", "Final del reducido"]


F_MIN = 36                         # mínimo de equipos del Federal A (si falta, reubicación)


F_DESC = 6                         # los 6 últimos de la zona Descenso bajan al Regional Amateur


def destino_f1(pos):
    return "→ Zona Campeonato" if pos <= 4 else "→ Zona Descenso"


def destino_f2(z, pos, n=0):
    if z == 0:
        if pos <= 3:
            return "Ascenso directo"
        return "Reducido" if pos <= 8 else ""
    return "Desciende" if pos > n - F_DESC else ""


def rotulo_f(SF, n):
    f1 = SF["f1_rondas"]
    if n <= f1:
        return f"Fecha {n} · Fase 1"
    if n <= f1 + SF.get("f2_rondas", 0):
        return f"Fecha {n} · Fase 2 (fecha {n - f1})"
    return f"Fecha {n} · {F_ETAPAS[n - f1 - SF['f2_rondas'] - 1]}"


# ----------------------------------------------------------------------------
# MOTOR FEDERAL A
# ----------------------------------------------------------------------------
def nueva_estructura_f(SF, rng):
    n = len(SF["nombres"])
    
    # Agrupar inicialmente por la región ideal
    por_region = {g: [] for g in F_GRUPOS_NOMBRES}
    for i, nom in enumerate(SF["nombres"]):
        por_region[region_de(nom)].append(i)

    # Formar la lista general y dividirla para que queden balanceados (7 u 8 equipos)
    todos = []
    for g in F_GRUPOS_NOMBRES:
        todos.extend(por_region[g])

    tamanos = [n // 5 + (1 if x < n % 5 else 0) for x in range(5)]
    SF["grupos"] = []
    idx = 0
    for t in tamanos:
        SF["grupos"].append(np.array(todos[idx:idx+t], dtype=int))
        idx += t

    SF["grupo_de"] = np.zeros(n, dtype=int)
    for g, ids in enumerate(SF["grupos"]):
        SF["grupo_de"][ids] = g

    idas = [generar_fixture(len(ids)) for ids in SF["grupos"]]
    rondas_ida = max((len(f) for f in idas), default=0)
    fechas = []
    for k in range(rondas_ida):
        fecha = []
        for ids, f in zip(SF["grupos"], idas):
            if k < len(f):
                fecha += [(int(ids[a]), int(ids[b])) for a, b in f[k]]
        fechas.append(fecha)
    # Ida y vuelta
    fechas += [[(v, l) for l, v in fecha] for fecha in fechas]
    SF["fechas"] = fechas
    SF["f1_rondas"] = rondas_ida * 2
    
    # Precalculamos las fechas de la fase 2 dinámicamente
    n_campeonato = len(SF["grupos"]) * 4
    n_descenso = n - n_campeonato
    
    # Si la cantidad de equipos es par, las fechas son N-1. Si es impar, son N.
    rondas_camp = n_campeonato - 1 if n_campeonato % 2 == 0 else n_campeonato
    rondas_desc = n_descenso - 1 if n_descenso % 2 == 0 else n_descenso
    
    SF["f2_rondas"] = max(rondas_camp, rondas_desc)
    SF["total"] = SF["f1_rondas"] + SF["f2_rondas"] + F_RED 

    SF["fecha"] = 0
    for k in STATS:
        SF[k] = np.zeros(n, dtype=int)
    SF["historial"] = []
    SF["log"] = []
    SF["pos_hist"] = []
    SF["bracket"] = []
    SF["tablas_f1"] = None
    SF["zonas2"] = None
    SF["zona2_de"] = None
    SF["fechas2"] = None
    SF["ord2"] = None
    SF["campeon"] = None
    SF["asc_directo"] = []
    SF["red"] = None
    SF["entrantes"] = None
    SF["asc_reducido"] = None
    SF["ascendidos"] = []
    SF["orden_f2_camp"] = None      # orden de la zona Campeonato tras el desempate por el título
    SF["desempate_camp"] = None     # info del desempate por el campeonato (si lo hubo)
    SF["orden_f2_desc"] = None      # orden de la zona Descenso tras el desempate por la permanencia
    SF["desempate_desc"] = None     # info del desempate por la permanencia (si lo hubo)
    SF["descendidos"] = []          # los 6 que bajan al Regional Amateur


def tabla_f_grupo(SF, g):
    """Tabla del grupo `g` (0-4, por cercanía) de la fase 1."""
    df = df_stats(SF["nombres"], SF["r"], SF, SF["grupos"][g])
    df.insert(0, "Pos", df.index + 1)
    df["Destino"] = [destino_f1(p) for p in df["Pos"]]
    return df


def tabla_f_f2(SF, z):
    """Tabla de la zona de la fase 2 (0 Campeonato, 1 Descenso)."""
    df = df_stats(SF["nombres"], SF["r"], SF, SF["zonas2"][z])
    orden = SF.get("orden_f2_camp") if z == 0 else SF.get("orden_f2_desc")
    if orden is not None:
        df = df.set_index("id").loc[orden].reset_index()
    df.insert(0, "Pos", df.index + 1)
    df["Destino"] = [destino_f2(z, p, len(df)) for p in df["Pos"]]
    return df


def desempate_campeon_f(SF, P, rng, n_fecha):
    """Federal A: si dos o más terminan igualados en puntos en el 1° puesto de la zona
    Campeonato, el título se define SIEMPRE con desempate (2 equipos: partido único; 3 o
    más: liguilla a partido único), en cancha neutral y con penales si empatan.
    El ganador queda 1°; el resto del bloque mantiene el orden por diferencia de gol.
    Las demás posiciones se siguen definiendo por diferencia de gol."""
    df = tabla_f_f2(SF, 0)
    pts, ids = df["Pts"].to_numpy(), df["id"].to_numpy()
    if len(pts) < 2 or pts[0] != pts[1]:
        return
    fin = 1
    while fin < len(pts) and pts[fin] == pts[0]:
        fin += 1
    bloque = [int(i) for i in ids[:fin]]
    r, nom = SF["r"], SF["nombres"]
    partidos = []

    def registrar(a, b, gl, gv, tanda, gana, comp):
        partido = nuevo_partido("Federal A", n_fecha, "Desempate por el campeonato", comp, nom[a], nom[b],
                                gl, gv, tanda=tanda, gana=nom[gana], neutral=True)
        partidos.append(partido)
        SF["log"].append(partido)
        return partido

    # El campeón sale del desempate (y, si la liguilla vuelve a quedar pareja arriba, de otra
    # definición entre los igualados: nunca por diferencia de gol). El resto del bloque
    # mantiene el orden de la tabla.
    campeon = definir_bloque(rng, r, bloque, P["sorpresa"], registrar, "Desempate campeonato",
                             "Liguilla por el campeonato", nom, campeonato=True, cupos=1)[0]
    orden = [campeon] + [e for e in bloque if e != campeon] + [int(i) for i in ids[fin:]]
    SF["orden_f2_camp"] = np.array(orden)
    SF["desempate_camp"] = {"equipos": [nom[e] for e in bloque], "partidos": partidos,
                            "campeon": nom[campeon]}


def desempate_descenso_f(SF, P, rng, n_fecha):
    """Federal A: descienden al Regional los 6 últimos de la zona Descenso. Si el límite
    (6° desde abajo) queda igualado en puntos, se define con desempate como en las demás
    ligas (2 equipos: partido único; 3 o más: liguilla), en cancha neutral y con penales si
    empatan: nunca por diferencia de gol."""
    df = tabla_f_f2(SF, 1)
    pts, ids = df["Pts"].to_numpy(), df["id"].to_numpy()
    n = len(ids)
    corte = n - F_DESC                               # 1er puesto que desciende (índice)
    if corte >= 1 and pts[corte - 1] == pts[corte]:
        inicio = corte - 1
        while inicio > 0 and pts[inicio - 1] == pts[corte]:
            inicio -= 1
        fin = corte + 1
        while fin < n and pts[fin] == pts[corte]:
            fin += 1
        bloque = [int(i) for i in ids[inicio:fin]]
        r, nom = SF["r"], SF["nombres"]
        partidos = []

        def registrar(a, b, gl, gv, tanda, gana, comp):
            partido = nuevo_partido("Federal A", n_fecha, "Desempate por la permanencia", comp, nom[a],
                                    nom[b], gl, gv, tanda=tanda, gana=nom[gana], neutral=True)
            partidos.append(partido)
            SF["log"].append(partido)
            return partido

        orden = definir_bloque(rng, r, bloque, P["sorpresa"], registrar, "Desempate Permanencia",
                               "Liguilla Permanencia", nom, cupos=corte - inicio)
        ids = np.array([int(i) for i in ids[:inicio]] + orden + [int(i) for i in ids[fin:]])
        SF["orden_f2_desc"] = ids
        SF["desempate_desc"] = {"equipos": [nom[e] for e in bloque], "partidos": partidos,
                                "salvados": corte - inicio}
    SF["descendidos"] = [int(i) for i in ids[max(corte, 0):]]


def iniciar_fase2_f(SF, rng):
    SF["tablas_f1"] = [tabla_f_grupo(SF, g) for g in range(len(SF["grupos"]))]
    # Los 4 mejores de cada una de las 5 zonas = 20 a Campeonato
    campeonato = pd.concat([df.head(4) for df in SF["tablas_f1"]])
    descenso = pd.concat([df.tail(len(df) - 4) for df in SF["tablas_f1"]])

    campeonato = campeonato.sort_values(["Pts", "DG", "GF"], ascending=False).reset_index(drop=True)
    descenso = descenso.sort_values(["Pts", "DG", "GF"], ascending=False).reset_index(drop=True)
    
    SF["zonas2"] = [campeonato["id"].to_numpy(), descenso["id"].to_numpy()]
    SF["zona2_de"] = np.full(len(SF["nombres"]), -1, dtype=int)
    for z, ids in enumerate(SF["zonas2"]):
        SF["zona2_de"][ids] = z

    for k in STATS:
        SF[k] = np.zeros(len(SF["nombres"]), dtype=int)

    base = [generar_fixture(len(SF["zonas2"][0])), generar_fixture(len(SF["zonas2"][1]))]
    f2_rondas = max(len(base[0]), len(base[1]))
    SF["f2_rondas"] = f2_rondas
    SF["total"] = SF["f1_rondas"] + f2_rondas + F_RED

    SF["fechas2"] = []
    for k in range(f2_rondas):
        fecha = []
        for ids, fx in zip(SF["zonas2"], base):
            if k < len(fx):
                fecha += [(int(ids[a]), int(ids[b])) for a, b in fx[k]]
        SF["fechas2"].append(fecha)


def iniciar_reducido_f(SF):
    ids = tabla_f_f2(SF, 0)["id"].to_numpy()
    SF["ord2"] = ids
    SF["campeon"] = int(ids[0])
    SF["asc_directo"] = [int(ids[0]), int(ids[1]), int(ids[2])]

    pts = 3 * SF["g"] + SF["e"]
    def bloque(idx, seed0):
        idx = np.asarray(idx)[None, :]
        return {"id": idx, "pts": pts[idx], "seed": np.arange(seed0, seed0 + idx.shape[1])[None, :]}

    SF["red"] = {
        "esperan_semis": bloque(ids[3:6], 4), # 4°, 5°, 6°
        "prelim": bloque(ids[6:8], 7)         # 7°, 8°
    }
    SF["entrantes"] = pd.DataFrame(
        [(i + 1, SF["nombres"][ids[3 + i]], f"{4 + i}° Campeonato") for i in range(5)],
        columns=["Mérito", "Equipo", "Origen"],
    )


def simular_fecha_f(SF, P, rng):
    f = SF["fecha"]
    if f >= SF["total"]:
        return
    r, nom = SF["r"], SF["nombres"]

    if f < SF["f1_rondas"] + SF["f2_rondas"]:                 
        if f < SF["f1_rondas"]:
            pares = SF["fechas"][f]
            etiqueta = lambda i: f"Zona {F_GRUPOS_NOMBRES[SF['grupo_de'][i]]}"
        else:
            pares = SF["fechas2"][f - SF["f1_rondas"]]
            etiqueta = lambda i: "Campeonato" if SF["zona2_de"][i] == 0 else "Descenso"
        if pares:
            h = np.array([x[0] for x in pares])
            a = np.array([x[1] for x in pares])
            gh, ga = jugar(rng, r[h], r[a], **P)
            sumar_partidos(SF, h, a, gh, ga)
            SF["historial"].append(_fila_historial(SF, [etiqueta(i) for i in h], h, a, gh, ga, ""))
            for x, y, g1, g2 in zip(h, a, gh, ga):
                SF["log"].append(nuevo_partido("Federal A", f + 1, rotulo_f(SF, f + 1),
                                               etiqueta(x), nom[x], nom[y], g1, g2))
            revisar_liga(SF, SF["log"][-len(h):], rng)
            if f < SF["f1_rondas"]:
                dfs = [tabla_f_grupo(SF, g) for g in range(len(SF["grupos"]))]
            else:
                dfs = [tabla_f_f2(SF, z) for z in range(2)]
            pos = np.zeros(len(nom), dtype=int)
            for dfz in dfs:
                pos[dfz["id"].to_numpy()] = dfz["Pos"].to_numpy()
            SF["pos_hist"].append((0 if f < SF["f1_rondas"] else 1, pos))
        SF["fecha"] += 1
        if SF["fecha"] == SF["f1_rondas"]:
            iniciar_fase2_f(SF, rng)
        elif SF["fecha"] == SF["f1_rondas"] + SF["f2_rondas"]:
            desempate_campeon_f(SF, P, rng, f + 1)
            desempate_descenso_f(SF, P, rng, f + 1)
            iniciar_reducido_f(SF)

    else:                                                  # ---- reducido
        etapa = f - SF["f1_rondas"] - SF["f2_rondas"]
        if etapa == 0:
            T = SF["red"]["prelim"]
        elif etapa == 1:
            T = unir(SF["red"]["esperan_semis"], SF["ganadores"])
        else:
            T = SF["ganadores"]
            
        A, B = cruces_mejor_peor(T)
        final = etapa == F_RED - 1
        loc, vis, gl, gv, gan, per, pen = jugar_reducido_federal(rng, r, A, B, P["sorpresa"], final)
        SF["ganadores"] = gan
        ronda = []
        for li, vi, g1, g2, wi, p in zip(loc["id"][0], vis["id"][0], gl[0], gv[0],
                                          gan["id"][0], pen[0]):
            tanda = tanda_penales(rng, wi == li) if (p and final) else None
            partido = nuevo_partido("Federal A", f + 1, rotulo_f(SF, f + 1), F_ETAPAS[etapa],
                                    nom[li], nom[vi], g1, g2, tanda=tanda, gana=nom[wi],
                                    neutral=final)
            ronda.append(partido)
            SF["log"].append(partido)
        SF["bracket"].append(ronda)
        definicion = []
        for m in ronda:
            if m["pen"]:
                definicion.append(f"Penales {m['pen'][0]}-{m['pen'][1]}: {m['gana']}")
            elif m["gl"] == m["gv"]:
                definicion.append(f"Ganó {m['gana']} por mejor posición en la tabla")
            else:
                definicion.append("")
        SF["historial"].append(_fila_historial(SF, F_ETAPAS[etapa], loc["id"][0], vis["id"][0],
                                               gl[0], gv[0], definicion))
        if final:
            SF["asc_reducido"] = int(gan["id"][0, 0])
            SF["ascendidos"] = SF["asc_directo"] + [SF["asc_reducido"]]
        SF["fecha"] += 1

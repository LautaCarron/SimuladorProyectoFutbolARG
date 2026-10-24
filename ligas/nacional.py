"""Primera Nacional: dos zonas, fase 2, reducido y cómo se juega cada fecha.
"""

import math

import numpy as np
import pandas as pd

from datos.equipos import NB
from motor.incidentes import revisar_liga
from motor.nucleo import (
    STATS,
    _fila_historial,
    balance_localias,
    cruces_mejor_peor,
    df_stats,
    fixture_revancha,
    generar_fixture,
    generar_fixture_interzonal,
    jugar,
    jugar_ko,
    ko_jugar,
    mods_ids,
    mods_nombres,
    nuevo_partido,
    sumar_partidos,
    tanda_penales,
    tope_descensos,
    ultimas_localias,
    unir,
)
from ligas.desempates import bloque_empatado, duelo_o_liguilla
from ligas.primera import definir_bloque, descensos, primera_terminada, promos, tabla_final


# Primera Nacional
# Los valores B_* de acá abajo son los del formato actual con los 36 equipos de siempre. La cantidad de
# equipos de la B puede cambiar (Modo dios), así que lo que se usa en cada temporada es el plan que
# arma plan_b(n, formato) y queda guardado en SB["plan"] (ver plan_de).
B_ZONA_TAM = NB // 2              # 18 equipos por zona en la fase 1


B_TAM2 = [12, 12, 12]             # Campeonato, Intermedia, Descenso


B_F1_ZONAL = B_ZONA_TAM - 1        # 17 fechas de zona (una rueda de 18)


B_F1_INTER = 8                     # 8 fechas interzonales antes de pasar a la fase 2


B_F1 = B_F1_ZONAL + B_F1_INTER     # 25 fechas en total en la fase 1 de la B


B_F2 = B_TAM2[2] - 1              # 11 fechas (las tres zonas son de 12)


B_RED = 4                         # octavos, cuartos, semifinales, final


B_TOTAL = B_F1 + B_F2 + B_RED + 1 # fase 1 + fase 2 + reducido + promoción

B_MAX_ANUAL = 24                  # con 24 equipos o menos la B se juega todos contra todos, ida y vuelta
B_DESC_MAX = 8                    # descensos que se pueden elegir en el Modo dios (0 a 8)
B_MIN_EQUIPOS = 20                # mínimo que se puede elegir en el Modo dios
B_MAX_EQUIPOS = 60                # máximo que se puede elegir en el Modo dios
B_ZONA2_TAM = 12                  # tamaño de las zonas Campeonato e Intermedia cuando hay más de 36 equipos
B_ENTRAN_OCTAVOS = 12             # el reducido siempre arranca con 12 en octavos (+ 2 directos a cuartos)


B_ETAPAS = ["Octavos del reducido", "Cuartos del reducido", "Semifinales del reducido",
            "Final del reducido"]


B_ZONAS2 = ["Campeonato", "Intermedia", "Descenso"]

FORMATOS_B = {
    "actual": "Formato actual (zonas + reducido)",
    "anual_ida": "Torneo anual · una rueda",
    "anual_ida_vuelta": "Torneo anual · ida y vuelta",
}
B_DESCIENDEN = 6                  # tope de descensos de la B (con 36 equipos bajan 6)
B_DIRECTOS_MAX = 8                # ascensos directos que se pueden elegir en el Modo dios (0 a 8)
B_RED_EQUIPOS_MAX = 24            # equipos que pueden jugar el reducido por el ascenso
B_DIRECTOS_DEF, B_RED_EQUIPOS_DEF = 2, 14   # formato actual: 2 directos y reducido de 14 (3° al 16°)


def cfg_b(S):
    """Lo que se eligió en el Modo dios para la Primera Nacional (se aplica al armar cada temporada)."""
    c = S.setdefault("cfg", {}).setdefault("b", {})
    c.setdefault("formato", "actual")
    c.setdefault("equipos", None)                # None: automático (cambia según ascensos y descensos)
    c.setdefault("descensos", None)              # None: automático según la cantidad de equipos
    c.setdefault("directos", None)               # ascensos directos (None: automático según el formato)
    c.setdefault("reducido", None)               # si hay reducido por un ascenso más (None: automático)
    c.setdefault("red_equipos", None)            # cuántos equipos juegan el reducido (None: automático)
    return c


def asc_defecto(formato_ef, k_desc=3):
    """Ascensos que se juegan si no se tocó nada: formato actual -> 2 directos + reducido de 14 (3° al 16°);
    torneo anual -> los primeros `k_desc` suben directo, sin reducido."""
    if formato_ef == "actual":
        return B_DIRECTOS_DEF, True, B_RED_EQUIPOS_DEF
    return max(0, min(B_DIRECTOS_MAX, k_desc)), False, 4


def asc_elegido(S, formato_ef):
    """(directos, hay_reducido, equipos_del_reducido) con los que se juega la B esta temporada (Modo dios)."""
    c = cfg_b(S)
    d0, r0, m0 = asc_defecto(formato_ef, int(S.get("cfg", {}).get("primera", {}).get("descensos", 3)))
    return (d0 if c["directos"] is None else int(c["directos"]),
            r0 if c["reducido"] is None else bool(c["reducido"]),
            m0 if c["red_equipos"] is None else int(c["red_equipos"]))


def equipos_objetivo_b(S, auto=None):
    """Cuántos equipos tendrá la B la temporada que viene. Si en el Modo dios no se fijó una cantidad, es la
    automática (`auto`, o los que tiene ahora): cambia con los ascensos y descensos. Entre B_MIN_EQUIPOS y
    B_MAX_EQUIPOS (si se fija a mano, en cantidad par para que las dos zonas de la fase 1 sean iguales)."""
    n = cfg_b(S)["equipos"]
    if n is None:                                     # automático: lo que dejan los movimientos, tal cual
        n = auto if auto is not None else len(S["b"]["nombres"])
        return max(B_MIN_EQUIPOS, min(B_MAX_EQUIPOS, int(n)))
    n = max(B_MIN_EQUIPOS, min(B_MAX_EQUIPOS, int(n)))
    return n - n % 2


def orden_final_b(SB):
    """Ids de la B ordenados del mejor al peor de la temporada terminada: en el torneo anual, la tabla; en el
    formato actual, la zona Campeonato, después la Intermedia y por último la Descenso."""
    return [int(i) for z in SB["ord2"] for i in z]


def k_prom(SB):
    """Promociones contra Primera que se juegan esta temporada (0, 1 o 2; las define Primera en el Modo dios)."""
    return int(SB.get("k_prom", 1))


def promo_cands(SB):
    """Equipos de la B que juegan la promoción, el mejor primero. Con una promoción juega el que sigue a los
    ascendidos (en el formato actual, el perdedor de la final del reducido); con dos, también el siguiente."""
    return list(SB.get("promo_orden") or [])[:k_prom(SB)]


def actualizar_promos_b(S):
    """Copia a la B lo que Primera tiene configurado (cantidad de promociones y puestos que las juegan)."""
    SB = S["b"]
    SB["k_prom"] = promos(S)
    SB["promo_pos"] = [len(S["nombres"]) - descensos(S) - j for j in range(SB["k_prom"])]


def formato_b(SB):
    """Formato con el que se está jugando esta temporada la Primera Nacional."""
    return SB.get("formato", "actual")


def _rondas(m):
    """Fechas de una rueda todos contra todos entre m equipos (si m es impar, uno descansa cada fecha)."""
    return m - 1 if m % 2 == 0 else m


def formato_efectivo(n, preferido="actual"):
    """Formato real según la cantidad de equipos: con B_MAX_ANUAL (24) o menos, todos contra todos ida y vuelta;
    con más, el que se eligió en el Modo dios (por defecto, el actual: zonas + reducido)."""
    if preferido == "anual_ida":                  # todos contra todos a una vuelta: se puede elegir con cualquier cantidad
        return "anual_ida"
    if n <= B_MAX_ANUAL:
        return "anual_ida_vuelta"
    if preferido == "anual_ida_vuelta":           # el ida y vuelta sólo con B_MAX_ANUAL equipos o menos: una sola rueda
        return "anual_ida"
    return preferido if preferido in FORMATOS_B else "actual"


def tam_zonas2(n):
    """Tamaño de las tres zonas de la fase 2 (Campeonato, Intermedia, Descenso). Con más de 36 equipos,
    12/12/X (40 -> 12/12/16); con 36 o menos, lo más parejas posible (36 -> 12/12/12, 28 -> 10/9/9)."""
    if n > NB:
        return [B_ZONA2_TAM, B_ZONA2_TAM, n - 2 * B_ZONA2_TAM]
    base, resto = divmod(n, 3)
    return [base + (1 if k < resto else 0) for k in range(3)]


def plan_reducido_b(directos, hay_reducido, equipos, n, desc):
    """Ascensos de la B con `n` equipos y `desc` descensos: `directos` suben directo (los primeros de la tabla) y,
    si hay reducido, juegan `equipos` clasificados (los que siguen a los directos) por un ascenso más. Los mejor
    ubicados esperan (pasan de ronda) y los peores juegan la primera ronda: con 14, 12 juegan los octavos y 2
    esperan en cuartos. Devuelve rondas, cuántos juegan la primera ronda y los nombres de las etapas."""
    directos = max(0, min(B_DIRECTOS_MAX, int(directos), n - desc))
    disponibles = n - desc - directos                        # los que bajan no pueden jugar el reducido
    vacio = {"directos": directos, "reducido": False, "equipos": 0, "rondas": 0, "juegan": 0, "etapas": []}
    if not hay_reducido or disponibles < 2:
        return vacio
    equipos = max(2, min(B_RED_EQUIPOS_MAX, int(equipos), disponibles))
    rondas = math.ceil(math.log2(equipos))
    juegan = 2 * (equipos - 2 ** (rondas - 1))               # equipos que juegan la primera ronda
    nombres = {2: "Final del reducido", 4: "Semifinales del reducido", 8: "Cuartos del reducido",
               16: "Octavos del reducido", 32: "Dieciseisavos del reducido"}
    etapas = []
    for k in range(rondas):
        lugares = 2 ** (rondas - k)
        etapas.append("Eliminatoria preliminar" if k == 0 and rondas > 1 and juegan <= lugares // 2
                      else nombres[lugares])
    return {"directos": directos, "reducido": True, "equipos": equipos, "rondas": rondas, "juegan": juegan,
            "etapas": etapas}


def plan_b(n, formato="actual", desc=None, asc=None):
    """Todo lo que depende de la cantidad de equipos `n` de la B: formato, zonas, cantidad de fechas,
    cuántos bajan y cuántos de la Intermedia entran al reducido. `desc` son los descensos elegidos en el Modo
    dios (0 a 8); sin elegir (None) se calculan según la cantidad de equipos."""
    formato = formato_efectivo(n, formato)
    asc = asc or asc_defecto(formato)                   # (directos, hay_reducido, equipos del reducido)
    if formato != "actual":
        vueltas = 2 if formato == "anual_ida_vuelta" else 1
        bajan = min(B_DESCIENDEN, max(1, n // 4)) if desc is None else max(0, min(desc, n - 1))
        bajan = min(bajan, tope_descensos(n, B_DESC_MAX))
        return {"n": n, "formato": formato, "base": vueltas * _rondas(n), "desc": bajan,
                "red": plan_reducido_b(asc[0], asc[1], asc[2], n, bajan)}
    za, zb = (n + 1) // 2, n // 2                       # fase 1: dos zonas (iguales si n es par)
    zonal = max(_rondas(za), _rondas(zb))
    inter = min(B_F1_INTER, zb)
    tam2 = tam_zonas2(n)
    c, i, d = tam2
    bajan = (min(B_DESCIENDEN, d // 2) if desc is None         # bajan la mitad de la zona Descenso (6 de 12)
             else max(0, min(desc, d - 1)))
    bajan = min(bajan, tope_descensos(n, B_DESC_MAX))
    return {"n": n, "formato": "actual", "zona_tam": [za, zb], "f1_zonal": zonal, "f1_inter": inter,
            "f1": zonal + inter, "tam2": tam2, "f2": max(_rondas(z) for z in tam2), "desc": bajan,
            "x_int": min(i, B_ENTRAN_OCTAVOS - (c - 4)),       # (sin uso en el reducido: ahora lo define "red")
            "red": plan_reducido_b(asc[0], asc[1], asc[2], n, bajan)}


def plan_de(SB):
    """Plan de la temporada de la B (se arma con la cantidad de equipos; las partidas viejas lo calculan acá)."""
    n = len(SB["nombres"])
    p = SB.get("plan")
    if p is None or p["n"] != n or "red" not in p:
        p = SB["plan"] = plan_b(n, formato_b(SB), SB.get("desc_pref"), SB.get("asc_pref"))
    return p


def red_b(SB):
    """Plan de los ascensos de esta temporada: directos, reducido (si hay), rondas y etapas."""
    return plan_de(SB)["red"]


def directos_b(SB):
    """Cuántos de la B ascienden directo esta temporada."""
    return red_b(SB)["directos"]


def b_f1(SB):
    """Fechas de la fase 1 (formato actual)."""
    return plan_de(SB).get("f1", 0)


def b_f2(SB):
    """Fechas de la fase 2 (formato actual), sin contar los desempates."""
    return plan_de(SB).get("f2", 0)


def b_total_base(SB):
    return total_base_b(SB)


def descensos_b(SB):
    """Cuántos equipos bajan de la B esta temporada."""
    return plan_de(SB)["desc"]


def es_anual_b(SB):
    return formato_b(SB) != "actual"


def total_base_b(SB):
    """Fechas de la liga sin contar promoción ni desempates (en el formato actual: fase 1 + fase 2)."""
    p = plan_de(SB)
    return p["base"] if es_anual_b(SB) else p["f1"] + p["f2"]


def _etapa_entrada(red, rank):
    """Etapa del reducido en la que entra el que termina `rank`° (1...) de la tabla ("" si no lo juega)."""
    d = red["directos"]
    if not red["reducido"] or not d < rank <= d + red["equipos"]:
        return ""
    return red["etapas"][0] if rank > d + red["equipos"] - red["juegan"] else red["etapas"][1]


def destino_b_anual(pos, k, n=NB, desc=B_DESCIENDEN, red=None, kp=1):
    """Torneo anual de la B: destino según la posición (k = cuántos suben directo, desc = cuántos bajan; `red` es
    el plan del reducido y `kp` las promociones que se juegan)."""
    if pos == 1 and k >= 1:
        return "Campeón · Ascenso"
    if pos <= k:
        return "Ascenso directo"
    if red and _etapa_entrada(red, pos):
        return _etapa_entrada(red, pos)
    if pos > n - desc:
        return "Desciende"
    if not (red and red["reducido"]) and pos <= k + kp:
        return "Promoción"
    return "Permanece"


def zona2_de_posicion(pos, z, plan):
    """Zona de la fase 2 (0 Campeonato, 1 Intermedia, 2 Descenso) a la que pasa el que termina `pos`° (1, 2...)
    en la zona `z` (0 = A, 1 = B) de la fase 1. Los puestos se reparten intercalados: 1°A, 1°B, 2°A, 2°B..."""
    c, i, _ = plan["tam2"]
    idx = 2 * (pos - 1) + z
    return 0 if idx < c else 1 if idx < c + i else 2


def destino_b1(pos, plan=None, z=0):
    """Fase 1 de la B: a qué zona de la fase 2 pasa según la posición en la zona A/B."""
    plan = plan or plan_b(NB)
    return ("→ Zona Campeonato", "→ Zona Intermedia", "→ Zona Descenso")[zona2_de_posicion(pos, z, plan)]


def destino_b2(z, pos, plan=None, kp=1):
    """Fase 2 de la B: destino según la zona (0 Campeonato, 1 Intermedia, 2 Descenso). Los ascensos, el reducido
    y la promoción salen del plan (Modo dios): se cuentan los puestos sumando las zonas (Campeonato, Intermedia,
    Descenso)."""
    plan = plan or plan_b(NB)
    red = plan["red"]
    rank = sum(plan["tam2"][:z]) + pos
    d = red["directos"]
    if rank <= d:
        return "Campeón · Ascenso" if rank == 1 else "Ascenso directo"
    if rank == 1 and not _etapa_entrada(red, rank):
        return "Campeón"                     # sin ascenso directo y fuera del reducido: sólo es el campeón
    if z == 2 and pos > plan["tam2"][2] - plan["desc"]:
        return "Desciende"
    if _etapa_entrada(red, rank):
        return _etapa_entrada(red, rank)
    if not red["reducido"] and rank <= d + kp:
        return "Promoción"
    return "Eliminado" if red["reducido"] and z < 2 else "Permanece"


def rangos_fase1(plan, z):
    """Textos de los puestos de la zona `z` (0 = A, 1 = B) de la fase 1 que pasan a cada zona de la fase 2
    (para la leyenda), p. ej. ["1°-6°", "7°-12°", "13°-18°"]."""
    tam = plan["zona_tam"][z]
    out = []
    for dest in range(3):
        pos = [p for p in range(1, tam + 1) if zona2_de_posicion(p, z, plan) == dest]
        out.append(f"{pos[0]}°-{pos[-1]}°" if pos else "-")
    return out


def total_b(SB):
    """Fechas de la Primera Nacional contando las de desempate (si las hubo) y la promoción."""
    hay_promo = 1 if k_prom(SB) > 0 else 0
    rondas = red_b(SB)["rondas"]                    # fechas del reducido (0 si esta temporada no hay)
    if es_anual_b(SB):
        return total_base_b(SB) + rondas + hay_promo
    return b_f1(SB) + b_f2(SB) + rondas + hay_promo + SB.get("extra_f2", 0)


def rotulo_b(SB, n):
    etapas = red_b(SB)["etapas"]
    if es_anual_b(SB):
        base = total_base_b(SB)
        if n <= base:
            vuelta = formato_b(SB) == "anual_ida_vuelta" and n > base // 2
            return f"Fecha {n}" + (" · Vuelta" if vuelta else "")
        if n <= base + len(etapas):
            return f"Fecha {n} · {etapas[n - base - 1]}"
        return f"Fecha {n} · Promoción"
    extra = SB.get("extra_f2", 0)
    f1, f2 = b_f1(SB), b_f2(SB)
    if n <= f1:
        return f"Fecha {n} · Fase 1"
    if n <= f1 + f2 + extra:
        if n <= f1 + f2:
            return f"Fecha {n} · Fase 2 (fecha {n - f1})"
        else:
            return f"Fecha {n} · Desempate Permanencia"
    if n <= f1 + f2 + extra + len(etapas):
        return f"Fecha {n} · {etapas[n - f1 - f2 - extra - 1]}"
    return f"Fecha {n} · Promoción"


def nueva_estructura_b(SB, rng, S=None):
    if S is not None:
        SB["k_prom"] = promos(S)                                   # la promoción la define Primera
        SB["promo_pos"] = [len(S["nombres"]) - descensos(S) - j for j in range(SB["k_prom"])]
    return _nueva_estructura_b(SB, rng, S)


def _nueva_estructura_b(SB, rng, S=None):
    """Arma la temporada de la B según el formato elegido en el Modo dios (si se pasa S; si no, mantiene el actual).
    Formato actual: sortea las zonas A y B (18 c/u) y arma el fixture de la fase 1.
    Torneo anual: todos contra todos (ida o ida y vuelta) en una sola tabla."""
    n = len(SB["nombres"])
    if S is not None:
        SB["formato_pref"] = cfg_b(S)["formato"]
        SB["asc_pref"] = asc_elegido(S, formato_efectivo(n, SB["formato_pref"]))   # ascensos y reducido (Modo dios)
    # El formato depende de cuántos equipos son: con 24 o menos, ida y vuelta todos contra todos
    if S is not None:
        SB["desc_pref"] = cfg_b(S)["descensos"]
    SB["plan"] = plan_b(n, SB.get("formato_pref", SB.get("formato", "actual")), SB.get("desc_pref"),
                        SB.get("asc_pref"))
    SB["formato"] = SB["plan"]["formato"]
    plan = SB["plan"]
    perm = rng.permutation(n)
    if es_anual_b(SB):
        SB["zonas"] = [np.arange(n)]
        SB["zona_de"] = np.zeros(n, dtype=int)
        fechas = [[(int(perm[a]), int(perm[b])) for a, b in par] for par in generar_fixture(n)]
        if formato_b(SB) == "anual_ida_vuelta":                    # la vuelta: mismas fechas con las localías al revés
            fechas += [[(v, l) for l, v in fecha] for fecha in fechas]
        SB["fechas"] = fechas
    else:
        za = plan["zona_tam"][0]
        SB["zonas"] = [perm[:za], perm[za:]]
        SB["zona_de"] = np.zeros(n, dtype=int)
        SB["zona_de"][SB["zonas"][1]] = 1
        bases = [generar_fixture(len(ids)) for ids in SB["zonas"]]
        fechas_zonal = [
            [(int(ids[a]), int(ids[b])) for ids, base in zip(SB["zonas"], bases) if k < len(base)
             for a, b in base[k]]
            for k in range(plan["f1_zonal"])
        ]
        m = min(len(SB["zonas"][0]), len(SB["zonas"][1]))
        fechas_inter = generar_fixture_interzonal(rng, SB["zonas"][0][:m], SB["zonas"][1][:m], plan["f1_inter"])
        SB["fechas"] = fechas_zonal + fechas_inter
    SB["fecha"] = 0
    for k in STATS:
        SB[k] = np.zeros(n, dtype=int)
    SB["historial"] = []
    SB["log"] = []
    SB["pos_hist"] = []
    SB["bracket"] = []          # partidos del reducido por ronda
    SB["promo_partido"] = None
    SB["tablas_f1"] = None
    SB["zonas2"] = None
    SB["zona2_de"] = None
    SB["fechas2"] = None
    SB["ord2"] = None
    SB["campeon"] = None
    SB["asc_directo"] = []
    SB["desc_b"] = []
    SB["red"] = None
    SB["entrantes"] = None
    SB["asc_reducido"] = None
    SB["perdedor_final"] = None
    SB["promo"] = None
    SB["promos"] = []                # una por cada promoción jugada
    SB["promo_partidos"] = []
    SB["promo_orden"] = []           # candidatos a la promoción, el mejor primero
    # Desempates: se limpian los de la temporada anterior (si no, la tabla usa ids viejos)
    SB["extra_f2"] = 0
    SB["orden_final_descenso"] = None
    SB["orden_final_campeonato"] = None
    SB["desempate_pendiente"] = False
    SB["ids_desempate"] = []
    SB["motivos_desempate"] = []


def tabla_b_f1(SB, z):
    """Tabla de la zona A (0) o B (1) de la fase 1."""
    df = df_stats(SB["nombres"], SB["r"], SB, SB["zonas"][z])
    df.insert(0, "Pos", df.index + 1)
    plan = plan_de(SB)
    df["Destino"] = [destino_b1(p, plan, z) for p in df["Pos"]]
    return df


def tabla_b_f2(SB, z):
    """Tabla de la zona de la fase 2 (0 Campeonato, 1 Intermedia, 2 Descenso)."""
    df = df_stats(SB["nombres"], SB["r"], SB, SB["zonas2"][z])
    
    # Inyectar los desempates: el del título en Campeonato y el de permanencia en Descenso
    if z == 2 and SB.get("orden_final_descenso") is not None:
        df = df.set_index("id").loc[SB["orden_final_descenso"]].reset_index()
    if z == 0 and SB.get("orden_final_campeonato") is not None:
        df = df.set_index("id").loc[SB["orden_final_campeonato"]].reset_index()

    df.insert(0, "Pos", df.index + 1)
    plan = plan_de(SB)
    df["Destino"] = [destino_b2(z, p, plan, k_prom(SB)) for p in df["Pos"]]

    if z in (0, 2) and SB.get("motivos_desempate"):
        ids_actuales = df["id"].to_numpy()
        for motivo in SB["motivos_desempate"]:
            partes = motivo.split()
            nombre_frontera = partes[1]
            if (nombre_frontera == "Campeonato") != (z == 0):
                continue
            inicio, fin = map(int, partes[2].split("-"))
            ids_bloque = ids_actuales[inicio:fin]
            df.loc[df["id"].isin(ids_bloque), "Destino"] = f"Desempate {nombre_frontera}"
            
    return df


def tabla_b_anual(SB, k=None):
    """Torneo anual de la B: tabla única. Suben directo los primeros (`k`, o los que se eligieron en el Modo
    dios), después el reducido (si hay) y los que siguen juegan la promoción."""
    df = df_stats(SB["nombres"], SB["r"], SB, SB["zonas"][0])
    df.insert(0, "Pos", df.index + 1)
    n, desc, red = len(df), descensos_b(SB), red_b(SB)
    k = red["directos"] if k is None else k
    df["Destino"] = [destino_b_anual(p, k, n, desc, red, k_prom(SB)) for p in df["Pos"]]
    return df


def cerrar_anual_b(S):
    """Fin del torneo anual de la B: campeón, ascensos, descensos y quién juega la promoción."""
    SB = S["b"]
    ids = [int(i) for i in tabla_b_anual(SB)["id"]]
    SB["ord2"] = [np.array(ids)]
    SB["campeon"] = ids[0]
    SB["desc_b"] = ids[len(ids) - descensos_b(SB):] if descensos_b(SB) else []
    _definir_ascensos_b(SB, ids)                      # directos, reducido (si hay) o los que juegan la promoción


def _definir_ascensos_b(SB, orden):
    """Con la tabla final (`orden`, del 1° al último) define los ascensos directos y arma el reducido por el
    ascenso siguiente. Sin reducido, juegan la promoción los que quedaron detrás de los directos."""
    pr = red_b(SB)
    d = pr["directos"]
    SB["asc_directo"] = [int(i) for i in orden[:d]]
    SB["asc_reducido"] = None
    bajan = set(SB["desc_b"])
    if not pr["reducido"]:
        SB["red"], SB["entrantes"] = None, None
        SB["promo_orden"] = [int(i) for i in orden[d:] if int(i) not in bajan][:2]
        return
    m, juegan = pr["equipos"], pr["juegan"]
    pts = 3 * SB["g"] + SB["e"]
    zona_de = SB["zona2_de"] if SB.get("zona2_de") is not None else np.zeros(len(SB["nombres"]), dtype=int)
    entran = np.array([int(i) for i in orden[d:d + m]], dtype=int)

    def bloque(desde, hasta):
        idx = entran[desde:hasta][None, :]
        return {"id": idx, "zona": zona_de[idx], "pts": pts[idx],
                "seed": np.arange(d + 1 + desde, d + 1 + hasta, dtype=int)[None, :]}

    SB["red"] = {"esperan": bloque(0, m - juegan), "primera": bloque(m - juegan, m), "ganadores": None,
                 "elim": [], "resto": [int(i) for i in orden[d + m:] if int(i) not in bajan]}
    zonas = SB.get("zonas2")
    limites = np.cumsum([len(z) for z in zonas]) if zonas is not None else None
    filas = []
    for j, i in enumerate(entran):
        rank = d + 1 + j
        if limites is None:
            origen_txt = f"{rank}° de la tabla"
        else:
            z = int(np.searchsorted(limites, rank, side="left"))
            origen_txt = f"{rank - (int(limites[z - 1]) if z else 0)}° {B_ZONAS2[z]}"
        filas.append((rank - d, SB["nombres"][i], origen_txt,
                      pr["etapas"][0] if j >= m - juegan else pr["etapas"][1]))
    SB["entrantes"] = pd.DataFrame(filas, columns=["Mérito", "Equipo", "Origen", "Entra en"])


def iniciar_fase2_b(SB, rng):
    """Fin de la fase 1: reparte en 3 zonas conservando los puntos acumulados."""
    SB["tablas_f1"] = [tabla_b_f1(SB, z) for z in range(2)]
    ordA = SB["tablas_f1"][0]["id"].to_numpy()
    ordB = SB["tablas_f1"][1]["id"].to_numpy()
    # Las tres zonas quedan lo más parejas posible (36 -> 12/12/12; 28 -> 10/9/9). Los puestos se reparten
    # intercalados (1°A, 1°B, 2°A, 2°B...): con 36 son 6+6 / 6+6 / 6+6.
    c, i, _ = plan_de(SB)["tam2"]
    intercalado = []
    for k in range(max(len(ordA), len(ordB))):
        intercalado += [x for x in (ordA[k:k + 1], ordB[k:k + 1]) if len(x)]
    intercalado = np.concatenate(intercalado)
    n_eq = len(intercalado)
    zonas2 = [rng.permutation(intercalado[a:b]) for a, b in ((0, c), (c, c + i), (c + i, n_eq))]
    SB["zonas2"] = zonas2
    SB["zona2_de"] = np.zeros(len(SB["nombres"]), dtype=int)
    for z, ids in enumerate(zonas2):
        SB["zona2_de"][ids] = z

    # Los que ya se cruzaron en la fase 1 (misma zona A/B) juegan la revancha con la
    # localía invertida; el resto se ordena para que las localías queden parejas.
    n = len(SB["nombres"])
    H = np.zeros((n, n), dtype=bool)
    for pares in SB["fechas"]:
        for a, b in pares:
            H[a, b] = True
    previas = ultimas_localias(SB["fechas"])
    balance = balance_localias(SB["fechas"])
    por_zona = [fixture_revancha(rng, ids, H, previas, balance) for ids in zonas2]
    SB["fechas2"] = []
    for k in range(b_f2(SB)):
        SB["fechas2"].append([p for fz in por_zona if k < len(fz) for p in fz[k]])


def iniciar_reducido(SB):
    """Fin de la fase 2: define ascensos directos y descensos y arma el reducido (si esta temporada hay)."""
    ids = [tabla_b_f2(SB, z)["id"].to_numpy() for z in range(3)]
    SB["ord2"] = ids
    SB["campeon"] = int(ids[0][0])
    plan = plan_de(SB)
    SB["desc_b"] = [int(i) for i in ids[2][len(ids[2]) - plan["desc"]:]] if plan["desc"] else []
    _definir_ascensos_b(SB, [int(i) for z in ids for i in z])      # puestos: Campeonato, Intermedia y Descenso


def simular_fecha_b(S, P):
    """Simula la próxima fecha de la B. La promoción espera a que termine la Primera."""
    SB, rng = S["b"], S["rng"]
    if es_anual_b(SB):
        return _simular_fecha_b_anual(S, P)
    f = SB["fecha"]
    extra = SB.get("extra_f2", 0)
    plan = plan_de(SB)
    b_f1_, b_f2_ = plan["f1"], plan["f2"]            # fechas de la fase 1 y de la fase 2 con esta cantidad de equipos
    R = plan["red"]["rondas"]                        # rondas del reducido (0 si esta temporada no hay)
    B_TOTAL_DYN = b_f1_ + b_f2_ + R + (1 if k_prom(SB) > 0 else 0) + extra  # se alarga si hay desempate

    # La promoción se juega contra el 27° de Primera: espera a que Primera termine
    # TODO, incluidos sus desempates (pueden cambiar quién queda 27°).
    if f >= B_TOTAL_DYN or (k_prom(SB) > 0 and f == B_TOTAL_DYN - 1 and not primera_terminada(S)):
        return

    if f < b_f1_ + b_f2_ + extra:                                 # ---- zonas (fase 1 y fase 2)
        _fecha_de_zonas_b(SB, P, rng, plan, f, extra)
    elif f < b_f1_ + b_f2_ + extra + R:                           # ---- reducido
        _ronda_reducido(S, P, f, f - b_f1_ - b_f2_ - extra)
    else:                                                         # ---- promoción
        _promocion_b(S, P, f)


def _fecha_de_zonas_b(SB, P, rng, plan, f, extra):
    """Una fecha de las zonas (fase 1 o fase 2) o de la fecha extra de desempates; al terminar la fase 2 detecta
    empates en el campeonato y la permanencia, y si no hay arranca el reducido."""
    b_f1_, b_f2_ = plan["f1"], plan["f2"]
    es_desempate = SB.get("desempate_pendiente") and f == b_f1_ + b_f2_ + extra - 1
    if es_desempate:
        _jugar_desempates_b(SB, P, rng, plan, f)
    else:
        _jugar_fecha_de_zonas_b(SB, P, rng, plan, f)

    if f < b_f1_:
        dfs, tag = [tabla_b_f1(SB, z) for z in range(2)], 1
    else:
        dfs, tag = [tabla_b_f2(SB, z) for z in range(3)], 2
    pos = np.zeros(len(SB["nombres"]), dtype=int)
    for dfz in dfs:
        pos[dfz["id"].to_numpy()] = dfz["Pos"].to_numpy()
    SB["pos_hist"].append((tag, pos))
    SB["fecha"] += 1

    if SB["fecha"] == b_f1_:
        iniciar_fase2_b(SB, rng)

    ya_se_jugo = (SB.get("orden_final_descenso") is not None
                  or SB.get("orden_final_campeonato") is not None)
    if SB["fecha"] == b_f1_ + b_f2_ + extra and not ya_se_jugo:
        if _armar_desempates_b(SB, plan, extra):
            return                                 # hay empates: se agregó una fecha para definirlos
    # Una vez sorteado el desempate, arranca la sangría del Reducido
    if SB["fecha"] == b_f1_ + b_f2_ + SB.get("extra_f2", 0):
        iniciar_reducido(SB)


def _jugar_fecha_de_zonas_b(SB, P, rng, plan, f):
    r, nom = SB["r"], SB["nombres"]
    b_f1_ = plan["f1"]
    if f < b_f1_:
        pares = SB["fechas"][f]
        if f < plan["f1_zonal"]:
            etiqueta = lambda i: f"Zona {'AB'[SB['zona_de'][i]]}"
        else:
            etiqueta = lambda i: "Interzonal"
    else:
        pares = SB["fechas2"][f - b_f1_]
        etiqueta = lambda i: f"Zona {B_ZONAS2[SB['zona2_de'][i]]}"
    h = np.array([x[0] for x in pares])
    a = np.array([x[1] for x in pares])
    gh, ga = jugar(rng, r[h], r[a], **P, **mods_ids(rng, nom, h, a))
    sumar_partidos(SB, h, a, gh, ga)
    SB["historial"].append(_fila_historial(
        SB, [etiqueta(i) for i in h], h, a, gh, ga, ""))
    for x, y, g1, g2 in zip(h, a, gh, ga):
        SB["log"].append(nuevo_partido("Primera Nacional", f + 1, rotulo_b(SB, f + 1),
                                       etiqueta(x), nom[x], nom[y], g1, g2))
    revisar_liga(SB, SB["log"][-len(h):], rng)


def _jugar_desempates_b(SB, P, rng, plan, f):
    """Fecha extra: desempates del campeonato y de la permanencia."""
    r, nom = SB["r"], SB["nombres"]
    ordenes = {}

    def registrar(a, b, gl, gv, tanda, gana, comp):
        partido = nuevo_partido("Primera Nacional", f + 1, "Desempate", comp, nom[a], nom[b],
                                gl, gv, tanda=tanda, gana=nom[gana], neutral=True)
        SB["log"].append(partido)
        return partido

    for motivo in SB.get("motivos_desempate", []):
        partes = motivo.split()
        nombre_frontera = partes[1]
        inicio, fin = map(int, partes[2].split("-"))
        z = 0 if nombre_frontera == "Campeonato" else 2
        if z not in ordenes:
            ordenes[z] = tabla_b_f2(SB, z)["id"].to_numpy().copy()
        ids_finales = ordenes[z]
        se_salvan = plan["tam2"][2] - plan["desc"]       # zona Descenso: se salvan del 1° al 6° (con 36)
        cupos = 1 if z == 0 else se_salvan - inicio
        ids_finales[inicio:fin] = definir_bloque(
            rng, r, ids_finales[inicio:fin], P["sorpresa"], registrar, nombre_frontera,
            f"Liguilla {nombre_frontera}", nom, campeonato=z == 0, cupos=cupos)

    if 0 in ordenes:
        SB["orden_final_campeonato"] = ordenes[0]
    if 2 in ordenes:
        SB["orden_final_descenso"] = ordenes[2]
    SB["desempate_pendiente"] = False


def _armar_desempates_b(SB, plan, extra):
    """Empates en puntos en el 1° de la Zona Campeonato y en la frontera de permanencia. Si hay, agrega una fecha para
    desempatar y devuelve True."""
    df_descenso = tabla_b_f2(SB, 2)
    pts = df_descenso["Pts"].to_numpy()
    ids_desc = df_descenso["id"].to_numpy()

    partidos_desempate = []
    ids_involucrados = []
    motivos = []

    # El campeón nunca sale por diferencia de gol: igualdad en puntos en el 1° puesto
    # de la Zona Campeonato = desempate
    df_camp = tabla_b_f2(SB, 0)
    pts_c, ids_c = df_camp["Pts"].to_numpy(), df_camp["id"].to_numpy()
    if len(pts_c) > 1 and pts_c[0] == pts_c[1]:
        _, fin_c = bloque_empatado(pts_c, 0)
        ids_bloque = [int(i) for i in ids_c[:fin_c]]
        ids_involucrados.extend(ids_bloque)
        tipo, partido = duelo_o_liguilla(ids_bloque)
        motivos.append(f"{tipo} Campeonato 0-{fin_c}")
        partidos_desempate.append(partido)

    # Los que bajan son los últimos `desc` de la zona (6 de 12 con 36 equipos: índices 6 a 11).
    # La frontera es entre el último que se salva (6°, índice 5) y el primero que baja (7°, índice 6)
    idx_frontera = plan["tam2"][2] - plan["desc"] - 1
    nombre_frontera = "Permanencia"

    if plan["desc"] > 0 and pts[idx_frontera] == pts[idx_frontera + 1]:
        inicio, fin = bloque_empatado(pts, idx_frontera)
        ids_bloque = [int(i) for i in ids_desc[inicio:fin]]
        ids_involucrados.extend(ids_bloque)
        tipo, partido = duelo_o_liguilla(ids_bloque)
        motivos.append(f"{tipo} {nombre_frontera} {inicio}-{fin}")
        partidos_desempate.append(partido)

    if not partidos_desempate:
        return False
    SB["desempate_pendiente"] = True
    SB["ids_desempate"] = ids_involucrados
    SB["motivos_desempate"] = motivos
    SB["extra_f2"] = extra + 1
    SB["fechas2"].append(partidos_desempate)
    return True



def _ronda_reducido(S, P, f, etapa):
    """Juega la ronda `etapa` (0 = la primera) del reducido por el ascenso. Los que pierden quedan anotados: el
    de la final juega la promoción y, si hay dos, el mejor ubicado de los otros que perdieron."""
    SB, rng = S["b"], S["rng"]
    r, nom = SB["r"], SB["nombres"]
    red = SB["red"]
    etapas = red_b(SB)["etapas"]
    if etapa == 0:
        T = red["primera"]
    else:
        if red.get("ganadores") is None:
            return
        T = unir(red["esperan"], red["ganadores"]) if etapa == 1 else red["ganadores"]
    A, B = cruces_mejor_peor(T)
    loc, vis, gl, gv, gan, per, pen = ko_jugar(rng, r, A, B, P["sorpresa"], nombres=nom)
    red["ganadores"] = gan
    ronda = []
    for li, vi, g1, g2, wi, p in zip(loc["id"][0], vis["id"][0], gl[0], gv[0], gan["id"][0], pen[0]):
        tanda = tanda_penales(rng, wi == li) if p else None
        partido = nuevo_partido("Primera Nacional", f + 1, rotulo_b(SB, f + 1), etapas[etapa],
                                nom[li], nom[vi], g1, g2, tanda=tanda, gana=nom[wi])
        ronda.append(partido)
        SB["log"].append(partido)
    SB["bracket"].append(ronda)
    definicion = [f"Penales {m['pen'][0]}-{m['pen'][1]}: {m['gana']}" if m["pen"] else "" for m in ronda]
    SB["historial"].append(_fila_historial(SB, etapas[etapa], loc["id"][0], vis["id"][0], gl[0], gv[0], definicion))
    red["elim"] += [(int(sd), int(i)) for sd, i in zip(per["seed"][0], per["id"][0])]
    if etapa == len(etapas) - 1:                          # final: asciende el ganador
        SB["asc_reducido"] = int(gan["id"][0, 0])
        SB["perdedor_final"] = int(per["id"][0, 0])
        otros = [i for _, i in sorted(red["elim"]) if i != SB["perdedor_final"]]    # el mejor ubicado primero
        SB["promo_orden"] = [SB["perdedor_final"]] + otros + red.get("resto", [])
    SB["fecha"] += 1


def _promocion_b(S, P, f):
    """Promociones (0, 1 o 2): cada candidato de la B juega contra uno de los de abajo de Primera, en cancha
    neutral. El mejor candidato de la B enfrenta al peor ubicado de los que juegan (N-k) y el segundo al de arriba."""
    SB, rng = S["b"], S["rng"]
    r, nom = SB["r"], SB["nombres"]
    final_p = tabla_final(S)
    n, k = len(S["nombres"]), descensos(S)
    filas, promos_l, partidos = [], [], []
    for j, b_id in enumerate(promo_cands(SB)):
        fila = final_p[final_p["Pos"] == n - k - j].iloc[0]
        p_id, p_nom = int(fila["id"]), fila["Equipo"]
        gl, gv, gana_b, pen = jugar_ko(rng, np.array([r[b_id]]), np.array([S["r"][p_id]]),
                                       P["sorpresa"], localia=0.0,
                                       **mods_nombres(rng, [nom[b_id]], [p_nom]))
        tanda = tanda_penales(rng, gana_b[0]) if pen[0] else None
        partido = nuevo_partido("Promoción", f + 1, "Promoción", "Promoción", nom[b_id], p_nom,
                                gl[0], gv[0], tanda=tanda,
                                gana=nom[b_id] if gana_b[0] else p_nom, neutral=True)
        SB["log"].append(partido)
        partidos.append(partido)
        partes = ["Cancha neutral"]
        if pen[0]:
            partes.append(f"Penales {partido['pen'][0]}-{partido['pen'][1]}: {partido['gana']}")
        filas.append(("Promoción", nom[b_id], int(gl[0]), int(gv[0]), p_nom, " · ".join(partes)))
        promos_l.append({"b_id": b_id, "p_id": p_id, "p_nombre": p_nom, "gana_b": bool(gana_b[0])})
    if filas:
        SB["historial"].append(pd.DataFrame(filas, columns=["Instancia", "Local", "GL", "GV", "Visitante", "Definición"]))
    SB["promos"], SB["promo_partidos"] = promos_l, partidos
    SB["promo_partido"] = partidos[0] if partidos else None          # compatibilidad con las pantallas
    SB["promo"] = promos_l[0] if promos_l else None
    SB["fecha"] += 1


def _simular_fecha_b_anual(S, P):
    """Torneo anual de la B: una sola tabla (ida o ida y vuelta) y después la promoción contra el de Primera."""
    SB, rng = S["b"], S["rng"]
    f, base = SB["fecha"], total_base_b(SB)
    if f >= total_b(SB) or (k_prom(SB) > 0 and f == total_b(SB) - 1 and not primera_terminada(S)):
        return
    if f >= base + red_b(SB)["rondas"]:
        _promocion_b(S, P, f)
        return
    if f >= base:
        _ronda_reducido(S, P, f, f - base)
        return
    r, nom = SB["r"], SB["nombres"]
    pares = SB["fechas"][f]
    h = np.array([x[0] for x in pares])
    a = np.array([x[1] for x in pares])
    gh, ga = jugar(rng, r[h], r[a], **P, **mods_ids(rng, nom, h, a))
    sumar_partidos(SB, h, a, gh, ga)
    SB["historial"].append(_fila_historial(SB, ["Liga"] * len(h), h, a, gh, ga, ""))
    for x, y, g1, g2 in zip(h, a, gh, ga):
        SB["log"].append(nuevo_partido("Primera Nacional", f + 1, rotulo_b(SB, f + 1), "Liga",
                                       nom[x], nom[y], g1, g2))
    revisar_liga(SB, SB["log"][-len(h):], rng)
    df = tabla_b_anual(SB)
    pos = np.zeros(len(nom), dtype=int)
    pos[df["id"].to_numpy()] = df["Pos"].to_numpy()
    SB["pos_hist"].append((1, pos))
    SB["fecha"] += 1
    if SB["fecha"] == base:
        cerrar_anual_b(S)


def ascensos_a_primera(S):
    """Nombres de los de la B que suben a Primera sin contar la promoción, en orden: los ascensos directos (el
    campeón primero) y el ganador del reducido (si esta temporada hay). Cuántos son lo define la B en el Modo dios
    (no tiene por qué coincidir con los descensos de Primera). Sólo tiene sentido cuando la B terminó. Los que
    juegan la promoción no suben por acá."""
    SB = S["b"]
    nom = SB["nombres"]
    suben = [nom[i] for i in SB["asc_directo"]]
    if SB["asc_reducido"] is not None:
        suben.append(nom[SB["asc_reducido"]])
    return suben

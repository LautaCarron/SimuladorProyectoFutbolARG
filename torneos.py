"""Torneos: formato de cada categoría y paso de una temporada a otra.

Primera División, Primera Nacional, Federal A, Primera B y Primera C: cómo se
arman las zonas, quién asciende, quién desciende y cómo se juega cada fecha.
Todas las funciones reciben el estado como parámetro (no usan variables globales).
"""

import numpy as np
import pandas as pd
import time

from regional import FINALES_REG, REGIONES_REG
from datos import (
    EQUIPOS,
    EQUIPOS_B,
    EQUIPOS_FEDERAL,
    EQUIPOS_PRIMERA_B,
    EQUIPOS_PRIMERA_C,
    EQUIPOS_REGIONAL,
    REGIONAL,
    F_GRUPOS_NOMBRES,
    N,
    NB,
    origen,
    region_de,
    region_regional,
)
from incidentes import revisar_liga
from motor import (
    MAX_R,
    MIN_R,
    REVERSION,
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
    jugar_reducido_federal,
    ko_jugar,
    nuevo_partido,
    sumar_partidos,
    tanda_penales,
    ultimas_localias,
    unir,
)


# Primera
ZONA_TAM = N // 3                 # 10 equipos por zona
FECHAS_F1 = N - 1                 # 29 fechas todos contra todos
FECHAS_F2 = ZONA_TAM - 1          # 9 fechas por zona
TOTAL_FECHAS = FECHAS_F1 + FECHAS_F2
ZONAS = ["Campeonato", "Intermedia", "Descenso"]

# Primera Nacional
B_ZONA_TAM = NB // 2              # 18 equipos por zona en la fase 1
B_TAM2 = [12, 12, 12]             # Campeonato, Intermedia, Descenso
B_F1_ZONAL = B_ZONA_TAM - 1        # 17 fechas de zona (una rueda de 18)
B_F1_INTER = 8                     # 8 fechas interzonales antes de pasar a la fase 2
B_F1 = B_F1_ZONAL + B_F1_INTER     # 25 fechas en total en la fase 1 de la B
B_F2 = B_TAM2[2] - 1              # 11 fechas (las tres zonas son de 12)
B_RED = 4                         # octavos, cuartos, semifinales, final
B_TOTAL = B_F1 + B_F2 + B_RED + 1 # + promoción = 31
B_ETAPAS = ["Octavos del reducido", "Cuartos del reducido", "Semifinales del reducido",
            "Final del reducido"]
B_ZONAS2 = ["Campeonato", "Intermedia", "Descenso"]

# Federal A: la fase 1 tiene 5 grupos "por cercanía" cuyo tamaño no es fijo (el plantel
# cambia con los ascensos/descensos), así que su cantidad de fechas se calcula por
# temporada (ver nueva_estructura_f), no acá.
F_ZONA_TAM = 10                   # Campeonato y Descenso en la fase 2 (10 y 10)
F_F2_RONDAS = F_ZONA_TAM - 1       # 9 fechas, una rueda
F_RED = 3                          # eliminatoria, semifinales, final
F_ETAPAS = ["Eliminatoria preliminar", "Semifinales del reducido", "Final del reducido"]
F_MIN = 36                         # mínimo de equipos del Federal A (si falta, reubicación)
F_DESC = 6                         # los 6 últimos de la zona Descenso bajan al Regional Amateur


def destino(pos):
    """Destino en Primera según la posición final (1-30)."""
    if 1 <= pos <= 5:
        return "Libertadores"
    if 6 <= pos <= 8:
        return "Sudamericana"
    if pos == 11:
        return "Fase previa Libertadores"
    if pos in (12, 13):
        return "Sudamericana"
    if pos == N - 3:
        return "Promoción"
    if pos >= N - 2:
        return "Desciende"
    return ""


def destino_b1(pos):
    """Fase 1 de la B: a qué zona de la fase 2 pasa según la posición en la zona A/B."""
    if pos <= 6:
        return "→ Zona Campeonato"
    if pos <= 12:
        return "→ Zona Intermedia"
    return "→ Zona Descenso"


def destino_b2(z, pos):
    """Fase 2 de la B: destino según la zona (0 Campeonato, 1 Intermedia, 2 Descenso)."""
    if z == 0:
        if pos == 1:
            return "Campeón · Ascenso"
        if pos == 2:
            return "Ascenso directo"
        return "Cuartos del reducido" if pos <= 4 else "Octavos del reducido"
    if z == 1:
        return "Octavos del reducido" if pos <= 4 else "Eliminado"
    return "Permanece" if pos <= 6 else "Desciende"


def destino_f1(pos):
    return "→ Zona Campeonato" if pos <= 4 else "→ Zona Descenso"


def destino_f2(z, pos, n=0):
    if z == 0:
        if pos <= 3:
            return "Ascenso directo"
        return "Reducido" if pos <= 8 else ""
    return "Desciende" if pos > n - F_DESC else ""


def total_primera(S):
    """Fechas de Primera contando las de desempate (si las hubo)."""
    return TOTAL_FECHAS + S.get("extra_f2", 0)


def primera_terminada(S):
    """Primera terminó de verdad: 38 fechas y también sus desempates."""
    return S["fecha"] >= total_primera(S)


def total_b(SB):
    """Fechas de la Primera Nacional contando las de desempate (si las hubo)."""
    return B_TOTAL + SB.get("extra_f2", 0)


def rotulo_p(S, n):
    extra = S.get("extra_f2", 0)
    if n <= FECHAS_F1:
        return f"Fecha {n}"
    if n <= TOTAL_FECHAS:
        return f"Fecha {n} · Fase 2"
    return f"Fecha {n} · Desempate"


def rotulo_b(SB, n):
    extra = SB.get("extra_f2", 0)
    if n <= B_F1:
        return f"Fecha {n} · Fase 1"
    if n <= B_F1 + B_F2 + extra:
        if n <= B_F1 + B_F2:
            return f"Fecha {n} · Fase 2 (fecha {n - B_F1})"
        else:
            return f"Fecha {n} · Desempate Permanencia"
    if n <= B_F1 + B_F2 + extra + B_RED:
        return f"Fecha {n} · {B_ETAPAS[n - B_F1 - B_F2 - extra - 1]}"
    return f"Fecha {n} · Promoción"


def rotulo_f(SF, n):
    f1 = SF["f1_rondas"]
    if n <= f1:
        return f"Fecha {n} · Fase 1"
    if n <= f1 + SF.get("f2_rondas", 0):
        return f"Fecha {n} · Fase 2 (fecha {n - f1})"
    return f"Fecha {n} · {F_ETAPAS[n - f1 - SF['f2_rondas'] - 1]}"


# ----------------------------------------------------------------------------
# MOTOR PRIMERA
# ----------------------------------------------------------------------------
def definir_bloque(rng, r, bloque, sorpresa, registrar, comp_duelo, comp_liguilla, nom,
                   campeonato=False, cupos=1, ronda=1):
    """Desempate de un bloque de equipos igualados en puntos: partido único en cancha neutral
    (si empatan, penales). 2 equipos: un partido; 3 o más: liguilla todos contra todos.
    En una definición por el campeonato, si el 1° puesto de la liguilla vuelve a quedar
    igualado en puntos, esos equipos juegan otra definición: el título nunca se decide por
    diferencia de gol. `registrar(a, b, gl, gv, tanda, gana, comp)` guarda cada partido y lo
    devuelve. Los partidos de una liguilla llevan el orden final y cuántos logran el objetivo
    (`cupos`) para pintar su tabla. Devuelve el bloque ordenado."""
    bloque = [int(e) for e in bloque]
    suf = "" if ronda == 1 else " · definición" if ronda == 2 else f" · definición {ronda - 1}"
    if len(bloque) == 2:
        a, b = bloque
        gl, gv, gana_l, pen = jugar_ko(rng, np.array([r[a]]), np.array([r[b]]), sorpresa, localia=0.0)
        tanda = tanda_penales(rng, gana_l[0]) if pen[0] else None
        gana = a if gana_l[0] else b
        registrar(a, b, gl[0], gv[0], tanda, gana, comp_duelo + suf)
        return [gana, b if gana == a else a]
    puntos = {e: 0 for e in bloque}
    partidos = []
    for i in range(len(bloque)):
        for j in range(i + 1, len(bloque)):
            a, b = bloque[i], bloque[j]
            gl, gv, gana_l, pen = jugar_ko(rng, np.array([r[a]]), np.array([r[b]]), sorpresa, localia=0.0)
            tanda = tanda_penales(rng, gana_l[0]) if pen[0] else None
            gana = a if gana_l[0] else b
            puntos[gana] += 3
            partidos.append(registrar(a, b, gl[0], gv[0], tanda, gana, comp_liguilla + suf))
    orden = sorted(bloque, key=lambda e: -puntos[e])
    if campeonato:
        arriba = [e for e in orden if puntos[e] == puntos[orden[0]]]
        if len(arriba) > 1:
            sub = definir_bloque(rng, r, arriba, sorpresa, registrar, comp_duelo, comp_liguilla, nom,
                                 campeonato=True, cupos=1, ronda=ronda + 1)
            orden = sub + [e for e in orden if e not in arriba]
    for partido in partidos:
        partido["orden"] = [nom[e] for e in orden]
        partido["cupos"] = cupos
    return orden


def nueva_estructura(S):
    """Reinicia stats y fixture de la Primera para la temporada actual."""
    perm = S["rng"].permutation(N)
    fechas = generar_fixture(N)
    S["fechas"] = [[(int(perm[a]), int(perm[b])) for a, b in p] for p in fechas]
    S["fecha"] = 0
    S["fase"] = 1
    S["zonas"] = None
    S["zona_de"] = None
    S["snap"] = None
    S["tabla_f1"] = None
    S["acumular"] = True
    for k in STATS:
        S[k] = np.zeros(N, dtype=int)
    S["historial"] = []
    S["log"] = []           
    S["pos_hist"] = []      
    S["sorpresas"] = 0
    S["cerrada"] = False
    
    # Nuevas variables para desempates dinámicos
    S["extra_f2"] = 0
    S["orden_final_campeonato"] = None
    S["orden_final_descenso"] = None
    S["desempate_pendiente"] = False
    S["ids_desempate"] = []
    S["motivos_desempate"] = []


def stats_visibles(S):
    """Estadísticas a mostrar (en la fase 2 pueden excluir la fase 1)."""
    if S["fase"] == 2 and not S["acumular"]:
        return {k: S[k] - S["snap"][k] for k in STATS}
    return {k: S[k] for k in STATS}


def df_base(S, ids):
    return df_stats(S["nombres"], S["r"], stats_visibles(S), ids)


def tabla_general(S):
    df = df_base(S, np.arange(N))
    df.insert(0, "Pos", df.index + 1)
    return df


def tabla_zona(S, z):
    df = df_base(S, S["zonas"][z])
    
    # Inyectar el desempate en la zona correspondiente
    if z == 0 and S.get("orden_final_campeonato") is not None:
        df = df.set_index("id").loc[S["orden_final_campeonato"]].reset_index()
    elif z == 2 and S.get("orden_final_descenso") is not None:
        df = df.set_index("id").loc[S["orden_final_descenso"]].reset_index()
        
    df.insert(0, "Pos", z * ZONA_TAM + df.index + 1)
    df["Destino"] = [destino(p) for p in df["Pos"]]
    
    # Pintar fronteras empatadas
    if S.get("motivos_desempate"):
        ids_act = df["id"].to_numpy()
        for motivo in S["motivos_desempate"]:
            partes = motivo.split()
            zona_motivo = int(partes[1])
            if zona_motivo == z:
                nombre_frontera = partes[2]
                inicio, fin = map(int, partes[3].split("-"))
                ids_bloque = ids_act[inicio:fin]
                df.loc[df["id"].isin(ids_bloque), "Destino"] = f"Desempate {nombre_frontera}"
                
    return df


def tabla_final(S):
    return pd.concat([tabla_zona(S, z) for z in range(3)])


def iniciar_fase2(S, acumular):
    """Arma las zonas según la tabla de la fase 1 y agrega las 9 fechas."""
    S["tabla_f1"] = tabla_general(S)          # queda guardada para consultarla después
    orden = S["tabla_f1"]["id"].to_numpy()
    S["zonas"] = [orden[z * ZONA_TAM:(z + 1) * ZONA_TAM] for z in range(3)]
    S["zona_de"] = np.zeros(N, dtype=int)
    for z, ids in enumerate(S["zonas"]):
        S["zona_de"][ids] = z
    S["snap"] = {k: S[k].copy() for k in STATS}
    S["acumular"] = acumular

    # H[x, y] = True si x fue local contra y en la fase 1
    H = np.zeros((N, N), dtype=bool)
    for pares in S["fechas"][:FECHAS_F1]:
        for a, b in pares:
            H[a, b] = True

    previas = ultimas_localias(S["fechas"][:FECHAS_F1])
    por_zona = [fixture_revancha(S["rng"], S["zonas"][z], H, previas) for z in range(3)]
    for k in range(FECHAS_F2):
        S["fechas"].append([p for z in range(3) for p in por_zona[z][k]])
    S["fase"] = 2


def simular_fecha(S, P, acumular=True):
    f = S["fecha"]
    extra = S.get("extra_f2", 0)
    TOTAL_DYN = TOTAL_FECHAS + extra
    
    if f >= TOTAL_DYN:
        return
        
    r, nom = S["r"], S["nombres"]
    es_desempate = S.get("desempate_pendiente") and f == TOTAL_DYN - 1
    
    if not es_desempate:
        pares = S["fechas"][f]
        h = np.array([x[0] for x in pares])
        a = np.array([x[1] for x in pares])
        gh, ga = jugar(S["rng"], S["r"][h], S["r"][a], **P)
        sumar_partidos(S, h, a, gh, ga)

        d = S["r"][h] - S["r"][a]
        sorp = ((d >= 3) & (ga > gh)) | ((d <= -3) & (gh > ga))
        S["sorpresas"] += int(sorp.sum())

        datos = {
            "Local": [nom[i] for i in h],
            "GL": gh, "GV": ga,
            "Visitante": [nom[i] for i in a],
        }
        if S["fase"] == 2:
            datos = {"Zona": [ZONAS[S["zona_de"][i]] for i in h], **datos}
        S["historial"].append(pd.DataFrame(datos))
        n_f = f + 1
        for x, y, g1, g2 in zip(h, a, gh, ga):
            comp = "Fase 1" if S["fase"] == 1 else f"Zona {ZONAS[S['zona_de'][x]]}"
            S["log"].append(nuevo_partido("Primera División", n_f, rotulo_p(S, n_f), comp,
                                          nom[x], nom[y], g1, g2))
        revisar_liga(S, S["log"][-len(h):], S["rng"])       # suspensiones y sanciones (rarísimo)
    else:
        # ---------------- EJECUCIÓN DE LOS DESEMPATES (CAMPEÓN/DESCENSO) ----------------
        motivos = S.get("motivos_desempate", [])
        for motivo in motivos:
            partes = motivo.split()
            tipo = partes[0]
            zona = int(partes[1])
            nombre_frontera = partes[2]
            inicio, fin = map(int, partes[3].split("-"))
            
            df_prev = tabla_zona(S, zona)
            ids_finales = df_prev["id"].to_numpy().copy()
            bloque = ids_finales[inicio:fin]
            
            def registrar(a, b, gl, gv, tanda, gana, comp):
                partido = nuevo_partido("Primera División", f + 1, "Desempate", comp, nom[a], nom[b],
                                        gl, gv, tanda=tanda, gana=nom[gana], neutral=True)
                S["log"].append(partido)
                return partido

            # cupos: cuántos del bloque logran el objetivo (título / permanencia / evitar promoción)
            cupos = {"Campeonato": 1, "Permanencia": 7 - inicio, "Promocion": 6 - inicio}.get(nombre_frontera, 1)
            ids_finales[inicio:fin] = definir_bloque(
                S["rng"], r, bloque, P["sorpresa"], registrar, nombre_frontera,
                f"Liguilla {nombre_frontera}", nom, campeonato=nombre_frontera == "Campeonato", cupos=cupos)

            if zona == 0:
                S["orden_final_campeonato"] = ids_finales
            elif zona == 2:
                S["orden_final_descenso"] = ids_finales
                
        S["desempate_pendiente"] = False

    tabla = tabla_general(S) if S["fase"] == 1 else tabla_final(S)
    pos = np.zeros(N, dtype=int)
    pos[tabla["id"].to_numpy()] = tabla["Pos"].to_numpy()
    S["pos_hist"].append((S["fase"], pos))
    S["fecha"] += 1

    if S["fase"] == 1 and S["fecha"] == FECHAS_F1:
        iniciar_fase2(S, acumular)
        
    # ---------------- DETECCIÓN DE EMPATES ----------------
    ya_se_jugo = S.get("orden_final_campeonato") is not None or S.get("orden_final_descenso") is not None
    if S["fase"] == 2 and S["fecha"] == TOTAL_FECHAS + extra and not ya_se_jugo:
        partidos_desempate = []
        ids_involucrados = []
        motivos = []
        
        # --- ZONA CAMPEONATO (1° Puesto) ---
        df_camp = tabla_zona(S, 0)
        pts_camp = df_camp["Pts"].to_numpy()
        ids_camp = df_camp["id"].to_numpy()
        if pts_camp[0] == pts_camp[1]:
            pts_empate = pts_camp[0]
            inicio, fin = 0, 1
            while fin < len(pts_camp) and pts_camp[fin] == pts_empate:
                fin += 1
            ids_bloque = [int(i) for i in ids_camp[inicio:fin]]
            ids_involucrados.extend(ids_bloque)
            if len(ids_bloque) == 2:
                motivos.append(f"Duelo 0 Campeonato {inicio}-{fin}")
                partidos_desempate.append((ids_bloque[0], ids_bloque[1]))
            else:
                motivos.append(f"Liguilla 0 Campeonato {inicio}-{fin}")
                partidos_desempate.append((ids_bloque[0], ids_bloque[0]))
                
        # --- ZONA DESCENSO (Permanencia y Promoción) ---
        df_desc = tabla_zona(S, 2)
        pts_desc = df_desc["Pts"].to_numpy()
        ids_desc = df_desc["id"].to_numpy()
        
        # 6 = Permanencia (27° vs 28° globales), 5 = Promocion (26° vs 27° globales)
        fronteras = [(6, "Permanencia"), (5, "Promocion")]
        bloques_procesados = set()
        for idx_f, nombre_f in fronteras:
            if pts_desc[idx_f] == pts_desc[idx_f + 1]:
                pts_empate = pts_desc[idx_f]
                inicio = idx_f
                while inicio > 0 and pts_desc[inicio - 1] == pts_empate:
                    inicio -= 1
                fin = idx_f + 1
                while fin < len(pts_desc) and pts_desc[fin] == pts_empate:
                    fin += 1
                
                if inicio not in bloques_procesados:
                    bloques_procesados.add(inicio)
                    ids_bloque = [int(i) for i in ids_desc[inicio:fin]]
                    ids_involucrados.extend(ids_bloque)
                    if len(ids_bloque) == 2:
                        motivos.append(f"Duelo 2 {nombre_f} {inicio}-{fin}")
                        partidos_desempate.append((ids_bloque[0], ids_bloque[1]))
                    else:
                        motivos.append(f"Liguilla 2 {nombre_f} {inicio}-{fin}")
                        partidos_desempate.append((ids_bloque[0], ids_bloque[0]))
                        
        if partidos_desempate:
            S["desempate_pendiente"] = True
            S["ids_desempate"] = ids_involucrados
            S["motivos_desempate"] = motivos
            S["extra_f2"] = extra + 1
            S["fechas"].append(partidos_desempate)
            return


def nueva_estructura_b(SB, rng):
    """Sortea las zonas A y B (18 c/u) y arma el fixture de la fase 1."""
    n = len(SB["nombres"])
    perm = rng.permutation(n)
    SB["zonas"] = [perm[:B_ZONA_TAM], perm[B_ZONA_TAM:]]
    SB["zona_de"] = np.zeros(n, dtype=int)
    SB["zona_de"][SB["zonas"][1]] = 1
    base = generar_fixture(B_ZONA_TAM)
    fechas_zonal = [
        [(int(ids[a]), int(ids[b])) for ids in SB["zonas"] for a, b in base[k]]
        for k in range(B_F1_ZONAL)
    ]
    fechas_inter = generar_fixture_interzonal(rng, SB["zonas"][0], SB["zonas"][1], B_F1_INTER)
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
    df["Destino"] = [destino_b1(p) for p in df["Pos"]]
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
    df["Destino"] = [destino_b2(z, p) for p in df["Pos"]]

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


def iniciar_fase2_b(SB, rng):
    """Fin de la fase 1: reparte en 3 zonas conservando los puntos acumulados."""
    SB["tablas_f1"] = [tabla_b_f1(SB, z) for z in range(2)]
    ordA = SB["tablas_f1"][0]["id"].to_numpy()
    ordB = SB["tablas_f1"][1]["id"].to_numpy()
    cortes = ((0, 6), (6, 12), (12, 18))       # 6+6 / 6+6 / 6+6 = 12 / 12 / 12
    zonas2 = []
    for a, b in cortes:
        ids = np.concatenate([ordA[a:b], ordB[a:b]])
        zonas2.append(rng.permutation(ids))
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
    for k in range(B_F2):
        SB["fechas2"].append([p for fz in por_zona if k < len(fz) for p in fz[k]])


def iniciar_reducido(SB):
    """Fin de la fase 2: define ascensos directos, descensos y arma el reducido."""
    ids = [tabla_b_f2(SB, z)["id"].to_numpy() for z in range(3)]
    SB["ord2"] = ids
    SB["campeon"] = int(ids[0][0])
    SB["asc_directo"] = [int(ids[0][0]), int(ids[0][1])]
    SB["desc_b"] = [int(i) for i in ids[2][6:]]

    pts = 3 * SB["g"] + SB["e"]

    def bloque(idx, seed0, zona):
        idx = np.asarray(idx)[None, :]
        return {"id": idx, "zona": np.full(idx.shape, zona), "pts": pts[idx],
                "seed": np.arange(seed0, seed0 + idx.shape[1])[None, :]}

    directos = bloque(ids[0][2:4], 1, 0)                                     # 3°-4° Campeonato
    octavos = unir(bloque(ids[0][4:12], 3, 0), bloque(ids[1][:4], 11, 1))    # 5°-12° C + 1°-4° I
    SB["red"] = {"directos": directos, "octavos": octavos, "ganadores": None}

    filas = []
    for i in range(2):
        filas.append((i + 1, SB["nombres"][ids[0][2 + i]], f"{3 + i}° Campeonato", "Cuartos"))
    for i in range(8):
        filas.append((3 + i, SB["nombres"][ids[0][4 + i]], f"{5 + i}° Campeonato", "Octavos"))
    for i in range(4):
        filas.append((11 + i, SB["nombres"][ids[1][i]], f"{1 + i}° Intermedia", "Octavos"))
    SB["entrantes"] = pd.DataFrame(filas, columns=["Mérito", "Equipo", "Origen", "Entra en"])


def simular_fecha_b(S, P):
    """Simula la próxima fecha de la B. La promoción espera a que termine la Primera."""
    SB, rng = S["b"], S["rng"]
    f = SB["fecha"]
    extra = SB.get("extra_f2", 0)
    B_TOTAL_DYN = B_TOTAL + extra  # Alarga el campeonato dinámicamente si hay desempate
    
    # La promoción se juega contra el 27° de Primera: espera a que Primera termine
    # TODO, incluidos sus desempates (pueden cambiar quién queda 27°).
    if f >= B_TOTAL_DYN or (f == B_TOTAL_DYN - 1 and not primera_terminada(S)):
        return
    r, nom = SB["r"], SB["nombres"]

    if f < B_F1 + B_F2 + extra:                                   # ---- zonas (fase 1 y fase 2)
        es_desempate = SB.get("desempate_pendiente") and f == B_F1 + B_F2 + extra - 1
        
        if not es_desempate:
            if f < B_F1:
                pares = SB["fechas"][f]
                if f < B_F1_ZONAL:
                    etiqueta = lambda i: f"Zona {'AB'[SB['zona_de'][i]]}"
                else:
                    etiqueta = lambda i: "Interzonal"
            else:
                pares = SB["fechas2"][f - B_F1]
                etiqueta = lambda i: f"Zona {B_ZONAS2[SB['zona2_de'][i]]}"
            h = np.array([x[0] for x in pares])
            a = np.array([x[1] for x in pares])
            gh, ga = jugar(rng, r[h], r[a], **P)
            sumar_partidos(SB, h, a, gh, ga)
            SB["historial"].append(_fila_historial(
                SB, [etiqueta(i) for i in h], h, a, gh, ga, ""))
            for x, y, g1, g2 in zip(h, a, gh, ga):
                SB["log"].append(nuevo_partido("Primera Nacional", f + 1, rotulo_b(SB, f + 1),
                                               etiqueta(x), nom[x], nom[y], g1, g2))
            revisar_liga(SB, SB["log"][-len(h):], rng)
        else:
            # ---------------- EJECUCIÓN DE LOS DESEMPATES (CAMPEONATO / PERMANENCIA) ----------------
            motivos = SB.get("motivos_desempate", [])
            ordenes = {}

            def registrar(a, b, gl, gv, tanda, gana, comp):
                partido = nuevo_partido("Primera Nacional", f + 1, "Desempate", comp, nom[a], nom[b],
                                        gl, gv, tanda=tanda, gana=nom[gana], neutral=True)
                SB["log"].append(partido)
                return partido

            for motivo in motivos:
                partes = motivo.split()
                nombre_frontera = partes[1]
                inicio, fin = map(int, partes[2].split("-"))
                z = 0 if nombre_frontera == "Campeonato" else 2
                if z not in ordenes:
                    ordenes[z] = tabla_b_f2(SB, z)["id"].to_numpy().copy()
                ids_finales = ordenes[z]
                cupos = 1 if z == 0 else 6 - inicio      # zona Descenso: se salvan del 1° al 6°
                ids_finales[inicio:fin] = definir_bloque(
                    rng, r, ids_finales[inicio:fin], P["sorpresa"], registrar, nombre_frontera,
                    f"Liguilla {nombre_frontera}", nom, campeonato=z == 0, cupos=cupos)

            if 0 in ordenes:
                SB["orden_final_campeonato"] = ordenes[0]
            if 2 in ordenes:
                SB["orden_final_descenso"] = ordenes[2]
            SB["desempate_pendiente"] = False

        if f < B_F1:
            dfs, tag = [tabla_b_f1(SB, z) for z in range(2)], 1
        else:
            dfs, tag = [tabla_b_f2(SB, z) for z in range(3)], 2
        pos = np.zeros(len(nom), dtype=int)
        for dfz in dfs:
            pos[dfz["id"].to_numpy()] = dfz["Pos"].to_numpy()
        SB["pos_hist"].append((tag, pos))
        SB["fecha"] += 1
        
        if SB["fecha"] == B_F1:
            iniciar_fase2_b(SB, rng)
            
        # ---------------- DETECCIÓN DE EMPATES (1° DE CAMPEONATO Y PERMANENCIA) ----------------
        ya_se_jugo = (SB.get("orden_final_descenso") is not None
                      or SB.get("orden_final_campeonato") is not None)
        if SB["fecha"] == B_F1 + B_F2 + extra and not ya_se_jugo:
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
                fin_c = 1
                while fin_c < len(pts_c) and pts_c[fin_c] == pts_c[0]:
                    fin_c += 1
                ids_bloque = [int(i) for i in ids_c[:fin_c]]
                ids_involucrados.extend(ids_bloque)
                motivos.append(f"{'Duelo' if fin_c == 2 else 'Liguilla'} Campeonato 0-{fin_c}")
                partidos_desempate.append((ids_bloque[0], ids_bloque[1] if fin_c == 2 else ids_bloque[0]))
            
            # Los que bajan son los últimos 6 (índices 6 a 11). La frontera es entre el 6° (índice 5) y el 7° (índice 6)
            idx_frontera = 5
            nombre_frontera = "Permanencia"
            
            if pts[idx_frontera] == pts[idx_frontera + 1]:
                puntos_empate = pts[idx_frontera]
                inicio = idx_frontera
                while inicio > 0 and pts[inicio - 1] == puntos_empate:
                    inicio -= 1
                fin = idx_frontera + 1
                while fin < len(pts) and pts[fin] == puntos_empate:
                    fin += 1
                    
                ids_bloque = [int(i) for i in ids_desc[inicio:fin]]
                ids_involucrados.extend(ids_bloque)
                
                if len(ids_bloque) == 2:
                    motivos.append(f"Duelo {nombre_frontera} {inicio}-{fin}")
                    partidos_desempate.append((ids_bloque[0], ids_bloque[1]))
                else:
                    motivos.append(f"Liguilla {nombre_frontera} {inicio}-{fin}")
                    partidos_desempate.append((ids_bloque[0], ids_bloque[0]))
                    
            if partidos_desempate:
                SB["desempate_pendiente"] = True
                SB["ids_desempate"] = ids_involucrados
                SB["motivos_desempate"] = motivos
                SB["extra_f2"] = extra + 1
                SB["fechas2"].append(partidos_desempate)
                return
                
        # Una vez sorteado el desempate, arranca la sangría del Reducido
        if SB["fecha"] == B_F1 + B_F2 + SB.get("extra_f2", 0):
            iniciar_reducido(SB)

    elif f < B_F1 + B_F2 + extra + B_RED:                         # ---- reducido
        etapa = f - B_F1 - B_F2 - extra
        red = SB["red"]
        if etapa == 0:
            T = red["octavos"]
        elif etapa == 1:
            if red.get("ganadores") is None:
                return
            T = unir(red["directos"], red["ganadores"])
        else:
            if red.get("ganadores") is None:
                return
            T = red["ganadores"]
        A, B = cruces_mejor_peor(T)
        loc, vis, gl, gv, gan, per, pen = ko_jugar(rng, r, A, B, P["sorpresa"])
        red["ganadores"] = gan
        ronda = []
        for li, vi, g1, g2, wi, p in zip(loc["id"][0], vis["id"][0], gl[0], gv[0], gan["id"][0], pen[0]):
            tanda = tanda_penales(rng, wi == li) if p else None
            partido = nuevo_partido("Primera Nacional", f + 1, rotulo_b(SB, f + 1), B_ETAPAS[etapa],
                                    nom[li], nom[vi], g1, g2, tanda=tanda, gana=nom[wi])
            ronda.append(partido)
            SB["log"].append(partido)
        SB["bracket"].append(ronda)
        definicion = [f"Penales {m['pen'][0]}-{m['pen'][1]}: {m['gana']}" if m["pen"] else "" for m in ronda]
        SB["historial"].append(_fila_historial(SB, B_ETAPAS[etapa], loc["id"][0], vis["id"][0], gl[0], gv[0], definicion))
        if etapa == B_RED - 1:
            SB["asc_reducido"] = int(gan["id"][0, 0])
            SB["perdedor_final"] = int(per["id"][0, 0])
        SB["fecha"] += 1

    else:                                                 # ---- promoción
        final_p = tabla_final(S)
        fila = final_p[final_p["Pos"] == N - 3].iloc[0]
        p_id, p_nom = int(fila["id"]), fila["Equipo"]
        b_id = SB["perdedor_final"]
        gl, gv, gana_b, pen = jugar_ko(rng, np.array([r[b_id]]), np.array([S["r"][p_id]]),
                                       P["sorpresa"], localia=0.0)
        tanda = tanda_penales(rng, gana_b[0]) if pen[0] else None
        partido = nuevo_partido("Promoción", f + 1, "Promoción", "Promoción", nom[b_id], p_nom,
                                gl[0], gv[0], tanda=tanda,
                                gana=nom[b_id] if gana_b[0] else p_nom, neutral=True)
        SB["log"].append(partido)
        SB["promo_partido"] = partido
        partes = ["Cancha neutral"]
        if pen[0]:
            partes.append(f"Penales {partido['pen'][0]}-{partido['pen'][1]}: {partido['gana']}")
        SB["historial"].append(pd.DataFrame({
            "Instancia": "Promoción", "Local": [nom[b_id]], "GL": gl, "GV": gv,
            "Visitante": [p_nom], "Definición": " · ".join(partes),
        }))
        SB["promo"] = {"b_id": b_id, "p_id": p_id, "p_nombre": p_nom, "gana_b": bool(gana_b[0])}
        SB["fecha"] += 1


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


VERSION_ESTADO = 11       # cambia si se modifica la estructura del estado guardado


# ----------------------------------------------------------------------------
# MOTOR PRIMERA B Y PRIMERA C
# ----------------------------------------------------------------------------
def destino_pb(pos, total):
    if pos <= 2: return "Ascenso directo"
    if total >= 18 and pos >= 18: return "Desciende"
    return ""


def destino_pc(pos):
    return "Ascenso directo" if pos <= 2 else ""


def nueva_estructura_liga(S_LIGA, rng):
    n = len(S_LIGA["nombres"])
    base = generar_fixture(n)
    fechas = [[(int(a), int(b)) for a, b in pares] for pares in base]
    fechas += [[(v, l) for l, v in fecha] for fecha in fechas] # Vuelta
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


def tabla_pb(SPB):
    df = df_stats(SPB["nombres"], SPB["r"], SPB, np.arange(len(SPB["nombres"])))
    if SPB.get("orden_final") is not None:
        df = df.set_index("id").loc[SPB["orden_final"]].reset_index()
        
    df.insert(0, "Pos", df.index + 1)
    df["Destino"] = [destino_pb(p, len(SPB["nombres"])) for p in df["Pos"]]
    
    if SPB.get("motivos_desempate"):
        ids_actuales = df["id"].to_numpy()
        for motivo in SPB["motivos_desempate"]:
            partes = motivo.split()
            nombre_frontera = partes[1]
            inicio, fin = map(int, partes[2].split("-"))
            ids_bloque = ids_actuales[inicio:fin]
            df.loc[df["id"].isin(ids_bloque), "Destino"] = f"Desempate {nombre_frontera}"
            
    return df

def tabla_pc(SPC):
    df = df_stats(SPC["nombres"], SPC["r"], SPC, np.arange(len(SPC["nombres"])))
    if SPC.get("orden_final") is not None:
        df = df.set_index("id").loc[SPC["orden_final"]].reset_index()
        
    df.insert(0, "Pos", df.index + 1)
    df["Destino"] = [destino_pc(p) for p in df["Pos"]]
    
    if SPC.get("motivos_desempate"):
        ids_actuales = df["id"].to_numpy()
        for motivo in SPC["motivos_desempate"]:
            partes = motivo.split()
            nombre_frontera = partes[1]
            inicio, fin = map(int, partes[2].split("-"))
            ids_bloque = ids_actuales[inicio:fin]
            df.loc[df["id"].isin(ids_bloque), "Destino"] = f"Desempate {nombre_frontera}"
            
    return df


# ----------------------------------------------------------------------------
# MOTOR TORNEO REGIONAL AMATEUR
# ----------------------------------------------------------------------------
# 12 regiones -> 12 campeones -> 6 cruces -> 6 ascensos al Federal A.
# 1) Cada región es una liga única (sin zonas): todos contra todos a una sola vuelta.
#    Campeón: el 1°. Si dos o más igualan en puntos en el 1° puesto, desempate (partido
#    único o liguilla, cancha neutral, penales si empatan): nunca por diferencia de gol.
# 2) Final por el ascenso: los 12 campeones se cruzan de a pares según el JSON, a ida y
#    vuelta (cierra de local el de mejor campaña; si el global empata, penales). Los 6
#    ganadores ascienden al Federal A.
REG_LIGA = "Regional Amateur"
REG_FINAL = "Final por el ascenso"


def region_reg(nombre):
    return region_regional(nombre)


def nueva_estructura_reg(SR, rng):
    """Arma las 12 ligas regionales (una rueda) con los clubes que hoy juegan el Regional."""
    nombres = SR["nombres"]
    n = len(nombres)
    SR["region_de"] = [region_reg(nm) for nm in nombres]
    SR["grupos"] = {reg: np.array([i for i, rg in enumerate(SR["region_de"]) if rg == reg], dtype=int)
                    for reg in REGIONES_REG}
    idas = {reg: generar_fixture(len(ids)) if len(ids) > 1 else [] for reg, ids in SR["grupos"].items()}
    rondas = max((len(f) for f in idas.values()), default=0)
    fechas = [[] for _ in range(rondas)]
    for reg, f in idas.items():
        ids = SR["grupos"][reg]
        for k, pares in enumerate(f):
            fechas[k] += [(int(ids[x]), int(ids[y])) for x, y in pares]
    SR["fechas"] = fechas
    SR["f_liga"] = rondas
    SR["f_final0"] = rondas                            # 1ª fecha de las finales (corre si hay desempate)
    SR["total"] = rondas + 2
    SR["fecha"] = 0
    for k in STATS:
        SR[k] = np.zeros(n, dtype=int)
    SR["historial"] = []
    SR["log"] = []
    SR["pos_hist"] = []
    SR["desempate_pendiente"] = False
    SR["motivos_desempate"] = {}                       # región -> cantidad de igualados arriba
    SR["orden_final"] = {}                             # región -> ids ordenados tras el desempate
    SR["campeones"] = {reg: None for reg in REGIONES_REG}
    SR["finales"] = []
    SR["ascendidos"] = []


def _coef_reg(SR, i):
    pj = max(int(SR["pj"][i]), 1)
    pts = 3 * int(SR["g"][i]) + int(SR["e"][i])
    return pts / pj, (int(SR["gf"][i]) - int(SR["gc"][i])) / pj, int(SR["gf"][i]) / pj


def tabla_reg_region(SR, reg):
    """Tabla de la liga de una región (con el desempate por el título aplicado, si lo hubo)."""
    df = df_stats(SR["nombres"], SR["r"], SR, SR["grupos"][reg])
    if reg in SR["orden_final"]:
        df = df.set_index("id").loc[SR["orden_final"][reg]].reset_index()
    df.insert(0, "Pos", df.index + 1)
    destinos = ["Campeón regional" if p == 1 else "" for p in df["Pos"]]
    igualados = SR["motivos_desempate"].get(reg)
    if SR["desempate_pendiente"] and igualados:
        destinos = ["Desempate Campeonato" if k < igualados else d for k, d in enumerate(destinos)]
    df["Destino"] = destinos
    return df


def _cierre_ligas_reg(SR):
    """Al terminar la rueda: campeón de cada región, o desempate si el 1° puesto está igualado."""
    for reg in REGIONES_REG:
        ids = SR["grupos"][reg]
        if len(ids) == 0:
            continue
        df = tabla_reg_region(SR, reg)
        pts = df["Pts"].to_numpy()
        if len(pts) > 1 and pts[0] == pts[1]:
            fin = 1
            while fin < len(pts) and pts[fin] == pts[0]:
                fin += 1
            SR["motivos_desempate"][reg] = fin
        else:
            SR["campeones"][reg] = int(df["id"].iloc[0])
    if SR["motivos_desempate"]:
        SR["desempate_pendiente"] = True
        SR["f_final0"] = SR["f_liga"] + 1
        SR["total"] += 1


def _jugar_desempates_reg(SR, P, rng, n_fecha):
    nom, r = SR["nombres"], SR["r"]
    for reg, fin in SR["motivos_desempate"].items():
        ids = tabla_reg_region(SR, reg)["id"].to_numpy()

        def registrar(a, b, gl, gv, tanda, gana, comp, reg=reg):
            partido = nuevo_partido(REG_LIGA, n_fecha, "Desempate", comp, nom[a], nom[b],
                                    gl, gv, tanda=tanda, gana=nom[gana], neutral=True)
            partido["region"] = reg
            SR["log"].append(partido)
            return partido

        orden = definir_bloque(rng, r, ids[:fin], P["sorpresa"], registrar, f"Región {reg} · Campeonato",
                               f"Liguilla Región {reg} · Campeonato", nom, campeonato=True, cupos=1)
        SR["orden_final"][reg] = np.array(orden + [int(i) for i in ids[fin:]])
        SR["campeones"][reg] = int(orden[0])
    SR["desempate_pendiente"] = False


def _armar_finales_reg(SR):
    SR["finales"] = []
    for ra, rb in FINALES_REG:
        ca, cb = SR["campeones"][ra], SR["campeones"][rb]
        if ca is None or cb is None:                    # región sin campeón: el otro asciende
            SR["finales"].append({"a": ca if ca is not None else cb, "b": None, "reg": f"{ra} / {rb}",
                                  "ronda": REG_FINAL, "ida": None, "vuelta": None,
                                  "gana": ca if ca is not None else cb, "ga": 0, "gb": 0, "pen": None})
            continue
        # cierra de local el de mejor campaña en su liga regional
        a, b = sorted([ca, cb], key=lambda i: tuple(-x for x in _coef_reg(SR, i)))
        SR["finales"].append({"a": int(a), "b": int(b), "reg": f"{ra} / {rb}", "ronda": REG_FINAL,
                              "ida": None, "vuelta": None, "gana": None, "ga": 0, "gb": 0, "pen": None})


def _jugar_pierna_reg(SR, P, rng, series, vuelta, n_fecha):
    series = [x for x in series if x["b"] is not None]
    if not series:
        return
    nom, r = SR["nombres"], SR["r"]
    a = np.array([x["a"] for x in series])
    b = np.array([x["b"] for x in series])
    loc, vis = (a, b) if vuelta else (b, a)             # el mejor ubicado cierra de local
    gl, gv = jugar(rng, r[loc], r[vis], **P)
    for x, l, v, g1, g2 in zip(series, loc, vis, gl, gv):
        g1, g2 = int(g1), int(g2)
        if vuelta:
            x["ga"] += g1
            x["gb"] += g2
        else:
            x["ga"] += g2
            x["gb"] += g1
        comp = REG_FINAL if x["ronda"] == REG_FINAL else f"Región {x['reg']}"
        rotulo = f"{x['ronda']} · {'vuelta' if vuelta else 'ida'}"
        tanda, gana = None, None
        if vuelta:
            if x["ga"] != x["gb"]:
                x["gana"] = x["a"] if x["ga"] > x["gb"] else x["b"]
            else:                                       # global empatado: penales
                p_a = float(np.clip(0.5 + (r[x["a"]] - r[x["b"]]) / 400, 0.35, 0.65))
                gana_a = bool(rng.random() < p_a)
                tanda = tanda_penales(rng, gana_a)      # patea primero el local (a)
                x["gana"] = x["a"] if gana_a else x["b"]
                x["pen"] = (sum(tanda[0]), sum(tanda[1]))
                gana = nom[x["gana"]]
        partido = nuevo_partido(REG_LIGA, n_fecha, rotulo, comp, nom[l], nom[v], g1, g2,
                                tanda=tanda, gana=gana)
        partido["region"] = x["reg"]
        x["vuelta" if vuelta else "ida"] = partido
        SR["log"].append(partido)


def rotulo_reg(SR, n):
    """Nombre de la fecha n (1, 2, ...) del Regional."""
    if n <= SR["f_liga"]:
        return f"Fecha {n}"
    if n <= SR["f_final0"]:
        return "Desempate por el campeonato"
    return f"{REG_FINAL} · {'vuelta' if n - SR['f_final0'] == 2 else 'ida'}"


def simular_fecha_reg(SR, P, rng):
    f = SR["fecha"]
    if f >= SR["total"]:
        return
    if f < SR["f_liga"]:                                # ---- ligas regionales
        pares = SR["fechas"][f]
        if pares:
            h = np.array([x[0] for x in pares])
            a = np.array([x[1] for x in pares])
            gh, ga = jugar(rng, SR["r"][h], SR["r"][a], **P)
            sumar_partidos(SR, h, a, gh, ga)
            nom = SR["nombres"]
            for x, y, g1, g2 in zip(h, a, gh, ga):
                reg = SR["region_de"][x]
                partido = nuevo_partido(REG_LIGA, f + 1, f"Fecha {f + 1}", f"Región {reg}",
                                        nom[x], nom[y], g1, g2)
                partido["region"] = reg
                SR["log"].append(partido)
            revisar_liga(SR, SR["log"][-len(h):], rng)
        SR["fecha"] += 1
        if SR["fecha"] == SR["f_liga"]:
            _cierre_ligas_reg(SR)
        return
    if f < SR["f_final0"]:                              # ---- desempates por el título
        _jugar_desempates_reg(SR, P, rng, f + 1)
    else:                                               # ---- finales por el ascenso
        vuelta = f - SR["f_final0"] == 1
        if not vuelta:
            _armar_finales_reg(SR)
        _jugar_pierna_reg(SR, P, rng, SR["finales"], vuelta, f + 1)
        if vuelta:
            SR["ascendidos"] = [x["gana"] for x in SR["finales"] if x["gana"] is not None]
    SR["fecha"] += 1


def simular_fecha_liga(S_LIGA, P, rng, nombre_liga, fn_tabla):
    f = S_LIGA["fecha"]
    if f >= S_LIGA["total"]: return
    r, nom = S_LIGA["r"], S_LIGA["nombres"]
    
    es_desempate = S_LIGA.get("desempate_pendiente") and f == S_LIGA["total"] - 1
    pares = S_LIGA["fechas"][f]
    h = np.array([x[0] for x in pares])
    a = np.array([x[1] for x in pares])
    
    if not es_desempate:
        gh, ga = jugar(rng, r[h], r[a], **P)
        sumar_partidos(S_LIGA, h, a, gh, ga)
        S_LIGA["historial"].append(_fila_historial(S_LIGA, [nombre_liga] * len(h), h, a, gh, ga, ""))
        for x, y, g1, g2 in zip(h, a, gh, ga):
            S_LIGA["log"].append(nuevo_partido(nombre_liga, f + 1, f"Fecha {f + 1}", "Liga", nom[x], nom[y], g1, g2))
        revisar_liga(S_LIGA, S_LIGA["log"][-len(h):], rng)
    else:
        df_prev = fn_tabla(S_LIGA)
        ids_finales = df_prev["id"].to_numpy().copy()
        motivos = S_LIGA.get("motivos_desempate", [])
        
        # ---------------- EJECUCIÓN DE LOS DESEMPATES ----------------
        for motivo in motivos:
            partes = motivo.split()
            tipo = partes[0] # "Duelo" o "Liguilla"
            nombre_frontera = partes[1]
            inicio, fin = map(int, partes[2].split("-"))
            
            bloque = ids_finales[inicio:fin]
            
            def registrar(a, b, gl, gv, tanda, gana, comp):
                partido = nuevo_partido(nombre_liga, f + 1, "Desempate", comp, nom[a], nom[b],
                                        gl, gv, tanda=tanda, gana=nom[gana], neutral=True)
                S_LIGA["log"].append(partido)
                return partido

            # cupos: cuántos del bloque logran el objetivo (título / ascenso / permanencia)
            frontera = {"Campeonato": 0, "Ascenso": 1, "Permanencia": 16}.get(nombre_frontera, 0)
            ids_finales[inicio:fin] = definir_bloque(
                rng, r, bloque, P["sorpresa"], registrar, nombre_frontera, f"Liguilla {nombre_frontera}",
                nom, campeonato=nombre_frontera == "Campeonato", cupos=frontera + 1 - inicio)

        S_LIGA["orden_final"] = ids_finales
        S_LIGA["desempate_pendiente"] = False 

    df = fn_tabla(S_LIGA)
    ids = df["id"].to_numpy()
    pos = np.zeros(len(nom), dtype=int)
    pos[ids] = np.arange(1, len(ids) + 1)
    S_LIGA["pos_hist"].append((1, pos))
    S_LIGA["fecha"] += 1
    
    # ---------------- DETECCIÓN DE EMPATES GENÉRICA ----------------
    ya_se_jugo = S_LIGA.get("orden_final") is not None

    # === MODO TEST: FORZAR RESULTADOS A DEDO ===
    # if S_LIGA["fecha"] == S_LIGA["total"] and not ya_se_jugo:
        
        # TEST 1: Cuadrangular por el campeonato (Descomentá estas 3 líneas)
        # for i in [0, 1, 2, 3]:
        #     S_LIGA["g"][ids[i]] = 30; S_LIGA["e"][ids[i]] = 0
            

        # TEST 2: Triangular por el segundo ascenso (1ro cortado, 2do-3ro-4to empatados)
        # S_LIGA["g"][ids[0]] = 35; S_LIGA["e"][ids[0]] = 0
        # for i in [1, 2, 3]:
        #     S_LIGA["g"][ids[i]] = 25; S_LIGA["e"][ids[i]] = 0
            

        # TEST 3: Empate por el descenso (17mo y 18vo con mismos puntos)
        # if nombre_liga == "Primera B" and len(ids) >= 18:
            # # Igualamos las estadísticas del 18° exactamente con las del 17°
            # S_LIGA["g"][ids[17]] = S_LIGA["g"][ids[16]]
            # S_LIGA["e"][ids[17]] = S_LIGA["e"][ids[16]]           
            # # Hundimos a los que están del 19° para abajo para que no estorben
            # for i in range(18, len(ids)):
            #     S_LIGA["g"][ids[i]] = 0
            #     S_LIGA["e"][ids[i]] = 0


        # TEST 4: Triangular por el campeonato (1ro, 2do y 3ro empatados)
        # for i in [0, 1, 2]:
        #     S_LIGA["g"][ids[i]] = 30; S_LIGA["e"][ids[i]] = 0


        # TEST 5: Triangular por el descenso (16to, 17to y 18vo empatados)
        # if nombre_liga == "Primera B" and len(ids) >= 18:
            # # Igualamos las estadísticas del 16°, 17° y 18° exactamente entre sí
            # S_LIGA["g"][ids[17]] = S_LIGA["g"][ids[16]] = S_LIGA["g"][ids[15]]
            # S_LIGA["e"][ids[17]] = S_LIGA["e"][ids[16]] = S_LIGA["e"][ids[15]]
            # # Hundimos a los que están del 19° para abajo para que no estorben
            # for i in range(18, len(ids)):
            #     S_LIGA["g"][ids[i]] = 0
            #     S_LIGA["e"][ids[i]] = 0


        # TEST 6: Cuadrangular por el descenso (15to, 16to, 17to y 18vo empatados)
        # if nombre_liga == "Primera B" and len(ids) >= 18:
            # # Igualamos las estadísticas del 15°, 16°, 17° y 18° exactamente entre sí
            # S_LIGA["g"][ids[17]] = S_LIGA["g"][ids[16]] = S_LIGA["g"][ids[15]] = S_LIGA["g"][ids[14]]
            # S_LIGA["e"][ids[17]] = S_LIGA["e"][ids[16]] = S_LIGA["e"][ids[15]] = S_LIGA["e"][ids[14]]
            # # Hundimos a los que están del 19° para abajo para que no estorben
            # for i in range(18, len(ids)):
            #     S_LIGA["g"][ids[i]] = 0
            #     S_LIGA["e"][ids[i]] = 0


        # TEST 7: Empate masivo en el descenso (del 16to al último)
        # if nombre_liga == "Primera B" and len(ids) >= 18:
            # Le copiamos las estadísticas del 16° (índice 15) a todos los de abajo
            # for i in range(16, len(ids)):
            #     S_LIGA["g"][ids[i]] = S_LIGA["g"][ids[15]]
            #     S_LIGA["e"][ids[i]] = S_LIGA["e"][ids[15]]

        # Refresca la tabla y los puntos en memoria para que el sistema se coma el amague
        # df = fn_tabla(S_LIGA)
        # pts = df["Pts"].to_numpy()
        # ids = df["id"].to_numpy()
    # ===========================================

    if S_LIGA["fecha"] == S_LIGA["total"] and not ya_se_jugo:
        pts = df["Pts"].to_numpy()
        partidos_desempate = []
        ids_involucrados = []
        motivos = []
        
        # Define qué límites importan para cortar la tabla
        fronteras = [(0, "Campeonato"), (1, "Ascenso")]
        if nombre_liga == "Primera B" and len(ids) >= 18:
            fronteras.append((16, "Permanencia"))
            
        bloques_procesados = set()
        
        for idx_frontera, nombre_frontera in fronteras:
            if pts[idx_frontera] == pts[idx_frontera + 1]:
                puntos_empate = pts[idx_frontera]
                
                # Busca dónde empieza y dónde termina el bloque de empatados
                inicio = idx_frontera
                while inicio > 0 and pts[inicio - 1] == puntos_empate:
                    inicio -= 1
                    
                fin = idx_frontera + 1
                while fin < len(pts) and pts[fin] == puntos_empate:
                    fin += 1
                    
                if inicio not in bloques_procesados:
                    bloques_procesados.add(inicio)
                    
                    ids_bloque = [int(i) for i in ids[inicio:fin]]
                    ids_involucrados.extend(ids_bloque)
                    
                    if len(ids_bloque) == 2:
                        motivos.append(f"Duelo {nombre_frontera} {inicio}-{fin}")
                        partidos_desempate.append((ids_bloque[0], ids_bloque[1]))
                    else:
                        motivos.append(f"Liguilla {nombre_frontera} {inicio}-{fin}")
                        partidos_desempate.append((ids_bloque[0], ids_bloque[0]))
                        
        if partidos_desempate:
            S_LIGA["desempate_pendiente"] = True
            S_LIGA["ids_desempate"] = ids_involucrados
            S_LIGA["motivos_desempate"] = motivos
            S_LIGA["total"] += 1 
            S_LIGA["fechas"].append(partidos_desempate)
            return 
    
    # ---------------- CIERRE DE LA TEMPORADA ----------------
    if S_LIGA["fecha"] == S_LIGA["total"]:
        ids_cierre = S_LIGA["orden_final"] if ya_se_jugo else ids
        S_LIGA["campeon"] = int(ids_cierre[0])
        S_LIGA["asc_directo"] = [int(ids_cierre[0]), int(ids_cierre[1])]
        if nombre_liga == "Primera B":
            S_LIGA["desc_directo"] = [int(i) for i in ids_cierre[17:]] if len(ids_cierre) >= 18 else []


def crear_estado():
    rng = np.random.default_rng(time.time_ns() % (2**32))
    S = {
        "rng": rng, "temp": 1, "campeones": [], "movimientos": None,
        "rating": {**{k: float(v) for k, v in EQUIPOS.items()},
                   **{k: float(v) for k, v in EQUIPOS_B.items()},
                   **{k: float(v) for k, v in EQUIPOS_FEDERAL.items()},
                   **{k: float(v) for k, v in EQUIPOS_PRIMERA_B.items()},
                   **{k: float(v) for k, v in EQUIPOS_PRIMERA_C.items()},
                   **{k: float(v) for k, v in EQUIPOS_REGIONAL.items()}},
        "nombres": list(EQUIPOS),
        "r": np.array(list(EQUIPOS.values()), dtype=float),
        "federal": list(EQUIPOS_FEDERAL),
        "primera_b": list(EQUIPOS_PRIMERA_B),
        "primera_c": list(EQUIPOS_PRIMERA_C),
        "regional": list(EQUIPOS_REGIONAL),
        "cerrada_ambas": False, "version": VERSION_ESTADO,
    }
    nueva_estructura(S)
    SB = {"nombres": list(EQUIPOS_B), "r": np.array(list(EQUIPOS_B.values()), dtype=float)}
    nueva_estructura_b(SB, rng)
    S["b"] = SB
    SF = {"nombres": list(EQUIPOS_FEDERAL), "r": np.array(list(EQUIPOS_FEDERAL.values()), dtype=float)}
    nueva_estructura_f(SF, rng)
    S["f"] = SF
    SPB = {"nombres": list(EQUIPOS_PRIMERA_B), "r": np.array(list(EQUIPOS_PRIMERA_B.values()), dtype=float)}
    nueva_estructura_liga(SPB, rng)
    S["pb"] = SPB
    SPC = {"nombres": list(EQUIPOS_PRIMERA_C), "r": np.array(list(EQUIPOS_PRIMERA_C.values()), dtype=float)}
    nueva_estructura_liga(SPC, rng)
    S["pc"] = SPC
    SREG = {"nombres": list(EQUIPOS_REGIONAL), "r": np.array(list(EQUIPOS_REGIONAL.values()), dtype=float)}
    nueva_estructura_reg(SREG, rng)
    S["reg"] = SREG
    from copas import sortear_copa
    S["copa"] = sortear_copa(S, rng)    # temporada 1: clasifican los de mejor media de cada liga
    return S


def nueva_temporada(S, volatilidad):
    SB, SF, SPB, SPC, rng = S["b"], S["f"], S["pb"], S["pc"], S["rng"]
    for lig in (S, SB, SF, SPB, SPC, S["reg"]):
        for nom, x in zip(lig["nombres"], lig["r"]):
            S["rating"][nom] = float(x)

    final = tabla_final(S)
    promo = SB["promo"]
    # Copa Argentina de la temporada que viene: clasifican por lo hecho en esta
    from copas import clasificados_copa
    S["copa_clasif"] = [(x[0], x[3]) for x in clasificados_copa(S)]

    # Campeón de cada liga en la temporada que termina (para el Historial)
    def _campeon(L):
        return L["nombres"][L["campeon"]] if L.get("campeon") is not None else ""
    S["campeones"].append({
        "Temporada": S["temp"], "Primera División": final.iloc[0]["Equipo"],
        "Primera Nacional": _campeon(SB), "Federal A": _campeon(SF), "Primera B": _campeon(SPB),
        "Primera C": _campeon(SPC),
        "Copa Argentina": (S["copa"]["nombres"][S["copa"]["campeon"]]
                           if S.get("copa", {}).get("campeon") is not None else ""),
        "Regional": {reg: S["reg"]["nombres"][c] for reg, c in S["reg"]["campeones"].items() if c is not None},
    })
    p27 = promo["p_nombre"]
    directos = [SB["nombres"][i] for i in SB["asc_directo"]]
    reducido = SB["nombres"][SB["asc_reducido"]]
    suben = directos + [reducido]
    bajan_p = list(final[final["Pos"] >= N - 2]["Equipo"])
    if promo["gana_b"]:
        suben.append(SB["nombres"][promo["b_id"]])
        bajan_p.append(p27)
        
    bajan_b = [SB["nombres"][i] for i in SB["desc_b"]]
    bajan_b_fed = [n for n in bajan_b if origen(n) == "Interior"]
    bajan_b_pb = [n for n in bajan_b if origen(n) == "Metropolitana"]

    S["nombres"] = [n for n in S["nombres"] if n not in bajan_p] + suben
    base_b = [n for n in SB["nombres"] if n not in suben and n not in bajan_b] + bajan_p

    # Ascensos y descensos internos
    ascendidos_f = [SF["nombres"][i] for i in SF["ascendidos"]]
    ascendidos_pb = [SPB["nombres"][i] for i in SPB["asc_directo"]]
    descendidos_pb = [SPB["nombres"][i] for i in SPB["desc_directo"]]
    ascendidos_pc = [SPC["nombres"][i] for i in SPC["asc_directo"]]
    garantizados = list(ascendidos_f) + list(ascendidos_pb)
    
    faltan = max(0, NB - len(base_b) - len(garantizados))
    descendidos_f = [SF["nombres"][i] for i in SF.get("descendidos", [])]
    pool_fed = [n for n in S["federal"] if n not in garantizados and n not in descendidos_f]
    pool_pb = [n for n in SPB["nombres"] if n not in garantizados and n not in descendidos_pb]
    pool = pool_fed + pool_pb
    
    if faltan > 0:
        w = np.exp((np.array([S["rating"][n] for n in pool]) - 50.0) / 6.0)
        elegidos = set(rng.choice(len(pool), size=faltan, replace=False, p=w / w.sum()).tolist())
    else:
        elegidos = set()
        
    entran = garantizados + [pool[i] for i in elegidos]
    
    # Reasignación a las ligas inferiores
    S["federal"] = [n for i, n in enumerate(pool) if i not in elegidos and origen(n) == "Interior"] + bajan_b_fed
    S["primera_b"] = [n for i, n in enumerate(pool) if i not in elegidos and origen(n) == "Metropolitana"] + bajan_b_pb + ascendidos_pc
    S["primera_c"] = [n for n in SPC["nombres"] if n not in ascendidos_pc] + descendidos_pb

    # Regional Amateur: los 6 ganadores de las finales ascienden al Federal A
    ascendidos_reg = [S["reg"]["nombres"][i] for i in S["reg"]["ascendidos"]]
    S["federal"] = S["federal"] + ascendidos_reg
    S["regional"] = [n for n in S["regional"] if n not in ascendidos_reg] + descendidos_f
    
    SB["nombres"] = base_b + entran

    S["movimientos"] = {
        "directos": directos, "reducido": reducido,
        "bajan_p": bajan_p, 
        "bajan_b_fed": bajan_b_fed, 
        "bajan_b_pb": bajan_b_pb,
        "suben_f_b": ascendidos_f,
        "suben_pb_b": ascendidos_pb,
        "suben_pc_pb": ascendidos_pc,
        "suben_reg_fed": ascendidos_reg,
        "bajan_fed_reg": descendidos_f,
        "bajan_pb_pc": descendidos_pb,
        "entran_fed": [n for n in entran if origen(n) == "Interior" and n not in ascendidos_f],
        "entran_pb": [n for n in entran if origen(n) == "Metropolitana" and n not in ascendidos_pb],
        "campeon_federal": SF["nombres"][SF["campeon"]] if SF["campeon"] is not None else None,
        "promo_texto": (f"La promoción la ganó {'el equipo de la B' if promo['gana_b'] else p27}"
                        + (f": asciende {suben[-1]} y baja {p27}." if promo["gana_b"] else f", que se mantiene en Primera.")),
    }

    # ---- Tribunal de Disciplina: avisos de la temporada al historial, descensos
    # administrativos (lo gravísimo: baja una categoría más) y quitas de puntos a cero
    ligas_t = (S, SB, SF, SPB, SPC, S["reg"], S.get("copa", {}))
    S.setdefault("alertas_hist", [])
    for L in ligas_t:
        S["alertas_hist"] += [dict(a, temp=S["temp"]) for a in L.get("alertas", [])]
    bajan_adm = []
    for club in dict.fromkeys(c for L in ligas_t for c in L.get("desc_adm", [])):
        if club in S["nombres"]:                         # Primera -> B (sube el mejor de la B)
            sube = max((n for n in SB["nombres"] if n != club), key=lambda n: S["rating"][n])
            S["nombres"].remove(club)
            SB["nombres"].remove(sube)
            S["nombres"].append(sube)
            SB["nombres"].append(club)
        elif club in SB["nombres"]:                      # B -> Federal A / Primera B (sube otro)
            SB["nombres"].remove(club)
            (S["federal"] if origen(club) == "Interior" else S["primera_b"]).append(club)
            sube = max((n for n in S["federal"] + S["primera_b"] if n != club), key=lambda n: S["rating"][n])
            (S["federal"] if sube in S["federal"] else S["primera_b"]).remove(sube)
            SB["nombres"].append(sube)
        elif club in S["federal"]:                       # Federal A -> Regional
            S["federal"].remove(club)
            S["regional"].append(club)
        elif club in S["primera_b"]:                     # Primera B -> Primera C
            S["primera_b"].remove(club)
            S["primera_c"].append(club)
        else:
            continue
        bajan_adm.append(club)
    S["movimientos"]["descenso_adm"] = bajan_adm
    # Plazas vacantes del Federal A (reubicación): si queda con menos de F_MIN equipos, las
    # completan los perdedores de las finales del Regional (y después los mejores campeones y
    # clubes del Regional). Así siempre alcanza para 20 en Zona Campeonato y 6 descensos.
    extra_reg = []
    if len(S["federal"]) < F_MIN:
        SRg = S["reg"]
        perdedores = [SRg["nombres"][x["b"] if x["gana"] == x["a"] else x["a"]] for x in SRg["finales"]
                      if x.get("b") is not None and x.get("gana") is not None]
        campeones = sorted((SRg["nombres"][c] for c in SRg["campeones"].values() if c is not None),
                           key=lambda n: -S["rating"][n])
        for n in dict.fromkeys(perdedores + campeones + sorted(S["regional"], key=lambda n: -S["rating"][n])):
            if len(S["federal"]) >= F_MIN:
                break
            if n in S["regional"]:
                S["regional"].remove(n)
                S["federal"].append(n)
                extra_reg.append(n)
    S["movimientos"]["suben_reg_fed_extra"] = extra_reg
    for L in ligas_t[:-1]:
        L["alertas"], L["quita"], L["desc_adm"] = [], {}, []

    for nombres in (S["nombres"], SB["nombres"], S["federal"], S["primera_b"], S["primera_c"],
                    S["regional"]):
        arr = np.array([S["rating"][n] for n in nombres])
        arr = arr + REVERSION * (arr.mean() - arr) + rng.normal(0, volatilidad, len(arr))
        arr = np.clip(arr, MIN_R, MAX_R)
        for n, x in zip(nombres, arr): S["rating"][n] = float(x)
            
    S["r"] = np.array([S["rating"][n] for n in S["nombres"]])
    SB["r"] = np.array([S["rating"][n] for n in SB["nombres"]])
    
    S["temp"] += 1
    S["cerrada_ambas"] = False

    # --- AGREGAR ESTAS DOS LÍNEAS PARA BORRAR FANTASMAS ---
    SF["nombres"] = list(S["federal"])
    SF["r"] = np.array([S["rating"][n] for n in SF["nombres"]])
    # ------------------------------------------------------

    nueva_estructura(S)
    nueva_estructura_b(SB, rng)
    nueva_estructura_f(SF, rng)
    
    S["pb"]["nombres"] = list(S["primera_b"])
    S["pb"]["r"] = np.array([S["rating"][n] for n in S["pb"]["nombres"]])
    nueva_estructura_liga(S["pb"], rng)
    
    S["pc"]["nombres"] = list(S["primera_c"])
    S["pc"]["r"] = np.array([S["rating"][n] for n in S["pc"]["nombres"]])
    nueva_estructura_liga(S["pc"], rng)

    # Regional: los clubes del JSON que siguen en el torneo (en el orden del JSON) y después
    # los que bajaron del Federal A (cada uno juega en la región de su provincia)
    quedan = set(S["regional"])
    del_json = [x["nombre"] for x in REGIONAL if x["nombre"] in quedan]
    S["reg"]["nombres"] = del_json + [n for n in S["regional"] if n not in set(del_json)]
    S["reg"]["r"] = np.array([S["rating"][n] for n in S["reg"]["nombres"]])
    nueva_estructura_reg(S["reg"], rng)
    from copas import sortear_copa
    S["copa"] = sortear_copa(S, rng)    # se juega durante la temporada, los miércoles

    #----------------- REINICIAR ESTADOS DE DESEMPATE -----------------
    for liga in [S["pb"], S["pc"]]:
        liga["desempate_pendiente"] = False
        liga["ids_desempate"] = []
        liga["motivos_desempate"] = []
        liga["orden_final"] = None

"""Torneos: formato de cada categoría y paso de una temporada a otra.

Primera División, Primera Nacional, Federal A, Primera B y Primera C: cómo se
arman las zonas, quién asciende, quién desciende y cómo se juega cada fecha.
Todas las funciones reciben el estado como parámetro (no usan variables globales).
"""

import numpy as np
import pandas as pd
import time

from datos import (
    EQUIPOS,
    EQUIPOS_B,
    EQUIPOS_FEDERAL,
    EQUIPOS_PRIMERA_B,
    EQUIPOS_PRIMERA_C,
    F_GRUPOS_NOMBRES,
    N,
    NB,
    origen,
    region_de,
)
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


def destino_f2(z, pos):
    if z == 0:
        if pos <= 3:
            return "Ascenso directo"
        return "Reducido" if pos <= 8 else ""
    return ""


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
            
            if tipo == "Duelo":
                id_1, id_2 = bloque[0], bloque[1]
                gl, gv, gana_l, pen = jugar_ko(S["rng"], np.array([r[id_1]]), np.array([r[id_2]]), P["sorpresa"], localia=0.0)
                tanda = tanda_penales(S["rng"], gana_l[0]) if pen[0] else None
                gana_id = id_1 if gana_l[0] else id_2
                
                partido = nuevo_partido("Primera División", f + 1, "Desempate", nombre_frontera, nom[id_1], nom[id_2], gl[0], gv[0], tanda=tanda, gana=nom[gana_id], neutral=True)
                S["log"].append(partido)
                
                if gana_id == id_2:
                    ids_finales[inicio], ids_finales[inicio+1] = ids_finales[inicio+1], ids_finales[inicio]
                    
            elif tipo == "Liguilla":
                puntos = {eq: 0 for eq in bloque}
                for i in range(len(bloque)):
                    for j in range(i+1, len(bloque)):
                        eq1, eq2 = bloque[i], bloque[j]
                        gl, gv, gana_l, pen = jugar_ko(S["rng"], np.array([r[eq1]]), np.array([r[eq2]]), P["sorpresa"], localia=0.0)
                        tanda = tanda_penales(S["rng"], gana_l[0]) if pen[0] else None
                        gana_id = eq1 if gana_l[0] else eq2
                        puntos[gana_id] += 3
                        
                        partido = nuevo_partido("Primera División", f + 1, "Desempate", f"Liguilla {nombre_frontera}", nom[eq1], nom[eq2], gl[0], gv[0], tanda=tanda, gana=nom[gana_id], neutral=True)
                        S["log"].append(partido)
                        
                bloque_ordenado = sorted(bloque, key=lambda x: puntos[x], reverse=True)
                ids_finales[inicio:fin] = bloque_ordenado
                
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


def tabla_b_f1(SB, z):
    """Tabla de la zona A (0) o B (1) de la fase 1."""
    df = df_stats(SB["nombres"], SB["r"], SB, SB["zonas"][z])
    df.insert(0, "Pos", df.index + 1)
    df["Destino"] = [destino_b1(p) for p in df["Pos"]]
    return df


def tabla_b_f2(SB, z):
    """Tabla de la zona de la fase 2 (0 Campeonato, 1 Intermedia, 2 Descenso)."""
    df = df_stats(SB["nombres"], SB["r"], SB, SB["zonas2"][z])
    
    # Inyectar el desempate SÓLO en la zona de descenso
    if z == 2 and SB.get("orden_final_descenso") is not None:
        df = df.set_index("id").loc[SB["orden_final_descenso"]].reset_index()
        
    df.insert(0, "Pos", df.index + 1)
    df["Destino"] = [destino_b2(z, p) for p in df["Pos"]]
    
    if z == 2 and SB.get("motivos_desempate"):
        ids_actuales = df["id"].to_numpy()
        for motivo in SB["motivos_desempate"]:
            partes = motivo.split()
            nombre_frontera = partes[1]
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
    
    if f >= B_TOTAL_DYN or (f == B_TOTAL_DYN - 1 and S["fecha"] < TOTAL_FECHAS):
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
        else:
            # ---------------- EJECUCIÓN DEL DESEMPATE DE LA MUERTE ----------------
            df_prev = tabla_b_f2(SB, 2)
            ids_finales = df_prev["id"].to_numpy().copy()
            motivos = SB.get("motivos_desempate", [])
            
            for motivo in motivos:
                partes = motivo.split()
                tipo = partes[0]
                nombre_frontera = partes[1]
                inicio, fin = map(int, partes[2].split("-"))
                bloque = ids_finales[inicio:fin]
                
                if tipo == "Duelo":
                    id_1, id_2 = bloque[0], bloque[1]
                    gl, gv, gana_l, pen = jugar_ko(rng, np.array([r[id_1]]), np.array([r[id_2]]), P["sorpresa"], localia=0.0)
                    tanda = tanda_penales(rng, gana_l[0]) if pen[0] else None
                    gana_id = id_1 if gana_l[0] else id_2
                    
                    partido = nuevo_partido("Primera Nacional", f + 1, "Desempate", nombre_frontera, nom[id_1], nom[id_2], gl[0], gv[0], tanda=tanda, gana=nom[gana_id], neutral=True)
                    SB["log"].append(partido)
                    
                    if gana_id == id_2:
                        ids_finales[inicio], ids_finales[inicio+1] = ids_finales[inicio+1], ids_finales[inicio]
                        
                elif tipo == "Liguilla":
                    puntos = {eq: 0 for eq in bloque}
                    for i in range(len(bloque)):
                        for j in range(i+1, len(bloque)):
                            eq1, eq2 = bloque[i], bloque[j]
                            gl, gv, gana_l, pen = jugar_ko(rng, np.array([r[eq1]]), np.array([r[eq2]]), P["sorpresa"], localia=0.0)
                            tanda = tanda_penales(rng, gana_l[0]) if pen[0] else None
                            gana_id = eq1 if gana_l[0] else eq2
                            puntos[gana_id] += 3
                            
                            partido = nuevo_partido("Primera Nacional", f + 1, "Desempate", f"Liguilla {nombre_frontera}", nom[eq1], nom[eq2], gl[0], gv[0], tanda=tanda, gana=nom[gana_id], neutral=True)
                            SB["log"].append(partido)
                            
                    bloque_ordenado = sorted(bloque, key=lambda x: puntos[x], reverse=True)
                    ids_finales[inicio:fin] = bloque_ordenado
                    
            SB["orden_final_descenso"] = ids_finales
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
            
        # ---------------- DETECCIÓN DE EMPATES (SÓLO ZONA DESCENSO) ----------------
        ya_se_jugo = SB.get("orden_final_descenso") is not None
        if SB["fecha"] == B_F1 + B_F2 + extra and not ya_se_jugo:
            df_descenso = tabla_b_f2(SB, 2)
            pts = df_descenso["Pts"].to_numpy()
            ids_desc = df_descenso["id"].to_numpy()
            
            partidos_desempate = []
            ids_involucrados = []
            motivos = []
            
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


def tabla_f_grupo(SF, g):
    """Tabla del grupo `g` (0-4, por cercanía) de la fase 1."""
    df = df_stats(SF["nombres"], SF["r"], SF, SF["grupos"][g])
    df.insert(0, "Pos", df.index + 1)
    df["Destino"] = [destino_f1(p) for p in df["Pos"]]
    return df


def tabla_f_f2(SF, z):
    """Tabla de la zona de la fase 2 (0 Campeonato, 1 Descenso)."""
    df = df_stats(SF["nombres"], SF["r"], SF, SF["zonas2"][z])
    df.insert(0, "Pos", df.index + 1)
    df["Destino"] = [destino_f2(z, p) for p in df["Pos"]]
    return df


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


VERSION_ESTADO = 6       # cambia si se modifica la estructura del estado guardado


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
            
            if tipo == "Duelo":
                id_1, id_2 = bloque[0], bloque[1]
                gl, gv, gana_l, pen = jugar_ko(rng, np.array([r[id_1]]), np.array([r[id_2]]), P["sorpresa"], localia=0.0)
                tanda = tanda_penales(rng, gana_l[0]) if pen[0] else None
                gana_id = id_1 if gana_l[0] else id_2
                
                partido = nuevo_partido(nombre_liga, f + 1, "Desempate", nombre_frontera, nom[id_1], nom[id_2], gl[0], gv[0], tanda=tanda, gana=nom[gana_id], neutral=True)
                S_LIGA["log"].append(partido)
                
                if gana_id == id_2: # Si el peor gana, invertimos los índices
                    ids_finales[inicio], ids_finales[inicio+1] = ids_finales[inicio+1], ids_finales[inicio]
                    
            elif tipo == "Liguilla":
                puntos = {eq: 0 for eq in bloque}
                for i in range(len(bloque)):
                    for j in range(i+1, len(bloque)):
                        eq1, eq2 = bloque[i], bloque[j]
                        gl, gv, gana_l, pen = jugar_ko(rng, np.array([r[eq1]]), np.array([r[eq2]]), P["sorpresa"], localia=0.0)
                        tanda = tanda_penales(rng, gana_l[0]) if pen[0] else None
                        gana_id = eq1 if gana_l[0] else eq2
                        puntos[gana_id] += 3
                        
                        partido = nuevo_partido(nombre_liga, f + 1, "Desempate", f"Liguilla {nombre_frontera}", nom[eq1], nom[eq2], gl[0], gv[0], tanda=tanda, gana=nom[gana_id], neutral=True)
                        S_LIGA["log"].append(partido)
                        
                bloque_ordenado = sorted(bloque, key=lambda x: puntos[x], reverse=True)
                ids_finales[inicio:fin] = bloque_ordenado
                
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
                   **{k: float(v) for k, v in EQUIPOS_PRIMERA_C.items()}},
        "nombres": list(EQUIPOS),
        "r": np.array(list(EQUIPOS.values()), dtype=float),
        "federal": list(EQUIPOS_FEDERAL),
        "primera_b": list(EQUIPOS_PRIMERA_B),
        "primera_c": list(EQUIPOS_PRIMERA_C),
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
    return S


def nueva_temporada(S, volatilidad):
    SB, SF, SPB, SPC, rng = S["b"], S["f"], S["pb"], S["pc"], S["rng"]
    for lig in (S, SB, SF, SPB, SPC):
        for nom, x in zip(lig["nombres"], lig["r"]):
            S["rating"][nom] = float(x)

    final = tabla_final(S)
    promo = SB["promo"]
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
    pool_fed = [n for n in S["federal"] if n not in garantizados]
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
    
    SB["nombres"] = base_b + entran

    S["movimientos"] = {
        "directos": directos, "reducido": reducido,
        "bajan_p": bajan_p, 
        "bajan_b_fed": bajan_b_fed, 
        "bajan_b_pb": bajan_b_pb,
        "suben_f_b": ascendidos_f,
        "suben_pb_b": ascendidos_pb,
        "suben_pc_pb": ascendidos_pc, 
        "bajan_pb_pc": descendidos_pb,
        "entran_fed": [n for n in entran if origen(n) == "Interior" and n not in ascendidos_f],
        "entran_pb": [n for n in entran if origen(n) == "Metropolitana" and n not in ascendidos_pb],
        "campeon_federal": SF["nombres"][SF["campeon"]] if SF["campeon"] is not None else None,
        "promo_texto": (f"La promoción la ganó {'el equipo de la B' if promo['gana_b'] else p27}"
                        + (f": asciende {suben[-1]} y baja {p27}." if promo["gana_b"] else f", que se mantiene en Primera.")),
    }

    for nombres in (S["nombres"], SB["nombres"], S["federal"], S["primera_b"], S["primera_c"]):
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


    # Limpiar la memoria de desempates de la temporada anterior
    for liga in [S["pb"], S["pc"]]:
        liga["desempate_pendiente"] = False
        liga["ids_desempate"] = []
        liga["motivos_desempate"] = []
        liga["orden_final"] = None
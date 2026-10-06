"""Primera B, Primera C y Promocional Amateur: ligas ida y vuelta con la misma mecánica.
"""

import numpy as np

from motor.incidentes import revisar_liga
from motor.nucleo import (
    STATS,
    _fila_historial,
    df_stats,
    generar_fixture,
    jugar,
    nuevo_partido,
    sumar_partidos,
)
from ligas.primera import definir_bloque


# ----------------------------------------------------------------------------
# MOTOR PRIMERA B, PRIMERA C y Torneo Promocional Amateur (Nueva Primera D)
# ----------------------------------------------------------------------------
def destino_pb(pos, total):
    if pos <= 2: return "Ascenso directo"
    if total >= 18 and pos >= 18: return "Desciende"
    return ""


def destino_pc(pos, total):
    if pos <= 2: return "Ascenso directo"
    if total >= 18 and pos >= 18: return "Desciende"
    return ""


def destino_pd(pos, total):
    if pos <= 2: return "Ascenso directo"
    return ""


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
    S_LIGA["motivos_desempate"] = []        # si no, la tabla nueva sigue marcando el desempate anterior


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
    df["Destino"] = [destino_pc(p, len(SPC["nombres"])) for p in df["Pos"]]
    
    if SPC.get("motivos_desempate"):
        ids_actuales = df["id"].to_numpy()
        for motivo in SPC["motivos_desempate"]:
            partes = motivo.split()
            nombre_frontera = partes[1]
            inicio, fin = map(int, partes[2].split("-"))
            ids_bloque = ids_actuales[inicio:fin]
            df.loc[df["id"].isin(ids_bloque), "Destino"] = f"Desempate {nombre_frontera}"
            
    return df


def tabla_pd(SPD):
    df = df_stats(SPD["nombres"], SPD["r"], SPD, np.arange(len(SPD["nombres"])))
    if SPD.get("orden_final") is not None:
        df = df.set_index("id").loc[SPD["orden_final"]].reset_index()
        
    df.insert(0, "Pos", df.index + 1)
    df["Destino"] = [destino_pd(p, len(SPD["nombres"])) for p in df["Pos"]]
    
    if SPD.get("motivos_desempate"):
        ids_actuales = df["id"].to_numpy()
        for motivo in SPD["motivos_desempate"]:
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
        if nombre_liga in ("Primera B", "Primera C") and len(ids) >= 18:   # descienden del 18° para abajo
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
        if nombre_liga in ("Primera B", "Primera C"):
            S_LIGA["desc_directo"] = [int(i) for i in ids_cierre[17:]] if len(ids_cierre) >= 18 else []

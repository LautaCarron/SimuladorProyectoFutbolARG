"""Primera Nacional: dos zonas, fase 2, reducido y cómo se juega cada fecha.
"""

import numpy as np
import pandas as pd

from datos.equipos import N, NB
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
    ultimas_localias,
    unir,
)
from ligas.primera import definir_bloque, descensos, primera_terminada, tabla_final


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

FORMATOS_B = {
    "actual": "Formato actual (zonas + reducido)",
    "anual_ida": "Torneo anual · una rueda",
    "anual_ida_vuelta": "Torneo anual · ida y vuelta",
}
B_DESCIENDEN = 6                  # cuántos bajan de la B (por ahora fijo)


def cfg_b(S):
    """Lo que se eligió en el Modo dios para la Primera Nacional (se aplica al armar cada temporada)."""
    c = S.setdefault("cfg", {}).setdefault("b", {})
    c.setdefault("formato", "actual")
    return c


def formato_b(SB):
    """Formato con el que se está jugando esta temporada la Primera Nacional."""
    return SB.get("formato", "actual")


def es_anual_b(SB):
    return formato_b(SB) != "actual"


def total_base_b(SB):
    """Fechas de la liga sin contar promoción ni desempates (en el formato actual: fase 1 + fase 2)."""
    f = formato_b(SB)
    if f == "anual_ida":
        return NB - 1
    if f == "anual_ida_vuelta":
        return 2 * (NB - 1)
    return B_F1 + B_F2


def destino_b_anual(pos, k):
    """Torneo anual de la B: destino según la posición (k = cuántos suben)."""
    if pos == 1 and k >= 1:
        return "Campeón · Ascenso"
    if pos <= k:
        return "Ascenso directo"
    if pos == k + 1:
        return "Promoción"
    if pos > NB - B_DESCIENDEN:
        return "Desciende"
    return "Permanece"


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


def total_b(SB):
    """Fechas de la Primera Nacional contando las de desempate (si las hubo) y la promoción."""
    if es_anual_b(SB):
        return total_base_b(SB) + 1
    return B_TOTAL + SB.get("extra_f2", 0)


def rotulo_b(SB, n):
    if es_anual_b(SB):
        if n <= total_base_b(SB):
            return f"Fecha {n}" + (" · Vuelta" if formato_b(SB) == "anual_ida_vuelta" and n > NB - 1 else "")
        return f"Fecha {n} · Promoción"
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


def nueva_estructura_b(SB, rng, S=None):
    """Arma la temporada de la B según el formato elegido en el Modo dios (si se pasa S; si no, mantiene el actual).
    Formato actual: sortea las zonas A y B (18 c/u) y arma el fixture de la fase 1.
    Torneo anual: todos contra todos (ida o ida y vuelta) en una sola tabla."""
    if S is not None:
        SB["formato"] = cfg_b(S)["formato"]
    n = len(SB["nombres"])
    perm = rng.permutation(n)
    if es_anual_b(SB):
        SB["zonas"] = [np.arange(n)]
        SB["zona_de"] = np.zeros(n, dtype=int)
        fechas = [[(int(perm[a]), int(perm[b])) for a, b in par] for par in generar_fixture(n)]
        if formato_b(SB) == "anual_ida_vuelta":                    # la vuelta: mismas fechas con las localías al revés
            fechas += [[(v, l) for l, v in fecha] for fecha in fechas]
        SB["fechas"] = fechas
    else:
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


def tabla_b_anual(SB, k=3):
    """Torneo anual de la B: tabla única (k = cuántos suben; el siguiente juega la promoción)."""
    df = df_stats(SB["nombres"], SB["r"], SB, SB["zonas"][0])
    df.insert(0, "Pos", df.index + 1)
    df["Destino"] = [destino_b_anual(p, k) for p in df["Pos"]]
    return df


def cerrar_anual_b(S):
    """Fin del torneo anual de la B: campeón, ascensos, descensos y quién juega la promoción."""
    SB = S["b"]
    k = descensos(S)
    ids = [int(i) for i in tabla_b_anual(SB, k)["id"]]
    SB["ord2"] = [np.array(ids)]                      # orden final: ascensos_a_primera toma los k primeros
    SB["campeon"] = ids[0]
    SB["asc_directo"] = [ids[0], ids[1]]
    SB["asc_reducido"] = None                         # no hay reducido
    SB["desc_b"] = ids[-B_DESCIENDEN:]
    SB["perdedor_final"] = ids[min(k, len(ids) - 1)]  # el que sigue a los ascendidos juega la promoción


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
    if es_anual_b(SB):
        return _simular_fecha_b_anual(S, P)
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
            gh, ga = jugar(rng, r[h], r[a], **P, **mods_ids(rng, nom, h, a))
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
        loc, vis, gl, gv, gan, per, pen = ko_jugar(rng, r, A, B, P["sorpresa"], nombres=nom)
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
        _promocion_b(S, P, f)


def _promocion_b(S, P, f):
    """Promoción: el elegido de la B contra el que queda en el puesto N-k de Primera (cancha neutral)."""
    SB, rng = S["b"], S["rng"]
    r, nom = SB["r"], SB["nombres"]
    final_p = tabla_final(S)
    fila = final_p[final_p["Pos"] == N - descensos(S)].iloc[0]       # el último que se salva: juega la promoción
    p_id, p_nom = int(fila["id"]), fila["Equipo"]
    b_id = SB["perdedor_final"]
    gl, gv, gana_b, pen = jugar_ko(rng, np.array([r[b_id]]), np.array([S["r"][p_id]]),
                                   P["sorpresa"], localia=0.0,
                                   **mods_nombres(rng, [nom[b_id]], [p_nom]))
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



def _simular_fecha_b_anual(S, P):
    """Torneo anual de la B: una sola tabla (ida o ida y vuelta) y después la promoción contra el de Primera."""
    SB, rng = S["b"], S["rng"]
    f, base = SB["fecha"], total_base_b(SB)
    if f > base or (f == base and not primera_terminada(S)):
        return
    if f == base:
        _promocion_b(S, P, f)
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
    df = tabla_b_anual(SB, descensos(S))
    pos = np.zeros(len(nom), dtype=int)
    pos[df["id"].to_numpy()] = df["Pos"].to_numpy()
    SB["pos_hist"].append((1, pos))
    SB["fecha"] += 1
    if SB["fecha"] == base:
        cerrar_anual_b(S)


def ascensos_a_primera(S):
    """Nombres de los de la B que suben a Primera por los cupos de descenso (sin contar la promoción), en orden:
    campeón, 2°, ganador del reducido y, si la cantidad de descensos pide más, los siguientes de la Zona Campeonato.
    Sólo tiene sentido cuando la B terminó. El perdedor de la final del reducido queda afuera: juega la promoción."""
    SB = S["b"]
    k = descensos(S)
    nom = SB["nombres"]
    if es_anual_b(SB):                                # torneo anual: suben los k primeros de la tabla
        return [nom[int(i)] for i in SB["ord2"][0][:k]]
    prioridad = [nom[i] for i in SB["asc_directo"]] + [nom[SB["asc_reducido"]]]
    if k > len(prioridad):
        excluidos = set(prioridad)
        if SB.get("perdedor_final") is not None:
            excluidos.add(nom[SB["perdedor_final"]])
        extras = [nom[int(i)] for i in SB["ord2"][0] if nom[int(i)] not in excluidos]
        prioridad += extras[:k - len(prioridad)]
    return prioridad[:k]

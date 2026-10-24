"""Primera División: formatos, zonas, fixture, fase 2, tablas y cómo se juega cada fecha.

FORMATOS (se eligen al comienzo de la temporada desde el "Modo dios" del simulador; ver cfg_primera):
  * "actual":            fase 1 todos contra todos (29 fechas) + fase 2 en tres zonas (9 fechas).
  * "anual_ida":         torneo anual a una rueda (29 fechas).
  * "anual_ida_vuelta":  torneo anual ida y vuelta (58 fechas).
  * "apertura_clausura": Apertura y Clausura con llaves (ligas/apertura_clausura.py).
DESCENSOS: cuántos bajan directo a la B (por defecto 3). El que queda en el puesto N-k juega la promoción
contra el perdedor del reducido de la B, y suben de la B tantos como bajan (ver ligas/nacional.py).
"""

import numpy as np
import pandas as pd

from ligas.desempates import bloque_empatado, duelo_o_liguilla
from datos.equipos import N
from ligas import apertura_clausura as ac
from motor.incidentes import revisar_liga
from motor.nucleo import (
    DESC_LIGA_MIN,
    STATS,
    df_stats,
    fixture_revancha,
    generar_fixture,
    jugar,
    jugar_ko,
    mods_ids,
    mods_nombres,
    nuevo_partido,
    sumar_partidos,
    tanda_penales,
    ultimas_localias,
)


# Primera
ZONA_TAM = N // 3                 # 10 equipos por zona


FECHAS_F1 = N - 1                 # 29 fechas todos contra todos


FECHAS_F2 = ZONA_TAM - 1          # 9 fechas por zona


TOTAL_FECHAS = FECHAS_F1 + FECHAS_F2


# Los valores de arriba son los de los 30 equipos de siempre. La cantidad de equipos de Primera puede cambiar
# (Modo dios): lo que se usa en cada temporada sale de len(S["nombres"]) con estos ayudantes.
PRIMERA_MIN, PRIMERA_MAX = DESC_LIGA_MIN, 48     # como en las demás ligas: nunca menos de 14 equipos
IDA_VUELTA_MAX = 24               # el torneo anual ida y vuelta sólo se puede jugar con 24 equipos o menos


def _rondas_p(m):
    return m - 1 if m % 2 == 0 else m


def tam_zonas_p(n):
    """Zonas de la fase 2 (Campeonato, Intermedia, Descenso): con más de 30 equipos, 10/10/X; si no, parejas."""
    if n > N:
        return [ZONA_TAM, ZONA_TAM, n - 2 * ZONA_TAM]
    base, resto = divmod(n, 3)
    return [base + (1 if k < resto else 0) for k in range(3)]


def zona_de_pos(pos, n):
    """Zona de la fase 2 (0, 1 o 2) que corresponde al puesto `pos` (1...n) de la fase 1."""
    c, i, _ = tam_zonas_p(n)
    return 0 if pos <= c else 1 if pos <= c + i else 2


def fechas_f1(S):
    return _rondas_p(len(S["nombres"]))


def fechas_f2(S):
    return max(_rondas_p(z) for z in tam_zonas_p(len(S["nombres"])))


def equipos_objetivo_p(S, auto=None):
    """Cuántos equipos tendrá Primera la temporada que viene. Si en el Modo dios no se fijó una cantidad, es la
    automática (`auto`, o los que tiene ahora): cambia con los ascensos de la B y los descensos de Primera."""
    n = cfg_primera(S).get("equipos")
    if n is None:
        n = auto if auto is not None else len(S["nombres"])
        return max(PRIMERA_MIN, min(PRIMERA_MAX, int(n)))
    n = max(PRIMERA_MIN, min(PRIMERA_MAX, int(n)))
    return n - n % 2


ZONAS = ["Campeonato", "Intermedia", "Descenso"]


FORMATOS = {
    "actual": "Formato actual (fase 1 + zonas)",
    "anual_ida": "Torneo anual · una rueda",
    "anual_ida_vuelta": "Torneo anual · ida y vuelta",
    "apertura_clausura": "Apertura y Clausura con llaves",
}
DESCENSOS_DEF = 3
DESCENSOS_MAX = 6
PROMOS_DEF = 1                    # series de promoción contra la B (0, 1 o 2)
PROMOS_MAX = 2


def promos(S):
    """Cuántas promociones se juegan esta temporada (Modo dios)."""
    return int(S.get("p_prom", PROMOS_DEF))


def cfg_primera(S):
    """Lo que se eligió en el Modo dios para Primera (se aplica al armar cada temporada)."""
    c = S.setdefault("cfg", {}).setdefault("primera", {})
    c.setdefault("formato", "actual")
    c.setdefault("descensos", DESCENSOS_DEF)
    c.setdefault("promociones", PROMOS_DEF)
    return c


ACTUAL_MIN, ANUAL_IDA_MIN = 27, 25      # equipos mínimos: formato actual 27, anual una vuelta 25


def formatos_posibles(n):
    """Formatos que se pueden elegir con `n` equipos: actual con 27 o más, anual una rueda con 25 o más y anual
    ida y vuelta con 24 o menos (Apertura y Clausura no se restringe por ahora)."""
    return [f for f in FORMATOS if f == "apertura_clausura"
            or (f == "actual" and n >= ACTUAL_MIN) or (f == "anual_ida" and n >= ANUAL_IDA_MIN)
            or (f == "anual_ida_vuelta" and n <= IDA_VUELTA_MAX)]


def formato_posible(f, n):
    """`f` si se puede con `n` equipos; si no, el que corresponde: 24 o menos ida y vuelta, 25-26 una rueda."""
    if f in formatos_posibles(n):
        return f
    return "anual_ida_vuelta" if n <= IDA_VUELTA_MAX else "anual_ida"


def formato(S):
    """Formato con el que se está jugando esta temporada."""
    return S.get("formato", "actual")


def descensos(S):
    """Cuántos descienden directo a la B esta temporada."""
    return int(S.get("k_desc", DESCENSOS_DEF))


def destino(pos, k=DESCENSOS_DEF, n=N, corrido=False, proms=PROMOS_DEF):
    """Destino en Primera según la posición final (1-n) y la cantidad de descensos k.
    Con el formato actual: 1°-5° Libertadores, 6°-8° y 12°-13° Sudamericana, 11° fase previa. Con los otros
    formatos (corrido=True) van en orden: 1°-5° Libertadores, 6° fase previa y 7°-11° Sudamericana."""
    if 1 <= pos <= 5:
        return "Libertadores"
    if corrido:
        if pos == 6:
            return "Fase previa Libertadores"
        if 7 <= pos <= 11:
            return "Sudamericana"
    else:
        if 6 <= pos <= 8:
            return "Sudamericana"
        if pos == 11:
            return "Fase previa Libertadores"
        if pos in (12, 13):
            return "Sudamericana"
    if proms > 0 and n - k - proms < pos <= n - k:
        return "Promoción"
    if pos > n - k:
        return "Desciende"
    return ""


def total_base(S):
    """Fechas del formato sin contar desempates."""
    f = formato(S)
    if f == "anual_ida":
        return fechas_f1(S)
    if f == "anual_ida_vuelta":
        return 2 * fechas_f1(S)
    if f == "apertura_clausura":
        return ac.TOTAL
    return fechas_f1(S) + fechas_f2(S)


def total_primera(S):
    """Fechas de Primera contando las de desempate (si las hubo)."""
    return total_base(S) + S.get("extra_f2", 0)


def primera_terminada(S):
    """Primera terminó de verdad: todas sus fechas y también sus desempates."""
    return S["fecha"] >= total_primera(S)


def rotulo_p(S, n):
    f = formato(S)
    if f == "apertura_clausura":
        return ac.rotulo(n)
    if f == "actual":
        if n <= fechas_f1(S):
            return f"Fecha {n}"
        if n <= fechas_f1(S) + fechas_f2(S):
            return f"Fecha {n} · Fase 2"
        return f"Fecha {n} · Desempate"
    if n <= total_base(S):
        return f"Fecha {n}" + (" · Vuelta" if f == "anual_ida_vuelta" and n > fechas_f1(S) else "")
    return f"Fecha {n} · Desempate"


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
        gl, gv, gana_l, pen = jugar_ko(rng, np.array([r[a]]), np.array([r[b]]), sorpresa, localia=0.0,
                                       **mods_nombres(rng, [nom[a]], [nom[b]]))
        tanda = tanda_penales(rng, gana_l[0]) if pen[0] else None
        gana = a if gana_l[0] else b
        registrar(a, b, gl[0], gv[0], tanda, gana, comp_duelo + suf)
        return [gana, b if gana == a else a]
    puntos = {e: 0 for e in bloque}
    gf = {e: 0 for e in bloque}
    gc = {e: 0 for e in bloque}
    partidos = []
    for i in range(len(bloque)):
        for j in range(i + 1, len(bloque)):
            a, b = bloque[i], bloque[j]
            gl, gv, gana_l, pen = jugar_ko(rng, np.array([r[a]]), np.array([r[b]]), sorpresa, localia=0.0,
                                           **mods_nombres(rng, [nom[a]], [nom[b]]))
            tanda = tanda_penales(rng, gana_l[0]) if pen[0] else None
            gana = a if gana_l[0] else b
            puntos[gana] += 3
            gf[a] += int(gl[0]); gc[a] += int(gv[0])
            gf[b] += int(gv[0]); gc[b] += int(gl[0])
            partidos.append(registrar(a, b, gl[0], gv[0], tanda, gana, comp_liguilla + suf))
    # Orden de la liguilla: puntos, diferencia de gol, goles a favor y, si siguen igualados, sorteo.
    # (Sin esto los equipos igualados en puntos quedaban en un orden arbitrario, ignorando el gol.)
    sorteo = {e: float(rng.random()) for e in bloque}
    orden = sorted(bloque, key=lambda e: (-puntos[e], -(gf[e] - gc[e]), -gf[e], sorteo[e]))
    if campeonato:
        # El título nunca se decide por diferencia de gol: si el 1° puesto queda igualado en
        # puntos, esos equipos juegan otra definición.
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
    """Reinicia stats y fixture de la Primera para la temporada actual, según el formato elegido en el Modo dios."""
    cfg = cfg_primera(S)
    S["formato"], S["k_desc"] = cfg["formato"], int(cfg["descensos"])
    S["p_prom"] = int(cfg["promociones"])
    n_eq = len(S["nombres"])
    if S["formato"] == "apertura_clausura" and n_eq != N:      # Apertura y Clausura está armado para 30 equipos
        S["formato"] = "actual"
    if S["formato"] != "apertura_clausura":                    # los demás formatos dependen de la cantidad de equipos
        S["formato"] = formato_posible(S["formato"], n_eq)
    perm = S["rng"].permutation(n_eq)
    if S["formato"] == "apertura_clausura":
        ac.nueva(S, perm)
    else:
        fechas = generar_fixture(n_eq)
        S["fechas"] = [[(int(perm[a]), int(perm[b])) for a, b in p] for p in fechas]
        if S["formato"] == "anual_ida_vuelta":                       # la vuelta: mismas fechas con las localías al revés
            S["fechas"] += [[(v, l) for l, v in fecha] for fecha in S["fechas"]]
        S["ac"] = None
    S["fecha"] = 0
    S["fase"] = 1
    S["zonas"] = None
    S["zona_de"] = None
    S["snap"] = None
    S["tabla_f1"] = None
    S["acumular"] = True
    for k in STATS:
        S[k] = np.zeros(n_eq, dtype=int)
    S["historial"] = []
    S["log"] = []
    S["pos_hist"] = []
    S["sorpresas"] = 0
    S["cerrada"] = False

    # Nuevas variables para desempates dinámicos
    S["extra_f2"] = 0
    S["orden_final_campeonato"] = None
    S["orden_final_descenso"] = None
    S["orden_final_general"] = None          # formatos anuales: orden de la tabla tras los desempates
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
    """Tabla de los 30 equipos (fase 1 del formato actual, o la tabla anual de los otros formatos)."""
    df = df_base(S, np.arange(len(S["nombres"])))
    if S.get("orden_final_general") is not None:
        df = df.set_index("id").loc[S["orden_final_general"]].reset_index()
    df.insert(0, "Pos", df.index + 1)
    if formato(S) != "actual":                                       # tabla anual: con destino por posición
        k = descensos(S)
        df["Destino"] = [destino(p, k, len(df), corrido=True, proms=promos(S)) for p in df["Pos"]]
        for motivo in S.get("motivos_desempate", []):
            partes = motivo.split()
            if int(partes[1]) == 9:
                inicio, fin = map(int, partes[3].split("-"))
                df.loc[df["id"].isin(df["id"].to_numpy()[inicio:fin]), "Destino"] = f"Desempate {partes[2]}"
    return df


def tabla_zona(S, z):
    df = df_base(S, S["zonas"][z])

    # Inyectar el desempate en la zona correspondiente
    if z == 0 and S.get("orden_final_campeonato") is not None:
        df = df.set_index("id").loc[S["orden_final_campeonato"]].reset_index()
    elif z == 2 and S.get("orden_final_descenso") is not None:
        df = df.set_index("id").loc[S["orden_final_descenso"]].reset_index()

    tam = tam_zonas_p(len(S["nombres"]))
    df.insert(0, "Pos", sum(tam[:z]) + df.index + 1)
    k = descensos(S)
    df["Destino"] = [destino(p, k, len(S["nombres"]), proms=promos(S)) for p in df["Pos"]]

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
    """Posiciones finales 1-30 (de las zonas en el formato actual; de la tabla anual en los demás)."""
    if formato(S) == "actual":
        return pd.concat([tabla_zona(S, z) for z in range(3)])
    return tabla_general(S)


def iniciar_fase2(S, acumular):
    """Arma las zonas según la tabla de la fase 1 y agrega las 9 fechas."""
    S["tabla_f1"] = tabla_general(S)          # queda guardada para consultarla después
    orden = S["tabla_f1"]["id"].to_numpy()
    n_eq = len(S["nombres"])
    tam = tam_zonas_p(n_eq)
    corte = [0, tam[0], tam[0] + tam[1], n_eq]
    S["zonas"] = [orden[corte[z]:corte[z + 1]] for z in range(3)]
    S["zona_de"] = np.zeros(n_eq, dtype=int)
    for z, ids in enumerate(S["zonas"]):
        S["zona_de"][ids] = z
    S["snap"] = {k: S[k].copy() for k in STATS}
    S["acumular"] = acumular

    # H[x, y] = True si x fue local contra y en la fase 1
    f1 = fechas_f1(S)
    H = np.zeros((n_eq, n_eq), dtype=bool)
    for pares in S["fechas"][:f1]:
        for a, b in pares:
            H[a, b] = True

    previas = ultimas_localias(S["fechas"][:f1])
    por_zona = [fixture_revancha(S["rng"], S["zonas"][z], H, previas) for z in range(3)]
    for k in range(fechas_f2(S)):
        S["fechas"].append([p for z in range(3) if k < len(por_zona[z]) for p in por_zona[z][k]])
    S["fase"] = 2


def _detectar_empates(S, extra):
    """Mira si hay igualdad en puntos en las fronteras que importan (título, permanencia, promoción) y, si la
    hay, deja pendiente una fecha más con los desempates. Devuelve True si agregó esa fecha."""
    k = descensos(S)
    partidos_desempate, ids_involucrados, motivos = [], [], []
    bloques = set()

    def revisar(df, zona, fronteras):
        pts, ids = df["Pts"].to_numpy(), df["id"].to_numpy()
        for idx_f, nombre in fronteras:
            if idx_f < 0 or idx_f + 1 >= len(pts) or pts[idx_f] != pts[idx_f + 1]:
                continue
            inicio, fin = bloque_empatado(pts, idx_f)
            if (zona, inicio) in bloques:
                continue
            bloques.add((zona, inicio))
            ids_bloque = [int(i) for i in ids[inicio:fin]]
            ids_involucrados.extend(ids_bloque)
            tipo, partido = duelo_o_liguilla(ids_bloque)
            motivos.append(f"{tipo} {zona} {nombre} {inicio}-{fin}")
            partidos_desempate.append(partido)

    if formato(S) == "actual":
        # --- Zona Campeonato (1° puesto) y Zona Descenso (permanencia y promoción)
        revisar(tabla_zona(S, 0), 0, [(0, "Campeonato")])
        # el puesto N-k es el índice d-1-k de la zona Descenso (9-k con 30 equipos: puestos 21 a 30)
        d = tam_zonas_p(len(S["nombres"]))[2]
        revisar(tabla_zona(S, 2), 2, ([(d - 1 - k, "Permanencia")] if k > 0 else []) + ([(d - 1 - k - promos(S), "Promocion")] if promos(S) > 0 else []))
    else:
        # --- Tabla anual (código de zona 9): título, permanencia (N-k / N-k+1) y promoción (N-k-1 / N-k)
        n_eq = len(S["nombres"])
        revisar(tabla_general(S), 9, [(0, "Campeonato")] + ([(n_eq - k - 1, "Permanencia")] if k > 0 else [])
                + ([(n_eq - k - promos(S) - 1, "Promocion")] if promos(S) > 0 else []))
    if not partidos_desempate:
        return False
    S["desempate_pendiente"] = True
    S["ids_desempate"] = ids_involucrados
    S["motivos_desempate"] = motivos
    S["extra_f2"] = extra + 1
    S["fechas"].append(partidos_desempate)
    return True


def simular_fecha(S, P, acumular=True):
    if formato(S) == "apertura_clausura":
        return ac.simular(S, P, tabla_general)
    f = S["fecha"]
    extra = S.get("extra_f2", 0)
    TOTAL_DYN = total_base(S) + extra

    if f >= TOTAL_DYN:
        return

    r, nom = S["r"], S["nombres"]
    k = descensos(S)
    es_desempate = S.get("desempate_pendiente") and f == TOTAL_DYN - 1

    if not es_desempate:
        pares = S["fechas"][f]
        h = np.array([x[0] for x in pares])
        a = np.array([x[1] for x in pares])
        gh, ga = jugar(S["rng"], S["r"][h], S["r"][a], **P, **mods_ids(S["rng"], nom, h, a))
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
            if formato(S) != "actual":
                comp = "Liga"
            else:
                comp = "Fase 1" if S["fase"] == 1 else f"Zona {ZONAS[S['zona_de'][x]]}"
            S["log"].append(nuevo_partido("Primera División", n_f, rotulo_p(S, n_f), comp,
                                          nom[x], nom[y], g1, g2))
        revisar_liga(S, S["log"][-len(h):], S["rng"])       # suspensiones y sanciones (rarísimo)
    else:
        # ---------------- EJECUCIÓN DE LOS DESEMPATES (CAMPEÓN / PERMANENCIA / PROMOCIÓN) ----------------
        motivos = S.get("motivos_desempate", [])
        for motivo in motivos:
            partes = motivo.split()
            zona = int(partes[1])
            nombre_frontera = partes[2]
            inicio, fin = map(int, partes[3].split("-"))

            df_prev = tabla_general(S) if zona == 9 else tabla_zona(S, zona)
            ids_finales = df_prev["id"].to_numpy().copy()
            bloque = ids_finales[inicio:fin]

            def registrar(a, b, gl, gv, tanda, gana, comp):
                partido = nuevo_partido("Primera División", f + 1, "Desempate", comp, nom[a], nom[b],
                                        gl, gv, tanda=tanda, gana=nom[gana], neutral=True)
                S["log"].append(partido)
                return partido

            # cupos: cuántos del bloque logran el objetivo (título / permanencia / evitar promoción)
            if zona == 9:                                    # tabla anual: puestos 1-30 del bloque
                cupos = {"Campeonato": 1, "Permanencia": len(S["nombres"]) - k - inicio, "Promocion": len(S["nombres"]) - k - promos(S) - inicio}.get(nombre_frontera, 1)
            else:                                            # zona Descenso: puestos 21-30
                cupos = {"Campeonato": 1, "Permanencia": tam_zonas_p(len(S["nombres"]))[2] - k - inicio, "Promocion": tam_zonas_p(len(S["nombres"]))[2] - k - promos(S) - inicio}.get(nombre_frontera, 1)
            ids_finales[inicio:fin] = definir_bloque(
                S["rng"], r, bloque, P["sorpresa"], registrar, nombre_frontera,
                f"Liguilla {nombre_frontera}", nom, campeonato=nombre_frontera == "Campeonato", cupos=cupos)

            if zona == 0:
                S["orden_final_campeonato"] = ids_finales
            elif zona == 2:
                S["orden_final_descenso"] = ids_finales
            else:
                S["orden_final_general"] = ids_finales

        S["desempate_pendiente"] = False

    tabla = tabla_general(S) if S["fase"] == 1 else tabla_final(S)
    pos = np.zeros(len(S["nombres"]), dtype=int)
    pos[tabla["id"].to_numpy()] = tabla["Pos"].to_numpy()
    S["pos_hist"].append((S["fase"], pos))
    S["fecha"] += 1

    if formato(S) == "actual" and S["fase"] == 1 and S["fecha"] == fechas_f1(S):
        iniciar_fase2(S, acumular)

    # ---------------- DETECCIÓN DE EMPATES ----------------
    ya_se_jugo = (S.get("orden_final_campeonato") is not None or S.get("orden_final_descenso") is not None
                  or S.get("orden_final_general") is not None)
    llego_al_final = S["fecha"] == total_base(S) + extra and (formato(S) != "actual" or S["fase"] == 2)
    if llego_al_final and not ya_se_jugo:
        _detectar_empates(S, extra)

"""Primera B, Primera C y Promocional Amateur: todos contra todos con la misma mecánica (ida y vuelta con 24 equipos
o menos, una sola vuelta con 25 o más).

Excepción: el Promocional Amateur con 25 equipos o más se juega en DOS ZONAS (A y B), siempre ida y vuelta, y no tiene
desempates (dentro de cada zona manda la diferencia de gol). Los ascensos se definen así (k = ascensos elegidos en el
Modo dios):
  * k = 1: asciende el campeón, que sale de la final entre los ganadores de cada zona.
  * k = 2: ascienden los ganadores de cada zona.
  * k = 3: ascienden los ganadores de zona y el ganador del partido entre los 2° de cada zona.
  * y así hasta el límite (ASC_MAX): con k par suben los k/2 primeros de cada zona y con k impar, además, el ganador
    del partido entre los que siguen.
La final entre los ganadores de zona se juega siempre (define al campeón del Promocional).
"""

import math

import numpy as np
import pandas as pd

from motor.incidentes import revisar_liga
from motor.nucleo import (
    STATS,
    _fila_historial,
    df_stats,
    generar_fixture,
    jugar,
    jugar_ko,
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
CLAVES_ZONAS = ("pd",)                      # ligas que con 25 o más equipos se parten en dos zonas (siempre ida y vuelta)
ZONAS_NOMBRES = ("Zona A", "Zona B")


def hay_zonas(n, clave=None):
    """True si la liga `clave` de n equipos se juega en dos zonas (sólo el Promocional con 25 equipos o más)."""
    return clave in CLAVES_ZONAS and n > IDA_VUELTA_MAX_SIMPLE


def hay_vuelta(n, clave=None):
    """True si la liga de n equipos se juega ida y vuelta (24 o menos; el Promocional también con 25 o más, en dos
    zonas). Las demás, con 25 o más, juegan una sola vuelta."""
    return n <= IDA_VUELTA_MAX_SIMPLE or hay_zonas(n, clave)


def formato_simple(n, clave=None):
    if hay_zonas(n, clave):
        return "Ida y vuelta · 2 zonas"
    return "Ida y vuelta" if hay_vuelta(n) else "Una sola vuelta"


def descripcion_zonas(k):
    """Cómo se reparten k ascensos entre las dos zonas (texto para la interfaz y el Modo dios)."""
    p = k // 2
    if k <= 0:
        return "no hay ascensos: la final entre los ganadores de zona define al campeón"
    if k == 1:
        return "asciende el campeón, que sale de la final entre los ganadores de cada zona"
    directos = "los ganadores de cada zona" if p == 1 else f"los {p} primeros de cada zona"
    if k % 2:
        return f"ascienden {directos} y el ganador del partido entre los {p + 1}° de cada zona"
    return f"ascienden {directos}"


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


def plan_simple(n, directos=2, descensos=None, reducido=False, red_equipos=4, zonas=False):
    """Plan de la temporada de una liga de n equipos, ya acotado para que sea posible.

    Con `zonas` (Promocional de 25 o más) "directos" son TODOS los ascensos (el reducido, si estaba elegido, cuenta como
    un ascenso más: en zonas no hay reducido) y no hay descensos."""
    if zonas:
        k = max(0, min(int(directos) + int(bool(reducido)), ASC_MAX, 2 * (n // 2 - 1)))
        return {"directos": k, "desc": 0, "reducido": False, "equipos": 0, "rondas": 0, "juegan": 0, "etapas": [],
                "zonas": True, "por_zona": k // 2, "playoff": k % 2 == 1}
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
        L["plan"] = plan_simple(len(L["nombres"]), descensos=None if clave in CON_DESCENSOS else 0,
                                zonas=L.get("zonas") is not None)
    return L["plan"]


def destino_liga(pos, total, plan):
    if pos <= plan["directos"]: return "Ascenso directo"
    if plan["reducido"] and pos <= plan["directos"] + plan["equipos"]: return "Reducido"
    if plan["desc"] and pos > total - plan["desc"]: return "Desciende"
    return ""


def nueva_estructura_liga(S_LIGA, rng, S=None, clave=None):
    n = len(S_LIGA["nombres"])
    zonas = hay_zonas(n, clave)                                # Promocional con 25 o más: dos zonas
    if S is not None and clave in CLAVES_CFG:               # Modo dios: lo elegido para esta temporada
        c = cfg_simple(S, clave)
        S_LIGA["plan"] = plan_simple(n, c["directos"], c["descensos"] if clave in CON_DESCENSOS else 0,
                                     c["reducido"], c["red_equipos"], zonas=zonas)
    else:
        S_LIGA["plan"] = plan_simple(n, descensos=None if clave in CON_DESCENSOS else 0, zonas=zonas)
    S_LIGA["red"], S_LIGA["bracket"], S_LIGA["asc_reducido"], S_LIGA["ascendidos"] = None, [], None, []
    S_LIGA["zonas"], S_LIGA["zona_de"], S_LIGA["fechas_zona"] = None, None, None
    S_LIGA["orden_zonas"], S_LIGA["playoffs"], S_LIGA["playoffs_pendiente"] = None, [], False
    if zonas:
        fechas = _fixture_zonas(S_LIGA, rng, n)
    else:
        base = generar_fixture(n)
        fechas = [[(int(a), int(b)) for a, b in pares] for pares in base]
        if hay_vuelta(n):                                      # 24 equipos o menos: ida y vuelta
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


# ---- Promocional en dos zonas ---------------------------------------------------------------------------
def _fixture_zonas(L, rng, n):
    """Sortea las dos zonas (la A se queda con el equipo de más si n es impar) y arma el fixture ida y vuelta de cada
    una. Las dos zonas juegan en las mismas fechas; si una tiene un equipo de más, termina unas fechas después.
    Devuelve las fechas (los cruces son ids de la liga entera)."""
    orden = [int(i) for i in rng.permutation(n)]
    tam_a = (n + 1) // 2
    zonas = [sorted(orden[:tam_a]), sorted(orden[tam_a:])]
    por_zona = []
    for z in zonas:
        ida = [[(z[a], z[b]) for a, b in pares] for pares in generar_fixture(len(z))]
        por_zona.append(ida + [[(v, l) for l, v in fecha] for fecha in ida])
    fechas = [sum((f[i] for f in por_zona if i < len(f)), []) for i in range(max(len(f) for f in por_zona))]
    zona_de = np.zeros(n, dtype=int)
    zona_de[zonas[1]] = 1
    L["zonas"], L["zona_de"], L["fechas_zona"] = zonas, zona_de, len(fechas)
    return fechas


def destino_zona(pos, plan):
    """Destino de la posición `pos` (1 = ganador) dentro de su zona, según los ascensos del plan."""
    k = plan["directos"]
    p = k // 2
    if k == 0:
        return "Final por el título" if pos == 1 else ""
    if k == 1:
        return "Final por el ascenso" if pos == 1 else ""
    if pos <= p:
        return "Ascenso directo"
    if k % 2 and pos == p + 1:
        return "Playoff por el ascenso"
    return ""


def tablas_zonas(L, clave="pd"):
    """Las dos tablas (Zona A, Zona B) del Promocional en zonas, cada una con su 'Pos' y su destino. En cada zona
    desempata la diferencia de gol (no hay partidos de desempate)."""
    plan = plan_de(L, clave)
    dfs = []
    for z, ids in enumerate(L["zonas"]):
        df = df_stats(L["nombres"], L["r"], L, np.asarray(ids))
        df.insert(0, "Pos", df.index + 1)
        df["Destino"] = [destino_zona(p, plan) for p in df["Pos"]]
        df["Zona"] = ZONAS_NOMBRES[z]
        dfs.append(df)
    return dfs


def tabla_liga(L, clave):
    """Tabla de una liga simple (clave: "pb", "pc" o "pd") con su destino y los desempates marcados. En el Promocional
    en zonas devuelve las dos tablas juntas (columna 'Zona'; para mostrarlas por separado, `tablas_zonas`)."""
    if L.get("zonas") is not None:
        return pd.concat(tablas_zonas(L, clave), ignore_index=True)
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
    if S_LIGA.get("zonas") is not None:                      # Promocional en dos zonas: sin desempates
        _simular_fecha_zonas(S_LIGA, P, rng, nombre_liga, f)
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
    zona_de = S_LIGA.get("zona_de")
    for x, y, g1, g2 in zip(h, a, gh, ga):
        comp = "Liga" if zona_de is None else ZONAS_NOMBRES[zona_de[x]]
        S_LIGA["log"].append(nuevo_partido(nombre_liga, f + 1, f"Fecha {f + 1}", comp, nom[x], nom[y], g1, g2))
    revisar_liga(S_LIGA, S_LIGA["log"][-len(h):], rng)


def _simular_fecha_zonas(L, P, rng, nombre_liga, f):
    """Una fecha del Promocional en zonas. Al terminar las dos zonas se arma una fecha más con las finales por el
    ascenso (ver _armar_playoffs); al jugarla se cierra la liga."""
    if L["playoffs_pendiente"] and f == L["total"] - 1:
        _jugar_playoffs(L, P, rng, nombre_liga, f)
        L["fecha"] += 1
        _cerrar_zonas(L, nombre_liga)
        return
    _jugar_fecha_normal(L, P, rng, nombre_liga, f)
    pos = np.zeros(len(L["nombres"]), dtype=int)             # posición dentro de la zona (para las flechas de la tabla)
    for df in tablas_zonas(L, NOMBRE_CLAVE.get(nombre_liga)):
        pos[df["id"].to_numpy()] = np.arange(1, len(df) + 1)
    L["pos_hist"].append((1, pos))
    L["fecha"] += 1
    if L["fecha"] == L["fechas_zona"]:
        _armar_playoffs(L, nombre_liga)


def _armar_playoffs(L, nombre_liga):
    """Terminadas las zonas: la final entre los ganadores (siempre; si hay un solo ascenso, es la final por el ascenso)
    y, con una cantidad impar de ascensos mayor que 1, un partido entre los que siguen de cada zona por el último
    ascenso. Pasa a cada cruce el mejor de su zona por puntos y, si hay empate, por diferencia de gol (sin desempate).
    Se agregan como una fecha más."""
    k = plan_de(L, NOMBRE_CLAVE.get(nombre_liga))["directos"]
    orden = [[int(i) for i in df["id"]] for df in tablas_zonas(L, NOMBRE_CLAVE.get(nombre_liga))]
    cruces = [{"a": orden[0][0], "b": orden[1][0], "comp": "Final",
               "rotulo": "Final por el ascenso" if k == 1 else "Final por el campeonato"}]
    if k > 1 and k % 2:
        p = k // 2
        cruces.append({"a": orden[0][p], "b": orden[1][p], "comp": "Playoff",
                       "rotulo": f"Playoff por el ascenso ({p + 1}° de cada zona)"})
    L["orden_zonas"], L["playoffs"], L["playoffs_pendiente"] = orden, cruces, True
    L["fechas"].append([(c["a"], c["b"]) for c in cruces])
    L["total"] += 1


def _jugar_playoffs(L, P, rng, nombre_liga, f):
    """Juega la fecha de las finales: partido único en cancha neutral, con penales si empatan."""
    nom, r = L["nombres"], L["r"]
    for c in L["playoffs"]:
        a, b = c["a"], c["b"]
        gl, gv, gana_local, pen = jugar_ko(rng, r[[a]], r[[b]], P["sorpresa"], localia=0.0,
                                           **mods_ids(rng, nom, [a], [b]))
        c["gana"] = a if bool(gana_local[0]) else b
        tanda = tanda_penales(rng, bool(gana_local[0])) if bool(pen[0]) else None
        L["log"].append(nuevo_partido(nombre_liga, f + 1, c["rotulo"], c["comp"], nom[a], nom[b], gl[0], gv[0],
                                      tanda=tanda, gana=nom[c["gana"]], neutral=True))
    L["playoffs_pendiente"] = False


def _cerrar_zonas(L, nombre_liga):
    """Campeón y ascendidos del Promocional en zonas. Con k ascensos suben los k // 2 primeros de cada zona (el campeón
    y el otro finalista primero) y, si k es impar y mayor que 1, el ganador del partido entre los que siguen. Con un solo
    ascenso sube el campeón de la final."""
    k = plan_de(L, NOMBRE_CLAVE.get(nombre_liga))["directos"]
    p = k // 2
    final = L["playoffs"][0]
    campeon = final["gana"]
    L["campeon"] = campeon
    otro = final["b"] if campeon == final["a"] else final["a"]
    if k >= 2:
        L["asc_directo"] = [campeon, otro] + [i for j in range(1, p) for i in (L["orden_zonas"][0][j], L["orden_zonas"][1][j])]
    else:
        L["asc_directo"] = []
    L["ascendidos"] = [campeon] if k == 1 else list(L["asc_directo"])
    if k > 1 and k % 2:
        L["ascendidos"].append(L["playoffs"][1]["gana"])
    L["orden_final"] = None


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

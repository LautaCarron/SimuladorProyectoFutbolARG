"""Regional Amateur: subgrupos, zona regional, desempates y finales.

Formato (dos fases y la final por el ascenso):

  Fase 1 · Subgrupos. Cada región se divide en subgrupos de unos 5 clubes armados por cercanía: se juntan los clubes
  de la misma liga y, si una liga no alcanza, los de la misma provincia. Todos contra todos, ida y vuelta.

  Fase 2 · Zona regional. Los 2 mejores de cada subgrupo pasan a la zona de su región (las tablas arrancan de cero).
  Todos contra todos, ida y vuelta. Si el 1° puesto queda igualado en puntos hay desempate (nunca se define por
  diferencia de gol). El campeón de la zona es el campeón regional. Una región chica, que no llega a dividirse en
  subgrupos, juega directo la zona regional con todos sus clubes.

  Final por el ascenso. Los campeones de las dos regiones de cada par juegan ida y vuelta (FINALES_REG).

Los subgrupos se arman de nuevo en cada temporada (sorteando el orden de provincias y ligas), así que un club no
comparte siempre el mismo grupo.
"""

import numpy as np
import pandas as pd

from datos.clubes_interior import datos_club
from datos.datos_regional import FINALES_REG, REGIONES_REG
from datos.equipos import region_regional
from motor.incidentes import revisar_liga
from motor.nucleo import (
    STATS,
    df_stats,
    generar_fixture,
    jugar,
    mods_ids,
    nuevo_partido,
    sumar_partidos,
    tanda_penales,
)
from ligas.primera import definir_bloque


REG_LIGA = "Regional Amateur"

REG_FINAL = "Final por el ascenso"
REG_GRUPO = 5            # tamaño que se busca para cada subgrupo de la fase 1
REG_GRUPO_MIN = 3        # un subgrupo nunca queda con menos clubes que esto
REG_MAX_GRUPOS = 8       # tope de subgrupos por región: la zona regional tiene a lo sumo 16 clubes
REG_PASAN = 2            # clasificados de cada subgrupo a la zona regional
REG_FASE1 = "Fase 1"
REG_ZONA = "Zona regional"


def region_reg(nombre):
    return region_regional(nombre)


# ---------------------------------------------------------------- armado de los subgrupos
def _cantidad_subgrupos(n):
    """Subgrupos de una región con `n` clubes (1 = no se divide: juega directo la zona regional)."""
    return min(REG_MAX_GRUPOS, max(1, round(n / REG_GRUPO)))


def _datos_clubes(nombres, ids):
    """{id: (provincia, liga, ciudad)}. Un club sin datos queda solo en su propia liga."""
    out = {}
    for i in ids:
        d = datos_club(nombres[int(i)]) or {}
        out[int(i)] = (d.get("provincia", ""), d.get("liga") or f"({nombres[int(i)]})", d.get("ciudad", ""))
    return out


def _armar_subgrupos(ids, datos, k, rng):
    """Parte los clubes en `k` subgrupos parejos manteniendo juntos a los de la misma liga y provincia.

    Se ordenan por provincia, liga y ciudad (el orden de provincias y ligas se sortea) y se corta la fila en `k`
    tramos de tamaño parecido. Cada corte se mueve hasta 2 puestos para caer, de mejor a peor, entre dos ligas, entre
    dos ciudades o, si no queda otra, en el medio de una ciudad (cada paso de distancia pesa como un nivel de esos)."""
    provincias = sorted({datos[int(i)][0] for i in ids})
    ligas = sorted({datos[int(i)][1] for i in ids})
    o_prov = dict(zip(provincias, rng.permutation(len(provincias))))
    o_liga = dict(zip(ligas, rng.permutation(len(ligas))))
    orden = sorted((int(i) for i in ids),
                   key=lambda i: (o_prov[datos[i][0]], o_liga[datos[i][1]], datos[i][2], i))
    n = len(orden)
    techo = -(-n // k) + 1                                  # ningún subgrupo pasa de esto
    cortes = [0]
    for j in range(1, k):
        ideal = round(j * n / k)
        minimo = cortes[-1] + REG_GRUPO_MIN                 # el subgrupo que se cierra no queda de menos
        maximo = min(n - (k - j) * REG_GRUPO_MIN, cortes[-1] + techo)    # y a los que faltan les alcanza
        candidatos = range(max(minimo, ideal - 2), min(maximo, ideal + 2) + 1)

        def costo(c):
            a, b = datos[orden[c - 1]], datos[orden[c]]
            borde = 0 if a[1] != b[1] else 1 if a[2] != b[2] else 2
            return (abs(c - ideal) + borde, borde)

        cortes.append(min(candidatos, key=costo) if len(candidatos) else min(max(ideal, minimo), maximo))
    cortes.append(n)
    return [orden[a:b] for a, b in zip(cortes, cortes[1:])]


def _ligas_texto(datos, ids):
    """Ligas de un subgrupo, de más a menos clubes: \"Liga Salteña, Liga de Metán +1\"."""
    cuenta = {}
    for i in ids:
        lg = datos[int(i)][1]
        cuenta[lg] = cuenta.get(lg, 0) + 1
    ordenadas = sorted(cuenta, key=lambda lg: (-cuenta[lg], lg))
    return ", ".join(ordenadas[:3]) + (f" +{len(ordenadas) - 3}" if len(ordenadas) > 3 else "")


def _doble_rueda(ids):
    """Todos contra todos, ida y vuelta (la vuelta repite la ida con la localía invertida). Lista de fechas."""
    ids = [int(i) for i in ids]
    ida = [[(ids[x], ids[y]) for x, y in fecha] for fecha in generar_fixture(len(ids))]
    return ida + [[(b, a) for a, b in fecha] for fecha in ida]


def _rondas_doble(q):
    """Fechas de un todos contra todos ida y vuelta con `q` clubes (con q impar, cada club descansa una fecha)."""
    return 0 if q < 2 else 2 * (q - 1 if q % 2 == 0 else q)


def nueva_estructura_reg(SR, rng):
    """Arma la temporada del Regional con los clubes que hoy lo juegan: los subgrupos de cada región (fase 1) y los
    datos de la zona regional (fase 2), que se completa al terminar la fase 1."""
    nombres = SR["nombres"]
    n = len(nombres)
    SR["region_de"] = [region_reg(nm) for nm in nombres]
    SR["grupos"] = {reg: np.array([i for i, rg in enumerate(SR["region_de"]) if rg == reg], dtype=int)
                    for reg in REGIONES_REG}
    SR["subgrupos"] = {}                                # clave -> ids de cada subgrupo
    SR["subgrupos_de"] = {}                             # región -> [claves] (vacío si no se divide)
    SR["desc_subgrupo"] = {}                            # clave -> ligas que juegan en el subgrupo
    SR["subgrupo_de"] = [None] * n                      # subgrupo de cada club
    SR["zona_de"] = [None] * n                          # donde juega cada club ahora: su subgrupo o su región
    SR["zona2"] = {}                                    # región -> ids de la zona regional (fase 2)
    fechas1, rondas2 = [], 0
    for reg in REGIONES_REG:
        ids = SR["grupos"][reg]
        k = _cantidad_subgrupos(len(ids)) if len(ids) else 0
        claves = []
        if k > 1:
            datos = _datos_clubes(nombres, ids)
            for j, g in enumerate(_armar_subgrupos(ids, datos, k, rng), start=1):
                clave = f"{reg} · Grupo {j}"
                claves.append(clave)
                SR["subgrupos"][clave] = np.array(sorted(g), dtype=int)
                SR["desc_subgrupo"][clave] = _ligas_texto(datos, g)
                for i in g:
                    SR["subgrupo_de"][i] = SR["zona_de"][i] = clave
                for t, pares in enumerate(_doble_rueda(g)):
                    while len(fechas1) <= t:
                        fechas1.append([])
                    fechas1[t] += pares
            SR["zona2"][reg] = np.array([], dtype=int)  # se arma con los clasificados
            rondas2 = max(rondas2, _rondas_doble(REG_PASAN * k))
        else:                                           # región chica: juega directo la zona con todos sus clubes
            SR["zona2"][reg] = ids
            for i in ids:
                SR["zona_de"][int(i)] = reg
            rondas2 = max(rondas2, _rondas_doble(len(ids)))
        SR["subgrupos_de"][reg] = claves
    SR["f_fase1"] = len(fechas1)
    SR["f_fase2"] = rondas2
    SR["f_liga"] = SR["f_fase1"] + rondas2             # fechas de las dos fases (sin desempate ni finales)
    SR["fechas"] = fechas1 + [[] for _ in range(rondas2)]
    SR["f_des"] = 0                                    # 1 si hay una fecha de desempates por el título de la zona
    SR["f_final0"] = SR["f_liga"]                      # última fecha antes de las finales (corre si hay desempate)
    SR["total"] = SR["f_liga"] + 2
    SR["fecha"] = 0
    for k in STATS:
        SR[k] = np.zeros(n, dtype=int)
    SR["historial"] = []
    SR["log"] = []
    SR["pos_hist"] = []
    SR["stats_f1"] = None                              # fotos de las tablas de la fase 1 cuando termina
    SR["f1_cerrada"] = False
    SR["desempate_pendiente"] = False
    SR["motivos_desempate"] = {}                       # región -> cantidad de igualados arriba
    SR["orden_final"] = {}                             # región -> ids ordenados tras el desempate
    SR["campeones"] = {reg: None for reg in REGIONES_REG}
    SR["finales"] = []
    SR["ascendidos"] = []
    if SR["f_fase1"] == 0:                             # ninguna región se divide: se pasa directo a la zona
        _cerrar_fase1(SR, rng)


def subgrupo_de_club(SR, club):
    """Subgrupo del club en la fase 1 (None si su región no se divide o el club no juega el Regional)."""
    if club not in SR["nombres"]:
        return None
    return SR["subgrupo_de"][SR["nombres"].index(club)]


# ---------------------------------------------------------------- tablas
def _v1(SR):
    """Estadísticas de la fase 1: la foto si la fase terminó, o las que se están jugando."""
    return SR.get("stats_f1") or SR


def tabla_subgrupo_reg(SR, clave):
    """Tabla de un subgrupo de la fase 1. `Pos` es el puesto en el subgrupo; los que pasan a la zona regional
    llevan `Destino` = \"Clasifica\" (una vez que empezó a jugarse)."""
    df = df_stats(SR["nombres"], SR["r"], _v1(SR), SR["subgrupos"][clave])
    df.insert(0, "Pos", df.index + 1)
    jugado = int(df["PJ"].sum()) > 0
    df["Destino"] = ["Clasifica" if jugado and p <= REG_PASAN else "" for p in df["Pos"]]
    return df


def tabla_zona_reg(SR, reg):
    """Tabla de la zona regional (fase 2), con el desempate por el título aplicado si lo hubo. `Pos` es el puesto
    en la zona. Vacía mientras la zona todavía no se armó."""
    df = df_stats(SR["nombres"], SR["r"], SR, SR["zona2"][reg])
    if reg in SR["orden_final"]:
        df = df.set_index("id").loc[SR["orden_final"][reg]].reset_index()
    df.insert(0, "Pos", df.index + 1)
    campeon = SR["campeones"].get(reg)
    igualados = SR["motivos_desempate"].get(reg) if SR["desempate_pendiente"] else None
    df["Destino"] = ["Desempate Campeonato" if igualados and p <= igualados else
                     "Campeón regional" if i == campeon else "" for p, i in zip(df["Pos"], df["id"])]
    return df


def _posiciones_subgrupo(SR):
    """{id: puesto en su subgrupo de la fase 1}."""
    pos = {}
    for clave in SR["subgrupos"]:
        df = tabla_subgrupo_reg(SR, clave)
        pos.update({int(i): int(p) for i, p in zip(df["id"], df["Pos"])})
    return pos


def tabla_reg_region(SR, reg):
    """Ranking de todos los clubes de la región (`Puesto`, 1 = campeón regional).

    Primero los de la zona regional, en el orden de su tabla (con el desempate aplicado); después los eliminados en la
    fase 1: por su puesto en el subgrupo (los 3° antes que los 4°, etc.) y a igual puesto por puntos, diferencia de gol
    y goles a favor por partido. Las columnas PJ, Pts, DG y GF de cada club son las de la fase en la que quedó."""
    partes = []
    if len(SR["zona2"][reg]):
        zona = tabla_zona_reg(SR, reg)
        zona["Fase"] = REG_ZONA
        partes.append(zona)
    en_zona = {int(i) for i in SR["zona2"][reg]}
    fuera = [int(i) for i in SR["grupos"][reg] if int(i) not in en_zona]
    if fuera:
        pos = _posiciones_subgrupo(SR)
        df = df_stats(SR["nombres"], SR["r"], _v1(SR), fuera)
        pj = df["PJ"].clip(lower=1)
        df["_o"] = list(zip([pos.get(int(i), 99) for i in df["id"]], -df["Pts"] / pj, -df["DG"] / pj, -df["GF"] / pj))
        df = df.sort_values("_o").drop(columns="_o").reset_index(drop=True)
        df["Destino"] = "Eliminado en la fase 1" if SR["f1_cerrada"] else ""
        df["Fase"] = REG_FASE1
        partes.append(df)
    df = pd.concat(partes, ignore_index=True)
    df["Puesto"] = np.arange(1, len(df) + 1)
    df["Pos"] = df["Puesto"]
    return df


def _coef_reg(SR, i):
    pj = max(int(SR["pj"][i]), 1)
    pts = 3 * int(SR["g"][i]) + int(SR["e"][i])
    return pts / pj, (int(SR["gf"][i]) - int(SR["gc"][i])) / pj, int(SR["gf"][i]) / pj


# ---------------------------------------------------------------- cierres de cada etapa
def _cerrar_fase1(SR, rng):
    """Termina la fase 1: guarda las tablas de los subgrupos, arma la zona de cada región con los 2 mejores de cada
    subgrupo y deja las tablas en cero para la fase 2."""
    n = len(SR["nombres"])
    SR["stats_f1"] = {k: SR[k].copy() for k in STATS}
    SR["stats_f1"]["quita"] = dict(SR.get("quita") or {})      # las quitas de puntos se quedan en la fase 1
    SR["f1_cerrada"] = True
    for reg in REGIONES_REG:
        claves = SR["subgrupos_de"][reg]
        if claves:
            pasan = [int(i) for clave in claves for i in tabla_subgrupo_reg(SR, clave)["id"].iloc[:REG_PASAN]]
            SR["zona2"][reg] = np.array(rng.permutation(pasan), dtype=int)
    for k in STATS:
        SR[k] = np.zeros(n, dtype=int)
    SR["quita"] = {}
    for reg in REGIONES_REG:
        ids = SR["zona2"][reg]
        for i in ids:
            SR["zona_de"][int(i)] = reg
        if len(ids) > 1:
            for t, pares in enumerate(_doble_rueda(ids)):
                SR["fechas"][SR["f_fase1"] + t] += pares


def _proclamar_campeon(SR, reg, campeon):
    SR["campeones"][reg] = int(campeon)


def _cierre_ligas_reg(SR):
    """Al terminar la zona regional: campeón de cada región, o desempate si el 1° puesto está igualado."""
    for reg in REGIONES_REG:
        ids = SR["zona2"][reg]
        if len(ids) == 0:
            continue
        df = tabla_zona_reg(SR, reg)
        pts = df["Pts"].to_numpy()
        if len(pts) > 1 and pts[0] == pts[1]:
            fin = 1
            while fin < len(pts) and pts[fin] == pts[0]:
                fin += 1
            SR["motivos_desempate"][reg] = fin
        else:
            _proclamar_campeon(SR, reg, df["id"].iloc[0])
    if SR["motivos_desempate"]:
        SR["desempate_pendiente"] = True
        SR["f_des"] = 1
        SR["f_final0"] += 1
        SR["total"] += 1


def _jugar_desempates_reg(SR, P, rng, n_fecha):
    nom, r = SR["nombres"], SR["r"]
    for reg, fin in SR["motivos_desempate"].items():
        ids = tabla_zona_reg(SR, reg)["id"].to_numpy()

        def registrar(a, b, gl, gv, tanda, gana, comp, reg=reg):
            partido = nuevo_partido(REG_LIGA, n_fecha, "Desempate", comp, nom[a], nom[b],
                                    gl, gv, tanda=tanda, gana=nom[gana], neutral=True)
            partido["region"] = reg
            SR["log"].append(partido)
            return partido

        orden = definir_bloque(rng, r, ids[:fin], P["sorpresa"], registrar, f"Región {reg} · Campeonato",
                               f"Liguilla Región {reg} · Campeonato", nom, campeonato=True, cupos=1)
        SR["orden_final"][reg] = np.array(orden + [int(i) for i in ids[fin:]])
        _proclamar_campeon(SR, reg, orden[0])
    SR["desempate_pendiente"] = False


# ---------------------------------------------------------------- finales por el ascenso
def _armar_finales_reg(SR):
    SR["finales"] = []
    for ra, rb in FINALES_REG:
        ca, cb = SR["campeones"][ra], SR["campeones"][rb]
        if ca is None and cb is None:                   # las dos regiones sin clubes: final desierta
            SR["finales"].append({"a": None, "b": None, "reg": f"{ra} / {rb}", "ronda": REG_FINAL,
                                  "ida": None, "vuelta": None, "gana": None, "ga": 0, "gb": 0, "pen": None})
            continue
        if ca is None or cb is None:                    # región sin campeón: el otro asciende
            SR["finales"].append({"a": ca if ca is not None else cb, "b": None, "reg": f"{ra} / {rb}",
                                  "ronda": REG_FINAL, "ida": None, "vuelta": None,
                                  "gana": ca if ca is not None else cb, "ga": 0, "gb": 0, "pen": None})
            continue
        # cierra de local el de mejor campaña en su zona regional
        a, b = sorted([ca, cb], key=lambda i: tuple(-x for x in _coef_reg(SR, i)))
        SR["finales"].append({"a": int(a), "b": int(b), "reg": f"{ra} / {rb}", "ronda": REG_FINAL,
                              "ida": None, "vuelta": None, "gana": None, "ga": 0, "gb": 0, "pen": None})


def _jugar_pierna_reg(SR, P, rng, series, vuelta, n_fecha):
    series = [x for x in series if x["a"] is not None and x["b"] is not None]
    if not series:
        return
    nom, r = SR["nombres"], SR["r"]
    a = np.array([x["a"] for x in series])
    b = np.array([x["b"] for x in series])
    loc, vis = (a, b) if vuelta else (b, a)             # el mejor ubicado cierra de local
    gl, gv = jugar(rng, r[loc], r[vis], **P, **mods_ids(rng, nom, loc, vis))
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


# ---------------------------------------------------------------- calendario y simulación
def rotulo_reg(SR, n):
    """Nombre de la fecha n (1, 2, ...) del Regional."""
    if n <= SR["f_fase1"]:
        return f"{REG_FASE1} · Fecha {n}"
    if n <= SR["f_liga"]:
        return f"{REG_ZONA} · Fecha {n - SR['f_fase1']}"
    if n <= SR["f_liga"] + SR["f_des"]:
        return "Desempate por el campeonato"
    return f"{REG_FINAL} · {'vuelta' if n - SR['f_final0'] == 2 else 'ida'}"


def fase_reg(SR):
    """Etapa en la que está el Regional: para mostrar en la interfaz."""
    f = SR["fecha"]
    if f >= SR["total"]:
        return "Terminado"
    if f < SR["f_fase1"]:
        return "Fase 1 · Subgrupos"
    if f < SR["f_liga"]:
        return "Fase 2 · Zona regional"
    if f < SR["f_final0"]:
        return "Desempate por el campeonato"
    return "Final por el ascenso"


def simular_fecha_reg(SR, P, rng):
    f = SR["fecha"]
    if f >= SR["total"]:
        return
    if f < SR["f_liga"]:                                # ---- fase 1 (subgrupos) y fase 2 (zona regional)
        pares = SR["fechas"][f]
        if pares:
            h = np.array([x[0] for x in pares])
            a = np.array([x[1] for x in pares])
            gh, ga = jugar(rng, SR["r"][h], SR["r"][a], **P, **mods_ids(rng, SR["nombres"], h, a))
            sumar_partidos(SR, h, a, gh, ga)
            nom = SR["nombres"]
            rotulo = rotulo_reg(SR, f + 1)
            for x, y, g1, g2 in zip(h, a, gh, ga):
                partido = nuevo_partido(REG_LIGA, f + 1, rotulo, f"Región {SR['zona_de'][x]}",
                                        nom[x], nom[y], g1, g2)
                partido["region"] = SR["region_de"][x]
                SR["log"].append(partido)
            revisar_liga(SR, SR["log"][-len(h):], rng)
        SR["fecha"] += 1
        if SR["fecha"] == SR["f_fase1"] and not SR["f1_cerrada"]:
            _cerrar_fase1(SR, rng)
        if SR["fecha"] == SR["f_liga"]:
            _cierre_ligas_reg(SR)
        return
    if f < SR["f_liga"] + SR["f_des"]:                  # ---- desempates por el título de la región
        _jugar_desempates_reg(SR, P, rng, f + 1)
    else:                                               # ---- finales por el ascenso
        vuelta = f - SR["f_final0"] == 1
        if not vuelta:
            _armar_finales_reg(SR)
        _jugar_pierna_reg(SR, P, rng, SR["finales"], vuelta, f + 1)
        if vuelta:
            SR["ascendidos"] = [x["gana"] for x in SR["finales"] if x["gana"] is not None]
    SR["fecha"] += 1

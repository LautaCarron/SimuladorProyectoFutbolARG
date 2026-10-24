"""Regional Amateur: ligas por región, desempates y finales.

Cada región es una liga de todos contra todos a una sola vuelta. Si una región tiene más de `REG_MAX_LIGA` clubes se
sortea en dos zonas (A y B): cada una juega su propia liga, y al terminar (y resolver los desempates de cada zona) los
dos campeones de zona juegan un partido único por el título de la región, antes de la final por el ascenso contra la
otra región. Las zonas se llaman "<región> · Zona A" y "<región> · Zona B"; una región que no se divide tiene una sola
zona, que se llama igual que la región.
"""

import numpy as np
import pandas as pd

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
from datos.datos_regional import FINALES_REG, REGIONES_REG
from ligas.primera import definir_bloque


REG_LIGA = "Regional Amateur"


REG_FINAL = "Final por el ascenso"
REG_CRUCE = "Final de región"          # entre los campeones de las dos zonas de una región
REG_MAX_LIGA = 24                      # una región con más clubes que esto se divide en dos zonas


def region_reg(nombre):
    return region_regional(nombre)


def _armar_zonas(SR, rng):
    """Zonas de la temporada: {clave: ids} y {región: [claves]}. Una región con más de REG_MAX_LIGA clubes se sortea en
    dos zonas del mismo tamaño (o con uno más la A); el resto es una sola zona que se llama como la región."""
    zonas, zonas_de = {}, {}
    for reg in REGIONES_REG:
        ids = SR["grupos"][reg]
        if len(ids) > REG_MAX_LIGA:
            mezcla = rng.permutation(ids)
            mitad = (len(ids) + 1) // 2
            claves = [f"{reg} · Zona A", f"{reg} · Zona B"]
            zonas[claves[0]], zonas[claves[1]] = np.sort(mezcla[:mitad]), np.sort(mezcla[mitad:])
        else:
            claves = [reg]
            zonas[reg] = ids
        zonas_de[reg] = claves
    return zonas, zonas_de


def region_de_zona(clave):
    """Región a la que pertenece una zona ("Centro · Zona A" -> "Centro")."""
    return clave.split(" · Zona ")[0]


def nueva_estructura_reg(SR, rng):
    """Arma las ligas regionales (una rueda) con los clubes que hoy juegan el Regional: una por región, o dos zonas
    sorteadas en las regiones con más de REG_MAX_LIGA clubes."""
    nombres = SR["nombres"]
    n = len(nombres)
    SR["region_de"] = [region_reg(nm) for nm in nombres]
    SR["grupos"] = {reg: np.array([i for i, rg in enumerate(SR["region_de"]) if rg == reg], dtype=int)
                    for reg in REGIONES_REG}
    SR["zonas"], SR["zonas_de"] = _armar_zonas(SR, rng)
    SR["zona_de"] = [None] * n                         # clave de la zona donde juega cada club
    for clave, ids in SR["zonas"].items():
        for i in ids:
            SR["zona_de"][int(i)] = clave
    idas = {clave: generar_fixture(len(ids)) if len(ids) > 1 else [] for clave, ids in SR["zonas"].items()}
    rondas = max((len(f) for f in idas.values()), default=0)
    fechas = [[] for _ in range(rondas)]
    for clave, f in idas.items():
        ids = SR["zonas"][clave]
        for k, pares in enumerate(f):
            fechas[k] += [(int(ids[x]), int(ids[y])) for x, y in pares]
    SR["fechas"] = fechas
    SR["f_liga"] = rondas
    SR["f_des"] = 0                                    # 1 si hay una fecha de desempates por el título de zona
    SR["f_cruce"] = 1 if any(len(c) == 2 for c in SR["zonas_de"].values()) else 0   # fecha entre campeones de zona
    SR["f_final0"] = rondas + SR["f_cruce"]            # última fecha antes de las finales (corre si hay desempate)
    SR["total"] = rondas + SR["f_cruce"] + 2
    SR["fecha"] = 0
    for k in STATS:
        SR[k] = np.zeros(n, dtype=int)
    SR["historial"] = []
    SR["log"] = []
    SR["pos_hist"] = []
    SR["desempate_pendiente"] = False
    SR["motivos_desempate"] = {}                       # zona -> cantidad de igualados arriba
    SR["orden_final"] = {}                             # zona -> ids ordenados tras el desempate
    SR["campeones_zona"] = {}                          # zona -> campeón de la zona
    SR["cruces"] = {}                                  # región dividida -> (campeón, finalista) del cruce de zonas
    SR["campeones"] = {reg: None for reg in REGIONES_REG}
    SR["finales"] = []
    SR["ascendidos"] = []


def _coef_reg(SR, i):
    pj = max(int(SR["pj"][i]), 1)
    pts = 3 * int(SR["g"][i]) + int(SR["e"][i])
    return pts / pj, (int(SR["gf"][i]) - int(SR["gc"][i])) / pj, int(SR["gf"][i]) / pj


def tabla_zona_reg(SR, clave):
    """Tabla de una zona (con el desempate por el título aplicado, si lo hubo). `Pos` es el puesto en la zona."""
    df = df_stats(SR["nombres"], SR["r"], SR, SR["zonas"][clave])
    if clave in SR["orden_final"]:
        df = df.set_index("id").loc[SR["orden_final"][clave]].reset_index()
    df.insert(0, "Pos", df.index + 1)
    return df


def tabla_reg_region(SR, reg):
    """Tabla de la liga de una región (con el desempate por el título aplicado, si lo hubo).

    Región de una sola zona: la tabla de la liga. Región dividida: las tablas de las dos zonas una debajo de la otra
    (`Pos` es el puesto en la zona y `Destino` dice a qué zona pertenece cada club). En los dos casos `Puesto` es el
    puesto en la región: en una región dividida, primero el campeón regional, después el otro campeón de zona y luego
    los demás por su puesto en la zona y su rendimiento."""
    claves = SR["zonas_de"][reg]
    partes = []
    for clave in claves:
        df = tabla_zona_reg(SR, clave)
        igualados = SR["motivos_desempate"].get(clave)
        pendiente = SR["desempate_pendiente"] and igualados
        if len(claves) == 1:
            destinos = ["Campeón regional" if p == 1 else "" for p in df["Pos"]]
        else:
            zona = clave.split(" · ")[-1]
            camp, fin = SR["campeones"].get(reg), (SR["cruces"].get(reg) or (None, None))[1]
            destinos = []
            for p, i in zip(df["Pos"], df["id"]):
                destinos.append("Campeón regional" if i == camp else "Finalista de región" if i == fin else
                                "Campeón de zona" if p == 1 else zona)
        if pendiente:
            destinos = ["Desempate Campeonato" if k < igualados else d for k, d in enumerate(destinos)]
        df["Destino"] = destinos
        df["Zona"] = clave.split(" · ")[-1] if len(claves) > 1 else ""
        partes.append(df)
    df = partes[0] if len(partes) == 1 else pd.concat(partes, ignore_index=True)
    df["Puesto"] = _puestos_region(SR, reg, df)
    return df


def _puestos_region(SR, reg, df):
    """Puesto de cada club en la región (ver tabla_reg_region)."""
    if len(SR["zonas_de"][reg]) == 1:
        return df["Pos"].to_numpy()
    camp, fin = SR["campeones"].get(reg), (SR["cruces"].get(reg) or (None, None))[1]

    def orden(f):
        i = int(f["id"])
        if i == camp:
            return (0,)
        if i == fin:
            return (1,)
        pj = max(int(f["PJ"]), 1)
        return (2, int(f["Pos"]), -float(f["Pts"]) / pj, -float(f["DG"]) / pj, -float(f["GF"]) / pj)

    ranking = sorted(range(len(df)), key=lambda k: orden(df.iloc[k]))
    puesto = np.zeros(len(df), dtype=int)
    for p, k in enumerate(ranking, start=1):
        puesto[k] = p
    return puesto


def _proclamar_zona(SR, clave, campeon):
    """Campeón de una zona; si es la única de su región, es el campeón regional."""
    SR["campeones_zona"][clave] = int(campeon)
    reg = region_de_zona(clave)
    if len(SR["zonas_de"][reg]) == 1:
        SR["campeones"][reg] = int(campeon)


def _cierre_ligas_reg(SR):
    """Al terminar la rueda: campeón de cada zona, o desempate si el 1° puesto está igualado."""
    for reg in REGIONES_REG:
        for clave in SR["zonas_de"][reg]:
            if len(SR["zonas"][clave]) == 0:
                continue
            df = tabla_zona_reg(SR, clave)
            pts = df["Pts"].to_numpy()
            if len(pts) > 1 and pts[0] == pts[1]:
                fin = 1
                while fin < len(pts) and pts[fin] == pts[0]:
                    fin += 1
                SR["motivos_desempate"][clave] = fin
            else:
                _proclamar_zona(SR, clave, df["id"].iloc[0])
    if SR["motivos_desempate"]:
        SR["desempate_pendiente"] = True
        SR["f_des"] = 1
        SR["f_final0"] += 1
        SR["total"] += 1


def _jugar_desempates_reg(SR, P, rng, n_fecha):
    nom, r = SR["nombres"], SR["r"]
    for clave, fin in SR["motivos_desempate"].items():
        reg = region_de_zona(clave)
        ids = tabla_zona_reg(SR, clave)["id"].to_numpy()

        def registrar(a, b, gl, gv, tanda, gana, comp, reg=reg):
            partido = nuevo_partido(REG_LIGA, n_fecha, "Desempate", comp, nom[a], nom[b],
                                    gl, gv, tanda=tanda, gana=nom[gana], neutral=True)
            partido["region"] = reg
            SR["log"].append(partido)
            return partido

        orden = definir_bloque(rng, r, ids[:fin], P["sorpresa"], registrar, f"Región {clave} · Campeonato",
                               f"Liguilla Región {clave} · Campeonato", nom, campeonato=True, cupos=1)
        SR["orden_final"][clave] = np.array(orden + [int(i) for i in ids[fin:]])
        _proclamar_zona(SR, clave, orden[0])
    SR["desempate_pendiente"] = False


def _jugar_cruces_reg(SR, P, rng, n_fecha):
    """Regiones divididas en dos zonas: los campeones de zona juegan un partido único en cancha neutral (penales si
    empatan) por el título de la región."""
    nom, r = SR["nombres"], SR["r"]
    for reg in REGIONES_REG:
        claves = SR["zonas_de"][reg]
        if len(claves) < 2:
            continue
        a, b = (SR["campeones_zona"][c] for c in claves)

        def registrar(x, y, gl, gv, tanda, gana, comp, reg=reg):
            partido = nuevo_partido(REG_LIGA, n_fecha, REG_CRUCE, comp, nom[x], nom[y],
                                    gl, gv, tanda=tanda, gana=nom[gana], neutral=True)
            partido["region"] = reg
            SR["log"].append(partido)
            return partido

        orden = definir_bloque(rng, r, [a, b], P["sorpresa"], registrar, f"Región {reg} · Final de zonas",
                               f"Liguilla Región {reg} · Final de zonas", nom, campeonato=True, cupos=1)
        SR["campeones"][reg] = int(orden[0])
        SR["cruces"][reg] = (int(orden[0]), int(orden[1]))


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
        # cierra de local el de mejor campaña en su liga regional
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


def rotulo_reg(SR, n):
    """Nombre de la fecha n (1, 2, ...) del Regional."""
    if n <= SR["f_liga"]:
        return f"Fecha {n}"
    if n <= SR["f_liga"] + SR["f_des"]:
        return "Desempate por el campeonato"
    if n <= SR["f_final0"]:
        return REG_CRUCE
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
            gh, ga = jugar(rng, SR["r"][h], SR["r"][a], **P, **mods_ids(rng, SR["nombres"], h, a))
            sumar_partidos(SR, h, a, gh, ga)
            nom = SR["nombres"]
            for x, y, g1, g2 in zip(h, a, gh, ga):
                reg = SR["region_de"][x]
                partido = nuevo_partido(REG_LIGA, f + 1, f"Fecha {f + 1}", f"Región {SR['zona_de'][x]}",
                                        nom[x], nom[y], g1, g2)
                partido["region"] = reg
                SR["log"].append(partido)
            revisar_liga(SR, SR["log"][-len(h):], rng)
        SR["fecha"] += 1
        if SR["fecha"] == SR["f_liga"]:
            _cierre_ligas_reg(SR)
        return
    if f < SR["f_liga"] + SR["f_des"]:                  # ---- desempates por el título de zona
        _jugar_desempates_reg(SR, P, rng, f + 1)
    elif f < SR["f_final0"]:                            # ---- campeón de cada región dividida en dos zonas
        _jugar_cruces_reg(SR, P, rng, f + 1)
    else:                                               # ---- finales por el ascenso
        vuelta = f - SR["f_final0"] == 1
        if not vuelta:
            _armar_finales_reg(SR)
        _jugar_pierna_reg(SR, P, rng, SR["finales"], vuelta, f + 1)
        if vuelta:
            SR["ascendidos"] = [x["gana"] for x in SR["finales"] if x["gana"] is not None]
    SR["fecha"] += 1

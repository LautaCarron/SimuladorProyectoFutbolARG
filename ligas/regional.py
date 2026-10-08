"""Regional Amateur: ligas por región, desempates y finales.
"""

import numpy as np

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
from datos.regional import FINALES_REG, REGIONES_REG
from ligas.primera import definir_bloque


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
            gh, ga = jugar(rng, SR["r"][h], SR["r"][a], **P, **mods_ids(rng, SR["nombres"], h, a))
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

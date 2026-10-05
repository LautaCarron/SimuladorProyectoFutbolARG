"""Estado de la partida y paso de una temporada a la siguiente (ascensos, descensos, copas, palmarés).
"""

import numpy as np
import time

from datos import (
    EQUIPOS_PRIMERA_D,
    EQUIPOS,
    EQUIPOS_B,
    EQUIPOS_FEDERAL,
    EQUIPOS_PRIMERA_B,
    EQUIPOS_PRIMERA_C,
    EQUIPOS_REGIONAL,
    N,
    NB,
    REGIONAL,
    origen,
)
from motor import MAX_R, MIN_R, REVERSION
from competencias import REGISTRO
from copas import clasificados_copa, sortear_copa
from internacional import MEDIA_EXT, fin_de_temporada, nuevas_internacionales
from palmares import palmares_inicial
from liga_federal import F_MIN, nueva_estructura_f
from liga_nacional import nueva_estructura_b
from liga_primera import nueva_estructura, tabla_final
from liga_regional import nueva_estructura_reg
from ligas_simples import nueva_estructura_liga


VERSION_ESTADO = 15       # cambia si se modifica la estructura del estado guardado


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
    SPD = {"nombres": list(EQUIPOS_PRIMERA_D), "r": np.array(list(EQUIPOS_PRIMERA_D.values()), dtype=float)}
    nueva_estructura_liga(SPD, rng)
    S["pd"] = SPD
    S["promocional"] = list(EQUIPOS_PRIMERA_D)
    SREG = {"nombres": list(EQUIPOS_REGIONAL), "r": np.array(list(EQUIPOS_REGIONAL.values()), dtype=float)}
    nueva_estructura_reg(SREG, rng)
    S["reg"] = SREG
    S["copa"] = sortear_copa(S, rng)    # temporada 1: clasifican los de mejor media de cada liga
    nuevas_internacionales(S, rng)      # Libertadores, Sudamericana y Recopa
    for comp in REGISTRO:               # Supercopa y Mundial de Clubes (la Copa se sortea arriba)
        if comp.crea_estado:
            S[comp.clave] = comp.nueva(S, rng)



    # Palmarés histórico oficial de cada liga y copa hasta 2025 (ver palmares.py); cada temporada
    # simulada le suma sus campeones
    S.update(palmares_inicial())

    return S


def nueva_temporada(S, volatilidad):
    SB, SF, SPB, SPC, SPD, rng = S["b"], S["f"], S["pb"], S["pc"], S["pd"], S["rng"]
    for lig in (S, SB, SF, SPB, SPC, SPD, S["reg"]):
        for nom, x in zip(lig["nombres"], lig["r"]):
            S["rating"][nom] = float(x)

    final = tabla_final(S)
    promo = SB["promo"]
    # Copa Argentina de la temporada que viene: clasifican por lo hecho en esta
    S["copa_clasif"] = [(x[0], x[3]) for x in clasificados_copa(S)]
    # copas CONMEBOL de la temporada que viene (tabla de Primera, Copa Argentina y campeones)
    fin_de_temporada(S)

    # Campeón de cada liga en la temporada que termina (para el Historial)
    def _campeon(L):
        return L["nombres"][L["campeon"]] if L.get("campeon") is not None else ""
    S["campeones"].append({
        "Temporada": S["temp"], "Primera División": final.iloc[0]["Equipo"],
        "Primera Nacional": _campeon(SB), "Federal A": _campeon(SF), "Primera B": _campeon(SPB),
        "Primera C": _campeon(SPC),
        "Copa Argentina": (S["copa"]["nombres"][S["copa"]["campeon"]]
                           if S.get("copa", {}).get("campeon") is not None else ""),
        "Libertadores": S.get("int", {}).get("lib", {}).get("campeon") or "",
        "Sudamericana": S.get("int", {}).get("sud", {}).get("campeon") or "",
        "Recopa": S.get("int", {}).get("rec", {}).get("campeon") or "",
        **{comp.col_historial: comp.campeon(S) or "" for comp in REGISTRO if comp.col_historial},
        "Regional": {reg: S["reg"]["nombres"][c] for reg, c in S["reg"]["campeones"].items() if c is not None},
    })

    # Sumar +1 al palmarés histórico de cada liga (campeón de la temporada que termina)
    ultimo = S["campeones"][-1]
    for clave_h, liga_h in (("hist_primera", "Primera División"), ("hist_nacional", "Primera Nacional"),
                            ("hist_federal", "Federal A"), ("hist_pb", "Primera B"), ("hist_pc", "Primera C")):
        camp_h = ultimo.get(liga_h)
        if camp_h:
            S.setdefault(clave_h, {})[camp_h] = S.get(clave_h, {}).get(camp_h, 0) + 1

    # Sumar +1 al ranking histórico de copas
    campeon_copa = S["copa"]["nombres"][S["copa"]["campeon"]] if S.get("copa", {}).get("campeon") is not None else None
    if campeon_copa: S.setdefault("hist_copa", {})[campeon_copa] = S["hist_copa"].get(campeon_copa, 0) + 1
    
    camp_lib = S.get("int", {}).get("lib", {}).get("campeon")
    if camp_lib: S.setdefault("hist_lib", {})[camp_lib] = S["hist_lib"].get(camp_lib, 0) + 1
    
    camp_sud = S.get("int", {}).get("sud", {}).get("campeon")
    if camp_sud: S.setdefault("hist_sud", {})[camp_sud] = S["hist_sud"].get(camp_sud, 0) + 1
    
    camp_rec = S.get("int", {}).get("rec", {}).get("campeon")
    if camp_rec: S.setdefault("hist_rec", {})[camp_rec] = S["hist_rec"].get(camp_rec, 0) + 1

    for comp in REGISTRO:               # palmarés de cada competencia del registro y su cierre de temporada
        camp = comp.campeon(S)
        if comp.hist and camp:
            S.setdefault(comp.hist, {})
            S[comp.hist][camp] = S[comp.hist].get(camp, 0) + 1
        comp.cerrar(S, rng)

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
    descendidos_pc = [SPC["nombres"][i] for i in SPC.get("desc_directo", [])]
    ascendidos_pd = [SPD["nombres"][i] for i in SPD["asc_directo"]]
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
    S["primera_c"] = [n for n in SPC["nombres"] if n not in ascendidos_pc and n not in descendidos_pc] + descendidos_pb + ascendidos_pd
    S["promocional"] = [n for n in SPD["nombres"] if n not in ascendidos_pd] + descendidos_pc

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
        "suben_pd_pc": ascendidos_pd,
        "bajan_pc_pd": descendidos_pc,
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

    S["pd"]["nombres"] = list(S["promocional"])
    S["pd"]["r"] = np.array([S["rating"][n] for n in S["pd"]["nombres"]])
    nueva_estructura_liga(S["pd"], rng)

    # Regional: los clubes del JSON que siguen en el torneo (en el orden del JSON) y después
    # los que bajaron del Federal A (cada uno juega en la región de su provincia)
    quedan = set(S["regional"])
    del_json = [x["nombre"] for x in REGIONAL if x["nombre"] in quedan]
    S["reg"]["nombres"] = del_json + [n for n in S["regional"] if n not in set(del_json)]
    S["reg"]["r"] = np.array([S["rating"][n] for n in S["reg"]["nombres"]])
    nueva_estructura_reg(S["reg"], rng)
    S["copa"] = sortear_copa(S, rng)    # se juega durante la temporada, los miércoles
    # clubes del exterior: su media cambia un poco cada año (vuelve hacia la de su club)
    ri = S.setdefault("rating_int", dict(MEDIA_EXT))
    for n, base in MEDIA_EXT.items():
        ri[n] = float(np.clip(ri.get(n, base) + 0.3 * (base - ri.get(n, base)) + rng.normal(0, 1.5), MIN_R, MAX_R))
    nuevas_internacionales(S, rng)
    for comp in REGISTRO:               # Supercopa y Mundial de Clubes (el Mundial se sortea cada 4 temporadas)
        if comp.crea_estado:
            S[comp.clave] = comp.nueva(S, rng)

    #----------------- REINICIAR ESTADOS DE DESEMPATE -----------------
    for liga in [S["pb"], S["pc"]]:
        liga["desempate_pendiente"] = False
        liga["ids_desempate"] = []
        liga["motivos_desempate"] = []
        liga["orden_final"] = None

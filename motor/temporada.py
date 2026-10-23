"""Estado de la partida y paso de una temporada a la siguiente (ascensos, descensos, copas, palmarés).
"""

import numpy as np
import time

from datos.equipos import (
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
from motor.nucleo import MAX_R, MIN_R, REVERSION
from copas.registro import REGISTRO
from copas.argentina import clasificados_copa, sortear_copa
from copas.conmebol import MEDIA_EXT, fin_de_temporada, nuevas_internacionales
from datos.palmares import palmares_inicial
from ligas.federal import nueva_estructura_f
from ligas.federal_b import (CREACION_MANTIENE_FEDERAL_A, FB_EQUIPOS, elegir_del_regional, nueva_liga_fb,
                             pendiente as fb_pendiente)
from ligas.nacional import ascensos_a_primera, equipos_objetivo_b, nueva_estructura_b, orden_final_b
from ligas.primera import equipos_objetivo_p, descensos, nueva_estructura, tabla_final
from ligas.regional import nueva_estructura_reg
from ligas.simples import nueva_estructura_liga
from motor.tamanos import ajustar as ajustar_tamanos, plan_equilibrado


VERSION_ESTADO = 18       # cambia si se modifica la estructura del estado guardado


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
        "federal_b": [], "fb": None,          # Federal B: se crea desde el Modo dios (ver ligas/federal_b.py)
        "cerrada_ambas": False, "version": VERSION_ESTADO,
    }
    nueva_estructura(S)
    SB = {"nombres": list(EQUIPOS_B), "r": np.array(list(EQUIPOS_B.values()), dtype=float)}
    nueva_estructura_b(SB, rng, S)
    S["b"] = SB
    SF = {"nombres": list(EQUIPOS_FEDERAL), "r": np.array(list(EQUIPOS_FEDERAL.values()), dtype=float)}
    nueva_estructura_f(SF, rng, S)
    S["f"] = SF
    SPB = {"nombres": list(EQUIPOS_PRIMERA_B), "r": np.array(list(EQUIPOS_PRIMERA_B.values()), dtype=float)}
    nueva_estructura_liga(SPB, rng, S, "pb")
    S["pb"] = SPB
    SPC = {"nombres": list(EQUIPOS_PRIMERA_C), "r": np.array(list(EQUIPOS_PRIMERA_C.values()), dtype=float)}
    nueva_estructura_liga(SPC, rng, S, "pc")
    S["pc"] = SPC
    SPD = {"nombres": list(EQUIPOS_PRIMERA_D), "r": np.array(list(EQUIPOS_PRIMERA_D.values()), dtype=float)}
    nueva_estructura_liga(SPD, rng, S, "pd")
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
    SFB = S.get("fb")                                   # Federal B (None mientras no se crea en el Modo dios)
    S.setdefault("federal_b", [])
    # quién jugaba dónde esta temporada (para el ajuste de tamaño de las ligas, ver motor/tamanos.py)
    viejas = {"p": list(S["nombres"]), "b": list(SB["nombres"]), "fa": list(SF["nombres"]),
              "fb": list(SFB["nombres"]) if SFB else None, "pb": list(SPB["nombres"]), "pc": list(SPC["nombres"]),
              "pd": list(SPD["nombres"]), "reg": list(S["reg"]["nombres"])}
    for lig in (S, SB, SF, SPB, SPC, SPD, S["reg"], *([SFB] if SFB else [])):
        for nom, x in zip(lig["nombres"], lig["r"]):
            S["rating"][nom] = float(x)

    final = tabla_final(S)
    promos_b = SB.get("promos") or []
    for pr in promos_b:                                 # el nombre ahora: los índices de la B cambian en el pase
        pr["b_nombre"] = SB["nombres"][pr["b_id"]]
    # Copa Argentina de la temporada que viene: clasifican por lo hecho en esta
    S["copa_clasif"] = [(x[0], x[3]) for x in clasificados_copa(S)]
    # copas CONMEBOL de la temporada que viene (tabla de Primera, Copa Argentina y campeones)
    fin_de_temporada(S)

    # Campeón de cada liga en la temporada que termina (para el Historial)
    def _campeon(L):
        return L["nombres"][L["campeon"]] if L.get("campeon") is not None else ""
    S["campeones"].append({
        "Temporada": S["temp"], "Primera División": final.iloc[0]["Equipo"],
        "Primera Nacional": _campeon(SB), "Federal A": _campeon(SF),
        **({"Federal B": _campeon(SFB)} if SFB else {}),
        "Primera B": _campeon(SPB),
        "Primera C": _campeon(SPC), "Promocional Amateur": _campeon(SPD),
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
                            ("hist_federal", "Federal A"), ("hist_federalB", "Federal B"),
                            ("hist_pb", "Primera B"), ("hist_pc", "Primera C"),
                            ("hist_pd", "Promocional Amateur")):
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

    reducido = SB["nombres"][SB["asc_reducido"]] if SB["asc_reducido"] is not None else None   # sin reducido en el torneo anual
    k_desc = descensos(S)                                         # Modo dios: cuántos bajan directo (suben tantos de la B)
    suben = ascensos_a_primera(S)
    directos = [n for n in suben if n != reducido]
    bajan_p = list(final[final["Pos"] > len(S["nombres"]) - k_desc]["Equipo"])
    for pr in promos_b:                                           # cada promoción ganada por la B es un ascenso más
        if pr["gana_b"]:
            suben.append(SB["nombres"][pr["b_id"]])
            bajan_p.append(pr["p_nombre"])
        
    bajan_b = [SB["nombres"][i] for i in SB["desc_b"]]

    # Modo dios: Primera puede tener más o menos equipos. Si faltan, suben de más los mejor ubicados de la B que
    # no ascendían; si sobran, bajan de más los peor ubicados de Primera.
    # Primera cambia de tamaño si suben más (o menos) de los que bajan; sólo se corrige si pasa los límites o si en
    # el Modo dios se fijó una cantidad de equipos.
    dif_p = equipos_objetivo_p(S, len(S["nombres"]) - len(bajan_p) + len(suben)) - (
        len(S["nombres"]) - len(bajan_p) + len(suben))
    if dif_p > 0:
        mejores = [SB["nombres"][i] for i in orden_final_b(SB)
                   if SB["nombres"][i] not in suben and SB["nombres"][i] not in bajan_b]
        extra_suben = mejores[:dif_p]
        suben += extra_suben
        directos += extra_suben
    elif dif_p < 0:
        peores_p = [n for n in reversed(list(final["Equipo"])) if n not in bajan_p]
        bajan_p += peores_p[:-dif_p]

    # Modo dios: la B puede tener menos equipos. Si con los ascendidos y los que bajan de Primera sobran, bajan
    # de más los peor ubicados de la tabla final (de los que se quedaban en la B).
    n_asc_f = len(SF["ascendidos"]) + len(SPB.get("ascendidos") or SPB["asc_directo"])         # los que suben del Federal A y de la Primera B
    se_quedan = [n for n in SB["nombres"] if n not in suben and n not in bajan_b]
    # Automático: la B queda con los que se quedan, los que bajan de Primera y los que suben de verdad del Federal A y la
    # Primera B (si bajan más de los que suben, se achica; sin rellenar con clubes elegidos al azar). Si en el Modo dios
    # se fijó una cantidad de equipos, se completa o se recorta hasta llegar a ella.
    objetivo_b = equipos_objetivo_b(S, len(se_quedan) + len(bajan_p) + n_asc_f)
    sobran = len(se_quedan) + len(bajan_p) + n_asc_f - objetivo_b
    bajan_b_extra = []
    if sobran > 0:
        peores = [SB["nombres"][i] for i in reversed(orden_final_b(SB)) if SB["nombres"][i] in se_quedan]
        bajan_b_extra = peores[:sobran]
        bajan_b = bajan_b + bajan_b_extra
    bajan_b_fed = [n for n in bajan_b if origen(n) == "Interior"]
    bajan_b_pb = [n for n in bajan_b if origen(n) == "Metropolitana"]

    S["nombres"] = [n for n in S["nombres"] if n not in bajan_p] + suben
    base_b = [n for n in SB["nombres"] if n not in suben and n not in bajan_b] + bajan_p

    # Ascensos y descensos internos
    ascendidos_f = [SF["nombres"][i] for i in SF["ascendidos"]]
    ascendidos_pb = [SPB["nombres"][i] for i in (SPB.get("ascendidos") or SPB["asc_directo"])]
    descendidos_pb = [SPB["nombres"][i] for i in SPB["desc_directo"]]
    ascendidos_pc = [SPC["nombres"][i] for i in (SPC.get("ascendidos") or SPC["asc_directo"])]
    descendidos_pc = [SPC["nombres"][i] for i in SPC.get("desc_directo", [])]
    ascendidos_pd = [SPD["nombres"][i] for i in (SPD.get("ascendidos") or SPD["asc_directo"])]
    garantizados = list(ascendidos_f) + list(ascendidos_pb)
    
    faltan = max(0, objetivo_b - len(base_b) - len(garantizados))
    descendidos_f = [SF["nombres"][i] for i in SF.get("descendidos", [])]
    pool_fed = [n for n in S["federal"] if n not in garantizados and n not in descendidos_f]
    pool_pb = [n for n in SPB["nombres"] if n not in garantizados and n not in descendidos_pb]
    pool = pool_fed + pool_pb
    faltan = min(faltan, len(pool))                          # si no alcanzan los clubes de abajo, la B queda más chica
    
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

    # Regional Amateur: los 6 ganadores de las finales ascienden (al Federal A, o al Federal B si existe)
    ascendidos_reg = [S["reg"]["nombres"][i] for i in S["reg"]["ascendidos"]]
    suben_reg_a, suben_reg_b, extra_reg = ascendidos_reg, [], []
    asc_fb, desc_fb = [], []
    creando_fb = fb_pendiente(S)
    if SFB is not None:                                  # Federal B en marcha
        asc_fb = [SFB["nombres"][i] for i in SFB["ascendidos"]]          # suben al Federal A
        desc_fb = [SFB["nombres"][i] for i in SFB.get("descendidos", [])]  # bajan al Regional
        suben_reg_a, suben_reg_b = [], ascendidos_reg
        S["federal"] = S["federal"] + asc_fb
        S["federal_b"] = ([n for n in SFB["nombres"] if n not in asc_fb and n not in desc_fb]
                          + descendidos_f + ascendidos_reg)
        S["regional"] = [n for n in S["regional"] if n not in ascendidos_reg] + desc_fb
    elif creando_fb:                                     # se crea ahora: bajan los del Federal A y suben los mejores del Regional
        if not CREACION_MANTIENE_FEDERAL_A:
            suben_reg_a, suben_reg_b = [], ascendidos_reg
        faltan_fb = max(0, FB_EQUIPOS - len(descendidos_f) - len(suben_reg_b))
        extra_reg = elegir_del_regional(S["reg"], ascendidos_reg, faltan_fb)
        S["federal"] = S["federal"] + suben_reg_a
        S["federal_b"] = list(descendidos_f) + suben_reg_b + extra_reg
        S["regional"] = [n for n in S["regional"] if n not in ascendidos_reg and n not in extra_reg]
    else:                                                # sin Federal B: como siempre
        S["federal"] = S["federal"] + ascendidos_reg
        S["regional"] = [n for n in S["regional"] if n not in ascendidos_reg] + descendidos_f
    hay_fb = SFB is not None or creando_fb
    
    SB["nombres"] = base_b + entran

    S["movimientos"] = {
        "directos": directos, "reducido": reducido if reducido in suben else None,
        "bajan_p": bajan_p, 
        "bajan_b_fed": bajan_b_fed, 
        "bajan_b_extra": bajan_b_extra,
        "bajan_b_pb": bajan_b_pb,
        "suben_f_b": ascendidos_f,
        "suben_pb_b": ascendidos_pb,
        "suben_pc_pb": ascendidos_pc,
        "suben_reg_fed": suben_reg_a,
        "bajan_fed_reg": [] if hay_fb else descendidos_f,
        "bajan_fed_fb": descendidos_f if hay_fb else [],
        "suben_reg_fb": suben_reg_b,
        "suben_reg_fb_extra": extra_reg,
        "suben_fb_f": asc_fb,
        "bajan_fb_reg": desc_fb,
        "fb_activa": hay_fb,
        "fb_nueva": creando_fb,
        "bajan_pb_pc": descendidos_pb,
        "suben_pd_pc": ascendidos_pd,
        "bajan_pc_pd": descendidos_pc,
        "entran_fed": [n for n in entran if origen(n) == "Interior" and n not in ascendidos_f],
        "entran_pb": [n for n in entran if origen(n) == "Metropolitana" and n not in ascendidos_pb],
        "campeon_federal": SF["nombres"][SF["campeon"]] if SF["campeon"] is not None else None,
        "promo_texto": (" ".join(
            (f"Promoción: {pr['b_nombre']} (B) le ganó a {pr['p_nombre']}: asciende y baja {pr['p_nombre']}."
             if pr["gana_b"] else f"Promoción: {pr['p_nombre']} se mantiene en Primera.") for pr in promos_b)
            or "Esta temporada no hubo promoción."),
    }

    # ---- Tribunal de Disciplina: avisos de la temporada al historial, descensos
    # administrativos (lo gravísimo: baja una categoría más) y quitas de puntos a cero
    ligas_t = (S, SB, SF, *([SFB] if SFB else []), SPB, SPC, S["reg"], S.get("copa", {}))
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
        elif club in S["federal"]:                       # Federal A -> Federal B (o Regional si no hay Federal B)
            S["federal"].remove(club)
            (S["federal_b"] if hay_fb else S["regional"]).append(club)
        elif club in S["federal_b"]:                     # Federal B -> Regional
            S["federal_b"].remove(club)
            S["regional"].append(club)
        elif club in S["primera_b"]:                     # Primera B -> Primera C
            S["primera_b"].remove(club)
            S["primera_c"].append(club)
        else:
            continue
        bajan_adm.append(club)
    S["movimientos"]["descenso_adm"] = bajan_adm

    # Tamaño de las ligas: el objetivo elegido en el Modo dios (de a poco) y el piso de equipos de cada una
    listas = {"p": S["nombres"], "b": SB["nombres"], "fa": S["federal"], "pb": S["primera_b"],
              "pc": S["primera_c"], "pd": S["promocional"], "reg": S["regional"]}
    if hay_fb:
        listas["fb"] = S["federal_b"]
    S["movimientos"]["ajustes"] = [{"club": c, "de": de, "a": a, "motivo": m}
                                   for c, de, a, m in ajustar_tamanos(S, listas, viejas, hay_fb)]
    # con tamaño objetivo, los ascensos y descensos de la temporada que viene quedan parejos y razonables
    plan_equilibrado(S, {k: len(v) for k, v in listas.items() if k != "reg"})
    S["movimientos"]["suben_reg_fed_extra"] = []          # sin reubicación: el Federal A cambia de tamaño
    for L in ligas_t[:-1]:
        L["alertas"], L["quita"], L["desc_adm"] = [], {}, []

    for nombres in (S["nombres"], SB["nombres"], S["federal"], S["primera_b"], S["primera_c"],
                    S["regional"], *([S["federal_b"]] if S["federal_b"] else [])):
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
    nueva_estructura_b(SB, rng, S)
    nueva_estructura_f(SF, rng, S)
    if S["federal_b"]:                                   # Federal B: se crea (la primera vez) o se renueva
        nueva_liga_fb(S, rng)

    S["pb"]["nombres"] = list(S["primera_b"])
    S["pb"]["r"] = np.array([S["rating"][n] for n in S["pb"]["nombres"]])
    nueva_estructura_liga(S["pb"], rng, S, "pb")
    
    S["pc"]["nombres"] = list(S["primera_c"])
    S["pc"]["r"] = np.array([S["rating"][n] for n in S["pc"]["nombres"]])
    nueva_estructura_liga(S["pc"], rng, S, "pc")

    S["pd"]["nombres"] = list(S["promocional"])
    S["pd"]["r"] = np.array([S["rating"][n] for n in S["pd"]["nombres"]])
    nueva_estructura_liga(S["pd"], rng, S, "pd")

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
    for liga in [S["pb"], S["pc"], S["pd"]]:
        liga["desempate_pendiente"] = False
        liga["ids_desempate"] = []
        liga["motivos_desempate"] = []
        liga["orden_final"] = None

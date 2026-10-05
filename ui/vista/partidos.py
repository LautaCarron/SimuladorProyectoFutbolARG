"""Partidos jugados y por jugar de cada liga, tarjetas de partido y próximo partido de un club.
"""

import streamlit as st

from motor.calendario import dia_partido, texto_dia
from datos.equipos import F_GRUPOS_NOMBRES
from ligas.federal import rotulo_f
from ligas.nacional import B_F1, B_F2, B_ZONAS2, rotulo_b
from ligas.primera import FECHAS_F1, TOTAL_FECHAS, ZONAS, rotulo_p
from ligas.regional import rotulo_reg
from ui.vista.base import _estado, chip, crest, esc
from datos.clubes_mundial import PAIS_MUNDIAL
from copas.registro import REGISTRO
from copas.conmebol import PAIS_EXT


def todos_los_partidos():
    S, SB, SF, SPB, SPC = _estado()
    return (S["log"] + S["b"]["log"] + S["f"]["log"] + S["pb"]["log"] + S["pc"]["log"] + S["pd"]["log"] + S["reg"]["log"]
            + [p for comp in REGISTRO for p in comp.log(S)]
            + [p for C in S.get("int", {}).values() for p in C["log"]])


def _categoria_arg(nombre):
    S, SB, SF, SPB, SPC = _estado()
    if nombre in S["nombres"]:
        return "Primera División"
    if nombre in S["b"]["nombres"]:
        return "Primera Nacional"
    if nombre in S["federal"]:
        return "Federal A"
    if nombre in S["primera_b"]:
        return "Primera B"
    if nombre in S["primera_c"]:
        return "Primera C"
    if nombre in st.session_state.S.get("promocional", []):
        return "Promocional Amateur"
    if nombre in st.session_state.S["reg"]["nombres"]:
        return "Regional Amateur"
    return ""


def categoria_de(nombre):
    cat = _categoria_arg(nombre)
    if cat:
        return cat
    return PAIS_EXT.get(nombre) or PAIS_MUNDIAL.get(nombre)


def marcador_html(p, crests=False):
    cl = crest(p["local"], 22) if crests else ""
    cv = crest(p["visita"], 22) if crests else ""
    if p["gl"] is None:
        return f'<div class="score">{cl}<span class="vs">VS</span>{cv}</div>'
    wl = ' w' if p["gana"] == p["local"] else ''
    wv = ' w' if p["gana"] == p["visita"] else ''
    pl = pv = ""
    if p["pen"]:
        pl, pv = f"<small>({p['pen'][0]})</small>", f"<small>({p['pen'][1]})</small>"
    return (f'<div class="score">{cl}<span class="n{wl}">{p["gl"]}</span>{pl}<span class="sep">–</span>'
            f'{pv}<span class="n{wv}">{p["gv"]}</span>{cv}</div>')


def tanda_html(p, abierto=False):
    if not p.get("tanda"):
        return ""
    filas = ""
    for nombre, serie, total in ((p["local"], p["tanda"][0], p["pen"][0]),
                                 (p["visita"], p["tanda"][1], p["pen"][1])):
        dots = "".join('<span class="pk ok">✓</span>' if x else '<span class="pk no">✗</span>'
                       for x in serie)
        filas += (f'<div class="trow">{crest(nombre, 18)}<span class="tn">{esc(nombre)}:</span>'
                  f'<span class="tt">{total}</span><span>{dots}</span></div>')
    return (f'<details class="tanda"{" open" if abierto else ""}><summary>Penales · '
            f'{esc(p["local"])} {p["pen"][0]} – {p["pen"][1]} {esc(p["visita"])}</summary>'
            f'{filas}</details>')


def fila_partido_html(p, abierto=False):
    """Partido en formato tarjeta."""
    wl = " w" if p["gana"] == p["local"] else ""
    wv = " w" if p["gana"] == p["visita"] else ""
    dia = dia_partido(st.session_state.S, p)
    meta = (chip(p["liga"]) + (chip(p["comp"]) if p["comp"] != p["liga"] else "")
            + f'<span style="opacity:.7;font-weight:600">{esc(p["rotulo"])}</span>'
            + (f'<span class="m-dia">{esc(texto_dia(dia, False))}</span>' if dia else "")
            + ('<span style="opacity:.6">· cancha neutral</span>' if p["neutral"] else "")
            + (f'<span class="inc-badge">⚠ {esc(p["incidente"])}</span>' if p.get("incidente") else ""))
    return (f'<div class="mrow"><div class="meta">{meta}</div><div class="mline">'
            f'<div class="side l{wl}">{esc(p["local"])} {crest(p["local"], 26)}</div>'
            f'{marcador_html(p)}'
            f'<div class="side{wv}">{crest(p["visita"], 26)} {esc(p["visita"])}</div></div>'
            f'{tanda_html(p, abierto)}</div>')


def lista_equipos_html(items):
    """items: lista de (nombre, detalle)."""
    if not items:
        return '<div style="opacity:.6">Por definir</div>'
    return '<div class="tlist">' + "".join(
        f'<span class="tl">{crest(n, 26)}{esc(n)}{f" <small>{esc(d)}</small>" if d else ""}</span>'
        for n, d in items) + "</div>"


def resultado_para(p, nombre):
    local = p["local"] == nombre
    gf, gc = (p["gl"], p["gv"]) if local else (p["gv"], p["gl"])
    letra = "G" if gf > gc else "P" if gf < gc else "E"
    return local, gf, gc, letra


# ---- Calendario: partidos jugados y por jugar -------------------------------
def pendiente(liga, n, rotulo, comp, local, visita):
    return {"liga": liga, "fecha": n, "rotulo": rotulo, "comp": comp, "local": local,
            "visita": visita, "gl": None, "gv": None, "gana": None, "tanda": None,
            "pen": None, "neutral": False}


def fechas_conocidas_p():
    S, SB, SF, SPB, SPC = _estado()
    return len(S["fechas"])


def partidos_fecha_p(n):
    S, SB, SF, SPB, SPC = _estado()
    if n <= S["fecha"]:
        return [p for p in S["log"] if p["fecha"] == n]
    nom = S["nombres"]

    def competencia(x):
        """Fase 1, zona del club x en la fase 2 o desempate (después de la última fecha regular)."""
        if n <= FECHAS_F1:
            return "Fase 1"
        if n <= TOTAL_FECHAS:
            return f"Zona {ZONAS[S['zona_de'][x]]}"
        return "Desempate"

    return [pendiente("Primera División", n, rotulo_p(S, n), competencia(x), nom[x], nom[y])
            for x, y in S["fechas"][n - 1]]


def fechas_conocidas_b():
    S, SB, SF, SPB, SPC = _estado()
    return max(SB["fecha"], B_F1 if SB["fechas2"] is None else B_F1 + len(SB["fechas2"]))


def partidos_fecha_b(n):
    S, SB, SF, SPB, SPC = _estado()
    if n <= SB["fecha"]:
        return [p for p in SB["log"] if p["fecha"] == n]
    nom = SB["nombres"]
    if n <= B_F1:
        return [pendiente("Primera Nacional", n, rotulo_b(SB, n), f"Zona {'AB'[SB['zona_de'][x]]}",
                          nom[x], nom[y]) for x, y in SB["fechas"][n - 1]]
    return [pendiente("Primera Nacional", n, rotulo_b(SB, n),
                      f"Zona {B_ZONAS2[SB['zona2_de'][x]]}" if n <= B_F1 + B_F2 else "Desempate Permanencia", nom[x], nom[y])
            for x, y in SB["fechas2"][n - 1 - B_F1]]


def fechas_conocidas_f():
    S, SB, SF, SPB, SPC = _estado()
    return max(SF["fecha"], SF["f1_rondas"] if SF["fechas2"] is None else SF["f1_rondas"] + SF.get("f2_rondas", 0))


def partidos_fecha_f(n):
    S, SB, SF, SPB, SPC = _estado()
    if n <= SF["fecha"]:
        return [p for p in SF["log"] if p["fecha"] == n]
    nom = SF["nombres"]
    if n <= SF["f1_rondas"]:
        return [pendiente("Federal A", n, rotulo_f(SF, n), f"Zona {F_GRUPOS_NOMBRES[SF['grupo_de'][x]]}",
                          nom[x], nom[y]) for x, y in SF["fechas"][n - 1]]
    return [pendiente("Federal A", n, rotulo_f(SF, n),
                      "Campeonato" if SF["zona2_de"][x] == 0 else "Descenso", nom[x], nom[y])
            for x, y in SF["fechas2"][n - 1 - SF["f1_rondas"]]]


def fechas_conocidas_pb():
    S, SB, SF, SPB, SPC = _estado()
    return SPB["total"]


def partidos_fecha_pb(n):
    S, SB, SF, SPB, SPC = _estado()
    if n <= SPB["fecha"]:
        return [p for p in SPB["log"] if p["fecha"] == n]
    nom = SPB["nombres"]
    
    rotulo = f"Fecha {n}"
    comp = "Liga"
    if SPB.get("desempate") and n > SPB["desempate"]["inicio"]:
        rotulo = f"Desempate (F. {n - SPB['desempate']['inicio']})"
        comp = "Desempate"
        
    return [pendiente("Primera B", n, rotulo, comp, nom[x], nom[y])
            for x, y in SPB["fechas"][n - 1]]


def fechas_conocidas_pc():
    S, SB, SF, SPB, SPC = _estado()
    return SPC["total"]


def partidos_fecha_pc(n):
    S, SB, SF, SPB, SPC = _estado()
    if n <= SPC["fecha"]: return [p for p in SPC["log"] if p["fecha"] == n]
    nom = SPC["nombres"]
    return [pendiente("Primera C", n, f"Fecha {n}", "Liga", nom[x], nom[y]) for x, y in SPC["fechas"][n - 1]]


def fechas_conocidas_pd():
    S, SB, SF, SPB, SPC = _estado()
    return S["pd"]["total"]


def partidos_fecha_pd(n):
    S, SB, SF, SPB, SPC = _estado()
    SPD = S["pd"]
    if n <= SPD["fecha"]: return [p for p in SPD["log"] if p["fecha"] == n]
    nom = SPD["nombres"]
    return [pendiente("Promocional Amateur", n, f"Fecha {n}", "Liga", nom[x], nom[y]) for x, y in SPD["fechas"][n - 1]]


def fechas_conocidas_reg():
    return st.session_state.S["reg"]["total"]


def partidos_fecha_reg(n, region=None):
    """Partidos de la fecha n del Regional (jugados o por jugar). Con `region`, sólo los de
    esa región (en zonas compartidas, los partidos donde juega algún club de la región)."""
    SR = st.session_state.S["reg"]
    nom = SR["nombres"]
    if n <= SR["fecha"]:
        lista = [p for p in SR["log"] if p["fecha"] == n]
    elif n <= SR["f_liga"]:
        lista = []
        for x, y in SR["fechas"][n - 1]:
            p = pendiente("Regional Amateur", n, rotulo_reg(SR, n), f"Región {SR['region_de'][x]}",
                          nom[x], nom[y])
            p["region"] = SR["region_de"][x]
            lista.append(p)
    else:
        lista = []                                   # desempates y finales: se arman al terminar la liga
    if region is None:
        return lista
    return [p for p in lista if region in {p["region"]} | set(p["region"].split(" / "))]


def proximo_partido(nombre):
    S, SB, SF, SPB, SPC = _estado()
    if nombre in S["nombres"]:
        for n in range(S["fecha"] + 1, fechas_conocidas_p() + 1):
            for p in partidos_fecha_p(n):
                if nombre in (p["local"], p["visita"]):
                    return p
    elif nombre in SB["nombres"]:
        for n in range(SB["fecha"] + 1, fechas_conocidas_b() + 1):
            for p in partidos_fecha_b(n):
                if nombre in (p["local"], p["visita"]):
                    return p
    elif nombre in SF["nombres"]:
        for n in range(SF["fecha"] + 1, fechas_conocidas_f() + 1):
            for p in partidos_fecha_f(n):
                if nombre in (p["local"], p["visita"]):
                    return p
    elif nombre in SPB["nombres"]:
        for n in range(SPB["fecha"] + 1, fechas_conocidas_pb() + 1):
            for p in partidos_fecha_pb(n):
                if nombre in (p["local"], p["visita"]):
                    return p
    elif nombre in SPC["nombres"]:
        for n in range(SPC["fecha"] + 1, fechas_conocidas_pc() + 1):
            for p in partidos_fecha_pc(n):
                if nombre in (p["local"], p["visita"]): return p
    elif nombre in st.session_state.S.get("pd", {}).get("nombres", []):
        for n in range(st.session_state.S["pd"]["fecha"] + 1, fechas_conocidas_pd() + 1):
            for p in partidos_fecha_pd(n):
                if nombre in (p["local"], p["visita"]): return p
    elif nombre in st.session_state.S["reg"]["nombres"]:
        for n in range(st.session_state.S["reg"]["fecha"] + 1, st.session_state.S["reg"]["f_liga"] + 1):
            for p in partidos_fecha_reg(n):
                if nombre in (p["local"], p["visita"]): return p
    return None

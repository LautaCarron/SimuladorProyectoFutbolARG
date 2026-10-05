"""Ficha de un club con el buscador de sus partidos.
"""

import pandas as pd
import streamlit as st

from motor.calendario import dia_partido, texto_dia
from ui.vista.base import _estado, chip, coincide, crest, esc, norm
from ui.vista.partidos import (
    categoria_de,
    fila_partido_html,
    proximo_partido,
    resultado_para,
    todos_los_partidos,
)
from ui.vista.tablas import tabla_html


# ---- Ficha de un club (con buscador de sus partidos) ------------------------
def render_ficha(nombre, clave):
    S, SB, SF, SPB, SPC = _estado()
    partidos = [p for p in todos_los_partidos() if nombre in (p["local"], p["visita"])]
    cat = categoria_de(nombre)
    filas, letras = [], []
    gf_t = gc_t = 0
    for p in partidos:
        local, gf, gc, letra = resultado_para(p, nombre)
        letras.append(letra)
        gf_t, gc_t = gf_t + gf, gc_t + gc
        rival = p["visita"] if local else p["local"]
        res = f"{gf}-{gc}"
        if p["pen"]:
            pf, pc = p["pen"] if local else p["pen"][::-1]
            res += f" ({pf}-{pc} pen.)"
        if letra == "G":
            desenlace = "Ganó"
        elif letra == "P":
            desenlace = "Perdió"
        elif p["pen"]:
            desenlace = ("Empató · ganó por penales" if p["gana"] == nombre
                         else "Empató · perdió por penales")
        else:
            desenlace = "Empató"
        cond = "Neutral" if p["neutral"] else ("Local" if local else "Visitante")
        comp = p["comp"] if p["comp"] == p["liga"] else f"{p['liga']} · {p['comp']}"
        if p.get("incidente"):
            desenlace += " · ⚠ " + p["incidente"]
        filas.append({
            "Fecha": p["fecha"], "Día": texto_dia(dia_partido(S, p), False),
            "Competición": comp, "Condición": cond,
            "Rival": rival, "Resultado": res, "Desenlace": desenlace,
            "_t": norm(f"{rival} {nombre} {comp} {cond} {desenlace} {p['rotulo']} "
                       f"{texto_dia(dia_partido(S, p))}"),
            "_m": f" {gf}-{gc} {gc}-{gf} ",
        })

    g, e, pp = letras.count("G"), letras.count("E"), letras.count("P")
    forma = "".join(f'<span class="fm {x}">{x}</span>' for x in letras[-5:])
    st.markdown(
        f'<div class="team-head">{crest(nombre, 64)}<div><div class="tn">{esc(nombre)}</div>'
        f'<div style="margin-top:6px">{chip(cat) if cat else ""} '
        f'<span style="font-size:.8rem;opacity:.65">Temporada {S["temp"]}</span></div></div></div>',
        unsafe_allow_html=True)
    st.markdown(
        f'<div class="rec"><div><b>{len(partidos)}</b><span>PJ</span></div>'
        f'<div><b>{g}</b><span>G</span></div><div><b>{e}</b><span>E</span></div>'
        f'<div><b>{pp}</b><span>P</span></div><div><b>{gf_t}</b><span>GF</span></div>'
        f'<div><b>{gc_t}</b><span>GC</span></div><div><b>{gf_t - gc_t:+d}</b><span>DG</span></div>'
        f'<div><span>Últimos 5</span><div class="form">{forma or "—"}</div></div></div>',
        unsafe_allow_html=True)
    prox = proximo_partido(nombre)
    if prox:
        rival = prox["visita"] if prox["local"] == nombre else prox["local"]
        cond = "Local" if prox["local"] == nombre else "Visitante"
        st.markdown(f'<div class="next"><b>Próximo partido</b> · {esc(prox["rotulo"])} · '
                    f'{chip(prox["comp"])} {cond} vs {crest(rival, 20)} <b>{esc(rival)}</b></div>',
                    unsafe_allow_html=True)
    if not filas:
        st.info("Este club todavía no jugó partidos esta temporada.")
        return

    q = st.text_input(":material/search: Buscar partido", key=f"q_{clave}_{nombre}",
                      placeholder="Rival, número de fecha, resultado (2-1), local, visitante, "
                                  "zona, octavos…")
    vis = [f for f in filas if coincide(q, f["_t"], f["Fecha"], f["_m"])] if q else filas
    if not vis:
        st.warning("No hay partidos que coincidan con la búsqueda.")
        return
    if q:
        st.caption(f"{len(vis)} de {len(filas)} partidos")
    # rival y resultado primero: en el celular se ven sin deslizar la tabla
    df = pd.DataFrame(vis)[["Fecha", "Día", "Rival", "Resultado", "Desenlace", "Condición", "Competición"]]

    def color_res(fila):
        d = fila["Desenlace"]
        c = ("rgba(46,125,79,.15)" if d == "Ganó" or "ganó por penales" in d else
             "rgba(184,58,46,.13)" if d == "Perdió" or "perdió por penales" in d else "rgba(15,27,45,.06)")
        return [f"background-color: {c}" if col in ("Resultado", "Desenlace") else ""
                for col in fila.index]

    st.markdown(tabla_html(df, color_res, clubes=("Rival",)).replace(
        'class="tabla-wrap"', 'class="tabla-wrap alto"', 1), unsafe_allow_html=True)
    penales = [p for p in partidos if p["pen"]]
    if penales:
        st.markdown('<div class="mlab">Definiciones por penales</div>'
                    + "".join(fila_partido_html(p) for p in penales), unsafe_allow_html=True)


@st.dialog("Ficha del club", width="large")
def ver_equipo(nombre):
    render_ficha(nombre, "dlg")

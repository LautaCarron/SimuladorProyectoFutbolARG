"""Pestaña Copas · Supercopa Uruguaya (sólo cuando el país activo es Uruguay).

Partido único en cancha neutral entre el campeón de la Liga AUF y el ganador del Intermedio. Todo sale de
`copas.registro.SupercopaUruguaya`.
"""

import streamlit as st

from copas.registro import REGISTRO, SupercopaUruguaya
from datos.logos import logo_img
from ui.vista import aviso, chip, crest, esc, fila_partido_html, lista_equipos_html

COPA = next(c for c in REGISTRO if isinstance(c, SupercopaUruguaya))


def render(ctx):
    S, P = ctx.S, ctx.P
    tab = ctx.pestanas.tab_scuy
    if not ctx.abierta(ctx.pestanas.tab_copas, tab):
        return
    E = S[COPA.clave]
    riv = COPA.rivales(S)
    lista = COPA.pendiente(S) is not None
    with tab:
        c1, c2 = st.columns([4, 1.6], vertical_alignment="center")
        c1.markdown(logo_img(COPA.nombre, 30) + " " + chip(COPA.nombre, "#1e5aa8") + " "
                    + chip("Partido único · cancha neutral", "#475569"), unsafe_allow_html=True)
        if not ctx.modo_mgr and c2.button(":material/sports_soccer: Jugar la Supercopa", key="scuy_jugar", width="stretch",
                                          type="primary", disabled=not lista):
            COPA.jugar(S, P, S["rng"])
            st.rerun()
        if E["jugada"]:
            cc = E["campeon"]
            sub = E["b"] if cc == E["a"] else E["a"]
            st.markdown(f'<div class="champ"><div class="t">Campeón · {COPA.nombre} · Temporada {S["temp"]}</div>'
                        f'<div style="margin-top:10px">{crest(cc, 64)}</div><div class="nm">{esc(cc)}</div>'
                        f'<div class="s">finalista: {esc(sub)}</div></div>', unsafe_allow_html=True)
            st.markdown(fila_partido_html(S, ctx.club, E["log"][0], abierto=True), unsafe_allow_html=True)
        elif lista:
            st.markdown(lista_equipos_html([(riv[0], "Campeón de la Liga AUF"), (riv[1], "Ganador del Intermedio")]),
                        unsafe_allow_html=True)
        else:
            aviso("Se juega cuando termina la Liga AUF Uruguaya (campeón vs. ganador del Intermedio).")

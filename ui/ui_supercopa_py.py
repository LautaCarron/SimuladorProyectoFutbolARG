"""Pestaña Copas · Supercopa Paraguay (sólo cuando el país activo es Paraguay).

Partido único en cancha neutral entre el campeón de la Primera y el campeón de la Copa Paraguay (si es el mismo club, el
rival es el subcampeón de la Primera). Todo sale de `copas.registro.SupercopaParaguay`.
"""

import streamlit as st

from copas.registro import REGISTRO, SupercopaParaguay
from datos.logos import logo_img
from ui.vista import aviso, chip, crest, esc, fila_partido_html, lista_equipos_html

COPA = next(c for c in REGISTRO if isinstance(c, SupercopaParaguay))
COLOR = "#d52b1e"


def render(ctx):
    S, P = ctx.S, ctx.P
    tab = ctx.pestanas.tab_scpy
    if not ctx.abierta(ctx.pestanas.tab_copas, tab):
        return
    E = COPA.estado(S)
    riv = COPA.rivales(S)
    lista = COPA.pendiente(S) is not None
    with tab:
        c1, c2 = st.columns([4, 1.6], vertical_alignment="center")
        c1.markdown(logo_img(COPA.nombre, 30) + " " + chip(COPA.nombre, COLOR) + " "
                    + chip("Partido único · cancha neutral", "#475569"), unsafe_allow_html=True)
        if not ctx.modo_mgr and c2.button(":material/sports_soccer: Jugar la Supercopa", key="scpy_jugar", width="stretch",
                                          type="primary", disabled=not lista):
            COPA.jugar(S, P, S["rng"])
            st.rerun()
        if E["jugada"]:
            cc = E["campeon"]
            sub = E["b"] if cc == E["a"] else E["a"]
            st.markdown(f'<div class="fx-head">{crest(cc, 22)} {chip("Campeón · " + cc, COLOR)} '
                        f'{chip("Finalista · " + sub, "#475569")}</div>', unsafe_allow_html=True)
            st.markdown(fila_partido_html(S, ctx.club, E["log"][0], abierto=True), unsafe_allow_html=True)
        elif lista:
            rol = "Campeón de la Copa Paraguay" if COPA.rival_es_copero(S) else "Subcampeón de la Primera (ganó el doblete)"
            st.markdown(lista_equipos_html([(riv[0], "Campeón de la Primera"), (riv[1], rol)]), unsafe_allow_html=True)
        else:
            aviso("Se juega cuando terminan la Primera y la Copa Paraguay (campeón vs. campeón; si es el mismo club, "
                  "enfrenta al subcampeón de la Primera).")

"""Pestaña Copas · Supercopa de Colombia (sólo cuando el país activo es Colombia).

Serie a ida y vuelta entre el campeón de la Liga BetPlay y el campeón de la Copa Colombia (si es el mismo club, el rival es el
subcampeón de la liga). Todo sale de `copas.registro.SupercopaColombia`.
"""

import streamlit as st

from copas.registro import REGISTRO, SupercopaColombia
from datos.logos import logo_img
from ui.vista import aviso, chip, crest, fila_partido_html, lista_equipos_html

COPA = next(c for c in REGISTRO if isinstance(c, SupercopaColombia))
COLOR = "#e0b400"


def render(ctx):
    S, P = ctx.S, ctx.P
    tab = ctx.pestanas.tab_sco
    if not ctx.abierta(ctx.pestanas.tab_copas, tab):
        return
    E = COPA.estado(S)
    riv = COPA.rivales(S)
    pendiente = COPA.pendiente(S)
    with tab:
        c1, c2 = st.columns([4, 1.6], vertical_alignment="center")
        c1.markdown(logo_img(COPA.nombre, 30) + " " + chip(COPA.nombre, COLOR) + " "
                    + chip("Ida y vuelta · penales si empata el global", "#475569"), unsafe_allow_html=True)
        texto = "Jugar la vuelta" if E["fecha"] == 1 else "Jugar la ida"
        if not ctx.modo_mgr and c2.button(f":material/sports_soccer: {texto}", key="sco_jugar", width="stretch",
                                          type="primary", disabled=pendiente is None):
            COPA.jugar(S, P, S["rng"])
            st.rerun()
        if E["campeon"]:
            cc = E["campeon"]
            sub = E["b"] if cc == E["a"] else E["a"]
            ga, gb = E["global"]
            glob = f"Global {ga}-{gb}" if cc == E["a"] else f"Global {gb}-{ga}"
            st.markdown(f'<div class="fx-head">{crest(cc, 22)} {chip("Campeón · " + cc, COLOR)} '
                        f'{chip("Finalista · " + sub, "#475569")} {chip(glob, "#475569")}</div>', unsafe_allow_html=True)
        for p in E["log"]:
            st.markdown(fila_partido_html(S, ctx.club, p, abierto=True), unsafe_allow_html=True)
        if not E["campeon"] and riv and riv[1]:
            rol = "Campeón de la Copa Colombia" if COPA.rival_es_copero(S) else "Subcampeón de la liga (la ganó toda)"
            st.markdown(lista_equipos_html([(riv[0], "Campeón de la Liga BetPlay"), (riv[1], rol)]), unsafe_allow_html=True)
        elif not E["log"]:
            aviso("Se juega cuando terminan la Liga BetPlay y la Copa Colombia (campeón vs. campeón; si es el mismo club, "
                  "enfrenta al subcampeón de la liga).")

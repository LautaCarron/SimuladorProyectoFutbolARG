"""Pestaña Avisos.

El código es el de simuladorafa.py, movido acá tal cual. `ctx` trae el estado y los ayudantes
compartidos de la interfaz (S, P, las pestañas, las banderas terminada_*, etc.).
"""

import streamlit as st
from vista import aviso, avisos_html, seccion


def render(ctx):
    (S, _abierta, _avisos, _sin_leer, _total_avisos, tab_av) = (
        ctx.S, ctx._abierta, ctx._avisos, ctx._sin_leer, ctx._total_avisos, ctx.tab_av)
    # ============================================================================
    # AVISOS
    # ============================================================================
    if _abierta(tab_av):
        with tab_av:
            seccion("Avisos", "Partidos suspendidos y sanciones del Tribunal de Disciplina", "#b83a2e")
            if _sin_leer:
                c1, c2 = st.columns([3, 1.4], vertical_alignment="center")
                c1.markdown(f'<div class="aviso-banner">🚨 <span><b>{_sin_leer} aviso{"s" if _sin_leer > 1 else ""} '
                            f'nuevo{"s" if _sin_leer > 1 else ""}</b></span></div>', unsafe_allow_html=True)
                if c2.button(":material/done_all: Marcar como leídos", key="avisos_leidos_btn", width="stretch"):
                    S["avisos_leidos"] = _total_avisos
                    st.rerun()
            if _avisos:
                st.markdown(f'<div class="mlab" style="margin-top:8px">Temporada {S["temp"]}</div>', unsafe_allow_html=True)
                st.markdown(avisos_html(_avisos), unsafe_allow_html=True)
            else:
                aviso("Esta temporada, por ahora, no hubo partidos suspendidos ni sanciones.")
            if S.get("alertas_hist"):
                st.markdown('<div class="mlab" style="margin-top:18px">Temporadas anteriores</div>', unsafe_allow_html=True)
                st.markdown(avisos_html(S["alertas_hist"], con_temporada=True), unsafe_allow_html=True)

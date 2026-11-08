"""Pestaña Avisos.

El código es el de simuladorafa.py, movido acá tal cual. `ctx` trae el estado y los ayudantes
compartidos de la interfaz (S, P, las pestañas, las banderas terminada_*, etc.).
"""

import streamlit as st
from motor import incidentes
from motor.progreso import marcar_avisos_leidos
from ui.vista import aviso, avisos_html


def _cb_tribunal(S, clave):
    """Al mover el interruptor rige ya: apagado, los partidos que se jueguen no tienen incidentes ni sanciones."""
    S["tribunal_on"] = bool(st.session_state[clave])
    incidentes.fijar(S)
    st.toast("Tribunal de Disciplina " + ("activado." if S["tribunal_on"] else "desactivado."))


def render(ctx):
    (S, _abierta, _avisos, _sin_leer, _total_avisos, tab_av) = (
        ctx.S, ctx.abierta, ctx.avisos, ctx.sin_leer, ctx.total_avisos, ctx.pestanas.tab_av)
    # ============================================================================
    # AVISOS
    # ============================================================================
    if _abierta(tab_av):
        with tab_av:
            encendido = bool(S.get("tribunal_on", True))
            st.toggle("Tribunal de Disciplina", value=encendido, key=f"tribunal_on_{S['temp']}_{int(encendido)}",
                      on_change=_cb_tribunal, args=(S, f"tribunal_on_{S['temp']}_{int(encendido)}"),
                      help="Encendido, de vez en cuando hay partidos suspendidos y sanciones. Apagado, no se genera "
                           "ninguno nuevo (los que ya ocurrieron quedan en los avisos).")
            if _sin_leer:
                c1, c2 = st.columns([3, 1.4], vertical_alignment="center")
                c1.markdown(f'<div class="aviso-banner">🚨 <span><b>{_sin_leer} aviso{"s" if _sin_leer > 1 else ""} '
                            f'nuevo{"s" if _sin_leer > 1 else ""}</b></span></div>', unsafe_allow_html=True)
                if c2.button(":material/done_all: Marcar como leídos", key="avisos_leidos_btn", width="stretch"):
                    marcar_avisos_leidos(S, ctx.pais, _total_avisos)
                    st.rerun()
            if _avisos:
                st.markdown(f'<div class="mlab" style="margin-top:8px">Temporada {S["temp"]}</div>', unsafe_allow_html=True)
                st.markdown(avisos_html(S, _avisos), unsafe_allow_html=True)
            else:
                aviso("El Tribunal de Disciplina está desactivado: no habrá partidos suspendidos ni sanciones."
                      if not encendido else
                      "Esta temporada, por ahora, no hubo partidos suspendidos ni sanciones."
                      if ctx.es_base else f"Todavía no hay avisos de {ctx.pais}: el Tribunal de Disciplina "
                      "(suspensiones y sanciones) por ahora sólo funciona en Argentina.")
            if ctx.avisos_hist:
                st.markdown('<div class="mlab" style="margin-top:18px">Temporadas anteriores</div>', unsafe_allow_html=True)
                st.markdown(avisos_html(S, ctx.avisos_hist, con_temporada=True), unsafe_allow_html=True)

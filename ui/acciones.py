"""Botones globales de arriba: Próximo día, Simular todo, Nueva temporada y Reiniciar."""

import streamlit as st

from config import VOLATILIDAD
from motor.calendario import jugar_proximo_dia, texto_dia
from motor.simulacion import simular_todo
from motor.temporada import crear_estado, nueva_temporada


def render_acciones(S, P, progreso, modo_mgr, acumular, hoy):
    """`hoy`: próximo día con partidos (None si no queda nada por jugar)."""
    g0, gd, g1, g2, g3 = st.container(key="acciones").columns([1.6, 1.4, 1.3, 1.5, 1.1], vertical_alignment="center")
    if gd.button(":material/calendar_today: Próximo día", disabled=hoy is None, width="stretch",
                 help=f"Juega todo lo del {texto_dia(hoy)}" if hoy else None):
        jugar_proximo_dia(S, P, acumular)
        st.rerun()
    if g1.button(":material/fast_forward: Simular todo", disabled=progreso.todas, width="stretch", type="primary"):
        if modo_mgr:                                   # modo manager: día por día, con pausa en los eventos
            from ui.manager import simular_hasta_pausa
            simular_hasta_pausa(S, P, acumular)
        else:
            simular_todo(S, P, acumular)
        st.rerun()
    if g2.button(":material/event_repeat: Nueva temporada", disabled=not progreso.todas, width="stretch"):
        nueva_temporada(S, VOLATILIDAD)
        st.rerun()
    if g3.button(":material/restart_alt: Reiniciar", width="stretch"):
        st.session_state.S = crear_estado()      # partida nueva: el club propio desaparece (solo vive en la partida que lo creó)
        st.rerun()

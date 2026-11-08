"""País activo: el que se elige en la pestaña Mundo y el que muestran Ligas, Copas, Calendario, Historial y Avisos.

Vive en st.session_state (no en la partida `S`): es una preferencia de la pantalla, no se guarda en el `.afa`.
Sin elegir nada, el país es Argentina.
"""

import streamlit as st

from datos.paises import PAIS_BASE, validar

CLAVE = "afa_pais"


def pais_activo():
    return validar(st.session_state.get(CLAVE, PAIS_BASE))


def elegir_pais(pais):
    """Sirve como on_click de un botón: la pantalla se vuelve a dibujar sola con el país nuevo."""
    st.session_state[CLAVE] = validar(pais)

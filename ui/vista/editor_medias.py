"""Editor de las medias internas de los equipos."""

import numpy as np
import pandas as pd
import streamlit as st

from config import ES_WEB
from motor.nucleo import MAX_R, MIN_R


def editar_medias(nombres, r, clave):
    """Editor de medias internas. En la versión web (stlite, corre en el navegador) st.data_editor no
    funciona, así que ahí se edita club por club."""
    if not ES_WEB:
        ed = st.data_editor(pd.DataFrame({"Equipo": nombres, "Media": r}),
                            disabled=["Equipo"], hide_index=True, width="stretch", key=clave)
        return np.clip(ed["Media"].to_numpy(float), MIN_R, MAX_R)
    r = np.array(r, dtype=float)
    c1, c2 = st.columns([3, 2], vertical_alignment="bottom")
    i = c1.selectbox("Club", range(len(nombres)), format_func=lambda k: nombres[k], key=f"{clave}_club")
    r[i] = c2.number_input("Media", MIN_R, MAX_R, float(round(r[i], 1)), 0.5, key=f"{clave}_media_{i}")
    return r

"""Editor de las medias internas de los equipos."""

import unicodedata

import numpy as np
import pandas as pd
import streamlit as st

from config import ES_WEB
from motor.nucleo import MAX_R, MIN_R


def _norm(txt):
    """Minúsculas y sin tildes, para que 'velez' encuentre 'Vélez'."""
    t = unicodedata.normalize("NFD", str(txt))
    return "".join(c for c in t if unicodedata.category(c) != "Mn").lower().strip()


def _filtrar(nombres, consulta):
    """Posiciones de los nombres que contienen todas las palabras de la búsqueda."""
    palabras = _norm(consulta).split()
    if not palabras:
        return list(range(len(nombres)))
    return [i for i, n in enumerate(nombres) if all(p in _norm(n) for p in palabras)]


def editar_medias(nombres, r, clave):
    """Editor de medias internas con buscador. En la versión web (stlite, corre en el navegador)
    st.data_editor no funciona, así que ahí se edita club por club."""
    r = np.array(r, dtype=float)
    consulta = st.text_input("Buscar club", placeholder="Escribí parte del nombre…",
                             key=f"{clave}_buscar", label_visibility="collapsed",
                             icon=":material/search:")
    pos = _filtrar(nombres, consulta)
    if not pos:
        st.caption("Ningún club coincide con la búsqueda.")
        return r

    if not ES_WEB:
        df = pd.DataFrame({"Equipo": [nombres[i] for i in pos], "Media": r[pos]}, index=pos)
        # La key incluye la búsqueda: al cambiar el filtro el editor arranca limpio con los valores ya guardados.
        ed = st.data_editor(df, disabled=["Equipo"], hide_index=True, width="stretch",
                            key=f"{clave}_{_norm(consulta)}")
        r[ed.index.to_numpy()] = np.clip(ed["Media"].to_numpy(float), MIN_R, MAX_R)
        return r

    c1, c2 = st.columns([3, 2], vertical_alignment="bottom")
    i = c1.selectbox("Club", pos, format_func=lambda k: nombres[k], key=f"{clave}_club_{_norm(consulta)}")
    r[i] = c2.number_input("Media", MIN_R, MAX_R, float(round(r[i], 1)), 0.5, key=f"{clave}_media_{i}")
    return r

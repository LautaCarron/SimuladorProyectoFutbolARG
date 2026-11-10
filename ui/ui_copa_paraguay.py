"""Pestaña Copas · Copa Paraguay (sólo cuando el país activo es Paraguay).

Tiene tres partes: Llaves (de la tercera fase a la final), Fixture y resultados (por ronda, desde la primera fase) y Clubes (los 58
participantes, de qué categoría vienen y hasta dónde llegaron). El palmarés está en la pestaña Historial. Todo sale de la copa
(`copas.registro.CopaParaguay`) y de copas/paraguay.py; la copa se sortea al armar la temporada con los clubes de la Primera, la
Intermedia y las dos Primera B.
"""

import pandas as pd
import streamlit as st

from copas import paraguay as copa_py
from copas.registro import REGISTRO, CopaParaguay
from datos.logos import logo_img
from motor import consultas
from motor.calendario import texto_dia
from ui.vista import aviso, chip, cuadro_llaves_html, esc, render_fecha, seccion, tabla_html

COPA = next(c for c in REGISTRO if isinstance(c, CopaParaguay))
COLOR = "#d52b1e"


def _fixture(ctx, L):
    S = ctx.S
    rondas, jugadas = L["rondas"], L["fecha"]
    key = f"fx_sel_{COPA.clave}_{S['temp']}_{jugadas}"
    if key not in st.session_state:
        st.session_state[key] = max(1, min(jugadas + 1, len(rondas)))
    elegida = st.selectbox("Ronda", list(range(1, len(rondas) + 1)), key=key, label_visibility="collapsed",
                           format_func=lambda n: rondas[n - 1]["rotulo"] + (" · jugada" if n <= jugadas else " · por jugar"))
    estado = chip("Jugada", "#16a34a") if elegida <= jugadas else (
        chip("Próxima ronda", "#2f7fd0") if elegida == jugadas + 1 else chip("Por jugar", "#64748b"))
    st.markdown(f'<div class="fx-head">{estado}<span class="m-dia">{esc(texto_dia(rondas[elegida - 1]["dia"]))}</span></div>',
                unsafe_allow_html=True)
    partidos = consultas.partidos_de_calendario(S, COPA.nombre, elegida)
    if not partidos:
        st.info("Los cruces de esta ronda se conocen cuando termina la anterior.")
        return
    render_fecha(S, ctx.club, partidos, f"{COPA.clave}{S['temp']}_{elegida}")


def _llaves(L):
    """Cuadro de eliminación de izquierda a derecha: tercera fase, octavos, cuartos, semifinales, final y campeón."""
    seccion("Llaves · tercera fase a la final", color=COLOR)
    st.caption("Entran los 12 de Primera en la tercera fase. Las dos primeras fases (con las dos Primera B y la Intermedia) están "
               "en Fixture y resultados.")
    st.markdown(cuadro_llaves_html(copa_py.llaves(L, 2), L["campeon"], f"Campeón · {COPA.nombre}",
                                   copa_py.LIBERTADORES, alto_por_cruce=72), unsafe_allow_html=True)


def _clubes(S, L):
    filas = copa_py.participantes(L)
    c1, c2 = st.columns(2)
    origen = c1.selectbox("Categoría", ["Todas", *copa_py.ORIGENES], key=f"cpy_origen_{S['temp']}")
    hasta = c2.selectbox("Hasta", ["Todas", *copa_py.NOMBRES_FASES, "Campeón"], key=f"cpy_hasta_{S['temp']}")
    filas = [x for x in filas if origen in ("Todas", x["Origen"]) and hasta in ("Todas", x["Hasta"])]
    df = pd.DataFrame(filas).rename(columns={"Club": "Equipo"})
    df.insert(0, "Pos", range(1, len(df) + 1))
    st.markdown(tabla_html(df[["Pos", "Equipo", "Origen", "Media", "Hasta"]], formatos={"Media": "{:.1f}"}),
                unsafe_allow_html=True)


def render(ctx):
    S, P = ctx.S, ctx.P
    tab = ctx.pestanas.tab_cpy
    if not ctx.abierta(ctx.pestanas.tab_copas, tab):
        return
    L = S[COPA.clave]
    with tab:
        c1, c2, c3 = st.columns([3, 1.4, 1.4], vertical_alignment="center")
        c1.markdown(logo_img(COPA.nombre, 30) + " " + chip(f"{COPA.nombre} · {len(L['nombres']) or 58} equipos", COLOR) + " "
                    + chip("Partido único · penales si empatan", "#475569") + " " + chip(copa_py.en_juego(L), "#475569"),
                    unsafe_allow_html=True)
        if not ctx.modo_mgr and c2.button(":material/skip_next: Próxima ronda", key="cpy_next", width="stretch",
                                          type="primary", disabled=COPA.pendiente(S) is None):
            COPA.jugar(S, P, S["rng"])
            st.rerun()
        if not ctx.modo_mgr and c3.button(":material/fast_forward: Hasta el final", key="cpy_all", width="stretch",
                                          disabled=COPA.pendiente(S) is None):
            COPA.jugar_todo(S, P, S["rng"])
            st.rerun()
        if not L["sorteada"]:
            aviso("La copa no se pudo sortear: hacen falta 12 clubes en la Primera, 16 en la Intermedia y entre 25 y 48 entre las dos Primera B.")
            return
        sub = st.tabs(["Llaves", "Fixture y resultados", "Clubes"])
        with sub[0]:
            _llaves(L)
        with sub[1]:
            _fixture(ctx, L)
        with sub[2]:
            _clubes(S, L)

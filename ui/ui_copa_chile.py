"""Pestaña Copas · Copa Chile (sólo cuando el país activo es Chile).

Tiene cuatro partes: Grupos (las ocho tablas de cuatro), Llaves (octavos a la final), Fixture y resultados (por ronda),
Clubes (los 32 participantes, su grupo y hasta dónde llegaron). El palmarés está en la pestaña Historial. Todo sale de la copa (`copas.registro.CopaChile`) y de copas/chile.py; la copa se sortea al armar la temporada
con los clubes de la Liga de Primera y de la Primera B.
"""

import pandas as pd
import streamlit as st

from copas import chile as copa_cl
from copas.registro import REGISTRO, CopaChile
from datos.logos import logo_img
from motor import consultas
from motor.calendario import texto_dia
from ui.vista import aviso, chip, cuadro_llaves_cruces_html, esc, render_fecha, seccion, tabla_html

COPA = next(c for c in REGISTRO if isinstance(c, CopaChile))
COLOR = "#c0392b"


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
        st.info("Los cruces de esta ronda se conocen cuando termina la fase anterior.")
        return
    render_fecha(S, ctx.club, partidos, f"{COPA.clave}{S['temp']}_{elegida}")


def _grupos(L):
    """Las ocho tablas: los dos primeros de cada grupo pasan a octavos (se marcan cuando terminan las seis fechas)."""
    seccion("Fase de grupos · los 2 primeros pasan a octavos", color=COLOR)
    terminados = L["fecha"] >= copa_cl.N_RONDAS_GRUPOS
    for zona, desde in (("Zona Norte", 0), ("Zona Sur", 4)):
        st.markdown(f"**{zona}**")
        cols = st.columns(2)
        for k, (letra, df) in enumerate(copa_cl.tablas_grupos(L)[desde:desde + 4]):
            df = df[["Pos", "Equipo", "PJ", "G", "E", "P", "GF", "GC", "DG", "Pts"]]
            estilo = (lambda fila: ["background-color: rgba(22,163,74,.16)" if terminados and fila["Pos"] <= 2 else ""] * len(fila))
            with cols[k % 2]:
                st.markdown(f"{chip('Grupo ' + letra, COLOR)}", unsafe_allow_html=True)
                st.markdown(tabla_html(df, estilo=estilo), unsafe_allow_html=True)


def _llaves(L):
    seccion("Llaves · octavos a la final", color=COLOR)
    st.markdown(cuadro_llaves_cruces_html(copa_cl.llaves(L), L["campeon"], f"Campeón · {COPA.nombre}",
                                          copa_cl.LIBERTADORES_PREVIA, alto_por_cruce=92), unsafe_allow_html=True)


def _clubes(S, L):
    filas = copa_cl.participantes(L)
    c1, c2 = st.columns(2)
    origen = c1.selectbox("Origen", ["Todos", "Primera", "Primera B"], key=f"ccl_origen_{S['temp']}")
    grupo = c2.selectbox("Grupo", ["Todos", *copa_cl.LETRAS], key=f"ccl_grupo_{S['temp']}")
    filas = [x for x in filas if origen in ("Todos", x["Origen"]) and grupo in ("Todos", x["Grupo"])]
    df = pd.DataFrame(filas).rename(columns={"Club": "Equipo"})
    df.insert(0, "Pos", range(1, len(df) + 1))
    st.markdown(tabla_html(df[["Pos", "Equipo", "Origen", "Grupo", "Media", "Hasta"]], formatos={"Media": "{:.1f}"}),
                unsafe_allow_html=True)


def render(ctx):
    S, P = ctx.S, ctx.P
    tab = ctx.pestanas.tab_ccl
    if not ctx.abierta(ctx.pestanas.tab_copas, tab):
        return
    L = S[COPA.clave]
    with tab:
        c1, c2, c3 = st.columns([3, 1.4, 1.4], vertical_alignment="center")
        c1.markdown(logo_img(COPA.nombre, 30) + " " + chip(f"{COPA.nombre} · 32 equipos", COLOR) + " "
                    + chip(copa_cl.en_juego(L), "#475569"), unsafe_allow_html=True)
        if not ctx.modo_mgr and c2.button(":material/skip_next: Próxima ronda", key="ccl_next", width="stretch",
                                          type="primary", disabled=COPA.pendiente(S) is None):
            COPA.jugar(S, P, S["rng"])
            st.rerun()
        if not ctx.modo_mgr and c3.button(":material/fast_forward: Hasta el final", key="ccl_all", width="stretch",
                                          disabled=COPA.pendiente(S) is None):
            COPA.jugar_todo(S, P, S["rng"])
            st.rerun()
        if not L["sorteada"]:
            aviso("La copa no se pudo sortear: hacen falta 16 clubes en la Liga de Primera y 16 en la Primera B.")
            return
        sub_tabs = st.tabs(["Grupos", "Llaves", "Fixture y resultados", "Clubes"])
        with sub_tabs[0]:
            _grupos(L)
        with sub_tabs[1]:
            _llaves(L)
        with sub_tabs[2]:
            _fixture(ctx, L)
        with sub_tabs[3]:
            _clubes(S, L)

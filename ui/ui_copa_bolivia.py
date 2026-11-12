"""Pestaña Copas · Copa Bolivia (sólo cuando el país activo es Bolivia).

Tiene cuatro partes: Grupos (las cuatro series de cuatro), Llaves (cuartos, semifinales y final a ida y vuelta), Fixture y
resultados (por ronda) y Clubes (los 16 participantes, su serie y hasta dónde llegaron). El palmarés está en la pestaña
Historial. Todo sale de la copa (`copas.registro.CopaBolivia`) y de copas/bolivia.py; el sorteo se realiza al armar la
temporada con los 16 clubes de la División Profesional.
"""

import pandas as pd
import streamlit as st

from copas import bolivia as copa_bo
from copas.registro import REGISTRO, CopaBolivia
from datos.logos import logo_img
from motor import consultas
from motor.calendario import texto_dia
from ui.vista import aviso, chip, cuadro_llaves_cruces_html, esc, render_fecha, seccion, tabla_html

COPA = next(c for c in REGISTRO if isinstance(c, CopaBolivia))
COLOR = "#0a8f3c"


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
    """Las cuatro series: los dos primeros de cada una pasan a cuartos (se marcan cuando terminan las cuatro fechas)."""
    seccion("Fase de grupos · los 2 primeros de cada serie pasan a cuartos", color=COLOR)
    terminados = L["fecha"] >= copa_bo.N_RONDAS_GRUPOS
    cols = st.columns(2)
    for k, (letra, df) in enumerate(copa_bo.tablas_grupos(L)):
        df = df[["Pos", "Equipo", "PJ", "G", "E", "P", "GF", "GC", "DG", "Pts"]]
        estilo = (lambda fila: ["background-color: rgba(22,163,74,.16)" if terminados and fila["Pos"] <= 2 else ""] * len(fila))
        with cols[k % 2]:
            st.markdown(f"{chip('Serie ' + letra, COLOR)}", unsafe_allow_html=True)
            st.markdown(tabla_html(df, estilo=estilo), unsafe_allow_html=True)
    st.caption("Cada club juega tres partidos de su serie y un clásico interserie (la A con la B y la C con la D); todo suma para la tabla.")


def _llaves(L):
    seccion("Llaves · cuartos de final a la final (ida y vuelta)", color=COLOR)
    st.markdown(cuadro_llaves_cruces_html(copa_bo.llaves(L), L["campeon"], f"Campeón · {COPA.nombre}",
                                          copa_bo.CUPO, alto_por_cruce=92), unsafe_allow_html=True)


def _clubes(S, L):
    filas = copa_bo.participantes(L)
    serie = st.selectbox("Serie", ["Todas", *[f"Serie {x}" for x in copa_bo.LETRAS]], key=f"cbo_serie_{S['temp']}")
    if serie != "Todas":
        filas = [x for x in filas if x["Grupo"] == serie[-1]]
    df = pd.DataFrame(filas).rename(columns={"Club": "Equipo", "Grupo": "Serie"})
    df.insert(0, "Pos", range(1, len(df) + 1))
    st.markdown(tabla_html(df[["Pos", "Equipo", "Serie", "Media", "Hasta"]], formatos={"Media": "{:.1f}"}), unsafe_allow_html=True)


def render(ctx):
    S, P = ctx.S, ctx.P
    tab = ctx.pestanas.tab_cbo
    if not ctx.abierta(ctx.pestanas.tab_copas, tab):
        return
    L = S[COPA.clave]
    with tab:
        c1, c2, c3 = st.columns([3, 1.4, 1.4], vertical_alignment="center")
        c1.markdown(logo_img(COPA.nombre, 30) + " " + chip(f"{COPA.nombre} · 16 equipos", COLOR) + " "
                    + chip(copa_bo.en_juego(L), "#475569"), unsafe_allow_html=True)
        if not ctx.modo_mgr and c2.button(":material/skip_next: Próxima ronda", key="cbo_next", width="stretch",
                                          type="primary", disabled=COPA.pendiente(S) is None):
            COPA.jugar(S, P, S["rng"])
            st.rerun()
        if not ctx.modo_mgr and c3.button(":material/fast_forward: Hasta el final", key="cbo_all", width="stretch",
                                          disabled=COPA.pendiente(S) is None):
            COPA.jugar_todo(S, P, S["rng"])
            st.rerun()
        if not L["sorteada"]:
            aviso("La Copa Bolivia necesita los 16 clubes de la División Profesional.")
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

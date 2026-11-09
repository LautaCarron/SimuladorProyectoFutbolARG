"""Pestaña Copas · Copa Colombia (sólo cuando el país activo es Colombia).

Tiene cuatro partes: Grupos (las cuatro tablas de cinco de la fase 1A), Llaves (la fase 1B, a la izquierda, y de octavos a la final),
Fixture y resultados (por ronda) y Clubes (los 36 participantes, su grupo y hasta dónde llegaron). El palmarés está en la pestaña
Historial. Todo sale de la copa (`copas.registro.CopaColombia`) y de copas/colombia.py; el sorteo se realiza cuando terminan las fases
clasificatorias del primer semestre de la Liga BetPlay y el Torneo BetPlay.
"""

import pandas as pd
import streamlit as st

from copas import colombia as copa_co
from copas.registro import REGISTRO, CopaColombia
from datos.logos import logo_img
from motor import consultas
from motor.calendario import texto_dia
from ui.vista import aviso, chip, cuadro_llaves_cruces_html, esc, render_fecha, seccion, tabla_html

COPA = next(c for c in REGISTRO if isinstance(c, CopaColombia))
COLOR = "#d4a017"


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
    """Las cuatro tablas de la fase 1A: los dos primeros de cada grupo pasan a octavos (se marcan cuando terminan las cinco fechas)."""
    seccion("Fase 1A · los 2 primeros de cada grupo pasan a octavos", color=COLOR)
    terminados = L["fecha"] >= copa_co.N_RONDAS_GRUPOS
    cols = st.columns(2)
    for k, (letra, df) in enumerate(copa_co.tablas_grupos(L)):
        df = df[["Pos", "Equipo", "PJ", "G", "E", "P", "GF", "GC", "DG", "Pts"]]
        estilo = (lambda fila: ["background-color: rgba(22,163,74,.16)" if terminados and fila["Pos"] <= 2 else ""] * len(fila))
        with cols[k % 2]:
            st.markdown(f"{chip('Grupo ' + letra, COLOR)}", unsafe_allow_html=True)
            st.markdown(tabla_html(df, estilo=estilo), unsafe_allow_html=True)
    st.caption("Fase 1B: los ocho primeros del Apertura de Primera y los ocho clasificados a cuadrangulares del Torneo BetPlay I.")


def _llaves(L):
    seccion("Llaves · fase 1B y octavos a la final", color=COLOR)
    previas = [(copa_co.NOMBRES_KO[copa_co.I_SERIES], copa_co.cruces_de_fase(L, copa_co.I_SERIES))]
    st.markdown(cuadro_llaves_cruces_html(copa_co.llaves(L), L["campeon"], f"Campeón · {COPA.nombre}",
                                          copa_co.SUDAMERICANA, alto_por_cruce=92, previas=previas), unsafe_allow_html=True)


def _clubes(S, L):
    filas = copa_co.participantes(L)
    c1, c2 = st.columns(2)
    origen = c1.selectbox("Origen", ["Todos", "Liga BetPlay", "Torneo BetPlay"], key=f"cco_origen_{S['temp']}")
    entra = c2.selectbox("Entra en", ["Todas", "Fase de grupos", "Fase 1B"], key=f"cco_entra_{S['temp']}")
    filas = [x for x in filas if origen in ("Todos", x["Origen"]) and entra in ("Todas", x["Entra en"])]
    df = pd.DataFrame(filas).rename(columns={"Club": "Equipo"})
    df.insert(0, "Pos", range(1, len(df) + 1))
    st.markdown(tabla_html(df[["Pos", "Equipo", "Origen", "Entra en", "Grupo", "Media", "Hasta"]], formatos={"Media": "{:.1f}"}),
                unsafe_allow_html=True)


def render(ctx):
    S, P = ctx.S, ctx.P
    tab = ctx.pestanas.tab_cco
    if not ctx.abierta(ctx.pestanas.tab_copas, tab):
        return
    L = S[COPA.clave]
    COPA.activa(S)  # intenta sortearla cuando ya están definidas las clasificaciones del primer semestre
    with tab:
        c1, c2, c3 = st.columns([3, 1.4, 1.4], vertical_alignment="center")
        c1.markdown(logo_img(COPA.nombre, 30) + " " + chip(f"{COPA.nombre} · 36 equipos", COLOR) + " "
                    + chip(copa_co.en_juego(L), "#475569"), unsafe_allow_html=True)
        if not ctx.modo_mgr and c2.button(":material/skip_next: Próxima ronda", key="cco_next", width="stretch",
                                          type="primary", disabled=COPA.pendiente(S) is None):
            COPA.jugar(S, P, S["rng"])
            st.rerun()
        if not ctx.modo_mgr and c3.button(":material/fast_forward: Hasta el final", key="cco_all", width="stretch",
                                          disabled=COPA.pendiente(S) is None):
            COPA.jugar_todo(S, P, S["rng"])
            st.rerun()
        if not L["sorteada"]:
            L1, L2 = S.get(COPA.LIGA_1), S.get(COPA.LIGA_2)
            if L1 and L2:
                aviso("La Copa Colombia se sorteará cuando terminen el Apertura de la Liga BetPlay y el Torneo BetPlay I. "
                      "Los ocho clasificados de cada división entrarán a la Fase 1B; los demás jugarán la Fase 1A.")
            else:
                aviso("La Copa Colombia necesita los 20 clubes de la Liga BetPlay y los 16 del Torneo BetPlay.")
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

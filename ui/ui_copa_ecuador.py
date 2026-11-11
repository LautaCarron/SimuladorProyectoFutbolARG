"""Pestaña Copas · Copa Ecuador.

Tiene tres partes: Llaves (las fases previas a la izquierda de los octavos y el cuadro de octavos a la final), Fixture y
resultados (por ronda) y Clubes (los 76 participantes, en qué fase entraron y hasta dónde llegaron). Todo sale de la copa
(`copas.registro.CopaEcuador`) y de copas/ecuador.py.
"""
import pandas as pd
import streamlit as st

from copas import ecuador as copa_ec
from copas.registro import REGISTRO, CopaEcuador
from datos.logos import logo_img
from motor import consultas
from motor.calendario import texto_dia
from ui.vista import aviso, chip, cuadro_llaves_cruces_html, esc, render_fecha, seccion, tabla_html

COPA = next(c for c in REGISTRO if isinstance(c, CopaEcuador))
COLOR = "#f0c400"


def _fixture(ctx, L):
    S = ctx.S
    rondas, jugadas = L["rondas"], L["fecha"]
    key = f"fx_sel_{COPA.clave}_{S['temp']}_{jugadas}"
    if key not in st.session_state:
        st.session_state[key] = max(1, min(jugadas + 1, len(rondas)))
    elegida = st.selectbox("Ronda", list(range(1, len(rondas) + 1)), key=key, label_visibility="collapsed",
                           format_func=lambda n: rondas[n - 1]["rotulo"] +
                           (" · jugada" if n <= jugadas else " · por jugar"))
    estado = chip("Jugada", "#16a34a") if elegida <= jugadas else (
        chip("Próxima ronda", "#2f7fd0") if elegida == jugadas + 1 else chip("Por jugar", "#64748b"))
    st.markdown(f'<div class="fx-head">{estado}<span class="m-dia">{esc(texto_dia(rondas[elegida - 1]["dia"]))}</span></div>',
                unsafe_allow_html=True)
    partidos = consultas.partidos_de_calendario(S, COPA.nombre, elegida)
    if partidos:
        render_fecha(S, ctx.club, partidos, f"{COPA.clave}{S['temp']}_{elegida}")
    else:
        st.info("Los cruces de esta ronda se conocen cuando termina la anterior.")


def _llaves(L):
    """Cuadro completo de izquierda a derecha: preliminar, treintaidosavos y dieciseisavos (columnas sin líneas porque el
    sorteo es libre), octavos, cuartos, semifinales, final y campeón."""
    seccion("Llaves · fase preliminar a la final", color=COLOR)
    previas = [(copa_ec.ETAPAS[f][0], copa_ec.cruces_de_fase(L, f)) for f in range(copa_ec.I_OCTAVOS)]
    sub = "Libertadores · Fase 1" if L.get("campeon") and L["origen"][L["nombres"].index(L["campeon"])] == "Serie A" else ""
    st.markdown(cuadro_llaves_cruces_html(copa_ec.llaves(L), L["campeon"], f"Campeón · {COPA.nombre}", sub,
                                          alto_por_cruce=92, previas=previas), unsafe_allow_html=True)


def _clubes(S, L):
    filas = copa_ec.participantes(L)
    c1, c2 = st.columns(2)
    origen = c1.selectbox("Origen", ["Todos", "Serie A", "Serie B", "Segunda Categoría"], key=f"cec_origen_{S['temp']}")
    entra = c2.selectbox("Entra en", ["Todas", *copa_ec.NOMBRES_FASES[:2]], key=f"cec_entra_{S['temp']}")
    filas = [x for x in filas if origen in ("Todos", x["Origen"]) and entra in ("Todas", x["Entra en"])]
    df = pd.DataFrame(filas).rename(columns={"Club": "Equipo"})
    df.insert(0, "Pos", range(1, len(df) + 1))
    st.markdown(tabla_html(df[["Pos", "Equipo", "Origen", "Entra en", "Media", "Hasta"]], formatos={"Media": "{:.1f}"}),
                unsafe_allow_html=True)


def render(ctx):
    S, P = ctx.S, ctx.P
    tab = ctx.pestanas.tab_cec
    if not ctx.abierta(ctx.pestanas.tab_copas, tab):
        return
    L = S[COPA.clave]
    with tab:
        c1, c2, c3 = st.columns([3, 1.4, 1.4], vertical_alignment="center")
        c1.markdown(logo_img(COPA.nombre, 30) + " " + chip(f"{COPA.nombre} · 76 equipos", COLOR) + " " +
                    chip(copa_ec.en_juego(L), "#475569"), unsafe_allow_html=True)
        if not ctx.modo_mgr and c2.button(":material/skip_next: Próxima ronda", key="cec_next",
                                          width="stretch", type="primary", disabled=COPA.pendiente(S) is None):
            COPA.jugar(S, P, S["rng"])
            st.rerun()
        if not ctx.modo_mgr and c3.button(":material/fast_forward: Hasta el final", key="cec_all",
                                          width="stretch", disabled=COPA.pendiente(S) is None):
            COPA.jugar_todo(S, P, S["rng"])
            st.rerun()
        if not L["sorteada"]:
            aviso("La Copa Ecuador se sortea con los clubes de Serie A, Serie B y Segunda Categoría.")
            return
        if L.get("campeon"):
            st.markdown(f'<div class="fx-head">{chip("Campeón · " + L["campeon"], COLOR)} '
                        f'{chip("Subcampeón · " + str(L.get("subcampeon") or "—"), "#475569")}</div>',
                        unsafe_allow_html=True)
        sub_tabs = st.tabs(["Llaves", "Fixture y resultados", "Clubes"])
        with sub_tabs[0]:
            _llaves(L)
        with sub_tabs[1]:
            _fixture(ctx, L)
        with sub_tabs[2]:
            _clubes(S, L)

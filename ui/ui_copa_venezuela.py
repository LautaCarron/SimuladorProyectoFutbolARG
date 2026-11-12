"""Pestaña Copas · Copa Venezuela (sólo cuando el país activo es Venezuela).

Tiene cuatro partes: Grupos (las cinco tablas de cuatro), Llaves (octavos a la final), Fixture y resultados (por ronda) y Clubes
(los 28 participantes, su grupo y hasta dónde llegaron). El palmarés está en la pestaña Historial. Todo sale de la copa
(`copas.registro.CopaVenezuela`) y de copas/venezuela.py; el sorteo se realiza al armar la temporada con los clubes de la
Liga FUTVE y de la Liga FUTVE 2.
"""

import pandas as pd
import streamlit as st

from copas import venezuela as copa_ve
from copas.registro import REGISTRO, CopaVenezuela
from datos.logos import logo_img
from motor import consultas
from motor.calendario import texto_dia
from ui.vista import aviso, chip, cuadro_llaves_cruces_html, esc, render_fecha, seccion, tabla_html

COPA = next(c for c in REGISTRO if isinstance(c, CopaVenezuela))
COLOR = "#b8860b"


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
    """Las cinco tablas: los primeros y los tres mejores segundos pasan a octavos (se marcan cuando terminan las seis fechas)."""
    seccion("Fase de grupos · pasan los 5 primeros y los 3 mejores segundos", color=COLOR)
    terminados = L["fecha"] >= copa_ve.N_RONDAS_GRUPOS
    pasan_segundo = {f["grupo"]: f["pasa_segundo"] for f in L["clasificados"]} if terminados else {}
    cols = st.columns(2)
    for k, (letra, df) in enumerate(copa_ve.tablas_grupos(L)):
        df = df[["Pos", "Equipo", "PJ", "G", "E", "P", "GF", "GC", "DG", "Pts"]]
        segundo_pasa = pasan_segundo.get(letra, False)

        def estilo(fila, segundo_pasa=segundo_pasa):
            pasa = terminados and (fila["Pos"] == 1 or (fila["Pos"] == 2 and segundo_pasa))
            return ["background-color: rgba(22,163,74,.16)" if pasa else ""] * len(fila)
        with cols[k % 2]:
            st.markdown(f"{chip('Grupo ' + letra, COLOR)}", unsafe_allow_html=True)
            st.markdown(tabla_html(df, estilo=estilo), unsafe_allow_html=True)
    st.caption("Ocho clubes de Primera entran directo a octavos (los de mayor media); los otros seis juegan los grupos "
               "junto con los 14 de la Liga FUTVE 2.")


def _llaves(L):
    seccion("Llaves · octavos de final a la final", color=COLOR)
    st.markdown(cuadro_llaves_cruces_html(copa_ve.llaves(L), L["campeon"], f"Campeón · {COPA.nombre}",
                                          copa_ve.CUPO, alto_por_cruce=92), unsafe_allow_html=True)
    st.caption("Octavos a partido único (de local el que entró directo); cuartos, semifinales y final a ida y vuelta.")


def _clubes(S, L):
    filas = copa_ve.participantes(L)
    c1, c2 = st.columns(2)
    origen = c1.selectbox("Origen", ["Todos", copa_ve.LIGA_1, copa_ve.LIGA_2], key=f"cve_origen_{S['temp']}")
    entra = c2.selectbox("Entra en", ["Todas", "Fase de grupos", "Octavos de final"], key=f"cve_entra_{S['temp']}")
    filas = [x for x in filas if origen in ("Todos", x["Origen"]) and entra in ("Todas", x["Entra en"])]
    df = pd.DataFrame(filas).rename(columns={"Club": "Equipo"})
    df.insert(0, "Pos", range(1, len(df) + 1))
    st.markdown(tabla_html(df[["Pos", "Equipo", "Origen", "Entra en", "Grupo", "Media", "Hasta"]], formatos={"Media": "{:.1f}"}),
                unsafe_allow_html=True)


def render(ctx):
    S, P = ctx.S, ctx.P
    tab = ctx.pestanas.tab_cve
    if not ctx.abierta(ctx.pestanas.tab_copas, tab):
        return
    L = S[COPA.clave]
    with tab:
        c1, c2, c3 = st.columns([3, 1.4, 1.4], vertical_alignment="center")
        c1.markdown(logo_img(COPA.nombre, 30) + " " + chip(f"{COPA.nombre} · 28 equipos", COLOR) + " "
                    + chip(copa_ve.en_juego(L), "#475569"), unsafe_allow_html=True)
        if not ctx.modo_mgr and c2.button(":material/skip_next: Próxima ronda", key="cve_next", width="stretch",
                                          type="primary", disabled=COPA.pendiente(S) is None):
            COPA.jugar(S, P, S["rng"])
            st.rerun()
        if not ctx.modo_mgr and c3.button(":material/fast_forward: Hasta el final", key="cve_all", width="stretch",
                                          disabled=COPA.pendiente(S) is None):
            COPA.jugar_todo(S, P, S["rng"])
            st.rerun()
        if not L["sorteada"]:
            aviso("La Copa Venezuela necesita los 14 clubes de la Liga FUTVE y los 14 de la Liga FUTVE 2.")
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

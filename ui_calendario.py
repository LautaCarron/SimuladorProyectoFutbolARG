"""Pestaña Calendario.

El código es el de simuladorafa.py, movido acá tal cual. `ctx` trae el estado y los ayudantes
compartidos de la interfaz (S, P, las pestañas, las banderas terminada_*, etc.).
"""

import streamlit as st
from calendario import anio, jugar_proximo_dia, nombre_mes, texto_dia
from logos import logo_img
from vista import calendario_mes_html, esc, eventos_calendario, seccion


def render(ctx):
    (P, S, _abierta, _hoy, _prox, acumular, tab_cal) = (
        ctx.P, ctx.S, ctx._abierta, ctx._hoy, ctx._prox, ctx.acumular, ctx.tab_cal)
    # ============================================================================
    # CALENDARIO
    # ============================================================================
    if _abierta(tab_cal):
        with tab_cal:
            seccion(f"Calendario {anio(S)}", "Cuándo se juega cada fecha de cada liga y cada ronda de la Copa "
                    "Argentina (los miércoles, en el medio de las ligas)", "#1e5aa8")
            c1, c2 = st.columns([3, 1.4], vertical_alignment="center")
            c1.markdown((f'Próximo día: <b>{esc(texto_dia(_hoy))}</b> · ' + " ".join(
                logo_img(c, 18) for c, (d, _) in _prox.items() if d == _hoy)) if _hoy else
                "Terminó la temporada: pasá a la siguiente desde <b>Nueva temporada</b>.", unsafe_allow_html=True)
            if c2.button(":material/calendar_today: Jugar ese día", key="cal_next", width="stretch", type="primary",
                         disabled=_hoy is None):
                jugar_proximo_dia(S, P, acumular)
                st.rerun()
            eventos = eventos_calendario(S)
            meses = sorted({d.month for d, *_ in eventos})
            mes_def = (_hoy or eventos[-1][0]).month
            clave_mes = f"cal_mes_{S['temp']}"
            # el mes elegido sigue al próximo día (cuando avanza el calendario, se mueve solo)
            if st.session_state.get(f"{clave_mes}_sigue") != mes_def or clave_mes not in st.session_state:
                st.session_state[clave_mes] = mes_def if mes_def in meses else meses[0]
                st.session_state[f"{clave_mes}_sigue"] = mes_def
            mes = st.segmented_control("Mes", meses, format_func=lambda m: nombre_mes(m)[:3], key=clave_mes,
                                       label_visibility="collapsed") or mes_def
            st.markdown(calendario_mes_html(S, eventos, mes, _hoy), unsafe_allow_html=True)
            st.caption("Tocá cada competición para ver sus partidos. ⚠ = partido con incidente (ver Avisos).")

"""Pestaña Copas · Copa Argentina.

El código es el de simuladorafa.py, movido acá tal cual. `ctx` trae el estado y los ayudantes
compartidos de la interfaz (S, P, las pestañas, las banderas terminada_*, etc.).
"""

import numpy as np
import pandas as pd
import streamlit as st
from copas.argentina import COPA_LLAVES, COPA_RONDAS, clasificados_inicial, cupos_copa, simular_ronda_copa
from datos.logos import logo_img
from ui.vista import (
    aviso,
    chip,
    crest,
    cuadro_final_copa_html,
    cuadro_llave_html,
    esc,
    fila_partido_html,
    seccion,
    tabla_html,
)


def _tabla_cupos(lista):
    """Tabla de cupos de la Copa: se arma con los clasificados reales, así que cambia si cambian los cupos."""
    filas, (total, total_def) = cupos_copa(lista)
    df = pd.DataFrame(filas + [("Total", "", total, total_def)],
                      columns=["Liga", "Clasifican", "Cupos", "Por defecto"])
    st.markdown(tabla_html(df, clubes=()), unsafe_allow_html=True)
    if any(c != d for _, _, c, d in filas) or total != total_def:
        st.caption("Los cupos de esta temporada no son los de siempre (por ejemplo, porque se cambió la cantidad de "
                   "equipos de Primera o de la B en el Modo dios).")
    else:
        st.caption("Si se cambia la cantidad de equipos de las ligas, esta tabla se actualiza.")


def render(ctx):
    (P, S, SC, _abierta, pct_copa, tab_ca, tab_copas, terminada, terminada_b, terminada_copa,
     terminada_f, terminada_pb, terminada_pc, terminada_reg) = (
        ctx.P, ctx.S, ctx.SC, ctx.abierta, ctx.progreso.pct_copa, ctx.pestanas.tab_ca, ctx.pestanas.tab_copas, ctx.progreso.terminada,
        ctx.progreso.terminada_b, ctx.progreso.terminada_copa, ctx.progreso.terminada_f, ctx.progreso.terminada_pb,
        ctx.progreso.terminada_pc, ctx.progreso.terminada_reg)
    # ============================================================================
    # COPA ARGENTINA
    # ============================================================================
    if _abierta(tab_copas, tab_ca):
        with tab_ca:
            c1, c2, c3 = st.columns([3, 1.4, 1.4], vertical_alignment="center")
            c1.markdown(logo_img("Copa Argentina", 30) + " " + chip("Copa Argentina · 128 equipos", "#1e5aa8") + " "
                        + chip("Partido único · cancha neutral", "#475569"), unsafe_allow_html=True)
            if c2.button(":material/skip_next: Próxima ronda", key="ca_next", width="stretch", type="primary",
                         disabled=not SC["sorteada"] or terminada_copa):
                simular_ronda_copa(SC, P, S["rng"])
                st.rerun()
            if c3.button(":material/fast_forward: Hasta el final", key="ca_all", width="stretch",
                         disabled=not SC["sorteada"] or terminada_copa):
                while SC["ronda"] < SC["total"]:
                    simular_ronda_copa(SC, P, S["rng"])
                st.rerun()
            ronda_txt = ("Sin sortear" if not SC["sorteada"] else "Terminada" if terminada_copa
                         else COPA_RONDAS[SC["ronda"]])

            if not SC["sorteada"]:
                seccion("Copa Argentina", "128 equipos · desde 64avos de final · partido único en cancha "
                        "neutral, penales si empatan", "#1e5aa8")
                aviso("La Copa se sortea al empezar la temporada.")
                _tabla_cupos(S.get("copa_clasif") or clasificados_inicial(S))
                pendientes = [n for n, t in (("Primera", terminada), ("B Nacional", terminada_b),
                                             ("Federal A", terminada_f), ("Federal B", ctx.progreso.terminada_fb),
                                             ("Primera B", terminada_pb),
                                             ("Primera C", terminada_pc), ("Regional", terminada_reg)) if not t]
                st.caption("Faltan terminar: " + ", ".join(pendientes))
            else:
                titulos_ca = ["Cuadro", "Partidos", "Clasificados", "Cupos", "Definiciones"]
                tab_ca_t = dict(zip(titulos_ca, st.tabs(titulos_ca)))
                with tab_ca_t["Cuadro"]:
                    seccion("Cuadro de la Copa Argentina", color="#1e5aa8")
                    opciones = [f"Llave {x}" for x in COPA_LLAVES] + ["Fase final"]
                    vista_llave = st.segmented_control("Llave", opciones, default="Llave A", key="ca_llave",
                                                       label_visibility="collapsed") or "Llave A"
                    if vista_llave == "Fase final":
                        st.markdown(cuadro_final_copa_html(SC), unsafe_allow_html=True)
                    else:
                        st.markdown(cuadro_llave_html(SC, vista_llave[-1]), unsafe_allow_html=True)
                with tab_ca_t["Partidos"]:
                    if not SC["log"]:
                        aviso("Todavía no se jugó ninguna ronda. Los cruces de 64avos están en el <b>Cuadro</b>.")
                    else:
                        jugadas = SC["ronda"]
                        ronda_sel = st.selectbox(":material/event: Ronda", range(jugadas), index=jugadas - 1,
                                                 format_func=lambda k: COPA_RONDAS[k], key=f"ca_ronda_{S['temp']}")
                        for m in SC["cuadro"][ronda_sel]:
                            st.markdown(fila_partido_html(S, ctx.club, m["p"]), unsafe_allow_html=True)
                with tab_ca_t["Clasificados"]:
                    seccion("Clasificados", "Los 128 equipos y por qué entraron (por la temporada anterior; "
                            "en la temporada 1, por media)", "#1e5aa8")
                    df_cl = pd.DataFrame({"Equipo": SC["nombres"], "Liga": SC["origen"],
                                          "Clasificó como": SC["criterio"],
                                          "Media": np.round(SC["r"], 1)})
                    df_cl["_o"] = df_cl["Liga"].map({x: k for k, x in enumerate(
                        ["Primera División", "Primera Nacional", "Federal A", "Primera B", "Primera C",
                         "Federal B", "Regional Amateur"])})
                    df_cl = df_cl.sort_values(["_o", "Media"], ascending=[True, False]).drop(columns="_o")
                    st.markdown(tabla_html(df_cl, formatos={"Media": "{:.1f}"}), unsafe_allow_html=True)
                with tab_ca_t["Cupos"]:
                    seccion("Cupos", "Cuántos equipos de cada liga clasificaron a la Copa de esta temporada", "#1e5aa8")
                    _tabla_cupos(list(zip(SC["nombres"], SC["criterio"])))
                with tab_ca_t["Definiciones"]:
                    seccion("Definiciones", color="#b7860b")
                    if SC["campeon"] is None:
                        aviso("El campeón aparece acá cuando se juega la final.")
                    else:
                        fin = SC["cuadro"][-1][0]
                        sub = fin["b"] if fin["gana"] == fin["a"] else fin["a"]
                        cc = SC["nombres"][SC["campeon"]]
                        st.markdown(f'<div class="champ"><div class="t">Campeón · Copa Argentina · Temporada {S["temp"]}'
                                    f'</div><div style="margin-top:10px">{crest(cc, 64)}</div>'
                                    f'<div class="nm">{esc(cc)}</div><div class="s">{esc(SC["origen"][SC["campeon"]])}'
                                    f' · finalista: {esc(SC["nombres"][sub])}</div></div>', unsafe_allow_html=True)
                        st.markdown(fila_partido_html(S, ctx.club, fin["p"], abierto=True), unsafe_allow_html=True)

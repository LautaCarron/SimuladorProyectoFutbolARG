"""Pestaña Copas · Copa Argentina.

El código es el de simuladorafa.py, movido acá tal cual. `ctx` trae el estado y los ayudantes
compartidos de la interfaz (S, P, las pestañas, las banderas terminada_*, etc.).
"""

import numpy as np
import pandas as pd
import streamlit as st
from copas import COPA_LLAVES, COPA_RONDAS, simular_ronda_copa
from logos import logo_img
from vista import (
    aviso,
    barra_estado,
    chip,
    crest,
    cuadro_final_copa_html,
    cuadro_llave_html,
    esc,
    fila_partido_html,
    seccion,
    tabla_html,
)


def render(ctx):
    (P, S, SC, _abierta, pct_copa, tab_ca, tab_copas, terminada, terminada_b, terminada_copa,
     terminada_f, terminada_pb, terminada_pc, terminada_reg) = (
        ctx.P, ctx.S, ctx.SC, ctx._abierta, ctx.pct_copa, ctx.tab_ca, ctx.tab_copas, ctx.terminada,
        ctx.terminada_b, ctx.terminada_copa, ctx.terminada_f, ctx.terminada_pb,
        ctx.terminada_pc, ctx.terminada_reg)
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
            barra_estado([("Próxima ronda" if SC["sorteada"] and not terminada_copa else "Estado", ronda_txt),
                          ("Rondas", f"{SC['ronda']} / {SC['total']}"), ("Partidos jugados", len(SC["log"]))],
                         pct_copa)

            if not SC["sorteada"]:
                seccion("Copa Argentina", "128 equipos · desde 64avos de final · partido único en cancha "
                        "neutral, penales si empatan", "#1e5aa8")
                aviso("La Copa se sortea al empezar la temporada.")
                cupos = pd.DataFrame([
                    ("Primera División", "Los 30 equipos", 30), ("Primera Nacional", "Los 36 equipos", 36),
                    ("Federal A", "Los 20 de Zona Campeonato y los 8 mejores de Zona Descenso", 28),
                    ("Primera B", "Los 12 primeros", 12), ("Primera C", "Los 10 primeros", 10),
                    ("Regional Amateur", "El campeón de cada una de las 12 regiones", 12)],
                    columns=["Liga", "Clasifican", "Cupos"])
                st.markdown(tabla_html(cupos, clubes=()), unsafe_allow_html=True)
                pendientes = [n for n, t in (("Primera", terminada), ("B Nacional", terminada_b),
                                             ("Federal A", terminada_f), ("Primera B", terminada_pb),
                                             ("Primera C", terminada_pc), ("Regional", terminada_reg)) if not t]
                st.caption("Faltan terminar: " + ", ".join(pendientes))
            else:
                titulos_ca = ["Cuadro", "Partidos", "Clasificados", "Definiciones"]
                tab_ca_t = dict(zip(titulos_ca, st.tabs(titulos_ca)))
                with tab_ca_t["Cuadro"]:
                    seccion("Cuadro de la Copa Argentina", "8 llaves de 16 equipos (64avos a octavos) · el ganador "
                            "de cada llave juega los cuartos · todo en cancha neutral · (n) = penales", "#1e5aa8")
                    st.caption("64avos por categoría: Primera vs. Regional Amateur, B Nacional vs. Primera C, "
                               "Federal A vs. Primera B; los que sobran se cruzan con la misma regla. Se juega "
                               "los miércoles, en el medio de las ligas (ver Calendario).")
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
                            st.markdown(fila_partido_html(m["p"]), unsafe_allow_html=True)
                with tab_ca_t["Clasificados"]:
                    seccion("Clasificados", "Los 128 equipos y por qué entraron (por la temporada anterior; "
                            "en la temporada 1, por media)", "#1e5aa8")
                    df_cl = pd.DataFrame({"Equipo": SC["nombres"], "Liga": SC["origen"],
                                          "Clasificó como": SC["criterio"],
                                          "Media": np.round(SC["r"], 1)})
                    df_cl["_o"] = df_cl["Liga"].map({x: k for k, x in enumerate(
                        ["Primera División", "Primera Nacional", "Federal A", "Primera B", "Primera C",
                         "Regional Amateur"])})
                    df_cl = df_cl.sort_values(["_o", "Media"], ascending=[True, False]).drop(columns="_o")
                    st.markdown(tabla_html(df_cl, formatos={"Media": "{:.1f}"}), unsafe_allow_html=True)
                with tab_ca_t["Definiciones"]:
                    seccion("Definiciones", "Campeón y finalista de la Copa Argentina", "#b7860b")
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
                        st.markdown(fila_partido_html(fin["p"], abierto=True), unsafe_allow_html=True)

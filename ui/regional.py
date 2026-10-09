"""Pestaña Ligas · Regional Amateur.

El código es el de simuladorafa.py, movido acá tal cual. `ctx` trae el estado y los ayudantes
compartidos de la interfaz (S, P, las pestañas, las banderas terminada_*, etc.).
Modo manager: se abre sola (y se marca con ⭐) la región donde juega el club que dirigís.
"""

import streamlit as st
from datos.regional import FINALES_REG, REGIONES_REG
from ligas.regional import simular_fecha_reg, tabla_reg_region
from ui.vista import (
    COLOR_ORO,
    aviso,
    barra_estado,
    chip,
    colorear_reg,
    esc,
    fila_partido_html,
    finales_reg_html,
    leyenda,
    lista_equipos_html,
    mostrar_tabla,
    render_movimientos,
    seccion,
    vista_fixture,
)
from ui.vista.mi_club import mi_club, modo_manager, region_de_club


def render(ctx):
    (P, S, SR, _abierta, editar_medias, html_tabla_liguilla, pct_reg, tab_ligas, tab_reg, terminada_reg) = (
        ctx.P, ctx.S, ctx.SR, ctx._abierta, ctx.editar_medias, ctx.html_tabla_liguilla, ctx.pct_reg,
        ctx.tab_ligas, ctx.tab_reg, ctx.terminada_reg)
    # ============================================================================
    # TORNEO REGIONAL AMATEUR
    # ============================================================================
    if _abierta(tab_ligas, tab_reg):
        with tab_reg:
            c1, c2, c3 = st.columns([3, 1.4, 1.4], vertical_alignment="center")
            c1.markdown(chip(f"Regional Amateur · {len(SR['nombres'])} clubes", "#0e7490") + " "
                        + chip("12 regiones · 6 ascensos al Federal A", "#475569"), unsafe_allow_html=True)
            if c2.button(":material/skip_next: Próxima fecha", key="reg_next", width="stretch", type="primary",
                         disabled=terminada_reg):
                simular_fecha_reg(SR, P, S["rng"])
                st.rerun()
            if c3.button(":material/fast_forward: Hasta el final", key="reg_all", width="stretch",
                         disabled=terminada_reg):
                while SR["fecha"] < SR["total"]:
                    simular_fecha_reg(SR, P, S["rng"])
                st.rerun()

            fase_reg = ("Ligas regionales" if SR["fecha"] < SR["f_liga"] else
                        "Desempate por el campeonato" if SR["fecha"] < SR["f_final0"] else
                        "Terminado" if terminada_reg else "Final por el ascenso")
            barra_estado([("Fase", fase_reg), ("Fecha", f"{SR['fecha']} / {SR['total']}"),
                          ("Partidos jugados", len(SR["log"]))], pct_reg)

            # modo manager: región del club que dirigís (None si no juega el Regional). La key lleva el
            # club, así al cambiar de club la región se vuelve a abrir en la nueva.
            club_mgr = mi_club()
            mi_reg = region_de_club(SR, club_mgr)
            _k = "_" + "".join(c if c.isalnum() else "_" for c in club_mgr) if mi_reg else ""
            _fmt = lambda r: r + " ⭐" if r == mi_reg else r

            desempates_r = [p for p in SR["log"] if p["rotulo"] == "Desempate"]
            titulos_r = ["Regiones", "Fixture y resultados"]
            if SR["desempate_pendiente"] or desempates_r:
                titulos_r.append("Desempate")
            titulos_r += ["Final por el ascenso", "Movimientos", "Definiciones"]
            tab_r = dict(zip(titulos_r, st.tabs(titulos_r)))

            with tab_r["Regiones"]:
                seccion("Regiones", "Cada región es una liga de todos contra todos a una sola vuelta · "
                        "el 1° es el campeón regional", "#0e7490")
                region = st.pills("Región", REGIONES_REG, default=mi_reg or REGIONES_REG[0],
                                  key=f"reg_region{_k}", format_func=_fmt,
                                  label_visibility="collapsed") or (mi_reg or REGIONES_REG[0])
                n_final, rival = next((k + 1, b if a == region else a) for k, (a, b) in enumerate(FINALES_REG)
                                      if region in (a, b))
                st.markdown(chip(f"{len(SR['grupos'][region])} clubes", "#0e7490") + " "
                            + chip(f"Final {n_final} por el ascenso vs. {rival}", "#b7860b"),
                            unsafe_allow_html=True)
                seccion(f"Región {region}", "Si hay igualdad en puntos en el 1° puesto, el título se define "
                        "con un desempate (nunca por diferencia de gol)", "#16a34a")
                mostrar_tabla(tabla_reg_region(SR, region), colorear_reg)
                leyenda([("Campeón regional", COLOR_ORO), ("Desempate Campeonato", "rgba(249, 115, 22, 0.3)")])
                if SR["fecha"] == 0 and not modo_manager():      # en modo manager no se tocan las medias
                    nom_reg_ed = [f"{n} · {rg}" for n, rg in zip(SR["nombres"], SR["region_de"])]
                    with st.expander(":material/tune: Editar medias internas de esta temporada (Regional Amateur)"):
                        SR["r"] = editar_medias(nom_reg_ed, SR["r"], f"editor_reg_{S['temp']}")

            if "Desempate" in tab_r:
                with tab_r["Desempate"]:
                    seccion("Desempates por el campeonato", "Igualdad en puntos en el 1° puesto de la región · "
                            "partido único en cancha neutral, penales si empatan", "#9333ea")
                    for reg in REGIONES_REG:
                        if SR["desempate_pendiente"] and reg in SR["motivos_desempate"]:
                            st.markdown(f'<div class="mlab" style="margin-top:14px">Región {esc(reg)}</div>',
                                        unsafe_allow_html=True)
                            df_des = tabla_reg_region(SR, reg).head(SR["motivos_desempate"][reg])
                            mostrar_tabla(df_des, colorear_reg)
                            continue
                        grupos_r = {}
                        for p in desempates_r:
                            if p["region"] == reg:
                                grupos_r.setdefault(p["comp"], []).append(p)
                        for comp_r, partes in grupos_r.items():
                            if "Liguilla" in comp_r:
                                seccion(f"Tabla final: {comp_r}", "Posiciones del mini-torneo a partido único", "#9333ea")
                                st.markdown(html_tabla_liguilla(partes), unsafe_allow_html=True)
                                with st.expander(f":material/visibility: Ver los {len(partes)} enfrentamientos",
                                                 expanded=False):
                                    for p in partes:
                                        st.markdown(fila_partido_html(p), unsafe_allow_html=True)
                            else:
                                seccion(f"Desempate: {comp_r}", "Partido único definitorio", "#dc2626")
                                for p in partes:
                                    st.markdown(fila_partido_html(p, abierto=True), unsafe_allow_html=True)

            with tab_r["Fixture y resultados"]:
                region_fx = st.selectbox(":material/map: Región", REGIONES_REG,
                                         index=REGIONES_REG.index(mi_reg) if mi_reg else 0,
                                         format_func=_fmt, key=f"reg_fx_region{_k}")
                vista_fixture("reg", region_fx)

            with tab_r["Final por el ascenso"]:
                seccion("Final por el ascenso", "Los 12 campeones regionales se cruzan de a pares, a ida y "
                        "vuelta · los 6 ganadores ascienden al Federal A", "#b7860b")
                campeones_ya = [(SR["nombres"][c], reg) for reg, c in SR["campeones"].items() if c is not None]
                if not campeones_ya:
                    aviso("Los cruces se completan con los campeones de cada región.")
                st.markdown(finales_reg_html(SR), unsafe_allow_html=True)
                if SR["ascendidos"]:
                    st.markdown('<div class="mlab up">▲ Ascienden al Federal A</div>'
                                + lista_equipos_html([(SR["nombres"][i], SR["region_de"][i])
                                                      for i in SR["ascendidos"]]), unsafe_allow_html=True)

            with tab_r["Movimientos"]:
                render_movimientos(SR["log"], SR["pos_hist"], SR["nombres"], "#0f766e")

            with tab_r["Definiciones"]:
                seccion("Definiciones de la temporada", "Campeones regionales y ascensos al Federal A", "#b7860b")
                if not any(c is not None for c in SR["campeones"].values()):
                    aviso("Las definiciones aparecen acá cuando termina la liga de cada región.")
                else:
                    with st.expander(":material/emoji_events: Campeones regionales", expanded=False):
                        st.markdown(lista_equipos_html([(SR["nombres"][c], reg) for reg, c in
                                                        SR["campeones"].items() if c is not None]),
                                    unsafe_allow_html=True)
                    if SR["ascendidos"]:
                        with st.expander(":material/arrow_upward: Ascensos al Federal A", expanded=False):
                            st.markdown(lista_equipos_html([(SR["nombres"][i], SR["region_de"][i])
                                                            for i in SR["ascendidos"]]), unsafe_allow_html=True)

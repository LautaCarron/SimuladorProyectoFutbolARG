"""Pestaña Ligas · Regional Amateur.

El código es el de simuladorafa.py, movido acá tal cual. `ctx` trae el estado y los ayudantes
compartidos de la interfaz (S, P, las pestañas, las banderas terminada_*, etc.).
Modo manager: se abre sola (y se marca con ⭐) la región donde juega el club que dirigís.
"""

import streamlit as st
from datos.datos_regional import FINALES_REG, REGIONES_REG
from ligas.regional import simular_fecha_reg, tabla_reg_region
from ui.vista.editor_medias import editar_medias
from ui.vista.liguilla import html_tabla_liguilla
from ui.vista import (
    COLOR_ORO,
    aviso,
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
from ui.vista.mi_club import region_de_club


def _zona_corta(clave, claves):
    """\"Zona A\" para una región dividida; \"\" si la región tiene una sola zona."""
    return clave.split(" · ")[-1] if len(claves) > 1 else ""


def _tabla_de_zona(df_reg, clave, claves):
    """Las filas de una zona dentro de la tabla de la región (que trae las dos zonas juntas)."""
    return df_reg[df_reg["Zona"] == _zona_corta(clave, claves)].reset_index(drop=True)


def _mostrar_region(SR, reg):
    """Tabla de la región: una sola tabla, o una tabla separada por cada zona si la región está dividida."""
    df = tabla_reg_region(SR, reg)
    claves = SR["zonas_de"][reg]
    if len(claves) == 1:
        mostrar_tabla(df, colorear_reg)
        return
    for clave in claves:
        sub = _tabla_de_zona(df, clave, claves)
        st.markdown(f'<div class="mlab" style="margin-top:14px">{esc(_zona_corta(clave, claves))} · '
                    f'{len(sub)} clubes</div>', unsafe_allow_html=True)
        mostrar_tabla(sub, colorear_reg)


def render(ctx):
    (P, S, SR, _abierta, pct_reg, tab_ligas, tab_reg, terminada_reg) = (
        ctx.P, ctx.S, ctx.SR, ctx.abierta, ctx.progreso.pct_reg,
        ctx.pestanas.tab_ligas, ctx.pestanas.tab_reg, ctx.progreso.terminada_reg)
    from ligas.federal_b import destino_ascenso_regional
    sube = destino_ascenso_regional(S)                  # "Federal A" (o "Federal B" si existe)
    # ============================================================================
    # TORNEO REGIONAL AMATEUR
    # ============================================================================
    if _abierta(tab_ligas, tab_reg):
        with tab_reg:
            c1, c2, c3 = st.columns([3, 1.4, 1.4], vertical_alignment="center")
            c1.markdown(chip(f"Regional Amateur · {len(SR['nombres'])} clubes", "#0e7490") + " "
                        + chip(f"12 regiones · 6 ascensos al {sube}", "#475569"), unsafe_allow_html=True)
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

            # modo manager: región del club que dirigís (None si no juega el Regional). La key lleva el
            # club, así al cambiar de club la región se vuelve a abrir en la nueva.
            club_mgr = ctx.club
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
                seccion("Regiones", color="#0e7490")
                region = st.pills("Región", REGIONES_REG, default=mi_reg or REGIONES_REG[0],
                                  key=f"reg_region{_k}", format_func=_fmt,
                                  label_visibility="collapsed") or (mi_reg or REGIONES_REG[0])
                n_final, rival = next((k + 1, b if a == region else a) for k, (a, b) in enumerate(FINALES_REG)
                                      if region in (a, b))
                st.markdown(chip(f"{len(SR['grupos'][region])} clubes", "#0e7490") + " "
                            + chip(f"Final {n_final} por el ascenso vs. {rival}", "#b7860b"),
                            unsafe_allow_html=True)
                seccion(f"Región {region}", color="#16a34a")
                _mostrar_region(SR, region)
                leyenda([("Campeón regional", COLOR_ORO), ("Desempate Campeonato", "rgba(249, 115, 22, 0.3)")])
                if SR["fecha"] == 0 and not ctx.modo_mgr:      # en modo manager no se tocan las medias
                    nom_reg_ed = [f"{n} · {rg}" for n, rg in zip(SR["nombres"], SR["region_de"])]
                    with st.expander(":material/tune: Editar medias internas de esta temporada (Regional Amateur)"):
                        SR["r"] = editar_medias(nom_reg_ed, SR["r"], f"editor_reg_{S['temp']}")

            if "Desempate" in tab_r:
                with tab_r["Desempate"]:
                    seccion("Desempates por el campeonato", color="#9333ea")
                    for reg in REGIONES_REG:
                        claves_reg = SR["zonas_de"][reg]
                        if SR["desempate_pendiente"]:
                            df_reg = None
                            for clave in claves_reg:
                                if clave not in SR["motivos_desempate"]:
                                    continue
                                if df_reg is None:
                                    df_reg = tabla_reg_region(SR, reg)
                                st.markdown(f'<div class="mlab" style="margin-top:14px">Región {esc(clave)}</div>',
                                            unsafe_allow_html=True)
                                df_des = _tabla_de_zona(df_reg, clave, claves_reg).head(SR["motivos_desempate"][clave])
                                mostrar_tabla(df_des, colorear_reg)
                        grupos_r = {}
                        for p in desempates_r:
                            if p["region"] == reg:
                                grupos_r.setdefault(p["comp"], []).append(p)
                        for comp_r, partes in grupos_r.items():
                            if "Liguilla" in comp_r:
                                seccion(f"Tabla final: {comp_r}", color="#9333ea")
                                st.markdown(html_tabla_liguilla(partes), unsafe_allow_html=True)
                                with st.expander(f":material/visibility: Ver los {len(partes)} enfrentamientos",
                                                 expanded=False):
                                    for p in partes:
                                        st.markdown(fila_partido_html(S, ctx.club, p), unsafe_allow_html=True)
                            else:
                                seccion(f"Desempate: {comp_r}", color="#dc2626")
                                for p in partes:
                                    st.markdown(fila_partido_html(S, ctx.club, p, abierto=True), unsafe_allow_html=True)

            with tab_r["Fixture y resultados"]:
                region_fx = st.selectbox(":material/map: Región", REGIONES_REG,
                                         index=REGIONES_REG.index(mi_reg) if mi_reg else 0,
                                         format_func=_fmt, key=f"reg_fx_region{_k}")
                vista_fixture(S, ctx.club, "reg", region_fx)

            with tab_r["Final por el ascenso"]:
                seccion("Final por el ascenso", color="#b7860b")
                campeones_ya = [(SR["nombres"][c], reg) for reg, c in SR["campeones"].items() if c is not None]
                if not campeones_ya:
                    aviso("Los cruces se completan con los campeones de cada región.")
                st.markdown(finales_reg_html(S), unsafe_allow_html=True)
                if SR["ascendidos"]:
                    st.markdown(f'<div class="mlab up">▲ Ascienden al {sube}</div>'
                                + lista_equipos_html([(SR["nombres"][i], SR["region_de"][i])
                                                      for i in SR["ascendidos"]]), unsafe_allow_html=True)

            with tab_r["Movimientos"]:
                render_movimientos(SR["log"], SR["pos_hist"], SR["nombres"], "#0f766e")

            with tab_r["Definiciones"]:
                seccion("Definiciones de la temporada", color="#b7860b")
                if not any(c is not None for c in SR["campeones"].values()):
                    aviso("Las definiciones aparecen acá cuando termina la liga de cada región.")
                else:
                    with st.expander(":material/emoji_events: Campeones regionales", expanded=False):
                        st.markdown(lista_equipos_html([(SR["nombres"][c], reg) for reg, c in
                                                        SR["campeones"].items() if c is not None]),
                                    unsafe_allow_html=True)
                    if SR["ascendidos"]:
                        with st.expander(f":material/arrow_upward: Ascensos al {sube}", expanded=False):
                            st.markdown(lista_equipos_html([(SR["nombres"][i], SR["region_de"][i])
                                                            for i in SR["ascendidos"]]), unsafe_allow_html=True)

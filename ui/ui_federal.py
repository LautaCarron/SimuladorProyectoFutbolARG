"""Pestaña Ligas · Federal A.

El código es el de simuladorafa.py, movido acá tal cual. `ctx` trae el estado y los ayudantes
compartidos de la interfaz (S, P, las pestañas, las banderas terminada_*, etc.).
Modo manager: se abre sola (y se marca con ⭐) la zona donde juega el club que dirigís
(su grupo por cercanía en la fase 1; Campeonato o Descenso en la fase 2).
"""

import streamlit as st
from datos.equipos import F_GRUPOS_NOMBRES, region_de, region_regional
from ligas.federal import F_DESC, plan_de_f, simular_fecha_f, tabla_f_f2, tabla_f_grupo
from ligas.federal_b import destino_descenso_federal_a
from ui.vista.editor_medias import editar_medias
from ui.vista.liguilla import html_tabla_liguilla
from ui.vista import (
    COLORES_F,
    LEY_F,
    aviso,
    bracket_html_f,
    chip,
    colorear_f,
    crest,
    esc,
    fila_partido_html,
    leyenda,
    lista_equipos_html,
    mostrar_tabla,
    render_movimientos,
    seccion,
    tabla_html,
    vista_fixture,
)
from ui.vista.mi_club import marcar, tabs_con_default, zona_federal


def render(ctx):
    """Federal A."""
    render_liga_f(ctx, ctx.SF, ctx.pestanas.tab_f, ctx.progreso.terminada_f, ctx.progreso.pct_f, "f")


def render_liga_f(ctx, SF, tab_f, terminada_f, pct_f, clave):
    """Pestaña de una liga con formato Federal: el Federal A (clave "f") o el Federal B (clave "fb"). Es el mismo
    formato (grupos por cercanía, zonas Campeonato y Descenso y reducido); sólo cambian el nombre, adónde suben
    y adónde bajan."""
    (P, S, _abierta, tab_ligas) = (
        ctx.P, ctx.S, ctx.abierta, ctx.pestanas.tab_ligas)
    nombre = SF.get("liga", "Federal A")                      # "Federal A" o "Federal B"
    es_b = nombre == "Federal B"
    sube_a = "el Federal A" if es_b else "la Primera Nacional"            # adónde asciende
    sube_a_txt = "Federal A" if es_b else "B Nacional"
    baja_a = "Regional Amateur" if es_b else destino_descenso_federal_a(S)  # adónde desciende
    n_desc = SF.get("desc_n", F_DESC)                         # cuántos descienden
    # ============================================================================
    # FEDERAL A / FEDERAL B
    # ============================================================================
    if _abierta(tab_ligas, tab_f):
        with tab_f:
            ff = SF["fecha"]
            nom_f = SF["nombres"]
            if ff < SF["f1_rondas"]:
                fase_txt_f = "1 · Grupos por cercanía"
            elif ff < SF["f1_rondas"] + SF.get("f2_rondas", 0):
                fase_txt_f = "2 · Campeonato y Descenso"
            elif ff < SF["total"]:
                fase_txt_f = "Reducido"
            else:
                fase_txt_f = "Terminada"

            c1, c2, c3 = st.columns([3, 1.4, 1.4], vertical_alignment="center")
            c1.markdown(chip(f"{nombre} · {len(nom_f)} equipos") + " " +
                        chip(f"Fase {fase_txt_f}", "#475569"), unsafe_allow_html=True)
            if c2.button(":material/skip_next: Próxima fecha", key=f"{clave}_next", width="stretch", type="primary",
                         disabled=terminada_f):
                simular_fecha_f(SF, P, S["rng"])
                st.rerun()
            if c3.button(":material/fast_forward: Hasta el final", key=f"{clave}_all", width="stretch", disabled=terminada_f):
                while SF["fecha"] < SF["total"]:
                    simular_fecha_f(SF, P, S["rng"])
                st.rerun()

                  
            if ff == SF["f1_rondas"]:
                aviso("Terminó la fase 1: clasificaron los mejores de cada grupo (" + str(len(SF["zonas2"][0])) + " equipos) a Zona Campeonato, "
                      "el resto a Zona Descenso, y <b>todos los puntos se reiniciaron a 0</b>.")
            if ff == SF["f1_rondas"] + SF.get("f2_rondas", 0):
                pr = plan_de_f(SF)
                d_f = pr["directos"]
                directos_txt = (f"los primeros {d_f} ascendieron directo" if d_f > 1 else
                                "el campeón ascendió directo" if d_f == 1 else "nadie asciende directo")
                desc_txt = (f"los {n_desc} últimos de Zona Descenso bajan al {baja_a}" if n_desc > 1 else
                            f"el último de Zona Descenso baja al {baja_a}" if n_desc == 1 else
                            "nadie desciende")
                aviso(f"Terminó la fase 2: {directos_txt} a la {sube_a_txt} y {desc_txt}. "
                      + ("Mirá el cuadro del reducido en la pestaña <b>Reducido</b>." if pr["reducido"] else
                         "No hay reducido: no hay más ascensos."))

            # ------------------ SISTEMA DE PESTAÑAS DINÁMICAS ------------------
            desempate_f = SF.get("desempate_camp")
            desempate_fd = SF.get("desempate_desc")
            titulos_f = ["Posiciones", "Fixture y resultados"]
            if desempate_f or desempate_fd: titulos_f.append("Desempate")
            titulos_f.extend(["Reducido", "Movimientos", "Definiciones"])
            tab_f = dict(zip(titulos_f, st.tabs(titulos_f)))
                       
            with tab_f["Posiciones"]:
                mi_zona = zona_federal(SF, ctx.club)          # modo manager: zona de mi club (o None)
                if ff < SF["f1_rondas"]:
                    cuota_f, extra_f = SF["cuota"][0], SF.get("extra", 0)
                    pasan_txt = (f"pasan los {cuota_f} mejores de cada grupo" +
                                 (f" y los {extra_f} mejores {cuota_f + 1}° " if extra_f > 1 else
                                  f" y el mejor {cuota_f + 1}° " if extra_f == 1 else " ") +
                                 f"a la Zona Campeonato ({cuota_f * len(SF['grupos']) + extra_f} equipos)")
                    seccion("Fase 1 · Grupos por cercanía", color="#4f46e5")
                    etiq, ini = marcar(list(F_GRUPOS_NOMBRES), mi_zona)
                    tabs_f = tabs_con_default(etiq, ini)
                    for g, tab in enumerate(tabs_f):
                        with tab:
                            mostrar_tabla(tabla_f_grupo(SF, g), colorear_f, SF["pos_hist"])
                    leyenda([(f"Primeros {cuota_f} de cada grupo → Zona Campeonato", COLORES_F["→ Zona Campeonato"])] +
                            ([(f"Mejores {cuota_f + 1}° (por puntos por partido) completan la Zona Campeonato",
                               COLORES_F["→ Zona Campeonato"])] if extra_f else []))
                else:
                    seccion("Fase 2 · Zonas", color="#16a34a")
                    etiq, ini = marcar(["Campeonato", "Descenso", "Fase 1"], mi_zona)
                    tabs_f = tabs_con_default(etiq, ini)
                    with tabs_f[0]:
                        mostrar_tabla(tabla_f_f2(SF, 0), colorear_f, SF["pos_hist"])
                    with tabs_f[1]:
                        mostrar_tabla(tabla_f_f2(SF, 1), colorear_f, SF["pos_hist"])
                    with tabs_f[2]:
                        for g, dfg in zip(F_GRUPOS_NOMBRES, SF["tablas_f1"]):
                            st.markdown(chip(g), unsafe_allow_html=True)
                            mostrar_tabla(dfg, colorear_f)
                        st.caption("Posiciones finales de la fase 1 (sus puntos ya no cuentan).")
                    leyenda(LEY_F)
            
                if ff == 0 and not ctx.modo_mgr:               # en modo manager no se tocan las medias
                    with st.expander(":material/tune: Editar medias internas de esta temporada ({nombre})"):
                        SF["r"] = editar_medias(nom_f, SF["r"], f"editor_{clave}_{S['temp']}")
                
            with tab_f["Fixture y resultados"]:
                vista_fixture(S, ctx.club, clave)
        
            def partidos_desempate_f(info):
                grupos_f = {}
                for p in info["partidos"]:
                    grupos_f.setdefault(p["comp"], []).append(p)
                for comp_f, partes in grupos_f.items():
                    if "Liguilla" in comp_f:
                        seccion(f"Tabla final: {comp_f}", color="#9333ea")
                        st.markdown(html_tabla_liguilla(partes), unsafe_allow_html=True)
                        with st.expander(f":material/visibility: Ver los {len(partes)} enfrentamientos",
                                         expanded=False):
                            for p in partes:
                                st.markdown(fila_partido_html(S, ctx.club, p), unsafe_allow_html=True)
                    else:
                        if len(grupos_f) > 1:
                            seccion(comp_f, color="#dc2626")
                        for p in partes:
                            st.markdown(fila_partido_html(S, ctx.club, p, abierto=True), unsafe_allow_html=True)

            if desempate_f or desempate_fd:
                with tab_f["Desempate"]:
                    if desempate_f:
                        seccion("Desempate por el campeonato", color="#9333ea")
                        partidos_desempate_f(desempate_f)
                        st.caption("El título se define con desempate en cancha neutral (penales si empatan). "
                                   "El resto de las posiciones se ordena por diferencia de gol.")
                    if desempate_fd:
                        seccion("Desempate por la permanencia", color="#9333ea")
                        partidos_desempate_f(desempate_fd)
                        st.caption(f"Partido único en cancha neutral (penales si empatan). "
                                   f"Los {n_desc} últimos bajan al {baja_a}.")

            with tab_f["Reducido"]:
                pr = plan_de_f(SF)
                seccion("Reducido por el último ascenso", color="#2563eb")
                if not pr["reducido"]:
                    aviso("Esta temporada no hay reducido: ascienden solo los que terminan en los primeros puestos "
                          "de la zona Campeonato.")
                elif ff < SF["f1_rondas"] + SF.get("f2_rondas", 0):
                    aviso(f"El cuadro se completa al terminar la fase 2. Entran del {pr['directos'] + 1}° al "
                          f"{pr['directos'] + pr['equipos']}° de Zona Campeonato.")
                if pr["reducido"]:
                    st.markdown(bracket_html_f(SF), unsafe_allow_html=True)
                if SF["entrantes"] is not None:
                    with st.expander("Clasificados al reducido (orden de mérito)"):
                        st.markdown(tabla_html(SF["entrantes"]), unsafe_allow_html=True)
                             
            with tab_f["Movimientos"]:
                render_movimientos(SF["log"], SF["pos_hist"], nom_f, "#0f766e")
        
            with tab_f["Definiciones"]:
                seccion("Definiciones de la temporada", color="#b7860b")
                if SF["campeon"] is None:
                    aviso(f"Las definiciones aparecen acá cuando termina la fase 2 del {nombre}.")
                else:
                    st.caption("Están cerradas para no spoilear: tocá cada una para verla.")
                    with st.expander(f":material/emoji_events: Campeón del {nombre}", expanded=False):
                        cf = nom_f[SF["campeon"]]
                        st.markdown(f'<div class="champ"><div class="t">Campeón · Temporada {S["temp"]}'
                                    f'</div><div style="margin-top:10px">{crest(cf, 64)}</div>'
                                    f'<div class="nm">{esc(cf)}</div><div class="s">Asciende '
                                    f'{"al Federal A" if es_b else "a la Primera Nacional"}</div></div>',
                                    unsafe_allow_html=True)
                        if SF.get("desempate_camp"):
                            dc = SF["desempate_camp"]
                            st.markdown(f'<div class="mlab" style="margin-top:14px">Título definido por '
                                        f'desempate · igualaron en puntos: {esc(", ".join(dc["equipos"]))}'
                                        f'</div>' + "".join(fila_partido_html(S, ctx.club, p) for p in dc["partidos"]),
                                        unsafe_allow_html=True)
                    with st.expander(":material/north: Clasificados · Ascensos", expanded=False):
                        asc_f = [(nom_f[i], "campeón" if k == 0 else f"{k + 1}°") for k, i in enumerate(SF["asc_directo"])]
                        if SF["asc_reducido"] is not None:
                            asc_f.append((nom_f[SF["asc_reducido"]], "reducido"))
                        st.markdown(lista_equipos_html(asc_f) + (
                            '' if SF["asc_reducido"] is not None or not plan_de_f(SF)["reducido"] else
                            '<div style="font-size:.8rem;opacity:.65">El último ascenso sale del '
                            'reducido.</div>'), unsafe_allow_html=True)
                    with st.expander(f":material/south: Descensos al {baja_a}", expanded=False):
                        a_regional = baja_a == "Regional Amateur"
                        st.markdown(f'<div class="mlab">Descienden los {n_desc} últimos de Zona Descenso'
                                    + (' (a la región de su provincia)' if a_regional else '') + '</div>'
                                    + lista_equipos_html([(nom_f[i], region_regional(nom_f[i]) if a_regional
                                                          else region_de(nom_f[i]))
                                                          for i in SF["descendidos"]]), unsafe_allow_html=True)

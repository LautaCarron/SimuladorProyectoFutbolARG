"""Pestaña Ligas · Federal A.

El código es el de simuladorafa.py, movido acá tal cual. `ctx` trae el estado y los ayudantes
compartidos de la interfaz (S, P, las pestañas, las banderas terminada_*, etc.).
Modo manager: se abre sola (y se marca con ⭐) la zona donde juega el club que dirigís
(su grupo por cercanía en la fase 1; Campeonato o Descenso en la fase 2).
"""

import streamlit as st
from datos.equipos import F_GRUPOS_NOMBRES, region_regional
from ligas.federal import simular_fecha_f, tabla_f_f2, tabla_f_grupo
from ui.vista import (
    COLORES_F,
    LEY_F,
    aviso,
    barra_estado,
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
from ui.vista.mi_club import marcar, mi_club, modo_manager, zona_federal


def render(ctx):
    (P, S, SF, _abierta, editar_medias, html_tabla_liguilla, pct_f, tab_f, tab_ligas, terminada_f) = (
        ctx.P, ctx.S, ctx.SF, ctx._abierta, ctx.editar_medias, ctx.html_tabla_liguilla, ctx.pct_f,
        ctx.tab_f, ctx.tab_ligas, ctx.terminada_f)
    # ============================================================================
    # FEDERAL A
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
            c1.markdown(chip(f"Federal A · {len(nom_f)} equipos") + " " +
                        chip(f"Fase {fase_txt_f}", "#475569"), unsafe_allow_html=True)
            if c2.button(":material/skip_next: Próxima fecha", key="f_next", width="stretch", type="primary",
                         disabled=terminada_f):
                simular_fecha_f(SF, P, S["rng"])
                st.rerun()
            if c3.button(":material/fast_forward: Hasta el final", key="f_all", width="stretch", disabled=terminada_f):
                while SF["fecha"] < SF["total"]:
                    simular_fecha_f(SF, P, S["rng"])
                st.rerun()

            barra_estado([("Fase", fase_txt_f), ("Fecha", f"{ff} / {SF['total']}"),
                          ("Partidos jugados", len(SF["log"]))], pct_f)
                  
            if ff == SF["f1_rondas"]:
                aviso("Terminó la fase 1: clasificaron los 4 primeros de cada grupo (20 equipos) a Zona Campeonato, "
                      "el resto a Zona Descenso, y <b>todos los puntos se reiniciaron a 0</b>.")
            if ff == SF["f1_rondas"] + SF.get("f2_rondas", 0):
                aviso("Terminó la fase 2: 1°, 2° y 3° ascendieron directo a la B Nacional y los 6 últimos "
                      "de Zona Descenso bajan al Regional Amateur. "
                      "El reducido arranca con el 7° y 8°. Mirá el cuadro en la pestaña <b>Reducido</b>.")

            # ------------------ SISTEMA DE PESTAÑAS DINÁMICAS ------------------
            desempate_f = SF.get("desempate_camp")
            desempate_fd = SF.get("desempate_desc")
            titulos_f = ["Posiciones", "Fixture y resultados"]
            if desempate_f or desempate_fd: titulos_f.append("Desempate")
            titulos_f.extend(["Reducido", "Movimientos", "Definiciones"])
            tab_f = dict(zip(titulos_f, st.tabs(titulos_f)))
                       
            with tab_f["Posiciones"]:
                mi_zona = zona_federal(SF, mi_club())          # modo manager: zona de mi club (o None)
                if ff < SF["f1_rondas"]:
                    seccion("Fase 1 · Grupos por cercanía", "Ida y vuelta · pasan los 4 primeros de "
                            "cada grupo", "#4f46e5")
                    etiq, ini = marcar(list(F_GRUPOS_NOMBRES), mi_zona)
                    tabs_f = st.tabs(etiq, default=ini)
                    for g, tab in enumerate(tabs_f):
                        with tab:
                            mostrar_tabla(tabla_f_grupo(SF, g), colorear_f, SF["pos_hist"])
                    leyenda([("1°-4° → Zona Campeonato", COLORES_F["→ Zona Campeonato"])])
                else:
                    seccion("Fase 2 · Zonas", "Puntos reiniciados a 0 · una rueda por zona", "#16a34a")
                    etiq, ini = marcar(["Campeonato", "Descenso", "Fase 1"], mi_zona)
                    tabs_f = st.tabs(etiq, default=ini)
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
            
                if ff == 0 and not modo_manager():               # en modo manager no se tocan las medias
                    with st.expander(":material/tune: Editar medias internas de esta temporada (Federal A)"):
                        SF["r"] = editar_medias(nom_f, SF["r"], f"editor_f_{S['temp']}")
                
            with tab_f["Fixture y resultados"]:
                vista_fixture("f")
        
            def partidos_desempate_f(info):
                grupos_f = {}
                for p in info["partidos"]:
                    grupos_f.setdefault(p["comp"], []).append(p)
                for comp_f, partes in grupos_f.items():
                    if "Liguilla" in comp_f:
                        seccion(f"Tabla final: {comp_f}", "Posiciones del mini-torneo a partido único", "#9333ea")
                        st.markdown(html_tabla_liguilla(partes), unsafe_allow_html=True)
                        with st.expander(f":material/visibility: Ver los {len(partes)} enfrentamientos",
                                         expanded=False):
                            for p in partes:
                                st.markdown(fila_partido_html(p), unsafe_allow_html=True)
                    else:
                        if len(grupos_f) > 1:
                            seccion(comp_f, "Partido único definitorio", "#dc2626")
                        for p in partes:
                            st.markdown(fila_partido_html(p, abierto=True), unsafe_allow_html=True)

            if desempate_f or desempate_fd:
                with tab_f["Desempate"]:
                    if desempate_f:
                        seccion("Desempate por el campeonato",
                                f"Igualaron en puntos en el 1° puesto: {', '.join(desempate_f['equipos'])}",
                                "#9333ea")
                        partidos_desempate_f(desempate_f)
                        st.caption("El título se define con desempate en cancha neutral (penales si empatan). "
                                   "El resto de las posiciones se ordena por diferencia de gol.")
                    if desempate_fd:
                        seccion("Desempate por la permanencia",
                                f"Igualaron en puntos en el límite del descenso (Zona Descenso): "
                                f"{', '.join(desempate_fd['equipos'])} · se salva"
                                f"{'n' if desempate_fd['salvados'] > 1 else ''} {desempate_fd['salvados']}",
                                "#9333ea")
                        partidos_desempate_f(desempate_fd)
                        st.caption("Partido único en cancha neutral (penales si empatan). Los 6 últimos bajan "
                                   "al Regional Amateur.")

            with tab_f["Reducido"]:
                seccion("Reducido por el cuarto ascenso",
                        "Eliminatoria → Semifinal → Final · partido único · gana el mejor ubicado si "
                        "empatan, menos en la final (cancha neutral, penales) · L = local, V = "
                        "visitante, N = neutral", "#2563eb")
                if ff < SF["f1_rondas"] + SF.get("f2_rondas", 0):
                    aviso("El cuadro se completa al terminar la fase 2. Entran del 4° al 8° de Zona "
                          "Campeonato.")
                st.markdown(bracket_html_f(SF), unsafe_allow_html=True)
                if SF["entrantes"] is not None:
                    with st.expander("Clasificados al reducido (orden de mérito)"):
                        st.markdown(tabla_html(SF["entrantes"]), unsafe_allow_html=True)
                             
            with tab_f["Movimientos"]:
                render_movimientos(SF["log"], SF["pos_hist"], nom_f, "#0f766e")
        
            with tab_f["Definiciones"]:
                seccion("Definiciones de la temporada", "Campeón y ascensos a la Primera Nacional",
                        "#b7860b")
                if SF["campeon"] is None:
                    aviso("Las definiciones aparecen acá cuando termina la fase 2 del Federal A.")
                else:
                    st.caption("Están cerradas para no spoilear: tocá cada una para verla.")
                    with st.expander(":material/emoji_events: Campeón del Federal A", expanded=False):
                        cf = nom_f[SF["campeon"]]
                        st.markdown(f'<div class="champ"><div class="t">Campeón · Temporada {S["temp"]}'
                                    f'</div><div style="margin-top:10px">{crest(cf, 64)}</div>'
                                    f'<div class="nm">{esc(cf)}</div><div class="s">Asciende a la Primera'
                                    f' Nacional</div></div>', unsafe_allow_html=True)
                        if SF.get("desempate_camp"):
                            dc = SF["desempate_camp"]
                            st.markdown(f'<div class="mlab" style="margin-top:14px">Título definido por '
                                        f'desempate · igualaron en puntos: {esc(", ".join(dc["equipos"]))}'
                                        f'</div>' + "".join(fila_partido_html(p) for p in dc["partidos"]),
                                        unsafe_allow_html=True)
                    with st.expander(":material/north: Clasificados · Ascensos", expanded=False):
                        asc_f = [(nom_f[SF["asc_directo"][0]], "campeón"), 
                                 (nom_f[SF["asc_directo"][1]], "2°"), 
                                 (nom_f[SF["asc_directo"][2]], "3°")]
                        if SF["asc_reducido"] is not None:
                            asc_f.append((nom_f[SF["asc_reducido"]], "reducido"))
                        st.markdown(lista_equipos_html(asc_f) + (
                            '' if SF["asc_reducido"] is not None else
                            '<div style="font-size:.8rem;opacity:.65">El cuarto ascenso sale del '
                            'reducido.</div>'), unsafe_allow_html=True)
                    with st.expander(":material/south: Descensos al Regional Amateur", expanded=False):
                        st.markdown('<div class="mlab">Descienden los 6 últimos de Zona Descenso (a la región '
                                    'de su provincia)</div>'
                                    + lista_equipos_html([(nom_f[i], region_regional(nom_f[i]))
                                                          for i in SF["descendidos"]]), unsafe_allow_html=True)

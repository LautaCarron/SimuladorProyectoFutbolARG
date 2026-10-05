"""Pestaña Ligas · Primera Nacional.

El código es el de simuladorafa.py, movido acá tal cual. `ctx` trae el estado y los ayudantes
compartidos de la interfaz (S, P, las pestañas, las banderas terminada_*, etc.).
"""

import streamlit as st
from datos import origen
from torneos import (
    B_F1,
    B_F2,
    B_RED,
    B_TOTAL,
    B_ZONAS2,
    primera_terminada,
    simular_fecha_b,
    tabla_b_f1,
    tabla_b_f2,
    total_b,
)
from vista import (
    COLORES_ZONA,
    LEY_B,
    aviso,
    barra_estado,
    bracket_html,
    chip,
    colorear_b,
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


def render(ctx):
    (P, S, SB, _abierta, b_espera_primera, editar_medias, html_tabla_liguilla, tab_b, tab_ligas,
     terminada_b) = (
        ctx.P, ctx.S, ctx.SB, ctx._abierta, ctx.b_espera_primera, ctx.editar_medias,
        ctx.html_tabla_liguilla, ctx.tab_b, ctx.tab_ligas, ctx.terminada_b)
    # ============================================================================
    # PRIMERA NACIONAL
    # ============================================================================
    if _abierta(tab_ligas, tab_b):
        with tab_b:
            fb = SB["fecha"]
            nom_b = SB["nombres"]
            extra = SB.get("extra_f2", 0)  # Offset dinámico por si se alarga con un desempate
    
            if fb < B_F1:
                fase_txt = "1 · Zonas A y B"
            elif fb < B_F1 + B_F2 + extra:
                if fb < B_F1 + B_F2:
                    fase_txt = "2 · Tres zonas"
                else:
                    fase_txt = "Desempate"
            elif fb < B_F1 + B_F2 + extra + B_RED:
                fase_txt = "Reducido"
            elif fb < B_TOTAL + extra:
                fase_txt = "Promoción"
            else:
                fase_txt = "Terminada"

            c1, c2, c3 = st.columns([3, 1.4, 1.4], vertical_alignment="center")
            c1.markdown(chip("Primera Nacional · 36 equipos") + " " + chip(f"Fase {fase_txt}", "#475569"),
                        unsafe_allow_html=True)
    
            if c2.button(":material/skip_next: Próxima fecha", key="b_next", width="stretch", type="primary",
                         disabled=terminada_b or b_espera_primera):
                simular_fecha_b(S, P)
                st.rerun()
        
            if c3.button(":material/fast_forward: Hasta el final", key="b_all", width="stretch",
                         disabled=terminada_b or b_espera_primera):
                while SB["fecha"] < total_b(SB) and not (SB["fecha"] == total_b(SB) - 1 and not primera_terminada(S)):
                    simular_fecha_b(S, P)
                st.rerun()

            pct_b_dyn = 100 * fb / (B_TOTAL + extra) if (B_TOTAL + extra) else 0
            barra_estado([("Fase", fase_txt), ("Fecha", f"{fb} / {B_TOTAL + extra}"),
                          ("Partidos jugados", len(SB["log"]))], pct_b_dyn)
                  
            if b_espera_primera:
                aviso("La Promoción se juega contra el 27° de Primera: terminá primero la temporada "
                      "de Primera División.")
            if fb == B_F1:
                aviso("Terminó la fase 1: se repartieron los equipos en las zonas Campeonato, "
                      "Intermedia y Descenso y <b>se conservan todos los puntos acumulados</b>.")
            if fb == B_F1 + B_F2 + extra:
                aviso("Terminó la fase 2 y sus definiciones: quedaron definidos los 12 clasificados al reducido. "
                      "Mirá el cuadro en la pestaña <b>Reducido</b>.")

            # ------------------ SISTEMA DE PESTAÑAS DINÁMICAS ------------------
            desempates_b = [p for p in SB["log"] if p["rotulo"] == "Desempate"]
            mostrar_desempate_b = SB.get("desempate_pendiente") or len(desempates_b) > 0
    
            titulos_b = ["Posiciones", "Fixture y resultados"]
            if mostrar_desempate_b: titulos_b.append("Desempate")
            titulos_b.extend(["Reducido", "Movimientos", "Definiciones"])
    
            sb = st.tabs(titulos_b)
            idx_b = 0
    
            with sb[idx_b]:
                if fb < B_F1:
                    seccion("Fase 1 · Zonas A y B", "Una rueda + 8 fechas interzonales · 18 equipos por zona", "#4f46e5")
                    tabs_b = st.tabs(["Zona A", "Zona B"])
                    for z, tab in enumerate(tabs_b):
                        with tab:
                            mostrar_tabla(tabla_b_f1(SB, z), colorear_b, SB["pos_hist"])
                    leyenda([("1°-6° → Zona Campeonato", COLORES_ZONA[0]),
                             ("7°-12° → Zona Intermedia", COLORES_ZONA[1]),
                             ("13°-18° → Zona Descenso", COLORES_ZONA[2])])
                else:
                    seccion("Fase 2 · Zonas", "Arrastran los puntos de la Fase 1 · una rueda por zona", "#16a34a")
                    tabs_b = st.tabs([f"Zona {n}" for n in B_ZONAS2] + ["Fase 1"])
                    for z in range(3):
                        with tabs_b[z]:
                            mostrar_tabla(tabla_b_f2(SB, z), colorear_b, SB["pos_hist"])
                    with tabs_b[3]:
                        for z, nz in enumerate(["Zona A", "Zona B"]):
                            st.markdown(chip(nz), unsafe_allow_html=True)
                            mostrar_tabla(SB["tablas_f1"][z], colorear_b)
                        st.caption("Posiciones finales de la fase 1 (sus puntos ya no cuentan).")
                    leyenda(LEY_B + [("Desempate Permanencia", "rgba(147, 51, 234, 0.3)")])
            
                with st.expander(":material/info: Formato de la Primera Nacional"):
                    st.markdown(
                        "Fase 1: dos zonas de 18, una rueda, más 8 fechas interzonales (localía fija "
                        "4 y 4) cruzando ambas zonas. "
                        "Después, conservando los puntos acumulados, se arman "
                        "Campeonato, Intermedia y Descenso (12 cada una), una rueda cada una "
                        "(si dos equipos ya se cruzaron en la fase 1, la revancha es con la localía "
                        "invertida). Campeonato: 1° campeón y ascenso, 2° ascenso, 3°-4° a cuartos, "
                        "5°-12° a octavos. Intermedia: 1°-4° a octavos. Descenso: bajan los 6 últimos. "
                        "Reducido a partido único con penales directos; el campeón asciende y el perdedor "
                        "de la final juega la promoción contra el 27° de Primera.")
                
                if fb == 0:
                    with st.expander(":material/tune: Editar medias internas de esta temporada (Primera Nacional)"):
                        SB["r"] = editar_medias(SB["nombres"], SB["r"], f"editor_b_{S['temp']}")
            idx_b += 1
    
            with sb[idx_b]: 
                vista_fixture("b")
            idx_b += 1
    
            if mostrar_desempate_b:
                with sb[idx_b]:
                    if SB.get("desempate_pendiente"):
                        seccion("Desempates en la Primera Nacional", "Están empatados en puntos. Jugarán un desempate.", "#9333ea")
                        for z_des in (0, 2):
                            df_des = tabla_b_f2(SB, z_des)
                            df_des = df_des[df_des["id"].isin(SB["ids_desempate"])]
                            if len(df_des):
                                mostrar_tabla(df_des, colorear_b)
                    else:
                        grupos = {}
                        for p in desempates_b:
                            m = p["comp"]
                            if m not in grupos: grupos[m] = []
                            grupos[m].append(p)
                
                        for motivo, parts in grupos.items():
                            if "Liguilla" in motivo:
                                seccion(f"Tabla final: {motivo}", "Posiciones del mini-torneo a partido único", "#9333ea")
                                st.markdown(html_tabla_liguilla(parts), unsafe_allow_html=True)
                                with st.expander(f":material/visibility: Ver los {len(parts)} enfrentamientos", expanded=False):
                                    for p in parts:
                                        st.markdown(fila_partido_html(p), unsafe_allow_html=True)
                            else:
                                seccion(f"Desempate: {motivo}", "Partido único definitorio", "#dc2626")
                                for p in parts:
                                    st.markdown(fila_partido_html(p, abierto=True), unsafe_allow_html=True)
                idx_b += 1

            with sb[idx_b]:
                seccion("Reducido por el tercer ascenso",
                        "Octavos → Cuartos → Semifinal → Final · partido único, penales si empatan · "
                        "L = local, V = visitante, N = neutral", "#2563eb")
                if fb < B_F1 + B_F2 + extra:
                    aviso("El cuadro se completa al terminar la fase 2 y sus posibles desempates. Entran 3°-4° de Zona Campeonato "
                          "(directo a cuartos), 5°-12° de Campeonato y 1°-4° de Intermedia (octavos).")
                st.markdown(bracket_html(SB), unsafe_allow_html=True)
                if SB["entrantes"] is not None:
                    with st.expander("Clasificados al reducido (orden de mérito)"):
                        st.markdown(tabla_html(SB["entrantes"]), unsafe_allow_html=True)
            idx_b += 1
    
            with sb[idx_b]:
                render_movimientos(SB["log"], SB["pos_hist"], nom_b, "#0f766e")
            idx_b += 1
        
            with sb[idx_b]:
                seccion("Definiciones de la temporada", "Campeón, ascensos, promoción y descensos",
                        "#b7860b")
                if SB["campeon"] is None:
                    aviso("Las definiciones aparecen acá cuando termina la fase 2 de la Primera Nacional.")
                else:
                    st.caption("Están cerradas para no spoilear: tocá cada una para verla.")
                    e1, e2 = st.columns(2)
                    with e1:
                        with st.expander(":material/emoji_events: Campeón de la Primera Nacional", expanded=False):
                            cb = nom_b[SB["campeon"]]
                            st.markdown(f'<div class="champ"><div class="t">Campeón · Temporada {S["temp"]}'
                                        f'</div><div style="margin-top:10px">{crest(cb, 64)}</div>'
                                        f'<div class="nm">{esc(cb)}</div><div class="s">Asciende a Primera'
                                        f'</div></div>', unsafe_allow_html=True)
                        with st.expander(":material/north: Clasificados · Ascensos", expanded=False):
                            asc = [(nom_b[SB["asc_directo"][0]], "campeón"), (nom_b[SB["asc_directo"][1]], "2°")]
                            if SB["asc_reducido"] is not None:
                                asc.append((nom_b[SB["asc_reducido"]], "reducido"))
                            if SB["promo"] and SB["promo"]["gana_b"]:
                                asc.append((nom_b[SB["promo"]["b_id"]], "promoción"))
                            st.markdown(lista_equipos_html(asc) + (
                                '' if SB["asc_reducido"] is not None else
                                '<div style="font-size:.8rem;opacity:.65">El tercer ascenso sale del '
                                'reducido.</div>'), unsafe_allow_html=True)
                    with e2:
                        with st.expander(":material/swap_vert: Promoción", expanded=False):
                            if SB["promo_partido"]:
                                st.markdown(fila_partido_html(SB["promo_partido"], abierto=True),
                                            unsafe_allow_html=True)
                            elif SB["perdedor_final"] is not None:
                                st.markdown('<div class="mlab">Juega la promoción (perdedor de la final)</div>'
                                            + lista_equipos_html([(nom_b[SB["perdedor_final"]], "")]),
                                            unsafe_allow_html=True)
                            else:
                                st.caption("La juega el perdedor de la final del reducido contra el 27° "
                                           "de Primera.")
                        with st.expander(":material/south: Descensos", expanded=False):
                            st.markdown(
                                '<div class="mlab">Descienden (7° al 12° de Zona Descenso): al Federal '
                                'A los del interior, a la Primera B los metropolitanos</div>'
                                + lista_equipos_html([
                                    (nom_b[i], "Federal A" if origen(nom_b[i]) == "Interior" else "Primera B")
                                    for i in SB["desc_b"]
                                ]), unsafe_allow_html=True)

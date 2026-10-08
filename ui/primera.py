"""Pestaña Ligas · Primera División.

El código es el de simuladorafa.py, movido acá tal cual. `ctx` trae el estado y los ayudantes
compartidos de la interfaz (S, P, las pestañas, las banderas terminada_*, etc.).
Modo manager: en la fase 2 se abre sola (y se marca con ⭐) la zona donde juega el club que dirigís.
"""

import streamlit as st
from datos.equipos import N
from ligas.primera import (
    FECHAS_F1,
    TOTAL_FECHAS,
    ZONAS,
    simular_fecha,
    tabla_final,
    tabla_general,
    tabla_zona,
)
from ui.vista import (
    LEY_DESTINOS,
    LEY_ZONAS,
    aviso,
    barra_estado,
    chip,
    colorear_destino,
    colorear_fase1,
    crest,
    esc,
    fila_partido_html,
    leyenda,
    lista_equipos_html,
    mostrar_tabla,
    render_movimientos,
    seccion,
    vista_fixture,
)
from ui.vista.mi_club import marcar, mi_club, zona_primera


def render(ctx):
    (P, S, SB, _abierta, acumular, editar_medias, html_tabla_liguilla, tab_ligas, tab_p) = (
        ctx.P, ctx.S, ctx.SB, ctx._abierta, ctx.acumular, ctx.editar_medias, ctx.html_tabla_liguilla,
        ctx.tab_ligas, ctx.tab_p)
    # ============================================================================
    # PRIMERA DIVISIÓN
    # ============================================================================
    if _abierta(tab_ligas, tab_p):
        with tab_p:
            c1, c2, c3 = st.columns([3, 1.4, 1.4], vertical_alignment="center")
            c1.markdown(chip("Liga Profesional · 30 equipos", "#1e5aa8") + " " +
                        chip("Fase 1 · todos contra todos" if S["fase"] == 1 else "Fase 2 · zonas"),
                        unsafe_allow_html=True)
                
            extra_p = S.get("extra_f2", 0)
            terminada_p_dyn = S["fecha"] >= TOTAL_FECHAS + extra_p
    
            if c2.button(":material/skip_next: Próxima fecha", key="p_next", disabled=terminada_p_dyn, width="stretch",
                         type="primary"):
                simular_fecha(S, P, acumular)
                st.rerun()
            if c3.button(":material/fast_forward: Hasta el final", key="p_all", disabled=terminada_p_dyn, width="stretch"):
                while S["fecha"] < TOTAL_FECHAS + S.get("extra_f2", 0):
                    simular_fecha(S, P, acumular)
                st.rerun()

            jugados = int(S["pj"].sum() // 2)
            pct = 100 * S["sorpresas"] / jugados if jugados else 0
            pct_p = 100 * S["fecha"] / (TOTAL_FECHAS + extra_p) if (TOTAL_FECHAS + extra_p) else 0
    
            barra_estado([("Fase", "1 · Todos contra todos" if S["fase"] == 1 else "2 · Zonas"),
                          ("Fecha", f"{S['fecha']} / {TOTAL_FECHAS + extra_p}"),
                          ("Sorpresas", f"{S['sorpresas']} ({pct:.0f}%)")], pct_p)
                  
            if S["fase"] == 2 and S["fecha"] == FECHAS_F1:
                aviso("Terminó la fase 1: se armaron las zonas Campeonato, Intermedia y Descenso. "
                      "Las 9 fechas siguientes se juegan dentro de cada zona, con la localía invertida.")

            desempates_p = [p for p in S["log"] if p["rotulo"] == "Desempate"]
            mostrar_desempate_p = S.get("desempate_pendiente") or len(desempates_p) > 0
    
            titulos_p = ["Posiciones", "Fixture y resultados"]
            if mostrar_desempate_p: titulos_p.append("Desempate")
            titulos_p.extend(["Movimientos", "Definiciones"])
    
            sp = st.tabs(titulos_p)
            idx_p = 0
    
            with sp[idx_p]:
                if S["fase"] == 1:
                    seccion("Tabla de posiciones", "Fase 1 · 29 fechas, todos contra todos", "#475569")
                    mostrar_tabla(tabla_general(S), colorear_fase1, S["pos_hist"])
                    leyenda(LEY_ZONAS)
                else:
                    seccion("Fase 2 · Zonas", "9 fechas dentro de cada zona, localía invertida", "#16a34a")
                    # modo manager: se abre sola la zona de mi club
                    etiq, ini = marcar([f"Zona {n}" for n in ZONAS] + ["Tabla fase 1"], zona_primera(S, mi_club()))
                    tabs = st.tabs(etiq, default=ini)
                    for z, tab in enumerate(tabs[:3]):
                        with tab:
                            mostrar_tabla(tabla_zona(S, z), colorear_destino, S["pos_hist"])
                    with tabs[3]:
                        mostrar_tabla(S["tabla_f1"], colorear_fase1)
                        st.caption("Tabla final de las 29 fechas de la fase 1.")
                    leyenda(LEY_DESTINOS + [("Desempate Campeonato", "rgba(249, 115, 22, 0.3)"), ("Desempate Permanencia/Promoción", "rgba(147, 51, 234, 0.3)")])
            
                if S["fecha"] == 0:
                    with st.expander(":material/tune: Editar medias internas de esta temporada"):
                        S["r"] = editar_medias(S["nombres"], S["r"], f"editor_p_{S['temp']}")
            idx_p += 1
    
            with sp[idx_p]:
                vista_fixture("p")
            idx_p += 1
    
            if mostrar_desempate_p:
                with sp[idx_p]:
                    if S.get("desempate_pendiente"):
                        seccion("Desempate en Primera", "Están empatados en puntos críticos. Jugarán un desempate.", "#9333ea")
                        for z in [0, 2]:
                            df_des = tabla_zona(S, z)
                            df_des = df_des[df_des["id"].isin(S.get("ids_desempate", []))]
                            if not df_des.empty:
                                mostrar_tabla(df_des, colorear_destino)
                    else:
                        grupos = {}
                        for p in desempates_p:
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
                idx_p += 1
        
            with sp[idx_p]:
                render_movimientos(S["log"], S["pos_hist"], S["nombres"], "#1e5aa8")
            idx_p += 1
    
            with sp[idx_p]:
                seccion("Definiciones de la temporada", "Campeón, copas, promoción y descensos", "#b7860b")
                if not terminada_p_dyn:
                    aviso("Las definiciones aparecen acá cuando termina la temporada de Primera. "
                          "Destinos: 1°-5° Libertadores · 6°-8° y 12°-13° Sudamericana · 11° fase previa "
                          "de Libertadores · 27° Promoción · 28°-30° descienden.")
                else:
                    final = tabla_final(S)
                    def equipos(posiciones):
                        sel = final[final["Pos"].isin(list(posiciones))]
                        return lista_equipos_html([(r.Equipo, f"{r.Pos}°") for r in sel.itertuples()])

                    st.caption("Están cerradas para no spoilear: tocá cada una para verla.")
                    e1, e2 = st.columns(2)
                    with e1:
                        with st.expander(":material/emoji_events: Campeón de Primera División", expanded=False):
                            campeon = final.iloc[0]["Equipo"]
                            st.markdown(f'<div class="champ"><div class="t">Campeón · Temporada {S["temp"]}'
                                        f'</div><div style="margin-top:10px">{crest(campeon, 64)}</div>'
                                        f'<div class="nm">{esc(campeon)}</div></div>', unsafe_allow_html=True)
                        with st.expander(":material/public: Clasificados · Copa Libertadores", expanded=False):
                            st.markdown('<div class="mlab">Fase de grupos (1° al 5°)</div>'
                                        + equipos(range(1, 6)) + '<div class="mlab">Fase previa (11°)</div>'
                                        + equipos([11]), unsafe_allow_html=True)
                        with st.expander(":material/public: Copa Sudamericana", expanded=False):
                            st.markdown('<div class="mlab">6° al 8° y 12°-13°</div>'
                                        + equipos(list(range(6, 9)) + [12, 13]), unsafe_allow_html=True)
                    with e2:
                        with st.expander(":material/swap_vert: Promoción", expanded=False):
                            txt = ('<div class="mlab">Juega la Promoción contra el perdedor de la final '
                                   'del reducido (27°)</div>' + equipos([N - 3]))
                            if SB["promo_partido"]:
                                txt += fila_partido_html(SB["promo_partido"])
                            st.markdown(txt, unsafe_allow_html=True)
                        with st.expander(":material/south: Descensos", expanded=False):
                            st.markdown('<div class="mlab">Descienden a la Primera Nacional (28° al 30°)</div>'
                                        + equipos(range(N - 2, N + 1)), unsafe_allow_html=True)

    # -----------------
    # Recordá que, ARRIBA DE TODO, el botón general ("Simular todo") 
    # debe arrancar así para leer el alargue:
    # while S["fecha"] < TOTAL_FECHAS + S.get("extra_f2", 0): 
    #     simular_fecha(S, P, acumular)

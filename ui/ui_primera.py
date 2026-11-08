"""Pestaña Ligas · Primera División.

Según el formato elegido en el Modo dios (ver ligas/primera.py) la pestaña muestra:
  * "actual": fase 1 + zonas Campeonato / Intermedia / Descenso.
  * "anual_ida" / "anual_ida_vuelta": una tabla anual.
  * "apertura_clausura": zonas A y B de cada torneo, tabla anual y llaves.
Modo manager: se abre sola (y se marca con ⭐) la zona donde juega el club que dirigís.
"""

import streamlit as st
from ligas import apertura_clausura as ac
from ligas.primera import (
    fechas_f1,
    fechas_f2,
    ZONAS,
    descensos,
    formato,
    primera_terminada,
    simular_fecha,
    tabla_general,
    tabla_zona,
    total_primera,
)
from ui.vista.editor_medias import editar_medias
from ui.vista.liguilla import html_tabla_liguilla
from ui.vista import (
    LEY_DESTINOS,
    LEY_ZONAS,
    aviso,
    chip,
    colorear_destino,
    colorear_fase1,
    fila_partido_html,
    leyenda,
    mostrar_tabla,
    render_movimientos,
    seccion,
    vista_fixture,
)
from ui.vista.formatos import colorear_llaves, cuadro_ac_html
from ui.vista.mi_club import marcar, tabs_con_default, zona_primera

_DESEMPATES = [("Desempate Campeonato", "rgba(249, 115, 22, 0.3)"),
               ("Desempate Permanencia/Promoción", "rgba(147, 51, 234, 0.3)")]


def _torneo_en_juego(S):
    """Torneo del Apertura/Clausura que se está jugando (0 o 1)."""
    return ac.etapa(min(S["fecha"] + 1, ac.TOTAL))[0]


def _desempates_html(ctx, grupos_log):
    """Los desempates ya jugados (partidos únicos y liguillas), agrupados por motivo."""
    S = ctx.S
    grupos = {}
    for p in grupos_log:
        grupos.setdefault(p["comp"], []).append(p)
    for motivo, parts in grupos.items():
        if "Liguilla" in motivo:
            seccion(f"Tabla final: {motivo}", color="#9333ea")
            st.markdown(html_tabla_liguilla(parts), unsafe_allow_html=True)
            with st.expander(f":material/visibility: Ver los {len(parts)} enfrentamientos", expanded=False):
                for p in parts:
                    st.markdown(fila_partido_html(S, ctx.club, p), unsafe_allow_html=True)
        else:
            seccion(f"Desempate: {motivo}", color="#dc2626")
            for p in parts:
                st.markdown(fila_partido_html(S, ctx.club, p, abierto=True), unsafe_allow_html=True)


def render(ctx):
    (P, S, SB, _abierta, acumular, tab_ligas, tab_p) = (
        ctx.P, ctx.S, ctx.SB, ctx.abierta, ctx.acumular, ctx.pestanas.tab_ligas, ctx.pestanas.tab_p)
    # ============================================================================
    # PRIMERA DIVISIÓN
    # ============================================================================
    if _abierta(tab_ligas, tab_p):
        with tab_p:
            fmt = formato(S)
            k = descensos(S)
            c1, c2, c3 = st.columns([3, 1.4, 1.4], vertical_alignment="center")
            chip_fase = {"actual": chip("Fase 1 · todos contra todos" if S["fase"] == 1 else "Fase 2 · zonas"),
                         "anual_ida": chip("Torneo anual · una rueda", "#475569"),
                         "anual_ida_vuelta": chip("Torneo anual · ida y vuelta", "#475569"),
                         "apertura_clausura": chip("Apertura y Clausura con llaves", "#475569")}[fmt]
            c1.markdown(chip(f"Liga Profesional · {len(S['nombres'])} equipos", "#1e5aa8") + " " + chip(f"Descienden {k}", "#b83a2e")
                        + " " + chip_fase, unsafe_allow_html=True)

            total_p = total_primera(S)
            terminada_p_dyn = primera_terminada(S)

            if not ctx.modo_mgr and c2.button(":material/skip_next: Próxima fecha", key="p_next", disabled=terminada_p_dyn, width="stretch",
                         type="primary"):
                simular_fecha(S, P, acumular)
                st.rerun()
            if not ctx.modo_mgr and c3.button(":material/fast_forward: Hasta el final", key="p_all", disabled=terminada_p_dyn, width="stretch"):
                while S["fecha"] < total_primera(S):
                    simular_fecha(S, P, acumular)
                st.rerun()

            jugados = int(S["pj"].sum() // 2)
            pct = 100 * S["sorpresas"] / jugados if jugados else 0
            pct_p = 100 * S["fecha"] / total_p if total_p else 0
            if fmt == "actual":
                fase_txt = "1 · Todos contra todos" if S["fase"] == 1 else "2 · Zonas"
            elif fmt == "apertura_clausura":
                fase_txt = "Terminada" if terminada_p_dyn else ac.rotulo(S["fecha"] + 1)
            else:
                fase_txt = "Torneo anual"

            if fmt == "actual" and S["fase"] == 2 and S["fecha"] == fechas_f1(S):
                aviso("Terminó la fase 1: se armaron las zonas Campeonato, Intermedia y Descenso. "
                      f"Las {fechas_f2(S)} fechas siguientes se juegan dentro de cada zona, con la localía invertida.")

            desempates_p = [p for p in S["log"] if p["rotulo"] == "Desempate"]
            mostrar_desempate_p = S.get("desempate_pendiente") or len(desempates_p) > 0

            titulos_p = ["Posiciones", "Fixture y resultados"]
            if mostrar_desempate_p:
                titulos_p.append("Desempate")
            if fmt == "apertura_clausura":
                titulos_p.append("Llaves")
            titulos_p.extend(["Movimientos"])

            sp = dict(zip(titulos_p, st.tabs(titulos_p)))

            # ------------------------------------------------------------ POSICIONES
            with sp["Posiciones"]:
                if fmt == "actual":
                    if S["fase"] == 1:
                        seccion("Tabla de posiciones", color="#475569")
                        mostrar_tabla(tabla_general(S), colorear_fase1(S), S["pos_hist"])
                        leyenda(LEY_ZONAS)
                    else:
                        seccion("Fase 2 · Zonas", color="#16a34a")
                        # modo manager: se abre sola la zona de mi club
                        etiq, ini = marcar([f"Zona {n}" for n in ZONAS] + ["Tabla fase 1"], zona_primera(S, ctx.club))
                        tabs = tabs_con_default(etiq, ini)
                        for z, tab in enumerate(tabs[:3]):
                            with tab:
                                mostrar_tabla(tabla_zona(S, z), colorear_destino, S["pos_hist"])
                        with tabs[3]:
                            mostrar_tabla(S["tabla_f1"], colorear_fase1(S))
                            st.caption("Tabla final de las 29 fechas de la fase 1.")
                        leyenda(LEY_DESTINOS + _DESEMPATES)
                elif fmt == "apertura_clausura":
                    t_juego = _torneo_en_juego(S)
                    t = ac.NOMBRES.index(st.segmented_control(
                        "Torneo", ac.NOMBRES, default=ac.NOMBRES[t_juego], key=f"ac_torneo_pos_{S['temp']}")
                        or ac.NOMBRES[t_juego])
                    seccion(f"{ac.NOMBRES[t]} · zonas", color="#16a34a")
                    etiq, ini = marcar(["Zona A", "Zona B", "Tabla anual"], zona_primera(S, ctx.club))
                    tabs = tabs_con_default(etiq, ini)
                    for z in (0, 1):
                        with tabs[z]:
                            mostrar_tabla(ac.tabla_zona(S, t, z), colorear_llaves)
                    with tabs[2]:
                        mostrar_tabla(tabla_general(S), colorear_destino, S["pos_hist"])
                        st.caption("Puntos de las dos etapas regulares (las llaves no suman). Define la copa, "
                                   "la promoción y los descensos; el primero es el Campeón de Liga.")
                    leyenda([("Pasa a las llaves", "rgba(46, 125, 79, 0.22)")] + LEY_DESTINOS)
                else:
                    seccion("Tabla anual", color="#475569")
                    mostrar_tabla(tabla_general(S), colorear_destino, S["pos_hist"])
                    leyenda([("Líder", LEY_DESTINOS[0][1])] + LEY_DESTINOS[1:] + _DESEMPATES)

                if S["fecha"] == 0 and not ctx.modo_mgr:       # en modo manager no se tocan las medias
                    with st.expander(":material/tune: Editar medias internas de esta temporada"):
                        S["r"] = editar_medias(S["nombres"], S["r"], f"editor_p_{S['temp']}")

            # ------------------------------------------------------------ FIXTURE
            with sp["Fixture y resultados"]:
                vista_fixture(S, ctx.club, "p")

            # ------------------------------------------------------------ DESEMPATE
            if mostrar_desempate_p:
                with sp["Desempate"]:
                    if S.get("desempate_pendiente"):
                        seccion("Desempate en Primera", color="#9333ea")
                        if fmt == "actual":
                            for z in [0, 2]:
                                df_des = tabla_zona(S, z)
                                df_des = df_des[df_des["id"].isin(S.get("ids_desempate", []))]
                                if not df_des.empty:
                                    mostrar_tabla(df_des, colorear_destino)
                        else:
                            df_des = tabla_general(S)
                            df_des = df_des[df_des["id"].isin(S.get("ids_desempate", []))]
                            if not df_des.empty:
                                mostrar_tabla(df_des, colorear_destino)
                    else:
                        _desempates_html(ctx, desempates_p)

            # ------------------------------------------------------------ LLAVES (Apertura y Clausura)
            if fmt == "apertura_clausura":
                with sp["Llaves"]:
                    t_juego = _torneo_en_juego(S)
                    t = ac.NOMBRES.index(st.segmented_control(
                        "Torneo", ac.NOMBRES, default=ac.NOMBRES[t_juego], key=f"ac_torneo_llaves_{S['temp']}",
                        label_visibility="collapsed") or ac.NOMBRES[t_juego])
                    T = S["ac"]["T"][t]
                    seccion(f"Llaves del {ac.NOMBRES[t]}", color="#2563eb")
                    if not T["cuadro"]:
                        aviso("Las llaves se arman al terminar la etapa regular (fecha 15 del torneo).")
                    st.markdown(cuadro_ac_html(S, t), unsafe_allow_html=True)

            # ------------------------------------------------------------ MOVIMIENTOS
            with sp["Movimientos"]:
                render_movimientos(S["log"], S["pos_hist"], S["nombres"], "#1e5aa8")


    # -----------------
    # Recordá que, ARRIBA DE TODO, el botón general ("Simular todo")
    # debe arrancar así para leer el alargue:
    # while S["fecha"] < total_primera(S):
    #     simular_fecha(S, P, acumular)

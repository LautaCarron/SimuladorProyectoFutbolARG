"""Pestaña Ligas · Primera División.

Según el formato elegido en el Modo dios (ver ligas/primera.py) la pestaña muestra:
  * "actual": fase 1 + zonas Campeonato / Intermedia / Descenso.
  * "anual_ida" / "anual_ida_vuelta": una tabla anual.
  * "apertura_clausura": zonas A y B de cada torneo, tabla anual y llaves.
Modo manager: se abre sola (y se marca con ⭐) la zona donde juega el club que dirigís.
"""

import streamlit as st
from ligas import apertura_clausura as ac
from ligas.primera import promos
from ligas.primera import (
    fechas_f1,
    fechas_f2,
    ZONAS,
    descensos,
    formato,
    primera_terminada,
    simular_fecha,
    tabla_final,
    tabla_general,
    tabla_zona,
    total_primera,
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
from ui.vista.formatos import colorear_llaves, cuadro_ac_html
from ui.vista.mi_club import marcar, mi_club, modo_manager, tabs_con_default, zona_primera

_DESEMPATES = [("Desempate Campeonato", "rgba(249, 115, 22, 0.3)"),
               ("Desempate Permanencia/Promoción", "rgba(147, 51, 234, 0.3)")]


def _torneo_en_juego(S):
    """Torneo del Apertura/Clausura que se está jugando (0 o 1)."""
    return ac.etapa(min(S["fecha"] + 1, ac.TOTAL))[0]


def _desempates_html(ctx, grupos_log):
    """Los desempates ya jugados (partidos únicos y liguillas), agrupados por motivo."""
    S, html_tabla_liguilla = ctx.S, ctx.html_tabla_liguilla
    grupos = {}
    for p in grupos_log:
        grupos.setdefault(p["comp"], []).append(p)
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


def render(ctx):
    (P, S, SB, _abierta, acumular, editar_medias, html_tabla_liguilla, tab_ligas, tab_p) = (
        ctx.P, ctx.S, ctx.SB, ctx._abierta, ctx.acumular, ctx.editar_medias, ctx.html_tabla_liguilla,
        ctx.tab_ligas, ctx.tab_p)
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

            extra_p = S.get("extra_f2", 0)
            total_p = total_primera(S)
            terminada_p_dyn = primera_terminada(S)

            if c2.button(":material/skip_next: Próxima fecha", key="p_next", disabled=terminada_p_dyn, width="stretch",
                         type="primary"):
                simular_fecha(S, P, acumular)
                st.rerun()
            if c3.button(":material/fast_forward: Hasta el final", key="p_all", disabled=terminada_p_dyn, width="stretch"):
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
            barra_estado([("Fase", fase_txt), ("Fecha", f"{S['fecha']} / {total_p}"),
                          ("Sorpresas", f"{S['sorpresas']} ({pct:.0f}%)")], pct_p)

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
            titulos_p.extend(["Movimientos", "Definiciones"])

            sp = dict(zip(titulos_p, st.tabs(titulos_p)))

            # ------------------------------------------------------------ POSICIONES
            with sp["Posiciones"]:
                if fmt == "actual":
                    if S["fase"] == 1:
                        seccion("Tabla de posiciones", "Fase 1 · 29 fechas, todos contra todos", "#475569")
                        mostrar_tabla(tabla_general(S), colorear_fase1, S["pos_hist"])
                        leyenda(LEY_ZONAS)
                    else:
                        seccion("Fase 2 · Zonas", "9 fechas dentro de cada zona, localía invertida", "#16a34a")
                        # modo manager: se abre sola la zona de mi club
                        etiq, ini = marcar([f"Zona {n}" for n in ZONAS] + ["Tabla fase 1"], zona_primera(S, mi_club()))
                        tabs = tabs_con_default(etiq, ini)
                        for z, tab in enumerate(tabs[:3]):
                            with tab:
                                mostrar_tabla(tabla_zona(S, z), colorear_destino, S["pos_hist"])
                        with tabs[3]:
                            mostrar_tabla(S["tabla_f1"], colorear_fase1)
                            st.caption("Tabla final de las 29 fechas de la fase 1.")
                        leyenda(LEY_DESTINOS + _DESEMPATES)
                elif fmt == "apertura_clausura":
                    t_juego = _torneo_en_juego(S)
                    t = ac.NOMBRES.index(st.segmented_control(
                        "Torneo", ac.NOMBRES, default=ac.NOMBRES[t_juego], key=f"ac_torneo_pos_{S['temp']}")
                        or ac.NOMBRES[t_juego])
                    seccion(f"{ac.NOMBRES[t]} · zonas", "15 fechas: todos contra todos en la zona y un clásico "
                            "interzonal · pasan a las llaves los 8 primeros de cada zona", "#16a34a")
                    etiq, ini = marcar(["Zona A", "Zona B", "Tabla anual"], zona_primera(S, mi_club()))
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
                    seccion("Tabla anual", ("29 fechas, todos contra todos" if fmt == "anual_ida"
                                            else "58 fechas, todos contra todos ida y vuelta"), "#475569")
                    mostrar_tabla(tabla_general(S), colorear_destino, S["pos_hist"])
                    leyenda([("Líder", LEY_DESTINOS[0][1])] + LEY_DESTINOS[1:] + _DESEMPATES)

                if S["fecha"] == 0 and not modo_manager():       # en modo manager no se tocan las medias
                    with st.expander(":material/tune: Editar medias internas de esta temporada"):
                        S["r"] = editar_medias(S["nombres"], S["r"], f"editor_p_{S['temp']}")

            # ------------------------------------------------------------ FIXTURE
            with sp["Fixture y resultados"]:
                vista_fixture("p")

            # ------------------------------------------------------------ DESEMPATE
            if mostrar_desempate_p:
                with sp["Desempate"]:
                    if S.get("desempate_pendiente"):
                        seccion("Desempate en Primera", "Están empatados en puntos críticos. Jugarán un desempate.", "#9333ea")
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
                    seccion(f"Llaves del {ac.NOMBRES[t]}", "Octavos, cuartos y semifinales a partido único (de local el "
                            "mejor ubicado) · final en cancha neutral · si empatan, penales", "#2563eb")
                    if not T["cuadro"]:
                        aviso("Las llaves se arman al terminar la etapa regular (fecha 15 del torneo).")
                    st.markdown(cuadro_ac_html(S, t), unsafe_allow_html=True)

            # ------------------------------------------------------------ MOVIMIENTOS
            with sp["Movimientos"]:
                render_movimientos(S["log"], S["pos_hist"], S["nombres"], "#1e5aa8")

            # ------------------------------------------------------------ DEFINICIONES
            with sp["Definiciones"]:
                seccion("Definiciones de la temporada", "Campeón, copas, promoción y descensos", "#b7860b")
                N = len(S["nombres"])                     # equipos de Primera esta temporada
                prom = N - k
                if not terminada_p_dyn:
                    aviso("Las definiciones aparecen acá cuando termina la temporada de Primera. "
                          + ("Destinos: 1°-5° Libertadores · 6°-8° y 12°-13° Sudamericana · 11° fase previa "
                             "de Libertadores · "
                             if fmt == "actual" else
                             "Destinos: 1°-5° Libertadores · 6° fase previa de Libertadores · 7°-11° Sudamericana · ")
                          + (f"{prom - promos(S) + 1}°-{prom}° Promoción · " if promos(S) > 1 else
                             f"{prom}° Promoción · " if promos(S) == 1 else "")
                          + (f"{prom + 1}°-{N}° descienden." if k else "no desciende nadie directo."))
                else:
                    final = tabla_final(S)

                    def equipos(posiciones):
                        sel = final[final["Pos"].isin(list(posiciones))]
                        return lista_equipos_html([(r.Equipo, f"{r.Pos}°") for r in sel.itertuples()])

                    st.caption("Están cerradas para no spoilear: tocá cada una para verla.")
                    e1, e2 = st.columns(2)
                    with e1:
                        if fmt == "apertura_clausura":
                            with st.expander(":material/emoji_events: Campeones del Apertura, del Clausura y de la Liga",
                                             expanded=False):
                                for rotulo_t, nombre_t in (
                                        ("Campeón del Apertura", S["nombres"][S["ac"]["T"][0]["campeon"]]),
                                        ("Campeón del Clausura", S["nombres"][S["ac"]["T"][1]["campeon"]]),
                                        ("Campeón de Liga (tabla anual)", final.iloc[0]["Equipo"])):
                                    st.markdown(f'<div class="champ"><div class="t">{rotulo_t} · Temporada {S["temp"]}'
                                                f'</div><div style="margin-top:10px">{crest(nombre_t, 64)}</div>'
                                                f'<div class="nm">{esc(nombre_t)}</div></div>', unsafe_allow_html=True)
                        else:
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
                            pp = promos(S)
                            if pp == 0:
                                st.caption("Esta temporada no hay promoción.")
                            else:
                                pos_p = list(range(prom - pp + 1, prom + 1))
                                txt = ('<div class="mlab">Juegan la Promoción contra equipos de la B ('
                                       + ", ".join(f"{p}°" for p in pos_p) + ')</div>' + equipos(pos_p))
                                for pm in SB.get("promo_partidos") or []:
                                    txt += fila_partido_html(pm)
                                st.markdown(txt, unsafe_allow_html=True)
                        with st.expander(":material/south: Descensos", expanded=False):
                            if k:
                                st.markdown(f'<div class="mlab">Descienden a la Primera Nacional ({prom + 1}° al {N}°)</div>'
                                            + equipos(range(prom + 1, N + 1)), unsafe_allow_html=True)
                            else:
                                st.caption("Esta temporada no desciende nadie directo (sólo se juega la promoción).")

    # -----------------
    # Recordá que, ARRIBA DE TODO, el botón general ("Simular todo")
    # debe arrancar así para leer el alargue:
    # while S["fecha"] < total_primera(S):
    #     simular_fecha(S, P, acumular)

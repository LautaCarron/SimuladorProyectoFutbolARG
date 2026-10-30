"""Pestaña Ligas · Primera Nacional.

El código es el de simuladorafa.py, movido acá tal cual. `ctx` trae el estado y los ayudantes
compartidos de la interfaz (S, P, las pestañas, las banderas terminada_*, etc.).
Modo manager: se abre sola (y se marca con ⭐) la zona donde juega el club que dirigís
(Zona A / B en la fase 1; Campeonato / Intermedia / Descenso en la fase 2).
"""

import streamlit as st
from datos.equipos import origen
from ligas.nacional import (
    B_MAX_ANUAL,
    B_ZONAS2,
    b_f1,
    b_f2,
    es_anual_b,
    formato_b,
    plan_de,
    rangos_fase1,
    red_b,
    simular_fecha_b,
    tabla_b_anual,
    tabla_b_f1,
    tabla_b_f2,
    total_b,
    total_base_b,
)
from ligas.nacional import k_prom, promo_cands
from ligas.primera import descensos, primera_terminada
from ui.vista.editor_medias import editar_medias
from ui.vista.liguilla import html_tabla_liguilla
from ui.vista import (
    COLORES_ZONA,
    LEY_B,
    aviso,
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
from ui.vista.base import COLORES_B
from ui.vista.mi_club import marcar, tabs_con_default, zona_nacional


def _vs_primera(SB):
    """'el 27° de Primera' / 'el 27° y el 26° de Primera' según las promociones de la temporada."""
    pos = SB.get("promo_pos") or []
    return " y el ".join(f"{p}°" for p in pos).join(["el ", " de Primera"]) if pos else "los de abajo de Primera"


def _promo_anual(SB):
    """Frase de la promoción para el torneo anual."""
    p = k_prom(SB)
    return ("no hay promoción" if p == 0 else
            f"el siguiente juega la promoción contra {_vs_primera(SB)}" if p == 1 else
            f"los dos siguientes juegan la promoción contra {_vs_primera(SB)}")


def _promo_reducido(SB):
    """Frase de la promoción cuando esta temporada hay reducido."""
    p = k_prom(SB)
    return ("no hay promoción" if p == 0 else
            f"el perdedor de la final juega la promoción contra {_vs_primera(SB)}" if p == 1 else
            f"el perdedor de la final y el mejor ubicado de los otros que perdieron juegan la promoción contra "
            f"{_vs_primera(SB)}")


def _promo_texto(SB):
    """Frase de la promoción según haya o no reducido esta temporada."""
    return _promo_reducido(SB) if red_b(SB)["reducido"] else _promo_anual(SB)


def _frase_ascensos(SB):
    """'Suben 2 directo y el ganador del reducido (3° al 16°)': lo que se juega esta temporada en la B."""
    pr = red_b(SB)
    d = pr["directos"]
    directos = ("no sube nadie directo" if d == 0 else "sube 1 directo (el campeón)" if d == 1
                else "suben 2 directo (el campeón y el 2°)" if d == 2
                else f"suben {d} directo (del 1° al {d}°)")
    if pr["reducido"]:
        return (f"{directos}, y el ganador del reducido (del {d + 1}° al {d + pr['equipos']}° de la tabla) "
                "sube uno más")
    return f"{directos}; no hay reducido"


def render(ctx):
    (P, S, SB, _abierta, b_espera_primera, tab_b, tab_ligas,
     terminada_b) = (
        ctx.P, ctx.S, ctx.SB, ctx.abierta, ctx.progreso.b_espera_primera, ctx.pestanas.tab_b, ctx.pestanas.tab_ligas, ctx.progreso.terminada_b)
    # ============================================================================
    # PRIMERA NACIONAL
    # ============================================================================
    if _abierta(tab_ligas, tab_b):
        with tab_b:
            fb = SB["fecha"]
            nom_b = SB["nombres"]
            extra = SB.get("extra_f2", 0)  # Offset dinámico por si se alarga con un desempate
    
            anual = es_anual_b(SB)                         # torneo anual (24 equipos o menos, o Modo dios): una sola tabla
            base_b = total_base_b(SB)
            plan = plan_de(SB)                             # zonas, fechas y descensos según la cantidad de equipos
            n_b, desc_b = len(nom_b), plan["desc"]
            B_F1, B_F2 = b_f1(SB), b_f2(SB)
            za, zb = plan.get("zona_tam", (0, 0))          # tamaño de las zonas A y B de la fase 1
            if anual:
                fase_txt = ("Terminada" if fb >= total_b(SB) else
                            "Promoción" if fb >= base_b + red_b(SB)["rondas"] else
                            "Reducido" if fb >= base_b else "Todos contra todos")
            elif fb < B_F1:
                fase_txt = "1 · Zonas A y B"
            elif fb < B_F1 + B_F2 + extra:
                if fb < B_F1 + B_F2:
                    fase_txt = "2 · Tres zonas"
                else:
                    fase_txt = "Desempate"
            elif fb < B_F1 + B_F2 + extra + red_b(SB)["rondas"]:
                fase_txt = "Reducido"
            elif fb < total_b(SB):
                fase_txt = "Promoción"
            else:
                fase_txt = "Terminada"

            c1, c2, c3 = st.columns([3, 1.4, 1.4], vertical_alignment="center")
            c1.markdown(chip(f"Primera Nacional · {n_b} equipos") + " " + chip(f"Fase {fase_txt}", "#475569"),
                        unsafe_allow_html=True)
    
            if not ctx.modo_mgr and c2.button(":material/skip_next: Próxima fecha", key="b_next", width="stretch", type="primary",
                         disabled=terminada_b or b_espera_primera):
                simular_fecha_b(S, P)
                st.rerun()
        
            if not ctx.modo_mgr and c3.button(":material/fast_forward: Hasta el final", key="b_all", width="stretch",
                         disabled=terminada_b or b_espera_primera):
                while SB["fecha"] < total_b(SB) and not (SB["fecha"] == total_b(SB) - 1 and not primera_terminada(S)):
                    simular_fecha_b(S, P)
                st.rerun()

            pct_b_dyn = 100 * fb / total_b(SB) if total_b(SB) else 0
                  
            if b_espera_primera and k_prom(SB) > 0:
                aviso(f"La Promoción se juega contra {_vs_primera(SB)}: terminá primero la temporada "
                      "de Primera División.")
            if not anual and fb == B_F1:
                aviso("Terminó la fase 1: se repartieron los equipos en las zonas Campeonato, "
                      "Intermedia y Descenso y <b>se conservan todos los puntos acumulados</b>.")
            if not anual and fb == B_F1 + B_F2 + extra:
                aviso("Terminó la fase 2 y sus definiciones: quedaron definidos los clasificados al reducido. "
                      "Mirá el cuadro en la pestaña <b>Reducido</b>." if red_b(SB)["reducido"] else
                      "Terminó la fase 2 y sus definiciones: esta temporada no hay reducido, así que quedaron "
                      "definidos los ascensos directos y los que juegan la promoción.")

            # ------------------ SISTEMA DE PESTAÑAS DINÁMICAS ------------------
            desempates_b = [p for p in SB["log"] if p["rotulo"] == "Desempate"]
            mostrar_desempate_b = SB.get("desempate_pendiente") or len(desempates_b) > 0
    
            titulos_b = ["Posiciones", "Fixture y resultados"]
            if mostrar_desempate_b: titulos_b.append("Desempate")
            hay_red = red_b(SB)["reducido"]                 # esta temporada se juega reducido por un ascenso
            titulos_b.extend((["Reducido"] if hay_red else []) + ["Movimientos", "Definiciones"])
    
            sb = st.tabs(titulos_b)
            idx_b = 0
    
            with sb[idx_b]:
                mi_zona = zona_nacional(SB, ctx.club)        # modo manager: zona de mi club (o None)
                if anual:
                    seccion("Torneo anual · " + ("ida y vuelta" if formato_b(SB) == "anual_ida_vuelta" else "una rueda"), color="#4f46e5")
                    mostrar_tabla(tabla_b_anual(SB), colorear_b, SB["pos_hist"])
                    leyenda([("Ascienden directo", COLORES_B["Ascenso directo"])]
                            + ([("Juega el reducido", COLORES_B["Reducido"])] if hay_red else [])
                            + ([("Juega la promoción", COLORES_B["Promoción"])] if k_prom(SB) and not hay_red else [])
                            + [(f"Descienden ({desc_b} últimos)", COLORES_B["Desciende"])])
                elif fb < B_F1:
                    seccion("Fase 1 · Zonas A y B", color="#4f46e5")
                    etiq, ini = marcar(["Zona A", "Zona B"], mi_zona)
                    tabs_b = tabs_con_default(etiq, ini)
                    for z, tab in enumerate(tabs_b):
                        with tab:
                            mostrar_tabla(tabla_b_f1(SB, z), colorear_b, SB["pos_hist"])
                    ra, rb = rangos_fase1(plan, 0), rangos_fase1(plan, 1)
                    rg = lambda k: ra[k] if ra[k] == rb[k] else f"{ra[k]} (A) · {rb[k]} (B)"
                    leyenda([(f"{rg(0)} → Zona Campeonato", COLORES_ZONA[0]),
                             (f"{rg(1)} → Zona Intermedia", COLORES_ZONA[1]),
                             (f"{rg(2)} → Zona Descenso", COLORES_ZONA[2])])
                else:
                    seccion("Fase 2 · Zonas", color="#16a34a")
                    etiq, ini = marcar([f"Zona {n}" for n in B_ZONAS2] + ["Fase 1"], mi_zona)
                    tabs_b = tabs_con_default(etiq, ini)
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
                    if anual:
                        st.markdown(
                            f"Torneo anual de {n_b} equipos, todos contra todos ({'ida y vuelta, ' if formato_b(SB) == 'anual_ida_vuelta' else 'una rueda, '}{base_b} fechas) "
                            f"en una sola tabla. El campeón es el 1°: {_frase_ascensos(SB)}; "
                            f"{_promo_texto(SB)} y descienden los {desc_b} últimos. "
                            f"(Con {B_MAX_ANUAL} equipos o menos la B se juega siempre así.)")
                    else:
                        c_z, i_z, d_z = plan["tam2"]
                        zonas_txt = (f"{c_z} cada una" if c_z == i_z == d_z else f"{c_z}, {i_z} y {d_z} equipos")
                        mitad = plan["f1_inter"] // 2
                        st.markdown(
                            f"Fase 1: dos zonas de {za if za == zb else f'{za} y {zb}'}, una rueda, más {plan['f1_inter']} fechas interzonales "
                            f"(localía fija {mitad} y {mitad}) cruzando ambas zonas. "
                            "Después, conservando los puntos acumulados, se arman "
                            f"Campeonato, Intermedia y Descenso ({zonas_txt}), una rueda cada una "
                            "(si dos equipos ya se cruzaron en la fase 1, la revancha es con la localía "
                            f"invertida). Campeonato: el 1° es el campeón; {_frase_ascensos(SB)} (los puestos se cuentan "
                            "sumando Campeonato, Intermedia y Descenso). "
                            f"Descenso: bajan los {desc_b} últimos. "
                            "El reducido es a partido único con penales directos; "
                            f"{_promo_texto(SB)}. "
                            f"(Con {B_MAX_ANUAL} equipos o menos la B pasa a ser un torneo anual ida y vuelta.)")
                
                if fb == 0 and not ctx.modo_mgr:               # en modo manager no se tocan las medias
                    with st.expander(":material/tune: Editar medias internas de esta temporada (Primera Nacional)"):
                        SB["r"] = editar_medias(SB["nombres"], SB["r"], f"editor_b_{S['temp']}")
            idx_b += 1
    
            with sb[idx_b]: 
                vista_fixture(S, ctx.club, "b")
            idx_b += 1
    
            if mostrar_desempate_b:
                with sb[idx_b]:
                    if SB.get("desempate_pendiente"):
                        seccion("Desempates en la Primera Nacional", color="#9333ea")
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
                                seccion(f"Tabla final: {motivo}", color="#9333ea")
                                st.markdown(html_tabla_liguilla(parts), unsafe_allow_html=True)
                                with st.expander(f":material/visibility: Ver los {len(parts)} enfrentamientos", expanded=False):
                                    for p in parts:
                                        st.markdown(fila_partido_html(S, ctx.club, p), unsafe_allow_html=True)
                            else:
                                seccion(f"Desempate: {motivo}", color="#dc2626")
                                for p in parts:
                                    st.markdown(fila_partido_html(S, ctx.club, p, abierto=True), unsafe_allow_html=True)
                idx_b += 1

            if hay_red:
                with sb[idx_b]:
                    pr_red = red_b(SB)
                    seccion(f"Reducido por el ascenso n.º {pr_red['directos'] + 1}", color="#2563eb")
                    if SB.get("red") is None:
                        aviso("El cuadro se completa al terminar " + ("el torneo" if anual else "la fase 2 y sus posibles "
                              "desempates") + f". Lo juegan {pr_red['equipos']} equipos: del {pr_red['directos'] + 1}° al "
                              f"{pr_red['directos'] + pr_red['equipos']}° de la tabla final"
                              + ("" if anual else " (Campeonato, después Intermedia)") + ".")
                    st.markdown(bracket_html(SB), unsafe_allow_html=True)
                    if SB["entrantes"] is not None:
                        with st.expander("Clasificados al reducido (orden de mérito)"):
                            st.markdown(tabla_html(SB["entrantes"]), unsafe_allow_html=True)
                idx_b += 1
    
            with sb[idx_b]:
                render_movimientos(SB["log"], SB["pos_hist"], nom_b, "#0f766e")
            idx_b += 1
        
            with sb[idx_b]:
                seccion("Definiciones de la temporada", color="#b7860b")
                if SB["campeon"] is None:
                    aviso("Las definiciones aparecen acá cuando termina el torneo." if anual else
                          "Las definiciones aparecen acá cuando termina la fase 2 de la Primera Nacional.")
                else:
                    st.caption("Están cerradas para no spoilear: tocá cada una para verla.")
                    e1, e2 = st.columns(2)
                    with e1:
                        with st.expander(":material/emoji_events: Campeón de la Primera Nacional", expanded=False):
                            cb = nom_b[SB["campeon"]]
                            st.markdown(f'<div class="champ"><div class="t">Campeón · Temporada {S["temp"]}'
                                        f'</div><div style="margin-top:10px">{crest(cb, 64)}</div>'
                                        f'<div class="nm">{esc(cb)}</div><div class="s">'
                                        + ("Asciende a Primera" if SB["asc_directo"] else "Campeón de la B (esta temporada "
                                           "no hay ascensos directos)") + '</div></div>', unsafe_allow_html=True)
                        with st.expander(":material/north: Clasificados · Ascensos", expanded=False):
                            asc = [(nom_b[i], "campeón" if j == 0 else f"{j + 1}°")
                                   for j, i in enumerate(SB["asc_directo"])]
                            if SB["asc_reducido"] is not None:
                                asc.append((nom_b[SB["asc_reducido"]], "reducido"))
                            for pr in SB.get("promos") or []:
                                if pr["gana_b"]:
                                    asc.append((nom_b[pr["b_id"]], "promoción"))
                            pr_red = red_b(SB)
                            st.markdown(lista_equipos_html(asc) + (
                                '' if (not pr_red["reducido"] or SB["asc_reducido"] is not None) else
                                '<div style="font-size:.8rem;opacity:.65">Un ascenso más sale del '
                                'reducido.</div>') + (
                                '<div style="font-size:.8rem;opacity:.65">No sube nadie directo ni por reducido '
                                'esta temporada.</div>' if not asc and not pr_red["reducido"] else ''),
                                unsafe_allow_html=True)
                    with e2:
                        with st.expander(":material/swap_vert: Promoción", expanded=False):
                            if k_prom(SB) == 0:
                                st.caption("Esta temporada no hay promoción.")
                            elif SB.get("promo_partidos"):
                                for pm in SB["promo_partidos"]:
                                    st.markdown(fila_partido_html(S, ctx.club, pm, abierto=True), unsafe_allow_html=True)
                            elif promo_cands(SB):
                                st.markdown('<div class="mlab">Juegan la promoción</div>'
                                            + lista_equipos_html([
                                                (nom_b[i], f"vs {SB['promo_pos'][j]}° de Primera")
                                                for j, i in enumerate(promo_cands(SB))]), unsafe_allow_html=True)
                            else:
                                st.caption("La juegan " + ("el perdedor de la final del reducido (y, si son dos, el mejor "
                                           "ubicado de los otros que perdieron)" if red_b(SB)["reducido"] else
                                           "los que quedan justo después de los ascendidos directos")
                                           + f" contra {_vs_primera(SB)}.")
                        with st.expander(":material/south: Descensos", expanded=False):
                            st.markdown(
                                '<div class="mlab">Descienden (' + (f"los {desc_b} últimos de la tabla" if anual else f"{plan['tam2'][2] - desc_b + 1}° al {plan['tam2'][2]}° de Zona Descenso") + '): al Federal '
                                'A los del interior, a la Primera B los metropolitanos</div>'
                                + lista_equipos_html([
                                    (nom_b[i], "Federal A" if origen(nom_b[i]) == "Interior" else "Primera B")
                                    for i in SB["desc_b"]
                                ]), unsafe_allow_html=True)

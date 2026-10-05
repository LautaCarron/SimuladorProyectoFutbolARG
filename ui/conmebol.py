"""Pestaña Copas · Libertadores, Sudamericana y Recopa.

El código es el de simuladorafa.py, movido acá tal cual. `ctx` trae el estado y los ayudantes
compartidos de la interfaz (S, P, las pestañas, las banderas terminada_*, etc.).
"""

import pandas as pd
import streamlit as st
from motor.calendario import anio
from copas.conmebol import fase_actual, listo, pais_de, simular_ronda_int
from datos.logos import logo_img
from ui.vista import (
    aviso,
    bandera,
    barra_estado,
    chip,
    crest,
    cuadro_int_html,
    esc,
    fila_partido_html,
    grupos_int_html,
    seccion,
    serie_int_html,
    series_int_html,
    tabla_html,
)


def render(ctx):
    (P, S, _abierta, tab_copas, tab_lib, tab_rec, tab_sud) = (
        ctx.P, ctx.S, ctx._abierta, ctx.tab_copas, ctx.tab_lib, ctx.tab_rec, ctx.tab_sud)
    # ============================================================================
    # COPAS CONMEBOL: LIBERTADORES, SUDAMERICANA Y RECOPA
    # ============================================================================
    def pestaña_int(clave, color):
        C = S["int"][clave]
        nombre = C["nombre"]
        terminada_c = C["ronda"] >= C["total"]
        c1, c2, c3 = st.columns([3, 1.4, 1.4], vertical_alignment="center")
        c1.markdown(logo_img(nombre, 30) + " " + chip(f"{nombre} · {len(C['via'])} equipos", color),
                    unsafe_allow_html=True)
        espera = not terminada_c and not listo(S, clave)
        if c2.button(":material/skip_next: Próxima ronda", key=f"{clave}_next", width="stretch", type="primary",
                     disabled=terminada_c or espera):
            simular_ronda_int(S, clave, P, S["rng"])
            st.rerun()
        if c3.button(":material/fast_forward: Hasta el final", key=f"{clave}_all", width="stretch",
                     disabled=terminada_c or espera):
            while listo(S, clave):
                simular_ronda_int(S, clave, P, S["rng"])
            st.rerun()
        barra_estado([("Próxima ronda" if not terminada_c else "Estado", fase_actual(C)),
                      ("Rondas", f"{C['ronda']} / {C['total']}"), ("Partidos jugados", len(C["log"]))],
                     100 * C["ronda"] / max(C["total"], 1))
        if espera:
            aviso("La Sudamericana espera a la Libertadores: sus grupos se arman con los que pierden la Fase 3 "
                  "y los playoffs, con los terceros de los grupos. Avanzá la Libertadores (o usá Próximo día).")
        if clave == "rec":
            seccion("Recopa Sudamericana", "Campeón de la Libertadores vs. campeón de la Sudamericana · ida y "
                    "vuelta (si el global empata, penales)", color)
            if not C["llaves"].get("Final"):
                aviso("Esta temporada no hay Recopa.")
            else:
                st.markdown('<div class="rf-grid">' + serie_int_html(C, C["llaves"]["Final"][0], "Recopa")
                            + '</div>', unsafe_allow_html=True)
            return
        es_lib = clave == "lib"
        titulos = (["Fase previa"] if es_lib else []) + ["Grupos"] + ([] if es_lib else ["Playoffs"]) + [
            "Eliminatorias", "Partidos", "Clasificados", "Definiciones"]
        t = dict(zip(titulos, st.tabs(titulos)))
        if es_lib:
            with t["Fase previa"]:
                seccion("Fase previa", "Fase 2 (16 equipos) y Fase 3 (8) a ida y vuelta · los 4 que ganan la Fase 3 "
                        "van a los grupos; los 4 que pierden, a la Sudamericana", color)
                for fase in ("Fase 2", "Fase 3"):
                    if C["llaves"].get(fase):
                        st.markdown(f'<div class="mlab" style="margin-top:10px">{fase}</div>'
                                    + series_int_html(C, fase), unsafe_allow_html=True)
        with t["Grupos"]:
            seccion("Fase de grupos", "8 grupos de 4 · ida y vuelta · " + (
                "1° y 2° a octavos, 3° a la Sudamericana" if es_lib else "1° a octavos, 2° a los playoffs"), color)
            if C["grupos"] is None:
                aviso("Los grupos se sortean cuando termina la fase previa de la Libertadores.")
            else:
                destinos = ([("oct", "Octavos"), ("oct", ""), ("sud", "Pasa a la Sudamericana"), ("", "")] if es_lib
                            else [("oct", "Octavos"), ("sud", "Playoffs"), ("", ""), ("", "")])
                st.markdown(grupos_int_html(C, destinos), unsafe_allow_html=True)
        if not es_lib:
            with t["Playoffs"]:
                seccion("Playoffs", "2° de cada grupo vs. los 3° de la Libertadores (cierran de local) · ida y vuelta",
                        color)
                if C["llaves"].get("Playoffs"):
                    st.markdown(series_int_html(C, "Playoffs"), unsafe_allow_html=True)
                else:
                    aviso("Se arman cuando terminan los grupos de las dos copas.")
        with t["Eliminatorias"]:
            seccion("Eliminatorias", "Octavos, cuartos y semis a ida y vuelta (cierra de local el de mejor campaña) · "
                    "final única en cancha neutral · se ve el global de cada serie", color)
            st.markdown(cuadro_int_html(C), unsafe_allow_html=True)
            fases = [f for f in ("Octavos", "Cuartos", "Semifinal") if C["llaves"].get(f)]
            if fases:
                with st.expander(":material/visibility: Ver ida y vuelta de cada serie"):
                    for f in fases:
                        st.markdown(f'<div class="mlab" style="margin-top:10px">{f}</div>' + series_int_html(C, f),
                                    unsafe_allow_html=True)
        with t["Partidos"]:
            if not C["log"]:
                aviso("Todavía no se jugó ninguna ronda.")
            else:
                rondas = sorted({p["fecha"] for p in C["log"]})
                r_sel = st.selectbox(":material/event: Ronda", rondas, index=len(rondas) - 1,
                                     format_func=lambda n: C["rondas"][n - 1], key=f"{clave}_ronda_{S['temp']}")
                for p in [p for p in C["log"] if p["fecha"] == r_sel]:
                    st.markdown(fila_partido_html(p, abierto=p["comp"] == "Final"), unsafe_allow_html=True)
        with t["Clasificados"]:
            seccion("Clasificados", "Argentina: por la tabla de Primera, la Copa Argentina y los campeones · "
                    "los otros países: cupos por país, los clubes se sortean cada año", color)
            filas = [{"Equipo": n, "País": pais_de(n), "Cómo clasificó": v, "Media": round(C["r"][n], 1)}
                     for n, v in C["via"].items()]
            filas.sort(key=lambda x: (x["País"] != "Argentina", x["País"], -x["Media"]))
            df_i = pd.DataFrame(filas)
            st.markdown(tabla_html(df_i, formatos={"Media": "{:.1f}"}), unsafe_allow_html=True)
        with t["Definiciones"]:
            seccion("Definiciones", f"Campeón de la {nombre}", "#b7860b")
            if C["campeon"] is None:
                aviso("El campeón aparece acá cuando se juega la final.")
            else:
                cc = C["campeon"]
                st.markdown(f'<div class="champ"><div class="t">Campeón · {esc(nombre)} {anio(S)}</div>'
                            f'<div style="margin-top:10px">{crest(cc, 64)}</div><div class="nm">{esc(cc)}</div>'
                            f'<div class="s">{bandera(pais_de(cc), 18)} {esc(pais_de(cc))} · finalista: '
                            f'{esc(C["subcampeon"])}</div></div>', unsafe_allow_html=True)
                st.caption("Clasifica a la Recopa y a la próxima Libertadores.")


    if _abierta(tab_copas, tab_lib):
        with tab_lib:
            pestaña_int("lib", "#8a6d1e")
    if _abierta(tab_copas, tab_sud):
        with tab_sud:
            pestaña_int("sud", "#1e5aa8")
    if _abierta(tab_copas, tab_rec):
        with tab_rec:
            pestaña_int("rec", "#475569")

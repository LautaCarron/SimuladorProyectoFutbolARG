"""Pestaña Copas · Mundial de Clubes.

El código es el de simuladorafa.py, movido acá tal cual. `ctx` trae el estado y los ayudantes
compartidos de la interfaz (S, P, las pestañas, las banderas terminada_*, etc.).
"""

import pandas as pd
import streamlit as st
from copas.mundial import (
    ANIO_BASE,
    CADA,
    RONDAS as MUNDIAL_RONDAS,
    anio_de as anio_mundial,
    calcular_clasificados,
    clasificacion_conmebol,
    fase_actual as fase_mundial,
    hay_mundial,
    medias as medias_mundial,
    mundial_terminado,
    pais_club,
    proxima_temporada,
    simular_ronda_mundial,
)
from ui.vista import (
    aviso,
    bandera,
    barra_estado,
    chip,
    crest,
    cuadro_mundial_html,
    esc,
    fila_partido_html,
    grupos_mundial_html,
    ranking_conmebol_html,
    seccion,
    tabla_html,
)


def render(ctx):
    (P, S, _abierta, tab_copas, tab_mun) = (
        ctx.P, ctx.S, ctx._abierta, ctx.tab_copas, ctx.tab_mun)
    # ============================================================================
    # MUNDIAL DE CLUBES (cada 4 temporadas: 2029, 2033...)
    # ============================================================================
    def ranking_sudamerica(temp, color):
        """Tabla del ranking CONMEBOL en vivo para la edición de la temporada `temp`."""
        R = clasificacion_conmebol(S, temp)
        y0, y1 = R["anios"][0], R["anios"][-1]
        seccion(f"Ranking CONMEBOL · Mundial {anio_mundial(temp)}",
                f"6 cupos: los campeones de la Libertadores {y0}-{y1} y el resto por ranking · "
                "máximo 2 clubes por país (salvo campeones)", color)
        if R["en_curso"] and not dict(R["campeones"]).get(R["en_curso"][0]):
            st.caption(f"En vivo: la Libertadores {R['en_curso'][0]} suma puntos partido a partido. "
                       "Mientras falten campeones, la tabla es una proyección.")
        st.markdown(ranking_conmebol_html(R), unsafe_allow_html=True)
        st.caption(f"Puntos (reglamento CONMEBOL): sólo la Copa Libertadores, desde la fase de grupos · 3 por "
                   f"llegar a los grupos · 3 por victoria y 1 por empate (una serie definida por penales cuenta "
                   f"como empate) · 3 más por cada ronda alcanzada: octavos, cuartos, semifinal y final. La fase "
                   f"previa y la Sudamericana no suman. {ANIO_BASE}: puntos reales. A igual puntaje, desempata el "
                   f"que sumó más en la última temporada.")

    def pestaña_mundial(color):
        M = S["mundial"]
        if not hay_mundial(S):
            prox = proxima_temporada(S["temp"])
            c1 = st.columns(1)[0]
            c1.markdown(chip("Mundial de Clubes · 32 equipos", color) + " " + chip(
                f"Próxima edición: {anio_mundial(prox)} (temporada {prox})", "#475569"), unsafe_allow_html=True)
            seccion("Camino al Mundial", "Los campeones continentales de los 4 años anteriores clasifican directo; "
                    "el resto de cada cupo sale del ranking (máximo 2 clubes por país)", color)
            aviso("Esta temporada no hay Mundial de Clubes. Se sortea al empezar la temporada de la edición, con "
                  "lo que haya pasado en las copas hasta entonces.")
            ranking_sudamerica(prox, color)
            with st.expander(":material/public: Clasificados de todas las confederaciones (hasta ahora)"):
                med = medias_mundial(S)
                filas = [{"Equipo": x["club"], "País": pais_club(x["club"]), "Confederación": x["conf"],
                          "Cómo clasifica": x["via"], "Media": round(med.get(x["club"], 0.0), 1)}
                         for x in calcular_clasificados(S, prox)]
                st.markdown(tabla_html(pd.DataFrame(filas), formatos={"Media": "{:.1f}"}), unsafe_allow_html=True)
            return
        terminado = M["ronda"] >= M["total"]
        c1, c2, c3 = st.columns([3, 1.4, 1.4], vertical_alignment="center")
        c1.markdown(chip(f"Mundial de Clubes {M['anio']} · 32 equipos", color), unsafe_allow_html=True)
        if c2.button(":material/skip_next: Próxima ronda", key="mun_next", width="stretch", type="primary",
                     disabled=terminado):
            simular_ronda_mundial(S, P, S["rng"])
            st.rerun()
        if c3.button(":material/fast_forward: Hasta el final", key="mun_all", width="stretch", disabled=terminado):
            while not mundial_terminado(S):
                simular_ronda_mundial(S, P, S["rng"])
            st.rerun()
        barra_estado([("Próxima ronda" if not terminado else "Estado", fase_mundial(M)),
                      ("Rondas", f"{M['ronda']} / {M['total']}"), ("Partidos jugados", len(M["log"]))],
                     100 * M["ronda"] / max(M["total"], 1))
        titulos = ["Grupos", "Eliminatorias", "Partidos", "Clasificados", "Ranking CONMEBOL", "Definiciones"]
        t = dict(zip(titulos, st.tabs(titulos)))
        with t["Grupos"]:
            seccion("Fase de grupos", "8 grupos de 4 · una rueda en cancha neutral · 1° y 2° a octavos", color)
            st.markdown(grupos_mundial_html(M), unsafe_allow_html=True)
        with t["Eliminatorias"]:
            seccion("Eliminatorias", "Octavos, cuartos, semifinales y final en cancha neutral · si empatan, penales",
                    color)
            st.markdown(cuadro_mundial_html(M), unsafe_allow_html=True)
        with t["Partidos"]:
            if not M["log"]:
                aviso("Todavía no se jugó ninguna ronda.")
            else:
                rondas = sorted({p["fecha"] for p in M["log"]})
                r_sel = st.selectbox(":material/event: Ronda", rondas, index=len(rondas) - 1,
                                     format_func=lambda n: MUNDIAL_RONDAS[n - 1], key=f"mun_ronda_{S['temp']}")
                for p in [p for p in M["log"] if p["fecha"] == r_sel]:
                    st.markdown(fila_partido_html(p, abierto=p["comp"] == "Final"), unsafe_allow_html=True)
        with t["Clasificados"]:
            seccion("Clasificados", "UEFA 12 · CONMEBOL 6 · AFC 4 · CAF 4 · Concacaf 4 · OFC 1 · anfitrión 1", color)
            orden_conf = ["UEFA", "CONMEBOL", "AFC", "CAF", "CONCACAF", "OFC"]
            filas = [{"Equipo": n, "País": pais_club(n), "Confederación": M["conf"][n], "Cómo clasificó": M["via"][n],
                      "Media": round(M["r"][n], 1)} for n in M["nombres"]]
            filas.sort(key=lambda x: (orden_conf.index(x["Confederación"]), -x["Media"]))
            st.markdown(tabla_html(pd.DataFrame(filas), formatos={"Media": "{:.1f}"}), unsafe_allow_html=True)
        with t["Ranking CONMEBOL"]:
            ranking_sudamerica(M["temp"], color)
            st.markdown('<div class="mlab" style="margin-top:22px">Camino al próximo Mundial</div>',
                        unsafe_allow_html=True)
            ranking_sudamerica(M["temp"] + CADA, color)
        with t["Definiciones"]:
            seccion("Definiciones", "Campeón del Mundial de Clubes", "#b7860b")
            if M["campeon"] is None:
                aviso("El campeón aparece acá cuando se juega la final.")
            else:
                cc = M["campeon"]
                st.markdown(f'<div class="champ"><div class="t">Campeón · Mundial de Clubes {M["anio"]}</div>'
                            f'<div style="margin-top:10px">{crest(cc, 64)}</div><div class="nm">{esc(cc)}</div>'
                            f'<div class="s">{bandera(pais_club(cc), 18)} {esc(pais_club(cc))} · finalista: '
                            f'{esc(M["subcampeon"])}</div></div>', unsafe_allow_html=True)


    if _abierta(tab_copas, tab_mun):
        with tab_mun:
            pestaña_mundial("#be185d")

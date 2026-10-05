"""Pestañas Ligas · Primera B, Primera C y Promocional Amateur.

Las tres son ligas ida y vuelta con la misma pantalla (barra de estado, posiciones, fixture, desempates,
movimientos y definiciones). Antes eran tres bloques casi idénticos; ahora hay una sola función y cada
liga solo declara lo que cambia (nombre, estado, tabla, leyenda y textos) en LIGAS.
`ctx` trae el estado y los ayudantes compartidos de la interfaz (S, P, las pestañas, terminada_*, etc.).
"""

import streamlit as st

from ligas.simples import simular_fecha_liga, tabla_pb, tabla_pc, tabla_pd
from ui.vista import (
    COLORES_B,
    aviso,
    barra_estado,
    chip,
    colorear_pb,
    colorear_pc,
    colorear_pd,
    crest,
    esc,
    fila_partido_html,
    leyenda,
    mostrar_tabla,
    render_movimientos,
    seccion,
    vista_fixture,
)

_NARANJA = "rgba(249, 115, 22, 0.3)"       # desempate por el campeonato / ascenso
_VIOLETA = "rgba(147, 51, 234, 0.3)"       # desempate por la permanencia

# clave: prefijo de las claves de widgets y del fixture · estado/tab/terminada: nombres que trae ctx
LIGAS = [
    dict(clave="pb", nombre="Primera B", estado="SPB", tab="tab_pb", terminada="terminada_pb",
         tabla=tabla_pb, colorear=colorear_pb, chip_color=None,
         sub_posiciones="Ida y vuelta · ascienden los 2 primeros, del 18° para abajo descienden",
         leyenda=[("1°-2° Ascenso a Primera Nacional", COLORES_B["Ascenso directo"]),
                  ("Desempate Campeonato / Ascenso", _NARANJA), ("Desempate Permanencia", _VIOLETA),
                  ("18° o peor Descenso a Primera C", COLORES_B["Desciende"])],
         sub_definiciones="Campeón, ascensos y descensos", expander_campeon="Campeón de la Primera B"),
    dict(clave="pc", nombre="Primera C", estado="SPC", tab="tab_pc", terminada="terminada_pc",
         tabla=tabla_pc, colorear=colorear_pc, chip_color=None,
         sub_posiciones="Ida y vuelta · ascienden los 2 primeros",
         leyenda=[("1°-2° Ascenso a Primera B", COLORES_B["Ascenso directo"]),
                  ("Desempate Campeonato / Ascenso", _NARANJA), ("Desempate Permanencia", _VIOLETA),
                  ("18° o peor Descenso al Promocional", COLORES_B["Desciende"])],
         sub_definiciones="Campeón y ascensos", expander_campeon="Campeón de la Primera C"),
    dict(clave="pd", nombre="Promocional Amateur", estado="SPD", tab="tab_pd", terminada="terminada_pd",
         tabla=tabla_pd, colorear=colorear_pd, chip_color="#0369a1",
         sub_posiciones="Ida y vuelta · ascienden los 2 primeros",
         leyenda=[("1°-2° Ascenso a Primera C", COLORES_B["Ascenso directo"]),
                  ("Desempate Campeonato / Ascenso", _NARANJA)],
         sub_definiciones="Campeón y ascensos", expander_campeon="Campeón del Promocional Amateur"),
]


def render(ctx):
    for cfg in LIGAS:
        _render_liga(ctx, cfg)


def _render_liga(ctx, cfg):
    S, P = ctx.S, ctx.P
    html_tabla_liguilla = ctx.html_tabla_liguilla       # ayudante definido en simuladorafa.py
    L = getattr(ctx, cfg["estado"])
    tab = getattr(ctx, cfg["tab"])
    terminada = getattr(ctx, cfg["terminada"])
    k, nombre, tabla, colorear = cfg["clave"], cfg["nombre"], cfg["tabla"], cfg["colorear"]
    if not ctx._abierta(ctx.tab_ligas, tab):
        return
    with tab:
        c1, c2, c3 = st.columns([3, 1.4, 1.4], vertical_alignment="center")
        c1.markdown(chip(f"{nombre} · {len(L['nombres'])} equipos", cfg["chip_color"]) + " "
                    + chip("Todos contra todos", "#475569"), unsafe_allow_html=True)
        if c2.button(":material/skip_next: Próxima fecha", key=f"{k}_next", width="stretch", type="primary",
                     disabled=terminada):
            simular_fecha_liga(L, P, S["rng"], nombre, tabla)
            st.rerun()
        if c3.button(":material/fast_forward: Hasta el final", key=f"{k}_all", width="stretch",
                     disabled=terminada):
            while L["fecha"] < L["total"]:
                simular_fecha_liga(L, P, S["rng"], nombre, tabla)
            st.rerun()

        pct = 100 * L["fecha"] / L["total"] if L["total"] else 0
        barra_estado([("Fase", "Liga ida y vuelta"), ("Fecha", f"{L['fecha']} / {L['total']}"),
                      ("Partidos jugados", len(L["log"]))], pct)

        desempates = [p for p in L["log"] if p["rotulo"] == "Desempate"]
        mostrar_desempate = L.get("desempate_pendiente") or len(desempates) > 0

        titulos = ["Posiciones", "Fixture y resultados"]
        if mostrar_desempate:
            titulos.append("Desempate")
        titulos.extend(["Movimientos", "Definiciones"])
        tabs = st.tabs(titulos)
        idx = 0

        with tabs[idx]:
            seccion("Tabla de posiciones", cfg["sub_posiciones"], "#4f46e5")
            mostrar_tabla(tabla(L), colorear, L["pos_hist"])
            leyenda(cfg["leyenda"])
            if L["fecha"] == 0:
                with st.expander(f":material/tune: Editar medias internas de esta temporada ({nombre})"):
                    L["r"] = ctx.editar_medias(L["nombres"], L["r"], f"editor_{k}_{S['temp']}")
        idx += 1

        with tabs[idx]:
            vista_fixture(k)
        idx += 1

        if mostrar_desempate:
            with tabs[idx]:
                if L.get("desempate_pendiente"):
                    seccion("Desempates por Posiciones", "Están empatados en puntos. Jugarán un partido único.",
                            "#9333ea")
                    df_des = tabla(L)
                    df_des = df_des[df_des["id"].isin(L["ids_desempate"])]
                    mostrar_tabla(df_des, colorear)
                else:
                    grupos = {}
                    for p in desempates:
                        grupos.setdefault(p["comp"], []).append(p)
                    for motivo, parts in grupos.items():
                        if "Liguilla" in motivo:
                            seccion(f"Tabla final: {motivo}", "Posiciones del mini-torneo a partido único", "#9333ea")
                            st.markdown(html_tabla_liguilla(parts), unsafe_allow_html=True)
                            with st.expander(f":material/visibility: Ver los {len(parts)} enfrentamientos",
                                             expanded=False):
                                for p in parts:
                                    st.markdown(fila_partido_html(p), unsafe_allow_html=True)
                        else:
                            seccion(f"Desempate: {motivo}", "Partido único definitorio", "#dc2626")
                            for p in parts:
                                st.markdown(fila_partido_html(p, abierto=True), unsafe_allow_html=True)
            idx += 1

        with tabs[idx]:
            render_movimientos(L["log"], L["pos_hist"], L["nombres"], "#0f766e")
        idx += 1

        with tabs[idx]:
            seccion("Definiciones de la temporada", cfg["sub_definiciones"], "#b7860b")
            if L["campeon"] is None:
                aviso("Las definiciones aparecen acá cuando termina la liga.")
            else:
                with st.expander(f":material/emoji_events: {cfg['expander_campeon']}", expanded=False):
                    campeon = L["nombres"][L["campeon"]]
                    st.markdown(f'<div class="champ"><div class="t">Campeón</div><div style="margin-top:10px">'
                                f'{crest(campeon, 64)}</div><div class="nm">{esc(campeon)}</div></div>',
                                unsafe_allow_html=True)

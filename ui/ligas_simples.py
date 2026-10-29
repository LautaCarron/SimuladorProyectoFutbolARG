"""Pestañas Ligas · Primera B, Primera C y Promocional Amateur.

Las tres son ligas todos contra todos (ida y vuelta hasta 24 equipos, una vuelta desde 25; el Promocional con 25 o más
se juega en dos zonas, ida y vuelta) con la misma pantalla (barra de estado, posiciones, fixture, desempates,
movimientos y definiciones). Antes eran tres bloques casi idénticos; ahora hay una sola función y cada
liga solo declara lo que cambia (nombre, estado, tabla, leyenda y textos) en LIGAS.
`ctx` trae el estado y los ayudantes compartidos de la interfaz (S, P, las pestañas, terminada_*, etc.).
"""

import streamlit as st

from ligas.simples import (
    ZONAS_NOMBRES,
    descripcion_zonas,
    formato_simple,
    plan_de,
    simular_fecha_liga,
    tabla_pb,
    tabla_pc,
    tabla_pd,
    tablas_zonas,
)
from ui.vista.cuadros import bracket_html_simple
from ui.vista.editor_medias import editar_medias
from ui.vista.liguilla import html_tabla_liguilla
from ui.vista.mi_club import marcar, tabs_con_default, zona_simple
from ui.vista import (
    COLORES_B,
    aviso,
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
    dict(clave="pb", nombre="Primera B", tab="tab_pb", terminada="terminada_pb",
         tabla=tabla_pb, colorear=colorear_pb, chip_color=None,
         sub_posiciones="ascienden los 2 primeros, del 18° para abajo descienden",
         leyenda=[("1°-2° Ascenso a Primera Nacional", COLORES_B["Ascenso directo"]),
                  ("Desempate Campeonato / Ascenso", _NARANJA), ("Desempate Permanencia", _VIOLETA),
                  ("18° o peor Descenso a Primera C", COLORES_B["Desciende"])],
         sub_definiciones="Campeón, ascensos y descensos", expander_campeon="Campeón de la Primera B"),
    dict(clave="pc", nombre="Primera C", tab="tab_pc", terminada="terminada_pc",
         tabla=tabla_pc, colorear=colorear_pc, chip_color=None,
         sub_posiciones="ascienden los 2 primeros",
         leyenda=[("1°-2° Ascenso a Primera B", COLORES_B["Ascenso directo"]),
                  ("Desempate Campeonato / Ascenso", _NARANJA), ("Desempate Permanencia", _VIOLETA),
                  ("18° o peor Descenso al Promocional", COLORES_B["Desciende"])],
         sub_definiciones="Campeón y ascensos", expander_campeon="Campeón de la Primera C"),
    dict(clave="pd", nombre="Promocional Amateur", tab="tab_pd", terminada="terminada_pd",
         tabla=tabla_pd, colorear=colorear_pd, chip_color="#0369a1",
         sub_posiciones="ascienden los 2 primeros",
         leyenda=[("1°-2° Ascenso a Primera C", COLORES_B["Ascenso directo"]),
                  ("Desempate Campeonato / Ascenso", _NARANJA)],
         sub_definiciones="Campeón y ascensos", expander_campeon="Campeón del Promocional Amateur"),
]


SUBE_A = {"pb": "Primera Nacional", "pc": "Primera B", "pd": "Primera C"}
BAJA_A = {"pb": "Primera C", "pc": "el Promocional"}


def _textos(k, plan, n):
    """Subtítulo y leyenda de la tabla según lo elegido en el Modo dios (ascensos, reducido y descensos)."""
    d, ds, m = plan["directos"], plan["desc"], plan["equipos"]
    if plan.get("zonas"):                                      # Promocional en dos zonas: los ascensos salen de cada zona
        p = d // 2
        if d == 0:
            ley = [("1° de cada zona: final por el título", COLORES_B["Reducido"])]
        elif d == 1:
            ley = [(f"1° de cada zona: final por el ascenso a {SUBE_A[k]}", COLORES_B["Reducido"])]
        else:
            ley = [(("1° de cada zona" if p == 1 else f"1°-{p}° de cada zona") + f" Ascenso a {SUBE_A[k]}",
                    COLORES_B["Ascenso directo"])]
            if d % 2:
                ley.append((f"{p + 1}° de cada zona: partido por el último ascenso", COLORES_B["Reducido"]))
        return formato_simple(n, k) + " · " + descripcion_zonas(d), ley
    partes = [f"ascienden {d} directo" + ("s" if d != 1 else "") if d else "no hay ascensos directos"]
    ley = [(f"1°-{d}° Ascenso a {SUBE_A[k]}" if d > 1 else f"1° Ascenso a {SUBE_A[k]}", COLORES_B["Ascenso directo"])] if d else []
    if plan["reducido"]:
        partes.append(f"reducido por un ascenso más ({d + 1}° al {d + m}°)")
        ley.append((f"{d + 1}°-{d + m}° Reducido por un ascenso más", COLORES_B["Reducido"]))
    ley.append(("Desempate Campeonato / Ascenso", _NARANJA))
    if ds and k in BAJA_A:
        partes.append(f"del {n - ds + 1}° para abajo descienden")
        ley += [("Desempate Permanencia", _VIOLETA),
                (f"{n - ds + 1}° o peor Descenso a {BAJA_A[k]}", COLORES_B["Desciende"])]
    return formato_simple(n, k) + " · " + ", ".join(partes), ley


def render(ctx):
    for cfg in LIGAS:
        _render_liga(ctx, cfg)


def _render_liga(ctx, cfg):
    S, P = ctx.S, ctx.P
    L = S[cfg["clave"]]
    tab = getattr(ctx.pestanas, cfg["tab"])
    terminada = getattr(ctx.progreso, cfg["terminada"])
    k, nombre, tabla, colorear = cfg["clave"], cfg["nombre"], cfg["tabla"], cfg["colorear"]
    if not ctx.abierta(ctx.pestanas.tab_ligas, tab):
        return
    with tab:
        c1, c2, c3 = st.columns([3, 1.4, 1.4], vertical_alignment="center")
        en_zonas = L.get("zonas") is not None
        c1.markdown(chip(f"{nombre} · {len(L['nombres'])} equipos", cfg["chip_color"]) + " "
                    + chip("Dos zonas · ida y vuelta" if en_zonas else "Todos contra todos", "#475569"),
                    unsafe_allow_html=True)
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
        if en_zonas and L["playoffs_pendiente"]:
            nom = L["nombres"]
            cruces = " · ".join(f"{esc(c['rotulo'])}: <b>{esc(nom[c['a']])}</b> vs <b>{esc(nom[c['b']])}</b>"
                                for c in L["playoffs"])
            aviso("Terminaron las dos zonas (no hay desempates: ante igualdad de puntos pasa el de mejor diferencia de "
                  f"gol). Queda una fecha con las finales. {cruces}")

        desempates = [p for p in L["log"] if p["rotulo"] == "Desempate"]
        mostrar_desempate = L.get("desempate_pendiente") or len(desempates) > 0

        titulos = ["Posiciones", "Fixture y resultados"]
        if mostrar_desempate:
            titulos.append("Desempate")
        titulos.extend(["Movimientos", "Definiciones"])
        tabs = st.tabs(titulos)
        idx = 0

        with tabs[idx]:
            sub, ley = _textos(k, plan_de(L, k), len(L["nombres"]))
            seccion("Tabla de posiciones", color="#4f46e5")
            if en_zonas:
                etiq, ini = marcar(list(ZONAS_NOMBRES), zona_simple(L, ctx.club))   # modo manager: abre la zona de mi club
                for tab_zona, df_zona in zip(tabs_con_default(etiq, ini), tablas_zonas(L, k)):
                    with tab_zona:
                        mostrar_tabla(df_zona, colorear, L["pos_hist"])
            else:
                mostrar_tabla(tabla(L), colorear, L["pos_hist"])
            leyenda(ley)
            if L["fecha"] == 0 and not ctx.modo_mgr:      # en modo manager no se tocan las medias
                with st.expander(f":material/tune: Editar medias internas de esta temporada ({nombre})"):
                    L["r"] = editar_medias(L["nombres"], L["r"], f"editor_{k}_{S['temp']}")
        idx += 1

        with tabs[idx]:
            vista_fixture(S, ctx.club, k)
        idx += 1

        if mostrar_desempate:
            with tabs[idx]:
                if L.get("desempate_pendiente"):
                    seccion("Desempates por Posiciones", color="#9333ea")
                    df_des = tabla(L)
                    df_des = df_des[df_des["id"].isin(L["ids_desempate"])]
                    mostrar_tabla(df_des, colorear)
                else:
                    grupos = {}
                    for p in desempates:
                        grupos.setdefault(p["comp"], []).append(p)
                    for motivo, parts in grupos.items():
                        if "Liguilla" in motivo:
                            seccion(f"Tabla final: {motivo}", color="#9333ea")
                            st.markdown(html_tabla_liguilla(parts), unsafe_allow_html=True)
                            with st.expander(f":material/visibility: Ver los {len(parts)} enfrentamientos",
                                             expanded=False):
                                for p in parts:
                                    st.markdown(fila_partido_html(S, ctx.club, p), unsafe_allow_html=True)
                        else:
                            seccion(f"Desempate: {motivo}", color="#dc2626")
                            for p in parts:
                                st.markdown(fila_partido_html(S, ctx.club, p, abierto=True), unsafe_allow_html=True)
            idx += 1

        with tabs[idx]:
            render_movimientos(L["log"], L["pos_hist"], L["nombres"], "#0f766e")
        idx += 1

        with tabs[idx]:
            seccion("Definiciones de la temporada", color="#b7860b")
            if L["campeon"] is None:
                aviso("Las definiciones aparecen acá cuando termina la liga.")
            else:
                with st.expander(f":material/emoji_events: {cfg['expander_campeon']}", expanded=False):
                    campeon = L["nombres"][L["campeon"]]
                    st.markdown(f'<div class="champ"><div class="t">Campeón</div><div style="margin-top:10px">'
                                f'{crest(campeon, 64)}</div><div class="nm">{esc(campeon)}</div></div>',
                                unsafe_allow_html=True)
                if L.get("bracket"):
                    with st.expander(":material/account_tree: Reducido por el ascenso", expanded=False):
                        st.markdown(bracket_html_simple(L, SUBE_A[k]), unsafe_allow_html=True)
                if en_zonas:
                    with st.expander(":material/sports_soccer: Finales por el ascenso", expanded=False):
                        for p in L["log"]:
                            if p["comp"] in ("Final", "Playoff"):
                                st.markdown(fila_partido_html(S, ctx.club, p, abierto=True), unsafe_allow_html=True)
                    with st.expander(f":material/trending_up: Ascienden a {SUBE_A[k]}", expanded=False):
                        if L["ascendidos"]:
                            for i in L["ascendidos"]:
                                st.markdown(f'<div style="margin:4px 0">{crest(L["nombres"][i], 28)} '
                                            f'<b>{esc(L["nombres"][i])}</b></div>', unsafe_allow_html=True)
                        else:
                            st.write("Esta temporada no hay ascensos.")

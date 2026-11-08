"""Ligas de primera división de otros países (Uruguay hoy; las demás se suman solas).

Van en la pestaña Ligas cuando el país activo (se elige en Mundo, ver ui/ui_mundo.py) es ese país. Cada liga tiene la
misma pantalla: barra de estado, posiciones (una tabla por torneo), fixture y resultados, y definiciones. Todo sale de la liga (`copas.registro.LigaExterior`) y de su formato (ligas/exterior.py):
agregar un país no pide tocar este archivo.
"""

import streamlit as st

from copas.registro import LIGAS_EXTERIOR
from datos.logos import logo_img
from motor import consultas
from motor.calendario import texto_dia
from ui.vista import (
    COLOR_ORO,
    COLORES_B,
    COLORES_DESTINO,
    aviso,
    chip,
    crest,
    esc,
    cuadro_campeonato_html,
    leyenda,
    mostrar_tabla,
    render_fecha,
    seccion,
    tabla_html,
)
from ui.vista.editor_medias import editar_medias

LEYENDA = [("Campeón / líder", COLOR_ORO), ("Libertadores", COLORES_DESTINO["Libertadores"]),
           ("Libertadores · Fase 2 / Fase 1", COLORES_DESTINO["Fase previa Libertadores"]),
           ("Sudamericana", COLORES_DESTINO["Sudamericana"]), ("A la final", COLORES_B["Ascenso directo"]),
           ("Desciende", COLORES_B["Desciende"])]
LEYENDA_SEGUNDA = [("Campeón / líder", COLOR_ORO), ("Asciende / a la final", COLORES_B["Ascenso directo"]),
                   ("Playoff por el tercer ascenso", COLORES_B["Reducido"])]


def _color_destino(txt):
    """Color de la fila según su destino; el texto puede combinar varios ("Campeón · Libertadores")."""
    if "Desciende" in txt:
        return COLORES_B["Desciende"]
    if "Campeón" in txt or "Líder" in txt:
        return COLOR_ORO
    if "Asciende" in txt:                      # segunda división: ascenso directo o por el playoff
        return COLORES_B["Ascenso directo"]
    if "Playoff" in txt:
        return COLORES_B["Reducido"]
    if "Libertadores · Fase" in txt:
        return COLORES_DESTINO["Fase previa Libertadores"]
    if "Libertadores" in txt:
        return COLORES_DESTINO["Libertadores"]
    if "Sudamericana" in txt:
        return COLORES_DESTINO["Sudamericana"]
    if "A la final" in txt:
        return COLORES_B["Ascenso directo"]
    return ""


def _colorear(fila):
    c = _color_destino(fila.get("Destino", ""))
    return [f"background-color: {c}" if c else ""] * len(fila)


def _leyenda_comp(comp, L):
    if comp.divisional > 1:
        if comp.formato.nombre == "todos_contra_todos":
            ley = [("Campeón / líder", COLOR_ORO), ("Asciende", COLORES_B["Ascenso directo"])]
            if L.get("descensos"):
                ley.append(("Desciende", COLORES_B["Desciende"]))
            return ley
        return LEYENDA_SEGUNDA + ([("Desciende a la tercera división", COLORES_B["Desciende"])] if L.get("descensos") else [])
    if comp.formato.nombre == "todos_contra_todos":
        ley = [("Campeón / líder", COLOR_ORO), ("Libertadores", COLORES_DESTINO["Libertadores"]),
               ("Libertadores · Fase 2 / Fase 1", COLORES_DESTINO["Fase previa Libertadores"]),
               ("Sudamericana", COLORES_DESTINO["Sudamericana"])]
        if L.get("descensos"):
            ley.append(("Desciende", COLORES_B["Desciende"]))
        return ley
    return LEYENDA


def _render_item_tabla(t):
    if t["df"] is None:
        aviso(t["nota"])
    elif t["tipo"] == "descenso":
        st.markdown(tabla_html(t["df"], _colorear, formatos={"Prom": "{:.3f}"}, fija="Equipo"),
                    unsafe_allow_html=True)
    else:
        mostrar_tabla(t["df"], _colorear)
    if t["df"] is not None and t["nota"]:
        st.caption(t["nota"])


def _tablas(ctx, comp, L):
    """Una pestaña por tabla del formato (Apertura, Intermedio, Clausura, Anual, Descenso...). En una primera división
    con definiciones por llaves (Uruguay) se suma "Campeones" justo antes de Descenso; en ligas regulares por puntos
    como Brasil no se muestra."""
    items = [(t["titulo"], t) for t in comp.formato.tablas(L)]
    if comp.divisional == 1 and bool(comp.formato.etapas_definicion):
        i = next((k for k, (n, _) in enumerate(items) if n == "Descenso"), len(items))
        items.insert(i, ("Campeones", None))
    if len(items) == 1:
        _render_item_tabla(items[0][1])
    else:
        for tab, (titulo, t) in zip(st.tabs([n for n, _ in items]), items):
            with tab:
                if t is None:
                    _campeones(ctx, comp, L)
                    continue
                _render_item_tabla(t)
    leyenda(_leyenda_comp(comp, L))


def _fixture(ctx, comp, L):
    S = ctx.S
    seccion("Fixture y resultados", color="#1e5aa8")
    rondas = L["rondas"]
    jugadas = L["fecha"]
    key = f"fx_sel_{comp.clave}_{S['temp']}_{jugadas}"
    if key not in st.session_state:
        st.session_state[key] = max(1, min(jugadas + 1, len(rondas)))
    elegida = st.selectbox("Fecha", list(range(1, len(rondas) + 1)), key=key, label_visibility="collapsed",
                           format_func=lambda n: rondas[n - 1]["rotulo"] + (" · jugada" if n <= jugadas else " · por jugar"))
    estado = chip("Jugada", "#16a34a") if elegida <= jugadas else (
        chip("Próxima fecha", "#2f7fd0") if elegida == jugadas + 1 else chip("Por jugar", "#64748b"))
    st.markdown(f'<div class="fx-head">{estado}<span class="m-dia">{esc(texto_dia(rondas[elegida - 1]["dia"]))}</span></div>',
                unsafe_allow_html=True)
    partidos = consultas.partidos_de_calendario(S, comp.nombre, elegida)
    if not partidos:
        st.info("Los cruces de esta fecha se conocen cuando termina la etapa anterior.")
        return
    render_fecha(S, ctx.club, partidos, f"{comp.clave}{S['temp']}_{elegida}")




def _campeones(ctx, comp, L):
    """Campeones de cada temporada y cómo se definió cada título (semifinales, finales y desempates, si los hubo).
    El campeón suma al palmarés (pestaña Historial) cuando se cierra la temporada."""
    S = ctx.S
    registros = list(reversed(S.get("ext_def", {}).get(comp.clave, [])))
    if L["campeon"] is not None:                     # la temporada en curso, si ya se definió
        registros.insert(0, {**comp.definiciones(S, L), "en_curso": True})
    if not registros:
        aviso("Todavía no hay campeones: el título se define al terminar la temporada.")
        return
    titulos = S.get(comp.hist, {})
    for k, reg in enumerate(registros):
        en_curso = reg.get("en_curso", False)
        etiqueta = (f"Temporada {reg['temp']} · {reg['campeon']}" + (" · en curso" if en_curso else ""))
        with st.expander(f":material/emoji_events: {etiqueta}", expanded=k == 0):
            sub = f" · Subcampeón: {esc(reg['subcampeon'])}" if reg.get("subcampeon") else ""
            st.markdown(f'<div class="champ"><div class="t">Campeón</div><div style="margin-top:10px">'
                        f'{crest(reg["campeon"], 64)}</div><div class="nm">{esc(reg["campeon"])}</div></div>'
                        f'<div style="opacity:.75;text-align:center;margin-top:4px">{sub.lstrip(" ·")}</div>',
                        unsafe_allow_html=True)
            if reg.get("via"):
                st.caption(reg["via"])
            if reg.get("ganadores"):
                st.markdown(" ".join(chip(f"{t}: {n}", "#475569") for t, n in reg["ganadores"].items()),
                            unsafe_allow_html=True)
            st.markdown(cuadro_campeonato_html(reg), unsafe_allow_html=True)
            if not any(p["comp"] in ("Semifinal", "Final") for p in reg["partidos"]):
                st.caption("Se definió sin semifinal ni final.")
            n = titulos.get(reg["campeon"], 0)
            st.caption(("Suma un título al palmarés cuando termina la temporada. " if en_curso else "")
                       + f"Títulos de {reg['campeon']} en {comp.nombre} (temporadas simuladas): {n}.")


def _render_liga(ctx, comp):
    S, P = ctx.S, ctx.P
    L, cfg = S[comp.clave], comp.cfg
    tab = (ctx.pestanas.tabs_ligas_ext or {}).get(cfg["clave"])    # sólo existe si el país activo es el de esta liga
    if not ctx.abierta(ctx.pestanas.tab_ligas, tab):
        return
    with tab:
        terminada = comp.terminada(S)
        c1, c2, c3 = st.columns([3, 1.4, 1.4], vertical_alignment="center")
        movimiento = (chip(f"Suben {L['ascensos']}", "#2e7d4f") if comp.divisional > 1
                      else chip(f"Descienden {L['descensos']}", "#b83a2e"))
        if comp.divisional > 1 and L.get("descensos"):         # segunda con descenso a una tercera división falsa
            movimiento += " " + chip(f"Descienden {L['descensos']}", "#b83a2e")
        c1.markdown(logo_img(cfg["nombre"], 30) + " " + chip(f"{L['nombre']} · {len(L['nombres'])} equipos", "#1e5aa8") + " "
                    + movimiento,
                    unsafe_allow_html=True)
        if not ctx.modo_mgr and c2.button(":material/skip_next: Próxima fecha", key=f"{comp.clave}_next",
                                          width="stretch", type="primary", disabled=terminada):
            comp.jugar(S, P, S["rng"])
            st.rerun()
        if not ctx.modo_mgr and c3.button(":material/fast_forward: Hasta el final", key=f"{comp.clave}_all",
                                          width="stretch", disabled=terminada):
            comp.jugar_todo(S, P, S["rng"])
            st.rerun()
        st.caption(comp.formato.reglas())
        sub = st.tabs(["Posiciones", "Fixture y resultados"])
        with sub[0]:
            seccion("Tablas de posiciones", color="#4f46e5")
            _tablas(ctx, comp, L)
            if L["fecha"] == 0 and not ctx.modo_mgr:       # en modo manager no se tocan las medias
                with st.expander(f":material/tune: Editar medias internas de esta temporada ({L['nombre']})"):
                    L["r"] = editar_medias(L["nombres"], L["r"], f"editor_{comp.clave}_{S['temp']}")
        with sub[1]:
            _fixture(ctx, comp, L)


def render(ctx):
    for comp in LIGAS_EXTERIOR:
        _render_liga(ctx, comp)

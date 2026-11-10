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
    cuadro_llaves_html,
    leyenda,
    mostrar_tabla,
    render_fecha,
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
    if "Playoff" in txt or "Fase final" in txt or "Segunda fase" in txt:
        # playoff de la segunda / fase final de la Primera Amateur / segunda fase de la Série D
        return COLORES_B["Reducido"]
    if "Libertadores · Fase 2" in txt or "Libertadores · Fase 1" in txt:
        return COLORES_DESTINO["Fase previa Libertadores"]
    if "Libertadores" in txt:
        return COLORES_DESTINO["Libertadores"]
    if "Sudamericana" in txt:
        return COLORES_DESTINO["Sudamericana"]
    if "A la final" in txt:
        return COLORES_B["Ascenso directo"]
    if "Cuadrangulares" in txt or "Clasifica" in txt:
        return COLORES_B["Reducido"]
    return ""


def _colorear(fila):
    c = _color_destino(fila.get("Destino", ""))
    return [f"background-color: {c}" if c else ""] * len(fila)


def _leyenda_comp(comp, L):
    if comp.formato.nombre == "paraguay":
        return [("Campeón / líder", COLOR_ORO), ("Libertadores", COLORES_DESTINO["Libertadores"]),
                ("Libertadores · Fase 2 / Fase 1", COLORES_DESTINO["Fase previa Libertadores"]),
                ("Sudamericana", COLORES_DESTINO["Sudamericana"]), ("Desciende", COLORES_B["Desciende"])]
    if comp.formato.nombre == "paraguay_segunda":
        return [("Campeón / líder", COLOR_ORO), ("Asciende a Primera", COLORES_B["Ascenso directo"]),
                ("Desciende a la tercera división", COLORES_B["Desciende"])]
    if comp.formato.nombre == "brasil_d":
        return [("Campeón / líder", COLOR_ORO), ("Asciende a la Série C", COLORES_B["Ascenso directo"]),
                ("Pasa a la segunda fase", COLORES_B["Reducido"])]
    if comp.formato.nombre == "uruguay_amateur":
        return [("Campeón / líder", COLOR_ORO), ("Asciende a la Segunda", COLORES_B["Ascenso directo"]),
                ("Pasa a la fase final", COLORES_B["Reducido"])]
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
    if comp.formato.nombre == "colombia":
        return [("Campeón / líder", COLOR_ORO), ("Clasifica a cuadrangulares", COLORES_B["Reducido"]),
                ("Clasifica a la final", COLORES_B["Ascenso directo"]),
                ("Libertadores", COLORES_DESTINO["Libertadores"]),
                ("Libertadores · Fase previa", COLORES_DESTINO["Fase previa Libertadores"]),
                ("Sudamericana", COLORES_DESTINO["Sudamericana"]),
                ("Desciende", COLORES_B["Desciende"])]
    return LEYENDA


def _render_item_tabla(t):
    if t["df"] is None:
        aviso(t["nota"])
    elif t["tipo"] == "descenso":
        st.markdown(tabla_html(t["df"], _colorear, formatos={"Prom": "{:.3f}", "Promedio": "{:.3f}"}, fija="Equipo"),
                    unsafe_allow_html=True)
    else:
        mostrar_tabla(t["df"], _colorear)


def _tablas(ctx, comp, L):
    """Una pestaña por tabla del formato (Apertura, Intermedio, Clausura, Anual, Descenso...). En una primera división
    con definiciones por llaves (Uruguay) se suma "Campeones" justo antes de Descenso; en ligas regulares por puntos
    como Brasil no se muestra. Las tablas con "agrupa" (los 16 grupos de la Série D) comparten una sola pestaña."""
    items = []                                         # (nombre de la pestaña, [tablas] | None | "llaves")
    for t in comp.formato.tablas(L):
        destino = t.get("agrupa") or t["titulo"]
        previo = next((it for it in items if it[0] == destino and isinstance(it[1], list)), None)
        if previo and t.get("agrupa"):
            previo[1].append(t)
        else:
            items.append((destino, [t]))
    if (comp.divisional == 1 and (bool(comp.formato.etapas_definicion) or comp.torneos)
            and comp.formato.nombre != "colombia"):
        i = next((k for k, (n, _) in enumerate(items) if n == "Descenso" or n.startswith("Tabla de descenso")), len(items))
        items.insert(i, ("Campeones", None))
    elif hasattr(comp.formato, "llaves"):              # fase final por llaves (Primera Amateur, Série D)
        items.append(("Llaves", "llaves"))
    if len(items) == 1:
        for t in items[0][1]:
            _render_item_tabla(t)
    else:
        for tab, (titulo, ts) in zip(st.tabs([n for n, _ in items]), items):
            with tab:
                if ts is None:
                    _campeones(ctx, comp, L)
                elif ts == "llaves":
                    _llaves(comp, L)
                else:
                    for t in ts:
                        if len(ts) > 1:
                            st.markdown(f"**{esc(t['titulo'])}**")
                        _render_item_tabla(t)
    leyenda(_leyenda_comp(comp, L))


def _llaves(comp, L):
    """Cuadro de la fase final de una liga con llaves (Primera Amateur, Série D): rondas, final y campeón."""
    info = getattr(comp.formato, "llaves_info", None)
    if info:                                           # el formato dice qué mostrar (Série D)
        aviso_txt, subtitulo, pie = info(L)
    else:                                              # Primera Amateur
        aviso_txt = None if L["hecho"]["Regular"] else \
            "La fase final se arma cuando termina la fase regular: pasan los 4 primeros de cada serie."
        subtitulo = "Asciende a la Segunda División"
        pie = ("Cuartos: 1° contra 4° y 2° contra 3° de la otra serie. Juega de local el mejor ubicado de la fase regular; "
               "la final, en cancha neutral. Ascienden el campeón y el subcampeón.")
    if aviso_txt:
        aviso(aviso_txt)
    st.markdown(cuadro_llaves_html(comp.formato.llaves(L), L["campeon"], f"Campeón · {L['nombre']}", subtitulo),
                unsafe_allow_html=True)


def _fixture(ctx, comp, L):
    S = ctx.S
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
    if L["campeon"] is not None or (comp.torneos and L.get("ganadores")):    # la temporada en curso, si ya se definió
        registros.insert(0, {**comp.definiciones(S, L), "en_curso": True})
    if not registros:
        aviso("Todavía no hay campeones: el título se define al terminar la temporada.")
        return
    titulos = S.get(comp.hist, {})
    for k, reg in enumerate(registros):
        en_curso = reg.get("en_curso", False)
        if comp.torneos:                             # Paraguay: dos torneos independientes, dos campeones
            _campeones_torneos(S, comp, reg, k == 0, en_curso)
            continue
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


def _campeones_torneos(S, comp, reg, abierto, en_curso):
    """Una temporada de una liga con torneos independientes (Paraguay): el campeón y el subcampeón de cada uno."""
    gan, subs = reg.get("ganadores", {}), reg.get("subcampeones", {})
    etiqueta = (f"Temporada {reg['temp']} · " + (f"Campeón {reg['campeon']} · " if reg.get("campeon") else "")
                + " · ".join(f"{t}: {n}" for t, n in gan.items()) + (" · en curso" if en_curso else ""))
    with st.expander(f":material/emoji_events: {etiqueta}", expanded=abierto):
        for col, t in zip(st.columns(len(comp.torneos)), comp.torneos):
            with col:
                club = gan.get(t)
                if club is None:
                    st.markdown(f"**{esc(t)}**")
                    st.caption("Todavía no se definió.")
                    continue
                sub = f'<div style="opacity:.75;text-align:center;margin-top:4px">Subcampeón: {esc(subs[t])}</div>' if subs.get(t) else ""
                st.markdown(f'<div class="champ"><div class="t">Campeón del {esc(t)}</div><div style="margin-top:10px">'
                            f'{crest(club, 64)}</div><div class="nm">{esc(club)}</div></div>{sub}', unsafe_allow_html=True)
        if reg.get("via"):
            st.caption(reg["via"])
        titulos = S.get(comp.hist, {})
        camp = reg.get("campeon")
        st.caption(("El campeón del año (el de la final, o el que ganó los dos torneos) suma un título al palmarés cuando termina la temporada. "
                    if en_curso else "")
                   + (f"Títulos de {camp} en {comp.nombre} (temporadas simuladas): {titulos.get(camp, 0)}" if camp else ""))


def _finales(ctx, comp, L):
    """Muestra las finales semestrales y las definiciones anuales/ascenso de Colombia."""
    S = ctx.S
    indices = []
    for i, ronda in enumerate(L.get("rondas", [])):
        etiqueta = f"{ronda.get('etapa', '')} {ronda.get('comp', '')}".casefold()
        if "final" in etiqueta:
            indices.append(i)
    if not indices:
        aviso("Las finales de Apertura y Clausura aparecerán cuando se clasifiquen los equipos.")
        return
    for i in indices:
        R = L["rondas"][i]
        titulo = R.get("rotulo") or R.get("comp") or R.get("etapa", "Final")
        st.markdown(f"**{esc(titulo)}**")
        st.caption(texto_dia(R["dia"]))
        partidos = consultas.partidos_de_calendario(S, comp.nombre, i + 1)
        if partidos:
            render_fecha(S, ctx.club, partidos, f"final_{comp.clave}_{S['temp']}_{i+1}")
        else:
            aviso("Los participantes de esta final se conocerán al terminar la fase anterior.")


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
        es_colombia = comp.formato.nombre in ("colombia", "colombia_segunda")
        nombres_sub = ["Posiciones", "Fixture y resultados"] + (["Finales"] if es_colombia else [])
        sub = st.tabs(nombres_sub)
        with sub[0]:
            _tablas(ctx, comp, L)
            if L["fecha"] == 0 and not ctx.modo_mgr:       # en modo manager no se tocan las medias
                with st.expander(f":material/tune: Editar medias internas de esta temporada ({L['nombre']})"):
                    L["r"] = editar_medias(L["nombres"], L["r"], f"editor_{comp.clave}_{S['temp']}")
        with sub[1]:
            _fixture(ctx, comp, L)
        if es_colombia:
            with sub[2]:
                _finales(ctx, comp, L)


def render(ctx):
    for comp in LIGAS_EXTERIOR:
        _render_liga(ctx, comp)

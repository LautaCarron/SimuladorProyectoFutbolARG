"""Pestaña Copas · Estaduales (sólo cuando el país activo es Brasil).

Los campeonatos estaduales (Paulistão, Carioca, Mineiro, Gaúcho...) de los clubes de la Série A a la D. Siempre se juegan:
no hay interruptor. La lógica está en copas/estaduales.py. Modo manager: no aplica (sólo se dirigen clubes argentinos).
"""

import pandas as pd
import streamlit as st

from copas.estaduales import (CORTO_CATEGORIA, ETAPAS_LLAVE, MIN_CLUBES, destino_grupo, fase_torneo, nombre_grupo,
                              simular_ronda_estaduales, tabla_grupo)
from datos.logos import logo_img
from ui.vista import (COLORES_B, aviso, chip, crest, esc, fila_partido_html, seccion, tabla_html)
from ui.vista.cuadros import _kb, _kb_final, _kb_ronda

COLOR = "#1f8a4c"
TODOS = "Todos los torneos"


def _estilo_grupo(fila):
    d = fila["Destino"]
    c = (COLORES_B["Ascenso directo"] if d == "Clasifica" else "rgba(249, 115, 22, 0.3)" if d == "Mejor tercero" else "")
    return [f"background-color: {c}" if c else ""] * len(fila)


def _tabla_de_grupo(R, t, k):
    df = tabla_grupo(R, t, k)
    df["Destino"] = [destino_grupo(t, int(i), int(p)) or "" for i, p in zip(df["id"], df["Pos"])]
    df = df.drop(columns="id")
    df = df[["Pos", "Equipo", "Categoría", "Pts", "PJ", "G", "E", "P", "GF", "GC", "DG", "Destino", "Media"]]
    st.markdown(tabla_html(df, _estilo_grupo, formatos={"Media": "{:.1f}"}, fija="Equipo"), unsafe_allow_html=True)


def _llave_html(R, t):
    """Cuadro de la llave del torneo: cuartos (si hay), semifinales, final y campeón. Lo que no se conoce, "A definir"."""
    B = t["llave"]
    cuadro = {"nombres": R["nombres"], "origen": R["cat"]}
    cols = []
    for k, etapa in enumerate(ETAPAS_LLAVE[B]):
        ronda = t["ko"][k]["partidos"] if k < len(t["ko"]) else [None] * (B >> (k + 1))
        cols.append(_kb_ronda(cuadro, etapa, ronda))
    c = t["campeon"]
    cols.append(_kb_final(f"Campeón · {t['corto']}", "Campeón", R["nombres"][c] if c is not None else None,
                          CORTO_CATEGORIA[R["cat"][c]] if c is not None else ""))
    return _kb(cols, max(2, B // 2) * 84)


def _tarjeta_campeon(S, R, t):
    c, s = t["campeon"], t["subcampeon"]
    st.markdown(f'<div class="champ"><div class="t">Campeón · {esc(t["nombre"])} · Temporada {S["temp"]}</div>'
                f'<div style="margin-top:10px">{crest(R["nombres"][c], 64)}</div>'
                f'<div class="nm">{esc(R["nombres"][c])}</div><div class="s">{esc(CORTO_CATEGORIA[R["cat"][c]])}'
                f' · finalista: {esc(R["nombres"][s])}</div></div>', unsafe_allow_html=True)


def _pestana_torneos(ctx, R, mi_torneo):
    S = ctx.S
    ids = [t["id"] for t in R["torneos"]]
    por_id = {t["id"]: t for t in R["torneos"]}
    # la key lleva el club: al cambiar de club, la pestaña se vuelve a abrir en su torneo
    k = "_" + "".join(c if c.isalnum() else "_" for c in ctx.club) if mi_torneo else ""
    elegido = st.pills("Torneo", ids, default=mi_torneo["id"] if mi_torneo else ids[0], key=f"est_torneo{k}_{S['temp']}",
                       format_func=lambda i: por_id[i]["corto"] + (" ⭐" if mi_torneo and i == mi_torneo["id"] else ""),
                       label_visibility="collapsed") or (mi_torneo["id"] if mi_torneo else ids[0])
    t = por_id[elegido]
    st.markdown(logo_img(t["nombre"], 34) + " " + chip(f"{len(t['ids'])} clubes", t["color"]) + " "
                + chip(f"{len(t['grupos'])} " + ("grupo" if len(t["grupos"]) == 1 else "grupos"), "#475569") + " "
                + chip(f"{t['llave']} a la llave", "#475569") + " "
                + chip(fase_torneo(t, R["ronda"]), "#16a34a" if t["campeon"] is None else "#b7860b"),
                unsafe_allow_html=True)
    st.caption(t["zona"])
    if t["campeon"] is not None:
        _tarjeta_campeon(S, R, t)
    seccion("Fase de grupos" if len(t["grupos"]) > 1 else "Tabla · todos contra todos", "cada club juega una vez contra los de los otros grupos" if t["cruzado"] else "una rueda", t["color"])
    for g in range(len(t["grupos"])):
        mio = ctx.club and ctx.club in [R["nombres"][i] for i in t["grupos"][g]]
        st.markdown(f'<div class="mlab" style="margin-top:14px">{esc(nombre_grupo(len(t["grupos"]), g))} · '
                    f'{len(t["grupos"][g])} clubes{" ⭐" if mio else ""}</div>', unsafe_allow_html=True)
        _tabla_de_grupo(R, t, g)
    seccion("Llave", "partido único · el mejor sembrado de local · la final, en cancha neutral", t["color"])
    st.markdown(_llave_html(R, t), unsafe_allow_html=True)


def _pestana_partidos(ctx, R, mi_torneo):
    S = ctx.S
    if not R["log"]:
        aviso("Todavía no se jugó ninguna ronda. Los cruces de cada fecha están en el <b>Calendario</b>.")
        return
    c1, c2 = st.columns(2)
    jugadas = R["ronda"]
    ronda = c1.selectbox(":material/event: Ronda", range(1, jugadas + 1), index=jugadas - 1,
                         format_func=lambda n: f"Ronda {n}", key=f"est_ronda_{S['temp']}")
    opciones = [TODOS] + [t["nombre"] for t in R["torneos"]]
    k = "_" + "".join(c if c.isalnum() else "_" for c in ctx.club) if mi_torneo else ""
    torneo = c2.selectbox(":material/map: Torneo", opciones, index=opciones.index(mi_torneo["nombre"]) if mi_torneo else 0,
                          key=f"est_filtro{k}_{S['temp']}")
    partidos = [p for p in R["log"] if p["fecha"] == ronda and (torneo == TODOS or p["comp"] == torneo)]
    if not partidos:
        aviso("Ese torneo no juega en esta ronda.")
    for p in partidos:
        st.markdown(fila_partido_html(S, ctx.club, p), unsafe_allow_html=True)


def _tabla_de_formato(filas):
    df = pd.DataFrame(filas, columns=["Torneo", "Estado", "Clubes", "Grupos", "A la llave"])
    st.markdown(tabla_html(df, clubes=()), unsafe_allow_html=True)


def _pestana_formato(R):
    st.markdown(
        "* **Quiénes juegan**: los clubes de la Série A, B, C y D, cada uno en el torneo de su estado. Entran primero los de "
        "la división más alta y los de mayor media; si el estado tiene pocos clubes, se completa con clubes complementarios "
        "(sin escudo, que no juegan ninguna liga nacional).\n"
        "* **Fase de grupos**: una tabla todos contra todos a una rueda. El Paulistão tiene 4 grupos de 4 y cada club juega una "
        "vez contra los de los otros grupos.\n"
        "* **Llaves**: cuartos de final (8 clasificados) o semifinales (4), y final, a partido único, penales si empatan; "
        "la final en cancha neutral.\n"
        "* Se juega una ronda cada 4 días desde el 10 de enero, antes de la Série B, la C y la D.")
    _tabla_de_formato([(t["nombre"], t["zona"], len(t["ids"]), len(t["grupos"]), t["llave"]) for t in R["torneos"]])
    if R["sin_torneo"]:
        st.caption("Sin lugar en su estadual esta temporada: " + ", ".join(R["sin_torneo"]))


def render(ctx):
    (P, S, _abierta, tab_copas, tab_est) = (ctx.P, ctx.S, ctx.abierta, ctx.pestanas.tab_copas, ctx.pestanas.tab_est)
    if not _abierta(tab_copas, tab_est):
        return
    R = S["estaduales"]
    with tab_est:
        c1, c2, c3 = st.columns([3, 1.4, 1.4], vertical_alignment="center")
        c1.markdown(logo_img("Estaduales", 30) + " " + chip("Estaduales", COLOR) + " "
                    + chip(f"{len(R['torneos'])} torneos · {len(R['nombres'])} clubes", "#475569"), unsafe_allow_html=True)
        listo = R["activo"] and R["ronda"] < R["total"]
        if not ctx.modo_mgr and c2.button(":material/skip_next: Próxima ronda", key="est_next", width="stretch",
                                          type="primary", disabled=not listo):
            simular_ronda_estaduales(S, P, S["rng"])
            st.rerun()
        if not ctx.modo_mgr and c3.button(":material/fast_forward: Hasta el final", key="est_all", width="stretch",
                                          disabled=not listo):
            while S["estaduales"]["ronda"] < S["estaduales"]["total"]:
                simular_ronda_estaduales(S, P, S["rng"])
            st.rerun()
        if not R["activo"]:
            aviso("Los Estaduales se arman con los clubes de las divisiones de Brasil, que todavía no están cargadas.")
            return
        mi_torneo = None
        titulos = ["Torneos", "Partidos", "Formato"]
        tabs = dict(zip(titulos, st.tabs(titulos)))
        with tabs["Torneos"]:
            _pestana_torneos(ctx, R, mi_torneo)
        with tabs["Partidos"]:
            _pestana_partidos(ctx, R, mi_torneo)
        with tabs["Formato"]:
            _pestana_formato(R)

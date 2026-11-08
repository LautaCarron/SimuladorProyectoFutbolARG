"""Pestaña Copas · Regionales.

Los torneos regionales por zona (Porteño, Sur y La Plata, Norte y Oeste, Bonaerense, Cordobés, Cuyano, Litoral,
Nordeste, Noroeste y Patagónico), al estilo de los estaduales de Brasil. Es una copa opcional: el interruptor de
arriba la activa o la desactiva (rige ya si la temporada no empezó; si no, desde la que viene). La lógica está en
copas/regionales.py. Modo manager: se abre sola (y se marca con ⭐) la zona donde juega el club que dirigís.
"""

import pandas as pd
import streamlit as st

from copas.regionales import (CORTO_CATEGORIA, ETAPAS_LLAVE, MIN_CLUBES, cambiar_activacion, destino_grupo,
                              fase_torneo, nombre_grupo, pendiente_de_aplicar, plan, simular_ronda_regionales,
                              tabla_grupo, torneo_del_club)
from datos.logos import logo_img
from ui.vista import (COLORES_B, aviso, chip, crest, esc, fila_partido_html, seccion, tabla_html)
from ui.vista.cuadros import _kb, _kb_final, _kb_ronda

COLOR = "#0d9488"
TODOS = "Todos los torneos"


def _cb_interruptor(S, clave, temporada_empezada):
    """Al mover el interruptor: se activa o desactiva (ahora, o desde la próxima temporada si ya empezó)."""
    rige = cambiar_activacion(S, S["rng"], st.session_state[clave], temporada_empezada)
    if rige:
        st.toast("Regionales " + ("activados." if S["regionales_on"] else "desactivados."))
    else:
        st.toast(("Los Regionales se juegan" if S["regionales_on"] else "Los Regionales no se juegan")
                 + " desde la próxima temporada (esta ya empezó).")


def _interruptor(ctx):
    S, R = ctx.S, ctx.S["regionales"]
    empezada = ctx.progreso.partidos_jugados > 0 or R["ronda"] > 0
    # la key lleva el valor elegido: si cambia desde otro lado (cargar una partida) el interruptor se vuelve a armar
    clave = f"rgs_on_{S['temp']}_{int(bool(S['regionales_on']))}"
    st.toggle("Jugar los Regionales", value=bool(S["regionales_on"]), key=clave, on_change=_cb_interruptor,
              args=(S, clave, empezada),
              help="Copa opcional con torneos regionales para los clubes de Primera, B Nacional, Federal A, Federal B, "
                   "Primera B y Primera C. Si la temporada ya empezó, rige desde la que viene.")
    if pendiente_de_aplicar(S):
        aviso("Elegiste " + ("<b>jugar</b>" if S["regionales_on"] else "<b>no jugar</b>")
              + " los Regionales: rige desde la <b>próxima temporada</b> (esta ya empezó"
              + (" y los Regionales siguen hasta el final)." if R["activo"] else ")."))


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
    elegido = st.pills("Torneo", ids, default=mi_torneo["id"] if mi_torneo else ids[0], key=f"rgs_torneo{k}_{S['temp']}",
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
    seccion("Fase de grupos", color=t["color"])
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
                         format_func=lambda n: f"Ronda {n}", key=f"rgs_ronda_{S['temp']}")
    opciones = [TODOS] + [t["nombre"] for t in R["torneos"]]
    k = "_" + "".join(c if c.isalnum() else "_" for c in ctx.club) if mi_torneo else ""
    torneo = c2.selectbox(":material/map: Torneo", opciones, index=opciones.index(mi_torneo["nombre"]) if mi_torneo else 0,
                          key=f"rgs_filtro{k}_{S['temp']}")
    partidos = [p for p in R["log"] if p["fecha"] == ronda and (torneo == TODOS or p["comp"] == torneo)]
    if not partidos:
        aviso("Ese torneo no juega en esta ronda.")
    for p in partidos:
        st.markdown(fila_partido_html(S, ctx.club, p), unsafe_allow_html=True)


def _tabla_de_formato(filas):
    df = pd.DataFrame(filas, columns=["Torneo", "Zona", "Clubes", "Grupos", "A la llave"])
    st.markdown(tabla_html(df, clubes=()), unsafe_allow_html=True)


def _pestana_formato(R):
    st.markdown(
        f"* **Quiénes juegan**: Primera, B Nacional, Federal A, Federal B (si existe), Primera B y Primera C. No juegan el "
        f"Promocional Amateur ni el Regional Amateur.\n"
        f"* **Cada club juega el torneo de su zona**. Un torneo con menos de {MIN_CLUBES} clubes no se juega.\n"
        "* **Fase de grupos**: todos contra todos a una rueda dentro del grupo (4 a 8 clubes: 1 grupo · 9 a 16: 2 · "
        "17 a 24: 3 · 25 o más: 4). Los grupos se sortean con bombos por media.\n"
        "* **Llaves**: pasan los 2 primeros de cada grupo (y los mejores terceros si faltan lugares). Cuartos, semifinales "
        "y final a partido único, penales si empatan; la final en cancha neutral.\n"
        "* Cada torneo empieza su llave apenas termina su fase de grupos. Se juega cada 3 días, desde el 7 de enero.")
    _tabla_de_formato([(t["nombre"], t["zona"], len(t["ids"]), len(t["grupos"]), t["llave"]) for t in R["torneos"]])
    if R["sin_torneo"]:
        st.caption("Sin torneo esta temporada (su zona tiene menos de 4 clubes): " + ", ".join(R["sin_torneo"]))


def _vista_previa(ctx):
    """Con los Regionales desactivados: cómo quedarían los torneos con los clubes de hoy."""
    S = ctx.S
    aviso("Los Regionales están <b>desactivados</b>. Activalos con el interruptor de arriba: juegan los clubes de "
          "Primera, B Nacional, Federal A, Federal B, Primera B y Primera C, cada uno en el torneo de su zona.")
    juegan = plan(S)
    if not juegan:
        return
    filas = [(p["torneo"]["nombre"], p["torneo"]["zona"], len(p["clubes"]), p["grupos"], p["llave"]) for p in juegan]
    st.markdown('<div class="mlab" style="margin-top:14px">Así quedarían los torneos con los clubes de hoy</div>',
                unsafe_allow_html=True)
    _tabla_de_formato(filas)
    total = sum(len(p["clubes"]) for p in juegan)
    st.caption(f"{total} clubes en {len(juegan)} torneos. Fase de grupos a una rueda y llaves de 2, 4 u 8 clasificados "
               f"con final en cancha neutral; se juega cada 3 días desde el 7 de enero.")


def render(ctx):
    (P, S, _abierta, tab_copas, tab_rgs) = (ctx.P, ctx.S, ctx.abierta, ctx.pestanas.tab_copas, ctx.pestanas.tab_rgs)
    # ============================================================================
    # REGIONALES
    # ============================================================================
    if not _abierta(tab_copas, tab_rgs):
        return
    R = S["regionales"]
    with tab_rgs:
        c1, c2, c3 = st.columns([3, 1.4, 1.4], vertical_alignment="center")
        c1.markdown(logo_img("Regionales", 30) + " " + chip("Regionales", COLOR) + " "
                    + (chip(f"{len(R['torneos'])} torneos · {len(R['nombres'])} clubes", "#475569") if R["activo"]
                       else chip("Desactivados", "#64748b")), unsafe_allow_html=True)
        listo = R["activo"] and R["ronda"] < R["total"]
        if not ctx.modo_mgr and c2.button(":material/skip_next: Próxima ronda", key="rgs_next", width="stretch",
                                          type="primary", disabled=not listo):
            simular_ronda_regionales(S, P, S["rng"])
            st.rerun()
        if not ctx.modo_mgr and c3.button(":material/fast_forward: Hasta el final", key="rgs_all", width="stretch",
                                          disabled=not listo):
            while S["regionales"]["ronda"] < S["regionales"]["total"]:
                simular_ronda_regionales(S, P, S["rng"])
            st.rerun()
        _interruptor(ctx)
        if not R["activo"]:
            _vista_previa(ctx)
            return
        mi_torneo = torneo_del_club(S, ctx.club) if ctx.club else None
        titulos = ["Torneos", "Partidos", "Formato"]
        tabs = dict(zip(titulos, st.tabs(titulos)))
        with tabs["Torneos"]:
            _pestana_torneos(ctx, R, mi_torneo)
        with tabs["Partidos"]:
            _pestana_partidos(ctx, R, mi_torneo)
        with tabs["Formato"]:
            _pestana_formato(R)

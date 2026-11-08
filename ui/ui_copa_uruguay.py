"""Pestaña Copas · Copa AUF Uruguay (sólo cuando el país activo es Uruguay).

Tiene tres partes: Grupos (una tabla por grupo), Fixture y resultados (por ronda) y Llaves (el cuadro de octavos a la
final, como el de la Libertadores, más los dieciseisavos).
Todo sale de la copa (`copas.registro.CopaUruguay`) y de copas/uruguay.py; la copa se sortea cuando termina el Torneo
Competencia de la Segunda División, así que hasta entonces la pantalla avisa que todavía no hay cuadro.
"""

import streamlit as st

from copas import uruguay as copa_uy
from copas.registro import REGISTRO, CopaUruguay
from datos.logos import logo_img
from motor import consultas
from motor.calendario import texto_dia
from ui.vista import (COLORES_B, aviso, chip, crest, cuadro_llaves_html, dieciseisavos_html, esc, leyenda, mostrar_tabla,
                      render_fecha, seccion)

COPA = next(c for c in REGISTRO if isinstance(c, CopaUruguay))


def _color(fila):
    c = COLORES_B["Ascenso directo"] if fila.get("Destino") == "Pasa" else \
        COLORES_B["Reducido"] if fila.get("Destino") == "Mejor tercero" else ""
    return [f"background-color: {c}" if c else ""] * len(fila)


def _grupos(L):
    """Una tabla por grupo, con quiénes pasan (los 2 primeros y, de los terceros, los 4 mejores)."""
    jugada = L["fecha"] >= copa_uy.FECHAS_GRUPOS
    pasan = set(copa_uy.clasificados_grupos(L)) if jugada else set()
    tablas = copa_uy.tablas_grupos(L)
    for fila in (tablas[:3], tablas[3:]):
        for col, (nombre, df) in zip(st.columns(3), fila):
            with col:
                st.markdown(f"**{nombre}**")
                df = df.copy()
                if jugada:
                    df["Destino"] = ["Pasa" if int(i) in pasan and p <= 2 else "Mejor tercero" if int(i) in pasan else ""
                                     for i, p in zip(df["id"], df["Pos"])]
                else:
                    df["Destino"] = ["Pasa" if p <= 2 else "" for p in df["Pos"]]
                mostrar_tabla(df, _color)
    leyenda([("Pasa a dieciseisavos", COLORES_B["Ascenso directo"]), ("Uno de los 4 mejores terceros", COLORES_B["Reducido"])])
    st.caption("Pasan los dos primeros de cada grupo y los cuatro mejores terceros (puntos, diferencia de gol y goles a "
               "favor). Los amateurs no juegan grupos: entran directo a los dieciseisavos.")


def _fixture(ctx, L):
    S = ctx.S
    seccion("Fixture y resultados", color="#1e5aa8")
    rondas, jugadas = L["rondas"], L["fecha"]
    key = f"fx_sel_{COPA.clave}_{S['temp']}_{jugadas}"
    if key not in st.session_state:
        st.session_state[key] = max(1, min(jugadas + 1, len(rondas)))
    elegida = st.selectbox("Ronda", list(range(1, len(rondas) + 1)), key=key, label_visibility="collapsed",
                           format_func=lambda n: rondas[n - 1]["rotulo"] + (" · jugada" if n <= jugadas else " · por jugar"))
    estado = chip("Jugada", "#16a34a") if elegida <= jugadas else (
        chip("Próxima ronda", "#2f7fd0") if elegida == jugadas + 1 else chip("Por jugar", "#64748b"))
    st.markdown(f'<div class="fx-head">{estado}<span class="m-dia">{esc(texto_dia(rondas[elegida - 1]["dia"]))}</span></div>',
                unsafe_allow_html=True)
    partidos = consultas.partidos_de_calendario(S, COPA.nombre, elegida)
    if not partidos:
        st.info("Los cruces de esta ronda se conocen cuando termina la anterior.")
        return
    render_fecha(S, ctx.club, partidos, f"{COPA.clave}{S['temp']}_{elegida}")


def _llaves(L):
    """Cuadro de eliminación: octavos, cuartos, semifinales, final y campeón (de izquierda a derecha), y abajo los
    dieciseisavos que lo anteceden (profesionales entre sí y amateurs entre sí)."""
    seccion("Llaves · octavos a la final", color="#1e5aa8")
    st.markdown(cuadro_llaves_html(copa_uy.llaves(L, 1), L["campeon"], f"Campeón · {COPA.nombre}",
                                   "Uruguay 4 · Libertadores", alto_por_cruce=92), unsafe_allow_html=True)
    st.caption("Los octavos se sortean entre los 16 que pasan de dieciseisavos. Desde ahí, el cuadro se lee de izquierda a "
               "derecha: cada par de cruces se une en la ronda siguiente. Semifinales y final, en cancha neutral.")
    seccion("Dieciseisavos de final", color="#4f46e5")
    ms = copa_uy.llaves(L, 0)[0][1]
    st.markdown(dieciseisavos_html(ms[:8], ms[8:]), unsafe_allow_html=True)


def render(ctx):
    S, P = ctx.S, ctx.P
    tab = ctx.pestanas.tab_cuy                         # sólo existe si el país activo es Uruguay
    if not ctx.abierta(ctx.pestanas.tab_copas, tab):
        return
    L = S[COPA.clave]
    with tab:
        activa = L["sorteada"]
        terminada = COPA.terminada(S)
        c1, c2, c3 = st.columns([3, 1.4, 1.4], vertical_alignment="center")
        c1.markdown(logo_img(COPA.nombre, 30) + " " + chip(f"{COPA.nombre} · 40 equipos", "#1e5aa8") + " "
                    + chip("Partido único · penales si empatan", "#475569"), unsafe_allow_html=True)
        if not ctx.modo_mgr and c2.button(":material/skip_next: Próxima ronda", key="cuy_next", width="stretch",
                                          type="primary", disabled=COPA.pendiente(S) is None):
            COPA.jugar(S, P, S["rng"])
            st.rerun()
        if not ctx.modo_mgr and c3.button(":material/fast_forward: Hasta el final", key="cuy_all", width="stretch",
                                          disabled=COPA.pendiente(S) is None):
            COPA.jugar_todo(S, P, S["rng"])
            st.rerun()
        st.caption("16 de la Liga AUF Uruguaya, los 8 mejores de la Segunda División (Torneo Competencia) y 16 amateurs. "
                   "Fase de grupos entre los 24 profesionales; dieciseisavos entre profesionales y entre amateurs; desde "
                   "octavos, un solo cuadro (pestaña Llaves). Se sortea cuando termina el Torneo Competencia de la Segunda.")
        if not activa:
            aviso("Todavía no está sorteada: se sortea cuando la Segunda División termina el Torneo Competencia.")
            return
        sub = st.tabs(["Grupos", "Fixture y resultados", "Llaves"])
        with sub[0]:
            seccion("Fase de grupos", color="#4f46e5")
            _grupos(L)
            st.markdown(" ".join(chip(f"{o}: {sum(x == o for x in L['origen'])}", "#475569")
                                 for o in ("Profesional", "Amateur")), unsafe_allow_html=True)
        with sub[1]:
            _fixture(ctx, L)
        with sub[2]:
            _llaves(L)

"""Pestaña Copas · Copa AUF Uruguay (sólo cuando el país activo es Uruguay).

Tiene tres partes: Grupos (una tabla por grupo), Fixture y resultados (por ronda, con el cuadro de las llaves) y Campeones.
Todo sale de la copa (`copas.registro.CopaUruguay`) y de copas/uruguay.py; la copa se sortea cuando termina el Torneo
Competencia de la Segunda División, así que hasta entonces la pantalla avisa que todavía no hay cuadro.
"""

import streamlit as st

from copas import uruguay as copa_uy
from copas.registro import REGISTRO, CopaUruguay
from datos.logos import logo_img
from motor import consultas
from motor.calendario import texto_dia
from ui.vista import COLORES_B, aviso, chip, crest, esc, leyenda, mostrar_tabla, render_fecha, seccion

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


def _campeones(ctx, L):
    S = ctx.S
    registros = list(reversed(S.get("ext_def", {}).get(COPA.clave, [])))
    if L["campeon"] is not None:                         # la temporada en curso, si ya se definió
        registros.insert(0, {**copa_uy.definicion(L, S["temp"]), "en_curso": True})
    if not registros:
        aviso("Todavía no hay campeones: se define al terminar la final de la copa.")
        return
    titulos = S.get(COPA.hist, {})
    for k, reg in enumerate(registros):
        en_curso = reg.get("en_curso", False)
        with st.expander(f":material/emoji_events: Temporada {reg['temp']} · {reg['campeon']}"
                         + (" · en curso" if en_curso else ""), expanded=k == 0):
            st.markdown(f'<div class="champ"><div class="t">Campeón</div><div style="margin-top:10px">'
                        f'{crest(reg["campeon"], 64)}</div><div class="nm">{esc(reg["campeon"])}</div></div>',
                        unsafe_allow_html=True)
            if reg.get("subcampeon"):
                st.caption(f"Subcampeón: {reg['subcampeon']}")
            for p in reg["partidos"]:
                pen = f" ({p['pen'][0]}-{p['pen'][1]} en los penales)" if p.get("pen") else ""
                st.markdown(f"**{p['comp']}** · {esc(texto_dia(p['dia']))}: {esc(p['local'])} {p['gl']} - {p['gv']} "
                            f"{esc(p['visita'])}{pen}")
            n = titulos.get(reg["campeon"], 0)
            st.caption(("Suma un título al palmarés cuando termina la temporada. " if en_curso else "")
                       + f"Títulos de {reg['campeon']} en la {COPA.nombre} (temporadas simuladas): {n}.")
    st.caption("El campeón se queda con el cupo Uruguay 4 de la Copa Libertadores (Fase 1). Si ya clasificó por la liga, "
               "el cupo pasa al mejor ubicado de la Tabla Anual que todavía no clasificó.")


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
                   "octavos, un solo cuadro. Se sortea cuando termina el Torneo Competencia de la Segunda.")
        if not activa:
            aviso("Todavía no está sorteada: se sortea cuando la Segunda División termina el Torneo Competencia.")
            _campeones(ctx, L)
            return
        sub = st.tabs(["Grupos", "Fixture y resultados", "Campeones"])
        with sub[0]:
            seccion("Fase de grupos", color="#4f46e5")
            _grupos(L)
            st.markdown(" ".join(chip(f"{o}: {sum(x == o for x in L['origen'])}", "#475569")
                                 for o in ("Profesional", "Amateur")), unsafe_allow_html=True)
        with sub[1]:
            _fixture(ctx, L)
        with sub[2]:
            _campeones(ctx, L)

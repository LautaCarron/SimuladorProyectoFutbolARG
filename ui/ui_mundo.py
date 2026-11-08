"""Pestaña Mundo: elegir el país.

Cada país es una tarjeta (Argentina, Uruguay y los que se sumen). El país elegido es el "país activo": Ligas, Copas,
Calendario, Historial y Avisos muestran sólo lo de ese país (más las copas internacionales donde puede jugar). Qué
competencias son de cada país está en datos/paises.py; acá no hay que tocar nada para sumar uno.
"""

import streamlit as st

from copas.registro import LIGAS_EXTERIOR
from datos import paises
from datos.paises import PAIS_BASE
from ui.pais_activo import elegir_pais
from ui.vista import bandera, chip, esc, seccion

POR_FILA = 3


def _liga_ext(pais):
    return next((c for c in LIGAS_EXTERIOR if c.cfg["pais"] == pais), None)


def resumen(S, pais):
    """Datos de la tarjeta: {"liga": nombre de su primera, "equipos": cuántos juegan, "ligas": nombres de sus ligas,
    "copas": sus copas nacionales, "campeon": (temporada, club) del último campeón de la liga o None}."""
    ligas = [n for n in paises.ligas_de(pais) if n != "Federal B" or S.get("fb") is not None]
    if pais == PAIS_BASE:
        liga, equipos, col = "Primera División", len(S["nombres"]), "Primera División"
    else:
        comp = _liga_ext(pais)
        liga, equipos, col = comp.nombre, len(S[comp.clave]["nombres"]), comp.col_historial
    campeon = next(((x["Temporada"], x[col]) for x in reversed(S["campeones"]) if x.get(col)), None)
    return {"liga": liga, "equipos": equipos, "ligas": ligas, "copas": paises.copas_nacionales_de(pais),
            "campeon": campeon}


def _bandera_html(pais, ancho):
    """Bandera como imagen; si no hay una conocida para ese país, el emoji de siempre."""
    return bandera(pais, ancho, sola=True) or esc(paises.bandera(pais))


def _tarjeta(S, pais, activo):
    r = resumen(S, pais)
    with st.container(border=True):
        st.markdown(
            f'<div style="font-size:2.4rem;line-height:1.1;margin-bottom:4px">{_bandera_html(pais, 60)}</div>'
            f'<div style="font-weight:800;font-size:1.3rem;margin:2px 0 6px">{esc(pais)}</div>'
            f'<div class="mlab">{esc(r["liga"])} · {r["equipos"]} equipos</div>'
            + " ".join(chip(t, "#475569") for t in (
                f'{len(r["ligas"])} liga{"s" if len(r["ligas"]) != 1 else ""}',
                f'{len(r["copas"])} copa{"s" if len(r["copas"]) != 1 else ""} nacional{"es" if len(r["copas"]) != 1 else ""}'))
            + (f'<div style="margin-top:8px;opacity:.8;font-size:.9rem">Último campeón (temporada {r["campeon"][0]}): '
               f'<b>{esc(r["campeon"][1])}</b></div>' if r["campeon"] else ""),
            unsafe_allow_html=True)
        st.button(":material/check_circle: Seleccionado" if activo else f"Ver {pais}", key=f"mundo_pais_{pais}",
                  width="stretch", type="primary" if activo else "secondary", disabled=activo,
                  on_click=elegir_pais, args=(pais,))


def indicador(pais, movil=False):
    """Qué país se está viendo. Va en la fila de los botones de arriba; con `movil` se dibuja aparte y sólo se ve en el
    celular (ahí esa fila no tiene lugar para el chip)."""
    chip = f'<span class="chip" style="--c:#1e5aa8">{_bandera_html(pais, 20)} {esc(pais)}</span>'
    st.markdown(f'<div class="pais-ind-movil">{chip}</div>' if movil else chip, unsafe_allow_html=True)


def render(ctx):
    tab = ctx.pestanas.tab_mundo
    if not ctx.abierta(tab):
        return
    with tab:
        seccion("Mundo", "Elegí un país: Ligas, Copas, Calendario, Historial y Avisos muestran lo suyo", "#1e5aa8")
        lista = paises.PAISES
        for i in range(0, len(lista), POR_FILA):
            fila = lista[i:i + POR_FILA]
            for col, pais in zip(st.columns(POR_FILA), fila):
                with col:
                    _tarjeta(ctx.S, pais, pais == ctx.pais)
        st.caption("Cada país muestra sus ligas, sus copas (más las internacionales donde pueden jugar sus clubes), su "
                   "calendario, su palmarés y sus avisos. El Modo dios, por ahora, es sólo de Argentina.")

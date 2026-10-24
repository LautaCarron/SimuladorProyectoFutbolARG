"""Cabecera de la página (masthead) de Proyecto AFA: marca, avance de cada categoría y botón de tema."""

import streamlit as st

from config import ES_WEB
from ligas.nacional import total_b
from ligas.primera import total_primera
from motor.calendario import texto_dia

# Sol de Mayo geométrico: 16 rayos alternando largo (mismo dibujo que la intro)
_RAYOS = "".join(
    f'<polygon points="-3.2,-21 0,-{36 if k % 2 else 47} 3.2,-21" transform="rotate({k * 22.5})"/>'
    for k in range(16))
SOL_SVG = (f'<svg viewBox="-50 -50 100 100" aria-hidden="true"><g fill="currentColor">{_RAYOS}'
           f'<circle r="16.5"/></g></svg>')

# En la web el tema claro/oscuro lo maneja la intro (index.html): este botón le avisa.
_BOTON_TEMA = (
    '<a class="mh-tema" href="#tema" title="Cambiar entre modo claro y oscuro" '
    'aria-label="Cambiar entre modo claro y oscuro">'
    '<svg class="sol-ico" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5">'
    '<circle cx="8" cy="8" r="3"/><path d="M8 1v2M8 13v2M1 8h2M13 8h2M3 3l1.4 1.4M11.6 11.6L13 13'
    'M3 13l1.4-1.4M11.6 4.4L13 3"/></svg>'
    '<svg class="luna" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5">'
    '<path d="M13.5 9.8A6 6 0 0 1 6.2 2.5a6 6 0 1 0 7.3 7.3z"/></svg></a>')


def _celda(nombre, fecha, total, pct):
    return (f'<div class="mh-c"><span>{nombre}</span><b>{fecha}/{total}</b>'
            f'<div class="bar"><i style="width:{pct:.1f}%"></i></div></div>')


def _celdas_de_avance(S, progreso):
    SB, SF, SFB, SPB, SPC, SR, SC = S["b"], S["f"], S.get("fb"), S["pb"], S["pc"], S["reg"], S["copa"]
    celdas = [_celda("Primera", S["fecha"], total_primera(S), progreso.pct_p),
              _celda("B Nacional", SB["fecha"], total_b(SB), progreso.pct_b),
              _celda("Federal A", SF["fecha"], SF["total"], progreso.pct_f)]
    if SFB:
        celdas.append(_celda("Federal B", SFB["fecha"], SFB["total"], progreso.pct_fb))
    celdas += [_celda("Primera B", SPB["fecha"], SPB["total"], progreso.pct_pb),
               _celda("Primera C", SPC["fecha"], SPC["total"], progreso.pct_pc),
               _celda("Regional", SR["fecha"], SR["total"], progreso.pct_reg),
               _celda("Copa Arg.", SC["ronda"], SC["total"], progreso.pct_copa)]
    return "".join(celdas)


def render_cabecera(S, progreso, hoy):
    """`hoy`: próximo día con partidos del calendario (None si no queda nada)."""
    # En la web (stlite) la marca vuelve a la intro de Proyecto AFA; en la PC no hay intro
    etiqueta = "a" if ES_WEB else "div"
    atributos = ' href="#inicio" title="Volver al inicio de Proyecto AFA"' if ES_WEB else ""
    proximo = texto_dia(hoy, False) if hoy else "—"
    st.markdown(
        f'<header class="masthead"><{etiqueta} class="mh-marca"{atributos}>{SOL_SVG}<div><b>Proyecto AFA</b>'
        f'<span>Simulador Fútbol Argentino</span></div></{etiqueta}>'
        f'<div class="mh-der"><div class="mh-tabla">'
        f'<div class="mh-c temp"><span>Temporada</span><b>{S["temp"]}</b></div>'
        f'{_celdas_de_avance(S, progreso)}'
        f'<div class="mh-c"><span>Partidos</span><b>{progreso.partidos_jugados}</b></div>'
        f'<div class="mh-c"><span>Próximo día</span><b>{proximo}</b></div></div>'
        f'{_BOTON_TEMA if ES_WEB else ""}</div></header>', unsafe_allow_html=True)

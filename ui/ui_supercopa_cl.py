"""Pestaña Copas · Supercopa de Chile (sólo cuando el país activo es Chile).

Final Four a partido único en cancha neutral: el 1° y el 2° de la Liga de Primera contra el campeón y el subcampeón de la Copa
Chile (semifinales y final). Todo sale de `copas.registro.SupercopaChile`.

La pestaña tiene una cabecera con el logo y los pasos del torneo y el cuadro (semifinales → final → campeón). El palmarés
histórico está en la pestaña Historial.
"""

import streamlit as st

from copas.registro import REGISTRO, SupercopaChile
from datos.logos import logo_img
from ui.vista import aviso, crest, esc

COPA = next(c for c in REGISTRO if isinstance(c, SupercopaChile))

# Lo que dice cada lugar del cuadro mientras todavía no se sabe quién lo ocupa (se conoce al terminar la liga y la copa)
_LUGARES = [("1° de la Liga de Primera", "Subcampeón de la Copa Chile"),
            ("2° de la Liga de Primera", "Campeón de la Copa Chile")]


def _equipo(nombre, detalle="", gol=None, estado=""):
    """Una fila del cuadro: escudo, club, de dónde viene y (si ya se jugó) el resultado.
    nombre=None es un lugar sin definir (se muestra el detalle como texto tenue)."""
    if nombre is None:
        return (f'<div class="scl-t tbd"><span class="scl-ph"></span>'
                f'<span class="scl-tn">{esc(detalle)}</span></div>')
    sub = f"<small>{esc(detalle)}</small>" if detalle else ""
    g = f'<b class="scl-g">{gol}</b>' if gol is not None else ""
    return (f'<div class="scl-t {estado}">{crest(nombre, 28)}'
            f'<span class="scl-tn" role="button" tabindex="0" data-club="{esc(nombre)}">{esc(nombre)}{sub}</span>{g}</div>')


def _partido(a, b, p=None, final=False):
    """Tarjeta de un cruce. a y b son (club o None, detalle); p es el partido jugado (o None si falta jugarlo)."""
    if p:
        ga, gb = (p["gl"], p["gv"]) if p["local"] == a[0] else (p["gv"], p["gl"])
        ea, eb = ("win", "lose") if p["gana"] == a[0] else ("lose", "win")
        filas = _equipo(a[0], a[1], ga, ea) + _equipo(b[0], b[1], gb, eb)
        if p.get("pen"):
            pa, pb = p["pen"] if p["local"] == a[0] else p["pen"][::-1]
            filas += f'<div class="scl-pen">Penales {pa} – {pb}</div>'
    else:
        filas = _equipo(*a) + _equipo(*b)
    return f'<div class="scl-m{" fin" if final else ""}">{filas}</div>'


def _cuadro(E, q, temp):
    """Cuadro completo: dos semifinales, la final y el campeón. Funciona aun sin clasificados (muestra los lugares)."""
    semis_jug = [p for p in E["log"] if p["comp"] == "Semifinales"]
    final_jug = next((p for p in E["log"] if p["comp"] == "Final"), None)
    if q:                                              # (1° liga vs. sub copa) y (2° liga vs. campeón copa)
        cruces = [(q[0], q[3]), (q[1], q[2])]
    else:
        cruces = [((None, a), (None, b)) for a, b in _LUGARES]
    semis = "".join(_partido(a, b, semis_jug[i] if i < len(semis_jug) else None) for i, (a, b) in enumerate(cruces))

    fin = E["finalistas"]
    if fin:
        final = _partido((fin[0], "Ganó la semifinal"), (fin[1], "Ganó la semifinal"), final_jug, final=True)
    else:
        final = _partido((None, "Ganador de la semifinal 1"), (None, "Ganador de la semifinal 2"), final=True)

    if E["campeon"]:
        copa = (f'<div class="scl-cup on"><div class="t">Campeón · Temporada {temp}</div>{logo_img(COPA.nombre, 40)}'
                f'{crest(E["campeon"], 64)}<div class="nm">{esc(E["campeon"])}</div>'
                f'<div class="s">Finalista: {esc(E["subcampeon"])}</div></div>')
    else:
        copa = (f'<div class="scl-cup"><div class="vac">{logo_img(COPA.nombre, 64)}</div>'
                f'<div class="s">Por definir</div></div>')
    return (f'<div class="scl-br">'
            f'<div class="scl-col"><div class="scl-h">Semifinales</div><div class="scl-b">{semis}</div></div>'
            f'<div class="scl-col"><div class="scl-h">Final</div><div class="scl-b">{final}</div></div>'
            f'<div class="scl-col"><div class="scl-h">Campeón</div><div class="scl-b">{copa}</div></div>'
            f'</div>')


def _cabecera(S, E, q):
    """Logo, nombre y los tres pasos del torneo (el que toca jugar queda resaltado)."""
    hechas = E["fecha"]
    pasos = [("1 · Semifinales", hechas >= 1, hechas == 0 and bool(q)),
             ("2 · Final", hechas >= 2, hechas == 1),
             ("3 · Campeón", bool(E["campeon"]), False)]
    html_pasos = "".join(f'<span class="scl-st{" ok" if ok else " now" if ahora else ""}">{"✓ " if ok else ""}{esc(n)}</span>'
                         for n, ok, ahora in pasos)
    return (f'<div class="scl-hero"><div class="scl-logo">{logo_img(COPA.nombre, 84)}</div>'
            f'<div class="scl-ttl"><div class="scl-k">Chile · Temporada {S["temp"]}</div>'
            f'<div class="scl-n">{esc(COPA.nombre)}</div>'
            f'<div class="scl-s">Final Four · partido único · cancha neutral</div>'
            f'<div class="scl-steps">{html_pasos}</div></div></div>')


def render(ctx):
    S, P = ctx.S, ctx.P
    tab = ctx.pestanas.tab_scl
    if not ctx.abierta(ctx.pestanas.tab_copas, tab):
        return
    E = COPA.estado(S)
    q = COPA.clasificados(S)
    pend = COPA.pendiente(S)
    with tab:
        st.markdown(_cabecera(S, E, q), unsafe_allow_html=True)

        if not ctx.modo_mgr:
            rotulo = "Jugar las semifinales" if E["fecha"] == 0 else "Jugar la final"
            _, c2 = st.columns([4, 1.8], vertical_alignment="center")
            if c2.button(f":material/sports_soccer: {rotulo}", key="scl_jugar", width="stretch", type="primary",
                         disabled=pend is None):
                COPA.jugar(S, P, S["rng"])
                st.rerun()

        if not q:
            aviso("Se juega cuando terminan la Liga de Primera y la Copa Chile: el 1° y el 2° de la liga contra el campeón y el "
                  "subcampeón de la copa (el 1° de la liga contra el subcampeón de la copa y el 2° contra el campeón).")
        st.markdown(_cuadro(E, q, S["temp"]), unsafe_allow_html=True)

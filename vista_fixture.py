"""Pantalla de fixture y resultados de cada liga.
"""

import streamlit as st

from calendario import dia_de, texto_dia
from torneos import rotulo_b, rotulo_f, rotulo_p, rotulo_reg
from vista_base import _estado, chip, esc, norm, seccion
from vista_ficha import ver_equipo
from vista_partidos import (
    fechas_conocidas_b,
    fechas_conocidas_f,
    fechas_conocidas_p,
    fechas_conocidas_pb,
    fechas_conocidas_pc,
    fechas_conocidas_pd,
    fechas_conocidas_reg,
    marcador_html,
    partidos_fecha_b,
    partidos_fecha_f,
    partidos_fecha_p,
    partidos_fecha_pb,
    partidos_fecha_pc,
    partidos_fecha_pd,
    partidos_fecha_reg,
    tanda_html,
)


# ---- Fixture y resultados ---------------------------------------------------
def render_fecha(partidos, clave):
    """Partidos de una fecha en dos columnas; cada club se puede tocar para ver su ficha."""
    grupos = []
    for p in partidos:
        if not grupos or grupos[-1][0] != p["comp"]:
            grupos.append((p["comp"], []))
        grupos[-1][1].append(p)
    for g, (comp, lista) in enumerate(grupos):
        if len(grupos) > 1 or comp not in ("Fase 1",):
            st.markdown(chip(comp) + (' <span style="opacity:.6;font-size:.75rem">cancha neutral'
                                      '</span>' if lista[0]["neutral"] else ""),
                        unsafe_allow_html=True)
        mitad = (len(lista) + 1) // 2
        cols = st.columns(2, gap="medium") if len(lista) > 1 else [st.container()]
        for lado, (c, sub) in enumerate(zip(cols, (lista[:mitad], lista[mitad:]))):
            with c, st.container(key=f"fx_{clave}_{g}_{lado}"):
                for i, p in enumerate(sub):
                    k = f"{clave}_{g}_{p['local']}_{p['visita']}"
                    c1, c2, c3 = st.columns([5, 3.6, 5], vertical_alignment="center", gap="small")
                    if c1.button(p["local"], key=f"{k}_l", help="Ver la ficha del club",
                                 width="stretch"):
                        ver_equipo(p["local"])
                    c2.markdown(marcador_html(p, crests=True), unsafe_allow_html=True)
                    if c3.button(p["visita"], key=f"{k}_v", help="Ver la ficha del club",
                                 width="stretch"):
                        ver_equipo(p["visita"])
                    if p["tanda"]:
                        st.markdown(tanda_html(p), unsafe_allow_html=True)


def _mover_fecha(key, delta, maximo):
    st.session_state[key] = min(max(1, st.session_state.get(key, 1) + delta), maximo)


def vista_fixture(liga, region=None):
    S, SB, SF, SPB, SPC = _estado()
    
    if liga == "p":
        # Lo separamos en dos líneas para que sea más claro
        total, jugadas, obtener = fechas_conocidas_p(), S["fecha"], partidos_fecha_p
        rotulo = lambda n: rotulo_p(S, n)
        extra = "" if S["fase"] == 2 else " · las 9 fechas de la fase 2 se arman al terminar la fase 1"
    elif liga == "b":
        total, jugadas, obtener = fechas_conocidas_b(), SB["fecha"], partidos_fecha_b
        rotulo = lambda n: rotulo_b(SB, n)
        extra = ("" if SB["fechas2"] is not None else
                 " · la fase 2 se arma al terminar la fase 1")
    elif liga == "pb":
        total, jugadas = fechas_conocidas_pb(), SPB["fecha"]
        obtener, rotulo = partidos_fecha_pb, lambda n: f"Fecha {n}"
        extra = ""
    elif liga == "pc":
        total, jugadas = fechas_conocidas_pc(), SPC["fecha"]
        obtener, rotulo = partidos_fecha_pc, lambda n: f"Fecha {n}"
        extra = ""
    elif liga == "pd":
        SPD = st.session_state.S["pd"]
        total, jugadas = fechas_conocidas_pd(), SPD["fecha"]
        obtener, rotulo = partidos_fecha_pd, lambda n: f"Fecha {n}"
        extra = ""
    elif liga == "reg":
        SREG = st.session_state.S["reg"]
        total, jugadas = fechas_conocidas_reg(), SREG["fecha"]
        obtener, rotulo = (lambda n: partidos_fecha_reg(n, region)), (lambda n: rotulo_reg(SREG, n))
        extra = (f" · {region}" if region else "") + " · desempates y finales se arman al terminar la liga"
    else:
        total, jugadas = fechas_conocidas_f(), SF["fecha"]
        obtener, rotulo = partidos_fecha_f, lambda n: rotulo_f(SF, n)
        extra = ("" if SF["zonas2"] is not None else
                 " · la fase 2 se arma al terminar la fase 1")
    seccion("Fixture y resultados", "Tocá un club para ver su ficha" + extra, "#1e5aa8")
    if total == 0:
        st.info("Todavía no hay fechas programadas.")
        return
    key = f"fx_sel_{liga}_{S['temp']}_{jugadas}" + (f"_{norm(region)}" if region else "")
    if key not in st.session_state:
        st.session_state[key] = max(1, min(jugadas, total))
    c1, c2, c3 = st.columns([1, 6, 1], vertical_alignment="bottom")
    c1.button(":material/chevron_left:", key=f"{key}_prev", width="stretch", on_click=_mover_fecha,
              args=(key, -1, total), disabled=st.session_state[key] <= 1)
    elegida = c2.selectbox("Fecha", list(range(1, total + 1)), key=key, format_func=lambda n:
                           rotulo(n) + (" · jugada" if n <= jugadas else " · por jugar"),
                           label_visibility="collapsed")
    c3.button(":material/chevron_right:", key=f"{key}_next", width="stretch", on_click=_mover_fecha,
              args=(key, 1, total), disabled=elegida >= total)
    estado = chip("Jugada", "#16a34a") if elegida <= jugadas else (
        chip("Próxima fecha", "#2f7fd0") if elegida == jugadas + 1 else chip("Por jugar", "#64748b"))
    liga_cal = {"p": "Primera División", "b": "Primera Nacional", "f": "Federal A", "pb": "Primera B",
                "pc": "Primera C", "reg": "Regional Amateur"}.get(liga)
    dia = dia_de(S, liga_cal, elegida) if liga_cal else None
    st.markdown(f'<div class="fx-head"><b style="font-size:1.05rem">{esc(rotulo(elegida))}</b>'
                f'{estado}<span class="m-dia">{esc(texto_dia(dia)) if dia else ""}</span></div>',
                unsafe_allow_html=True)
    partidos = obtener(elegida)
    if not partidos:
        st.info("No hay partidos de esta región en esta fecha." if region else
                "Los partidos de esta fecha se conocen cuando termina la liga.")
        return
    render_fecha(partidos, f"{liga}{S['temp']}_{elegida}" + (f"_{norm(region)}" if region else ""))

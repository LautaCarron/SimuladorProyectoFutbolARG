"""Pantalla de fixture y resultados de cada liga.
"""

from contextlib import nullcontext

import streamlit as st

from motor.calendario import dia_de, texto_dia
from ligas.federal import rotulo_f
from ligas.nacional import es_anual_b, rotulo_b
from ligas.primera import fechas_f2
from ligas.primera import formato, rotulo_p
from ligas.regional import rotulo_reg
from ui.vista.base import chip, esc, norm, seccion
from motor import consultas
from ui.vista.partidos import marcador_html, tanda_html
from ui.vista.ficha import ver_equipo


# ---- Fixture y resultados ---------------------------------------------------
def render_fecha(S, club, partidos, clave):
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
                    es_mio = bool(club) and club in (p["local"], p["visita"])
                    # el partido de mi club va en un contenedor con key mi_partido_* (ver estilo_mi_club)
                    with (st.container(key=f"mi_partido_{clave}_{g}_{lado}_{i}") if es_mio else nullcontext()):
                        c1, c2, c3 = st.columns([5, 3.6, 5], vertical_alignment="center", gap="small")
                        if c1.button(p["local"], key=f"{k}_l", help="Ver la ficha del club",
                                     width="stretch"):
                            ver_equipo(S, club, p["local"])
                        c2.markdown(marcador_html(p, crests=True), unsafe_allow_html=True)
                        if c3.button(p["visita"], key=f"{k}_v", help="Ver la ficha del club",
                                     width="stretch"):
                            ver_equipo(S, club, p["visita"])
                        if p["tanda"]:
                            st.markdown(tanda_html(p), unsafe_allow_html=True)


def _mover_fecha(key, delta, maximo):
    st.session_state[key] = min(max(1, st.session_state.get(key, 1) + delta), maximo)


def vista_fixture(S, club, liga, region=None):
    SB, SF = S["b"], S["f"]
    if liga == "p":
        # Lo separamos en dos líneas para que sea más claro
        total, jugadas, obtener = consultas.fechas_conocidas_p(S), S["fecha"], lambda n: consultas.partidos_fecha_p(S, n)
        rotulo = lambda n: rotulo_p(S, n)
        f_p = formato(S)
        extra = (" · las llaves se arman al terminar la etapa regular de cada torneo" if f_p == "apertura_clausura"
                 else "" if (f_p != "actual" or S["fase"] == 2)
                 else f" · las {fechas_f2(S)} fechas de la fase 2 se arman al terminar la fase 1")
    elif liga == "b":
        total, jugadas, obtener = consultas.fechas_conocidas_b(S), SB["fecha"], lambda n: consultas.partidos_fecha_b(S, n)
        rotulo = lambda n: rotulo_b(SB, n)
        extra = ("" if (es_anual_b(SB) or SB["fechas2"] is not None) else
                 " · la fase 2 se arma al terminar la fase 1")
    elif liga == "pb":
        total, jugadas = consultas.fechas_conocidas_simple(S["pb"]), S["pb"]["fecha"]
        obtener, rotulo = lambda n: consultas.partidos_fecha_pb(S, n), lambda n: f"Fecha {n}"
        extra = ""
    elif liga == "pc":
        total, jugadas = consultas.fechas_conocidas_simple(S["pc"]), S["pc"]["fecha"]
        obtener, rotulo = lambda n: consultas.partidos_fecha_pc(S, n), lambda n: f"Fecha {n}"
        extra = ""
    elif liga == "pd":
        total, jugadas = consultas.fechas_conocidas_simple(S["pd"]), S["pd"]["fecha"]
        obtener, rotulo = lambda n: consultas.partidos_fecha_pd(S, n), lambda n: f"Fecha {n}"
        extra = ""
    elif liga == "fb":
        SFB = S["fb"]
        total, jugadas = consultas.fechas_conocidas_f(SFB), SFB["fecha"]
        obtener, rotulo = lambda n: consultas.partidos_fecha_f(SFB, n), lambda n: rotulo_f(SFB, n)
        extra = ("" if SFB["zonas2"] is not None else
                 " · la fase 2 se arma al terminar la fase 1")
    elif liga == "reg":
        SREG = S["reg"]
        total, jugadas = consultas.fechas_conocidas_reg(S), SREG["fecha"]
        obtener, rotulo = (lambda n: consultas.partidos_fecha_reg(S, n, region)), (lambda n: rotulo_reg(SREG, n))
        extra = (f" · {region}" if region else "") + " · desempates y finales se arman al terminar la liga"
    else:
        total, jugadas = consultas.fechas_conocidas_f(SF), SF["fecha"]
        obtener, rotulo = lambda n: consultas.partidos_fecha_f(SF, n), lambda n: rotulo_f(SF, n)
        extra = ("" if SF["zonas2"] is not None else
                 " · la fase 2 se arma al terminar la fase 1")
    seccion("Fixture y resultados", color="#1e5aa8")
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
    liga_cal = {"p": "Primera División", "b": "Primera Nacional", "f": "Federal A", "fb": "Federal B",
                "pb": "Primera B", "pc": "Primera C", "reg": "Regional Amateur"}.get(liga)
    dia = dia_de(S, liga_cal, elegida) if liga_cal else None
    st.markdown(f'<div class="fx-head"><b style="font-size:1.05rem">{esc(rotulo(elegida))}</b>'
                f'{estado}<span class="m-dia">{esc(texto_dia(dia)) if dia else ""}</span></div>',
                unsafe_allow_html=True)
    partidos = obtener(elegida)
    if not partidos:
        st.info("No hay partidos de esta región en esta fecha." if region else
                "Los partidos de esta fecha se conocen cuando termina la liga.")
        return
    render_fecha(S, club, partidos, f"{liga}{S['temp']}_{elegida}" + (f"_{norm(region)}" if region else ""))

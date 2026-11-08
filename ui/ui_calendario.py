"""Pestaña Calendario.

El código es el de simuladorafa.py, movido acá tal cual. `ctx` trae el estado y los ayudantes
compartidos de la interfaz (S, P, las pestañas, las banderas terminada_*, etc.).
Modo manager: si dirigís un club, el calendario se ve en grilla mensual con SUS partidos (escudo del
rival, competencia y resultado). Con "Todos los equipos" se vuelve a la lista de siempre.
Tocando un día (desde el próximo en adelante) el botón pasa a "Simular hasta esa fecha".
Muestra las competencias del país activo (se elige en Mundo) más las copas internacionales; el botón de arriba
sigue jugando el próximo día de todo el simulador. Con un club dirigido (Argentina), "Mis partidos" muestra todo lo suyo.
"""

import datetime as dt

import streamlit as st
from motor.calendario import anio, jugar_proximo_dia, nombre_mes, proximos, texto_dia
from datos import paises
from datos.logos import logo_img
from ui.vista import calendario_mes_html, esc, eventos_calendario, seccion
from ui.vista.vista_calendario import calendario_grilla_html

VISTA_MIS, VISTA_TODOS = "Mis partidos", "Todos los equipos"


def _mover_mes(clave, meses, paso):
    i = meses.index(st.session_state[clave]) + paso
    st.session_state[clave] = meses[min(max(i, 0), len(meses) - 1)]


def _cb_simular(S, M, P, acumular, hasta):
    """Sin día elegido juega el próximo día; con día elegido juega todos los días hasta esa fecha (inclusive).
    En modo manager, si aparece un evento se frena ahí (hay que resolverlo antes de seguir)."""
    if M:
        from motor.manager import sincronizar_manager
    interrumpido = False
    for _ in range(1 if hasta is None else 400):          # tope de seguridad: más que una temporada
        prox = proximos(S)
        if not prox or (hasta is not None and min(d for d, _ in prox.values()) > hasta):
            break
        jugar_proximo_dia(S, P, acumular)
        if M:
            for texto in sincronizar_manager(S, M):         # ofertas, ascensos, avisos de los días que pasan
                st.toast(texto)
            if M.get("evento"):
                interrumpido = True
                break
    if not interrumpido:
        st.session_state.pop("cal_dia_sel", None)         # si lo interrumpió un evento, el día elegido sigue


def render(ctx):
    (P, S, _abierta, _hoy, _prox, acumular, tab_cal) = (
        ctx.P, ctx.S, ctx.abierta, ctx.hoy, ctx.prox, ctx.acumular, ctx.pestanas.tab_cal)
    # ============================================================================
    # CALENDARIO
    # ============================================================================
    if _abierta(tab_cal):
        with tab_cal:
            seccion(f"Calendario {anio(S)}", color="#1e5aa8")
            # día elegido tocándolo en el calendario (llega por el puente). Tocar el mismo día lo desmarca.
            iso = st.session_state.pop("_dia_a_elegir", "")
            if iso:
                try:
                    tocado = dt.date.fromisoformat(iso)
                except ValueError:
                    tocado = None
                if tocado and _hoy and tocado >= _hoy:
                    st.session_state["cal_dia_sel"] = None if st.session_state.get("cal_dia_sel") == tocado else tocado
            sel = st.session_state.get("cal_dia_sel")
            if sel and (_hoy is None or sel < _hoy):          # ese día ya pasó (o terminó la temporada)
                sel = None
                st.session_state.pop("cal_dia_sel", None)

            propias = paises.competencias_de(ctx.pais) | set(paises.COPAS_INTERNACIONALES)   # del país activo + internacionales
            prox_pais = {c: dn for c, dn in _prox.items() if c in propias}
            hoy_pais = min((d for d, _ in prox_pais.values()), default=None)
            c1, c2 = st.columns([3, 1.4], vertical_alignment="center")
            if hoy_pais:
                texto_prox = (f'Próximo día de {esc(ctx.pais)}: <b>{esc(texto_dia(hoy_pais))}</b> · ' + " ".join(
                    logo_img(c, 18) for c, (d, _) in prox_pais.items() if d == hoy_pais))
            elif _hoy:
                texto_prox = f'No quedan partidos de {esc(ctx.pais)} esta temporada.'
            else:
                texto_prox = "Terminó la temporada: pasá a la siguiente desde <b>Nueva temporada</b>."
            if _hoy and _hoy != hoy_pais:           # el botón juega el próximo día de todo el simulador
                texto_prox += (f'<br><span style="opacity:.65">El simulador juega primero el {esc(texto_dia(_hoy))} '
                               f'(de otro país).</span>')
            if sel:
                texto_prox += (f'<br>Elegiste: <b>{esc(texto_dia(sel))}</b> · tocá el día de nuevo para quitarlo')
            elif _hoy:
                texto_prox += '<br><span style="opacity:.65">Tocá un día para simular hasta esa fecha</span>'
            c1.markdown(texto_prox, unsafe_allow_html=True)
            c2.button(":material/fast_forward: Simular hasta esa fecha" if sel
                      else ":material/calendar_today: Jugar ese día", key="cal_next", width="stretch",
                      type="primary", disabled=_hoy is None, on_click=_cb_simular, args=(S, ctx.manager, P, acumular, sel))
            club = ctx.club if ctx.es_base else None    # modo manager: club que dirigís (sólo existe en Argentina)
            vista = VISTA_TODOS
            if club:
                vista = st.segmented_control("Vista", [VISTA_MIS, VISTA_TODOS], default=VISTA_MIS,
                                             key="cal_vista", label_visibility="collapsed") or VISTA_MIS
            eventos = eventos_calendario(S)
            if not (club and vista == VISTA_MIS):       # "Mis partidos" muestra todo lo de mi club
                eventos = [e for e in eventos if e[1] in propias]
            meses = sorted({d.month for d, *_ in eventos})
            pendientes = [d for d, _, _, jugada in eventos if not jugada]
            mes_def = (min(pendientes) if pendientes else eventos[-1][0]).month    # el mes del próximo partido del país

            if club and vista == VISTA_MIS:
                # ---- grilla mensual con los partidos de mi club, con flechas para cambiar de mes
                kg = f"cal_grilla_{S['temp']}"
                if st.session_state.get(f"{kg}_sigue") != mes_def or kg not in st.session_state:
                    st.session_state[kg] = mes_def if mes_def in meses else meses[0]
                    st.session_state[f"{kg}_sigue"] = mes_def           # el mes sigue al próximo día
                n1, n2, n3 = st.columns([1, 4, 1], vertical_alignment="center")
                n1.button(":material/chevron_left:", key="cal_mes_prev", width="stretch", on_click=_mover_mes,
                          args=(kg, meses, -1), disabled=st.session_state[kg] == meses[0])
                n3.button(":material/chevron_right:", key="cal_mes_next", width="stretch", on_click=_mover_mes,
                          args=(kg, meses, 1), disabled=st.session_state[kg] == meses[-1])
                mes = st.session_state[kg]
                n2.markdown(f'<div style="text-align:center;font-weight:700;font-size:1.15rem">'
                            f'{esc(nombre_mes(mes))} {anio(S)}</div>', unsafe_allow_html=True)
                st.markdown(calendario_grilla_html(S, eventos, mes, _hoy, club, seleccion=sel), unsafe_allow_html=True)
                st.caption(f"Partidos de {club}. Borde verde / gris / rojo: ganó / empató / perdió · "
                           "fondo violeta: copas · gris azulado: días que ya pasaron · contorno violeta: próximo día. "
                           "Tocá un día futuro para elegirlo y simular hasta esa fecha. Pasá el mouse "
                           "un partido para ver el detalle. Los cruces de copa aparecen cuando se conocen.")
            else:
                clave_mes = f"cal_mes_{S['temp']}"
                # el mes elegido sigue al próximo día (cuando avanza el calendario, se mueve solo)
                if st.session_state.get(f"{clave_mes}_sigue") != mes_def or clave_mes not in st.session_state:
                    st.session_state[clave_mes] = mes_def if mes_def in meses else meses[0]
                    st.session_state[f"{clave_mes}_sigue"] = mes_def
                mes = st.segmented_control("Mes", meses, format_func=lambda m: nombre_mes(m)[:3], key=clave_mes,
                                           label_visibility="collapsed") or mes_def
                st.markdown(calendario_mes_html(S, ctx.club, eventos, mes, _hoy, seleccion=sel), unsafe_allow_html=True)
                st.caption("Tocá cada competición para ver sus partidos. ⚠ = partido con incidente (ver Avisos)."
                           + (" Los partidos de tu club van en amarillo." if club else ""))

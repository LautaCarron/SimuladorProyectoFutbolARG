"""Pestaña Historial.

El código es el de simuladorafa.py, movido acá tal cual. `ctx` trae el estado y los ayudantes
compartidos de la interfaz (S, P, las pestañas, las banderas terminada_*, etc.).
"""

import pandas as pd
import streamlit as st
from datos.equipos import region_regional
from datos.logos import logo_img
from datos.regional import REGIONES_REG
from ui.vista import aviso, crest, esc, lista_equipos_html, seccion, tabla_html


def render(ctx):
    (S, _abierta, tab_h) = (
        ctx.S, ctx._abierta, ctx.tab_h)
    # ============================================================================
    # HISTORIAL
    # ============================================================================

    def tabla_ranking_html(titulo, logo, actual, base):
        """Tarjeta de palmarés de una liga o copa: posición, escudo, club y títulos. Los ganados
        en las temporadas simuladas se marcan aparte (+n)."""
        lista = sorted(((n, t) for n, t in actual.items() if t > 0), key=lambda x: (-x[1], x[0]))
        total = sum(t for _, t in lista)
        filas, pos, previo = "", 0, None
        for k, (n, t) in enumerate(lista):
            if t != previo:
                pos, previo = k + 1, t
            extra = t - base.get(n, 0)
            clase = " oro" if pos == 1 else ""
            filas += (f'<div class="pal-f{clase}"><span class="pal-pos">{pos}</span>{crest(n, 22)}'
                      f'<span class="pal-nm" role="button" tabindex="0" data-club="{esc(n)}" title="{esc(n)}">{esc(n)}</span>'
                      + (f'<span class="pal-mas" title="Ganados en las temporadas simuladas">+{extra}</span>' if extra > 0 else "")
                      + f'<b class="pal-t">{t}</b></div>')
        if not filas:
            filas = '<div class="pal-vacio">Todavía no hay campeones.</div>'
        return (f'<div class="pal"><div class="pal-h">{logo_img(logo, 26)}<span class="pal-tit">{esc(titulo)}</span>'
                f'<span class="pal-tot">{total} títulos</span></div><div class="pal-lista">{filas}</div></div>')


    if _abierta(tab_h):
        with tab_h:
            seccion("Historial", "Campeones de cada temporada y rankings históricos", "#b7860b")

            if S["campeones"]:
                ligas_c = ["Primera División", "Primera Nacional", "Federal A", "Primera B", "Primera C",
                           "Copa Argentina", "Supercopa", "Libertadores", "Sudamericana", "Recopa", "Mundial"]
                with st.expander(":material/emoji_events: Campeones por temporada", expanded=False):
                    df_c = pd.DataFrame([{k: x.get(k) or None for k in ["Temporada"] + ligas_c} for x in S["campeones"]])
                    st.markdown(tabla_html(df_c, clubes=tuple(ligas_c)), unsafe_allow_html=True)
                with st.expander(":material/emoji_events: Campeones del Regional Amateur (por región)", expanded=False):
                    df_r = pd.DataFrame([{"Temporada": x["Temporada"],
                                          **{reg: x.get("Regional", {}).get(reg) or None for reg in REGIONES_REG}}
                                         for x in S["campeones"]])
                    st.markdown(tabla_html(df_r, clubes=tuple(REGIONES_REG)), unsafe_allow_html=True)
            else:
                aviso("Los campeones de cada liga aparecen acá al pasar a la temporada siguiente.")

            # Palmarés histórico: títulos oficiales hasta 2025 (palmares.py) + los de las temporadas simuladas
            from datos.palmares import PALMARES
            st.markdown('<div class="mlab" style="margin-top:20px">Palmarés histórico · ligas</div>', unsafe_allow_html=True)
            st.markdown('<div class="pal-grid">' + "".join(
                tabla_ranking_html(titulo, logo, S.get(clave, {}), PALMARES.get(clave, {}))
                for titulo, logo, clave in (("Primera División", "Primera División", "hist_primera"),
                                            ("Primera Nacional", "Primera Nacional", "hist_nacional"),
                                            ("Federal A", "Federal A", "hist_federal"),
                                            ("Primera B Metropolitana", "Primera B", "hist_pb"),
                                            ("Primera C Metropolitana", "Primera C", "hist_pc"))) + '</div>',
                        unsafe_allow_html=True)
            st.markdown('<div class="mlab" style="margin-top:18px">Palmarés histórico · copas</div>', unsafe_allow_html=True)
            st.markdown('<div class="pal-grid">' + "".join(
                tabla_ranking_html(titulo, logo, S.get(clave, {}), PALMARES.get(clave, {}))
                for titulo, logo, clave in (("Copa Argentina", "Copa Argentina", "hist_copa"),
                                            ("Supercopa Argentina", "Supercopa Argentina", "hist_super"),
                                            ("Mundial de Clubes", "Mundial de Clubes", "hist_mundial"),
                                            ("Copa Libertadores", "Copa Libertadores", "hist_lib"),
                                            ("Copa Sudamericana", "Copa Sudamericana", "hist_sud"),
                                            ("Recopa Sudamericana", "Recopa Sudamericana", "hist_rec"))) + '</div>',
                        unsafe_allow_html=True)
            st.caption("Títulos oficiales hasta 2025 (AFA / CONMEBOL): Primera, era amateur y profesional; "
                       "B Nacional, Primera B Metropolitana y Primera C, desde 1986-87; Federal A, desde 2014. "
                       "En verde (+n), los ganados en las temporadas simuladas. Tocá un club para ver su ficha.")

            if S["movimientos"]:
                mv = S["movimientos"]
                with st.expander(f":material/swap_vert: Cambios de categoría para la temporada {S['temp']}", expanded=False):
                    st.markdown(
                        '<div class="catgrid">'
                        f'<div><div class="mlab up">▲ Ascendieron a Primera</div>'
                        f'{lista_equipos_html([(n, "directo") for n in mv["directos"]] + ([(mv["reducido"], "reducido")] if mv["reducido"] else []))}</div>'
                        f'<div><div class="mlab down">▼ Descendieron a B Nacional</div>'
                        f'{lista_equipos_html([(n, "") for n in mv["bajan_p"]])}</div>'
                
                        f'<div><div class="mlab up">▲ Ascendieron a B Nacional</div>'
                        f'{lista_equipos_html([(n, "del Federal A") for n in mv.get("suben_f_b", [])] + [(n, "de la B Metro") for n in mv.get("suben_pb_b", [])])}</div>'
                        f'<div><div class="mlab down">▼ Descendieron al Federal A</div>'
                        f'{lista_equipos_html([(n, "") for n in mv.get("bajan_b_fed", [])])}</div>'
                
                        f'<div><div class="mlab down">▼ Descendieron a la B Metro</div>'
                        f'{lista_equipos_html([(n, "") for n in mv.get("bajan_b_pb", [])])}</div>'
                        f'<div><div class="mlab up">▲ Ascendieron a la B Metro</div>'
                        f'{lista_equipos_html([(n, "de la C") for n in mv.get("suben_pc_pb", [])])}</div>'
                
                        f'<div><div class="mlab down">▼ Descendieron a Primera C</div>'
                        f'{lista_equipos_html([(n, "") for n in mv.get("bajan_pb_pc", [])])}</div>'
                        f'<div><div class="mlab up">▲ Ascendieron al Federal A</div>'
                        f'{lista_equipos_html([(n, "del Regional") for n in mv.get("suben_reg_fed", [])] + [(n, "reubicación") for n in mv.get("suben_reg_fed_extra", [])])}</div>'
                    
                        f'<div><div class="mlab down">▼ Descendieron al Promocional Amateur</div>'
                        f'{lista_equipos_html([(n, "") for n in mv.get("bajan_pc_pd", [])])}</div>'
                        f'<div><div class="mlab up">▲ Ascendieron a Primera C</div>'
                        f'{lista_equipos_html([(n, "del Promocional") for n in mv.get("suben_pd_pc", [])])}</div>'
                    
                        f'<div><div class="mlab down">▼ Descendieron al Regional</div>'
                        f'{lista_equipos_html([(n, region_regional(n)) for n in mv.get("bajan_fed_reg", [])])}</div>'
                        + (f'<div><div class="mlab down">▼ Descenso administrativo (Tribunal de Disciplina)</div>'
                           f'{lista_equipos_html([(n, "sanción") for n in mv.get("descenso_adm", [])])}</div>'
                           if mv.get("descenso_adm") else "") +
                        f'</div>', unsafe_allow_html=True)

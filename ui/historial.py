"""Pestaña Historial.

El código es el de simuladorafa.py, movido acá tal cual. `ctx` trae el estado y los ayudantes
compartidos de la interfaz (S, P, las pestañas, las banderas terminada_*, etc.).
"""

import pandas as pd
import streamlit as st
from copas.registro import LIGAS_EXTERIOR, REGISTRO
from datos import ligas_ext, paises
from datos.equipos import region_regional
from datos.logos import logo_img
from datos.datos_regional import REGIONES_REG
from ui.vista import aviso, crest, esc, tabla_html, tabla_ranking_html


def _mov_clubes(items):
    return "".join(f'<span class="mv-cl">{crest(n, 20)}<span class="mv-nm" role="button" tabindex="0" '
                   f'data-club="{esc(n)}">{esc(n)}</span>{f"<small>{esc(d)}</small>" if d else ""}</span>'
                   for n, d in items)


def movimientos_html(mv):
    """Cambios de categoría ordenados por liga (de Primera para abajo): quién sube y quién baja de cada una."""
    g = mv.get
    ligas = ([
        ("Primera División", "Primera División", [], [("la B Nacional", [(n, "") for n in g("bajan_p", [])])]),
        ("Primera Nacional", "Primera Nacional",
         [("Primera", [(n, "directo") for n in g("directos", [])]
           + ([(g("reducido"), "reducido")] if g("reducido") else []))],
         [("el Federal A", [(n, "") for n in g("bajan_b_fed", [])]),
          ("la Primera B", [(n, "") for n in g("bajan_b_pb", [])])]),
        ("Federal A", "Federal A",
         [("la B Nacional", [(n, "") for n in g("suben_f_b", [])])],
         [("el Federal B", [(n, "") for n in g("bajan_fed_fb", [])]),
          ("el Regional", [(n, region_regional(n)) for n in g("bajan_fed_reg", [])])])]
        + ([("Federal B", "Federal B", [("el Federal A", [(n, "") for n in g("suben_fb_f", [])])],
             [("el Regional", [(n, region_regional(n)) for n in g("bajan_fb_reg", [])])])] if g("fb_activa") else [])
        + [
        ("Primera B Metropolitana", "Primera B", [("la B Nacional", [(n, "") for n in g("suben_pb_b", [])])],
         [("la Primera C", [(n, "") for n in g("bajan_pb_pc", [])])]),
        ("Primera C", "Primera C", [("la Primera B", [(n, "") for n in g("suben_pc_pb", [])])],
         [("el Promocional", [(n, "") for n in g("bajan_pc_pd", [])])]),
        ("Promocional Amateur", "Promocional Amateur", [("la Primera C", [(n, "") for n in g("suben_pd_pc", [])])], []),
        ("Regional Amateur", "Regional Amateur",
         [("el Federal A", [(n, "final regional") for n in g("suben_reg_fed", [])]
           + [(n, "reubicación") for n in g("suben_reg_fed_extra", [])]),
          ("el Federal B", [(n, "final regional") for n in g("suben_reg_fb", [])]
           + [(n, "reubicación") for n in g("suben_reg_fb_extra", [])])], []),
    ])
    tarjetas = ""
    for titulo, logo, suben, bajan in ligas:
        filas = ""
        for flecha, clase, verbo, grupos in (("▲", "up", "Suben a", suben), ("▼", "down", "Bajan a", bajan)):
            for destino, items in grupos:
                if items:
                    filas += (f'<div class="mv-sec"><div class="mv-lab {clase}">{flecha} {f'{verbo} {destino}'.replace(' a el ', ' al ')}'
                              f'<b>{len(items)}</b></div><div class="mv-lista">{_mov_clubes(items)}</div></div>')
        tarjetas += (f'<div class="mv-card"><div class="mv-h">{logo_img(logo, 22)}<span>{esc(titulo)}</span></div>'
                     + (filas or '<div class="mv-vacio">Sin cambios</div>') + '</div>')
    if g("descenso_adm"):
        tarjetas += ('<div class="mv-card mv-adm"><div class="mv-h"><span>Tribunal de Disciplina</span></div>'
                     '<div class="mv-sec"><div class="mv-lab down">▼ Descenso administrativo'
                     f'<b>{len(g("descenso_adm"))}</b></div><div class="mv-lista">'
                     f'{_mov_clubes([(n, "sanción") for n in g("descenso_adm")])}</div></div></div>')
    if g("ajustes"):
        # Modo dios: los que suben o bajan de más para llegar al tamaño elegido o no dejar una liga sin equipos
        from motor.tamanos import NOMBRES
        corto = {"p": "Primera", "b": "B Nacional", "pb": "Primera B", "pc": "Primera C", "pd": "Promocional",
                 "reg": "Regional"}
        items = [(x["club"], f'{corto.get(x["de"], NOMBRES[x["de"]])} → {corto.get(x["a"], NOMBRES[x["a"]])}')
                 for x in g("ajustes")]
        tarjetas += ('<div class="mv-card"><div class="mv-h"><span>Ajuste automático de tamaño</span></div>'
                     '<div class="mv-sec"><div class="mv-lab">⇅ Cambian de categoría de más'
                     f'<b>{len(items)}</b></div><div class="mv-lista">{_mov_clubes(items)}</div></div></div>')
    return f'<div class="mv-grid">{tarjetas}</div>'


def render(ctx):
    (S, _abierta, tab_h) = (
        ctx.S, ctx.abierta, ctx.pestanas.tab_h)
    # ============================================================================
    # HISTORIAL
    # ============================================================================

    if _abierta(tab_h):
        with tab_h:
            es_base, pais = ctx.es_base, ctx.pais
            ligas_pais = [c for c in LIGAS_EXTERIOR if c.cfg["pais"] == pais]          # ligas simuladas de otro país

            if S["campeones"]:
                if es_base:
                    ligas_c = ["Primera División", "Primera Nacional", "Federal A"]
                    if any("Federal B" in x for x in S["campeones"]) or S.get("fb") is not None:
                        ligas_c.append("Federal B")                  # la columna aparece recién cuando existe el Federal B
                    ligas_c += ["Primera B", "Primera C", "Promocional Amateur", "Copa Argentina", "Supercopa"]
                else:
                    ligas_c = [col for c in ligas_pais for col in [c.col_historial] + [f"{c.col_historial} · {t}" for t in c.torneos]
                              ] + paises.copas_nacionales_de(pais)
                ligas_c += ["Libertadores", "Sudamericana", "Recopa", "Mundial"]      # internacionales: van en todos los países
                with st.expander(":material/emoji_events: Campeones por temporada", expanded=False):
                    df_c = pd.DataFrame([{k: x.get(k) or None for k in ["Temporada"] + ligas_c} for x in S["campeones"]])
                    nombres_col = {c.col_historial: c.nombre for c in ligas_pais}      # "Uruguay" -> "Liga AUF Uruguaya"
                    nombres_col.update({f"{c.col_historial} · {t}": f"{c.nombre} · {t}" for c in ligas_pais for t in c.torneos})
                    st.markdown(tabla_html(df_c.rename(columns=nombres_col),
                                           clubes=tuple(nombres_col.get(c, c) for c in ligas_c)), unsafe_allow_html=True)
                if es_base:
                    with st.expander(":material/emoji_events: Campeones del Regional Amateur (por región)", expanded=False):
                        df_r = pd.DataFrame([{"Temporada": x["Temporada"],
                                              **{reg: x.get("Regional", {}).get(reg) or None for reg in REGIONES_REG}}
                                             for x in S["campeones"]])
                        st.markdown(tabla_html(df_r, clubes=tuple(REGIONES_REG)), unsafe_allow_html=True)
            else:
                aviso("Los campeones de cada liga aparecen acá al pasar a la temporada siguiente.")

            # Palmarés histórico: títulos oficiales hasta 2025 (palmares.py) + los de las temporadas simuladas
            from datos.palmares import PALMARES
            if es_base:
                st.markdown('<div class="mlab" style="margin-top:20px">Palmarés histórico · ligas</div>', unsafe_allow_html=True)
                _ligas_pal = [("Primera División", "Primera División", "hist_primera"),
                              ("Primera Nacional", "Primera Nacional", "hist_nacional"),
                              ("Federal A", "Federal A", "hist_federal")]
                if S.get("fb") is not None:                      # palmarés oculto hasta que se crea el Federal B
                    _ligas_pal.append(("Federal B", "Federal B", "hist_federalB"))
                st.markdown('<div class="pal-grid">' + "".join(
                    tabla_ranking_html(titulo, logo, S.get(clave, {}), PALMARES.get(clave, {}))
                    for titulo, logo, clave in (*_ligas_pal,
                                                ("Primera B Metropolitana", "Primera B", "hist_pb"),
                                                ("Primera C Metropolitana", "Primera C", "hist_pc"),
                                                ("Promocional Amateur (Ex Primera D)", "Promocional Amateur", "hist_pd"))) + '</div>',
                            unsafe_allow_html=True)
            elif ligas_pais:                                 # palmarés histórico + títulos de las temporadas simuladas
                st.markdown('<div class="mlab" style="margin-top:20px">Palmarés · ligas</div>', unsafe_allow_html=True)
                st.markdown('<div class="pal-grid">' + "".join(
                    tabla_ranking_html(c.nombre, c.nombre, S.get(c.hist, {}), PALMARES.get(c.hist, {})) for c in ligas_pais) + '</div>',
                    unsafe_allow_html=True)
            copas_ext = [c for c in REGISTRO if not es_base and c.hist and c.nombre in paises.copas_nacionales_de(pais)]
            if copas_ext:                                    # palmarés histórico + títulos de las temporadas simuladas
                st.markdown('<div class="mlab" style="margin-top:18px">Palmarés · copas nacionales</div>',
                            unsafe_allow_html=True)
                st.markdown('<div class="pal-grid">' + "".join(
                    tabla_ranking_html(c.nombre, c.nombre, S.get(c.hist, {}), PALMARES.get(c.hist, {})) for c in copas_ext) + '</div>',
                    unsafe_allow_html=True)
            if es_base:                                      # copas del país
                st.markdown('<div class="mlab" style="margin-top:18px">Palmarés histórico · copas nacionales</div>',
                            unsafe_allow_html=True)
                st.markdown('<div class="pal-grid">' + "".join(
                    tabla_ranking_html(titulo, logo, S.get(clave, {}), PALMARES.get(clave, {}))
                    for titulo, logo, clave in (("Copa Argentina", "Copa Argentina", "hist_copa"),
                                                ("Supercopa Argentina", "Supercopa Argentina", "hist_super"))) + '</div>',
                            unsafe_allow_html=True)
            st.markdown('<div class="mlab" style="margin-top:18px">Palmarés histórico · copas internacionales</div>',
                        unsafe_allow_html=True)
            st.markdown('<div class="pal-grid">' + "".join(
                tabla_ranking_html(titulo, logo, S.get(clave, {}), PALMARES.get(clave, {}))
                for titulo, logo, clave in (("Mundial de Clubes", "Mundial de Clubes", "hist_mundial"),
                                            ("Copa Libertadores", "Copa Libertadores", "hist_lib"),
                                            ("Copa Sudamericana", "Copa Sudamericana", "hist_sud"),
                                            ("Recopa Sudamericana", "Recopa Sudamericana", "hist_rec"))) + '</div>',
                        unsafe_allow_html=True)
            # Regionales: un palmarés por torneo (sale de los campeones de cada temporada), en un desplegable
            from copas.regionales import TORNEOS as _TORN
            if es_base and (S.get("regionales_on") or any(x.get("Regionales") for x in S["campeones"])):
                with st.expander(":material/emoji_events: Palmarés de los Regionales (por torneo)", expanded=False):
                    def _titulos(nombre):
                        cuenta = {}
                        for x in S["campeones"]:
                            club = x.get("Regionales", {}).get(nombre)
                            if club:
                                cuenta[club] = cuenta.get(club, 0) + 1
                        return cuenta
                    st.markdown('<div class="pal-grid">' + "".join(
                        tabla_ranking_html(tt["nombre"], tt["nombre"], _titulos(tt["nombre"]), {}) for tt in _TORN)
                        + '</div>', unsafe_allow_html=True)
            if pais == "Brasil" and any(x.get("Estaduales") for x in S["campeones"]):
                from copas.estaduales import TORNEOS as _TORN_BR
                with st.expander(":material/emoji_events: Palmarés de los Estaduales (por estado)", expanded=False):
                    def _titulos_br(nombre):
                        cuenta = {}
                        for x in S["campeones"]:
                            club = x.get("Estaduales", {}).get(nombre)
                            if club:
                                cuenta[club] = cuenta.get(club, 0) + 1
                        return cuenta
                    st.markdown('<div class="pal-grid">' + "".join(
                        tabla_ranking_html(tt["nombre"], tt["nombre"], _titulos_br(tt["nombre"]), {}) for tt in _TORN_BR)
                        + '</div>', unsafe_allow_html=True)
            if es_base:
                st.caption("Títulos oficiales hasta 2025 (AFA / CONMEBOL): Primera, era amateur y profesional; "
                           "B Nacional, Primera B Metropolitana y Primera C, desde 1986-87; Federal A, desde 2014. "
                           "El Federal B suma desde que se crea en el Modo dios. "
                           "En verde (+n), los ganados en las temporadas simuladas. Tocá un club para ver su ficha.")
            else:
                st.caption(f"El palmarés de {pais} combina los títulos históricos cargados con los ganados durante las temporadas simuladas. "
                           "Las copas internacionales traen los títulos oficiales hasta 2025 (CONMEBOL), con los ganados en las "
                           "temporadas simuladas en verde (+n). Tocá un club para ver su ficha.")

            if es_base and S["movimientos"]:
                mv = S["movimientos"]
                with st.expander(f":material/swap_vert: Cambios de categoría para la temporada {S['temp']}",
                                 expanded=False):
                    st.markdown(movimientos_html(mv), unsafe_allow_html=True)
            for comp in (c for c in ligas_pais if c.divisional == 1):     # ascensos y descensos de la liga de otro país
                mov = S.get("ext_mov", {}).get(comp.clubes_key)
                abajo = ligas_ext.CONFIG.get(comp.cfg.get("inferior"))
                if mov:
                    with st.expander(f":material/swap_vert: Cambios de categoría tras la temporada {mov['temp']}",
                                     expanded=False):
                        st.markdown(f'<div class="mv-grid"><div class="mv-card"><div class="mv-h"><span>{esc(comp.nombre)}'
                                    f'</span></div><div class="mv-sec"><div class="mv-lab up">▲ Suben<b>{len(mov["suben"])}</b></div>'
                                    f'<div class="mv-lista">{_mov_clubes([(n, "") for n in mov["suben"]])}</div></div>'
                                    f'<div class="mv-sec"><div class="mv-lab down">▼ Bajan a {esc(abajo["nombre"] if abajo else "la Segunda División")}'
                                    f'<b>{len(mov["bajan"])}</b></div><div class="mv-lista">'
                                    f'{_mov_clubes([(n, "") for n in mov["bajan"]])}</div></div></div></div>',
                                    unsafe_allow_html=True)
                mov3 = S.get("ext_mov3", {}).get(comp.cfg["pais"])
                tercera = ligas_ext.CONFIG.get(abajo.get("inferior")) if abajo else None
                nom3 = " y ".join(x["nombre"] for x in (tercera, ligas_ext.CONFIG.get(abajo.get("inferior_b")) if abajo else None) if x) \
                    or "la tercera división"
                if mov3:                                       # segunda división <-> tercera (Primera Amateur)
                    with st.expander(f":material/swap_vert: Segunda División y {nom3} tras la temporada {mov3['temp']}",
                                     expanded=False):
                        st.markdown(f'<div class="mv-grid"><div class="mv-card"><div class="mv-h"><span>'
                                    f'{esc(abajo["nombre"] if abajo else "Segunda División")}</span></div>'
                                    f'<div class="mv-sec"><div class="mv-lab up">▲ Suben de {esc(nom3)}'
                                    f'<b>{len(mov3["suben"])}</b></div><div class="mv-lista">'
                                    f'{_mov_clubes([(n, "") for n in mov3["suben"]])}</div></div>'
                                    f'<div class="mv-sec"><div class="mv-lab down">▼ Bajan a {esc(nom3)}'
                                    f'<b>{len(mov3["bajan"])}</b></div><div class="mv-lista">'
                                    f'{_mov_clubes([(n, "") for n in mov3["bajan"]])}</div></div></div></div>',
                                    unsafe_allow_html=True)
                mov4 = S.get("ext_mov4", {}).get(comp.cfg["pais"])
                cuarta = ligas_ext.CONFIG.get(tercera.get("inferior")) if tercera else None
                if mov4 and cuarta:                            # tercera división <-> cuarta (Série C y Série D)
                    with st.expander(f":material/swap_vert: {esc(tercera['nombre'])} y {esc(cuarta['nombre'])} tras la temporada {mov4['temp']}",
                                     expanded=False):
                        st.markdown(f'<div class="mv-grid"><div class="mv-card"><div class="mv-h"><span>'
                                    f'{esc(tercera["nombre"])}</span></div>'
                                    f'<div class="mv-sec"><div class="mv-lab up">▲ Suben de {esc(cuarta["nombre"])}'
                                    f'<b>{len(mov4["suben"])}</b></div><div class="mv-lista">'
                                    f'{_mov_clubes([(n, "") for n in mov4["suben"]])}</div></div>'
                                    f'<div class="mv-sec"><div class="mv-lab down">▼ Bajan a {esc(cuarta["nombre"])}'
                                    f'<b>{len(mov4["bajan"])}</b></div><div class="mv-lista">'
                                    f'{_mov_clubes([(n, "") for n in mov4["bajan"]])}</div></div></div></div>',
                                    unsafe_allow_html=True)

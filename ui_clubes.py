"""Pestaña Clubes.

El código es el de simuladorafa.py, movido acá tal cual. `ctx` trae el estado y los ayudantes
compartidos de la interfaz (S, P, las pestañas, las banderas terminada_*, etc.).
"""

import streamlit as st
from regional import REGIONES_REG
from vista import crest, esc, norm, render_ficha, seccion, ver_equipo


def render(ctx):
    (S, SB, SR, _abierta, tab_c) = (
        ctx.S, ctx.SB, ctx.SR, ctx._abierta, ctx.tab_c)
    # ============================================================================
    # CLUBES
    # ============================================================================
    if _abierta(tab_c):
        with tab_c:
            seccion("Clubes", "Elegí un club para ver su ficha y buscar sus partidos", "#1e5aa8")
            cat = st.segmented_control("Categoría",
                                       ["Primera División", "Primera Nacional", "Federal A", "Primera B", "Primera C",
                                        "Regional Amateur"],
                                       default="Primera División", key="cat_clubes")
            cat = cat or "Primera División"
            if cat == "Regional Amateur":            # 245 clubes: se elige la región
                region_c = st.pills("Región", REGIONES_REG, default=REGIONES_REG[0], key="club_reg_region",
                                    label_visibility="collapsed") or REGIONES_REG[0]
                lista = sorted([n for n, r in zip(SR["nombres"], SR["region_de"]) if r == region_c], key=norm)
                region_club = dict(zip(SR["nombres"], SR["region_de"]))
                buscables = sorted(SR["nombres"], key=norm)          # el buscador: todas las regiones
            else:
                lista = sorted({"Primera División": S["nombres"], "Primera Nacional": SB["nombres"],
                                "Federal A": S["federal"], "Primera B": S["primera_b"], "Primera C": S["primera_c"]}[cat],
                               key=norm)
                buscables = lista
            elegido = st.selectbox(":material/search: Buscar club", buscables, index=None,
                                   placeholder=("Escribí un club de cualquier región…" if cat == "Regional Amateur"
                                                else "Escribí o elegí un club…"),
                                   format_func=(lambda n: f"{n} · {region_club[n]}") if cat == "Regional Amateur"
                                   else str, key=f"club_sel_{cat}")
            if elegido:
                with st.container(border=True):
                    render_ficha(elegido, "clubes")
            st.markdown(f'<div class="mlab" style="margin-top:14px">{esc(cat if cat != "Regional Amateur" else f"Regional · {region_c}")} · {len(lista)} clubes · '
                        f'tocá uno para ver su ficha</div>', unsafe_allow_html=True)
            # Grilla de clubes: cada casilla es un botón (invisible, ocupa toda la casilla) que abre la ficha
            slug = norm(cat if cat != "Regional Amateur" else f"reg {region_c}").replace(" ", "_")
            with st.container(key=f"cgrid_{slug}"):
                for i, n in enumerate(lista):
                    with st.container(key=f"ctile_{slug}_{i}"):
                        st.markdown(f'<div class="ct-in">{crest(n, 52)}<span>{esc(n)}</span></div>',
                                    unsafe_allow_html=True)
                        if st.button(n, key=f"clubbtn_{slug}_{i}"):
                            ver_equipo(n)

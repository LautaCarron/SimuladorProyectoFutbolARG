"""Pestaña Clubes.

El código es el de simuladorafa.py, movido acá tal cual. `ctx` trae el estado y los ayudantes
compartidos de la interfaz (S, P, las pestañas, las banderas terminada_*, etc.).
"""

import streamlit as st
from datos.datos_regional import REGIONES_REG
from ui.vista import crest, esc, norm, render_ficha, seccion, ver_equipo


def render(ctx):
    (S, SB, SR, _abierta, tab_c) = (
        ctx.S, ctx.SB, ctx.SR, ctx.abierta, ctx.pestanas.tab_c)
    # ============================================================================
    # CLUBES
    # ============================================================================
    if _abierta(tab_c):
        with tab_c:
            seccion("Clubes", "Elegí un club para ver su ficha y buscar sus partidos", "#1e5aa8")
            # Buscador global: cualquier club de cualquier categoría (y de cualquier región del Regional).
            # Al elegir uno se salta a su categoría / región, así la grilla de abajo queda parada donde está.
            orden = [("Primera División", S["nombres"]), ("Primera Nacional", SB["nombres"]), ("Federal A", S["federal"]),
                     ("Primera B", S["primera_b"]), ("Primera C", S["primera_c"]), ("Promocional Amateur", S["promocional"]),
                     ("Federal B", S.get("federal_b", []) if S.get("fb") is not None else [])]
            donde = {}                                    # club -> (categoría, región o None)
            for categoria_n, nombres_n in orden:
                for n in nombres_n:
                    donde.setdefault(n, (categoria_n, None))
            for n, r in zip(SR["nombres"], SR["region_de"]):
                donde.setdefault(n, ("Regional Amateur", r))
            buscables = sorted(donde, key=norm)

            def _ir_al_club():
                n = st.session_state.get("club_busca_global")
                if n in donde:
                    st.session_state["cat_clubes"], reg_n = donde[n]
                    if reg_n:
                        st.session_state["club_reg_region"] = reg_n

            def _etiqueta(n):
                c_n, r_n = donde[n]
                return f"{n} · Regional · {r_n}" if r_n else f"{n} · {c_n}"

            elegido = st.selectbox(":material/search: Buscar club", buscables, index=None,
                                   placeholder="Escribí cualquier club, de la categoría que sea…",
                                   format_func=_etiqueta, key="club_busca_global", on_change=_ir_al_club)
            if elegido:
                with st.container(border=True):
                    render_ficha(S, ctx.club, elegido, "clubes")

            st.session_state.setdefault("cat_clubes", "Primera División")
            st.session_state.setdefault("club_reg_region", REGIONES_REG[0])
            cat = st.segmented_control("Categoría",
                                       [*[c for c, _ in orden[:6]], *(["Federal B"] if S.get("fb") is not None else []),
                                        "Regional Amateur"],
                                       key="cat_clubes")
            cat = cat or "Primera División"
            if cat == "Regional Amateur":            # 245 clubes: se elige la región
                region_c = st.pills("Región", REGIONES_REG, key="club_reg_region",
                                    label_visibility="collapsed") or REGIONES_REG[0]
                lista = sorted([n for n, r in zip(SR["nombres"], SR["region_de"]) if r == region_c], key=norm)
            else:
                lista = sorted(dict(orden)[cat], key=norm)
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
                            ver_equipo(S, ctx.club, n)

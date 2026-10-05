"""Pestaña Copas · Supercopa Argentina.

El código es el de simuladorafa.py, movido acá tal cual. `ctx` trae el estado y los ayudantes
compartidos de la interfaz (S, P, las pestañas, las banderas terminada_*, etc.).
"""

import streamlit as st
from copas import rivales_supercopa, simular_supercopa, supercopa_lista
from logos import logo_img
from vista import aviso, barra_estado, chip, crest, esc, fila_partido_html, lista_equipos_html, seccion


def render(ctx):
    (P, S, SS, _abierta, tab_copas, tab_sup, terminada, terminada_copa) = (
        ctx.P, ctx.S, ctx.SS, ctx._abierta, ctx.tab_copas, ctx.tab_sup, ctx.terminada,
        ctx.terminada_copa)
    # ============================================================================
    # SUPERCOPA ARGENTINA
    # ============================================================================
    if _abierta(tab_copas, tab_sup):
        with tab_sup:
            listo_sup = supercopa_lista(S)
            c1, c2 = st.columns([4, 1.6], vertical_alignment="center")
            c1.markdown(logo_img("Supercopa Argentina", 30) + " " + chip("Supercopa Argentina", "#b7860b") + " "
                        + chip("Partido único · cancha neutral", "#475569"), unsafe_allow_html=True)
            if c2.button(":material/sports_soccer: Jugar la Supercopa", key="sup_jugar", width="stretch",
                         type="primary", disabled=not listo_sup):
                simular_supercopa(S, P, S["rng"])
                st.rerun()
            estado_sup = ("Terminada" if SS["jugada"] else "Lista para jugar" if listo_sup
                          else "Esperando a Primera y a la Copa")
            barra_estado([("Estado", estado_sup), ("Partidos jugados", len(SS["log"]))],
                         100 if SS["jugada"] else 0)
            seccion("Supercopa Argentina", "Campeón de Primera vs. campeón de la Copa Argentina · partido único "
                    "en cancha neutral, penales si empatan", "#b7860b")
            if SS["jugada"]:
                cc = SS["campeon"]
                sub = SS["b"] if cc == SS["a"] else SS["a"]
                st.markdown(f'<div class="champ"><div class="t">Campeón · Supercopa Argentina · Temporada {S["temp"]}'
                            f'</div><div style="margin-top:10px">{crest(cc, 64)}</div>'
                            f'<div class="nm">{esc(cc)}</div><div class="s">finalista: {esc(sub)}</div></div>',
                            unsafe_allow_html=True)
                st.markdown(fila_partido_html(SS["p"], abierto=True), unsafe_allow_html=True)
                st.caption(f"{esc(SS['a'])}: {SS['crit_a']} · {esc(SS['b'])}: {SS['crit_b']}")
            elif listo_sup:
                a_s, _, ca_s, b_s, _, cb_s = rivales_supercopa(S)
                st.markdown(lista_equipos_html([(a_s, ca_s), (b_s, cb_s)]), unsafe_allow_html=True)
                st.caption("Se juega el miércoles siguiente a la última fecha de Primera (ver Calendario).")
            else:
                aviso("Se juega cuando terminan Primera División y la Copa Argentina. Si el mismo club gana las "
                      "dos, el rival es el subcampeón de Primera.")
                faltan_sup = [n for n, ok in (("Primera División", terminada), ("Copa Argentina", terminada_copa))
                              if not ok]
                st.caption("Faltan terminar: " + ", ".join(faltan_sup))

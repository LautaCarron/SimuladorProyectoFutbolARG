"""Modo dios del simulador (va en ui/dios.py): cambiar los campeonatos desde la barra lateral.

Por ahora: Primera División (formato, descensos y promociones), Primera Nacional (formato, descensos, ascensos
directos y reducido por el ascenso), el Federal A, la Primera B y la Primera C (ascensos, descensos y reducido). Los ascensos de la B son independientes de los descensos de
Primera: si no coinciden, cambia la cantidad de equipos de cada categoría.
Cuando Primera todavía no empezó la temporada los cambios se aplican en el momento; si ya empezó, se guardan
para la temporada que viene. Lo que se elige queda guardado en S["cfg"]["primera"] y S["cfg"]["b"] y se usa cada
vez que se arma una temporada (ver ligas/primera.py y ligas/nacional.py). La cantidad de equipos de la B siempre
rige desde la próxima temporada (los equipos se reacomodan en el pase de temporada).
"""

import streamlit as st
from datos.equipos import N
from ligas.federal import (F_DIRECTOS_MAX, F_RED_EQUIPOS_MAX, cfg_federal, nueva_estructura_f, plan_reducido_f)
from ligas.nacional import nueva_estructura_b
from ligas.simples import (ASC_MAX, DESC_MAX, RED_MAX, cfg_simple, desc_auto, nueva_estructura_liga, plan_simple)
from ligas.nacional import (B_DESC_MAX, B_DIRECTOS_MAX, B_MAX_ANUAL, B_RED_EQUIPOS_MAX, FORMATOS_B,
                            actualizar_promos_b, asc_defecto, asc_elegido, cfg_b, equipos_objetivo_b,
                            formato_efectivo, plan_b, plan_reducido_b, tam_zonas2)
from ligas.primera import (DESCENSOS_MAX, FORMATOS, IDA_VUELTA_MAX, PROMOS_MAX, cfg_primera, descensos,
                           equipos_objetivo_p, formato, formato_posible, formatos_posibles, nueva_estructura, ACTUAL_MIN, ANUAL_IDA_MIN, promos, tam_zonas_p)

DETALLE = {
    "actual": "Fase 1 de 29 fechas todos contra todos y fase 2 de 9 fechas en tres zonas (Campeonato, Intermedia "
              "y Descenso). Campeón: el 1° de la zona Campeonato.",
    "anual_ida": "29 fechas todos contra todos, una sola tabla. Campeón: el 1°.",
    "anual_ida_vuelta": "58 fechas, todos contra todos ida y vuelta, una sola tabla. Campeón: el 1°.",
    "apertura_clausura": "Dos torneos con dos zonas de 15 (15 fechas cada uno) y llaves con los 8 primeros de cada "
                         "zona. Hay campeón del Apertura, del Clausura y de Liga: el 1° de la tabla anual (suma de "
                         "las dos etapas regulares), que además define la copa y los descensos.",
}


def _panel_simple(S, clave, nombre, sube_a, baja_a):
    """Primera B / Primera C: cuántos ascienden directo, cuántos descienden y si hay reducido por un ascenso más.
    Rige ahora si la liga no empezó; si no, desde la próxima temporada (los equipos se reacomodan en el pase)."""
    L, cfg = S[clave], cfg_simple(S, clave)
    ya = L["fecha"] > 0 or bool(L["log"])
    n = len(L["nombres"])
    st.markdown(f"**{nombre}**")
    st.caption(f"Elegís cuántos suben a {sube_a} y cuántos bajan{' a ' + baja_a if baja_a else ''}, y si hay reducido "
               "por un ascenso más. " + ("Ya empezó: rige desde la próxima temporada." if ya else "Rige ahora mismo."))
    d0 = int(cfg["directos"])
    desc_ini = desc_auto(n) if cfg["descensos"] is None else int(cfg["descensos"])
    d = st.slider("Ascienden directo", 0, ASC_MAX, d0, key=f"dios_{clave}_directos")
    ds = st.slider("Descienden", 0, DESC_MAX, min(DESC_MAX, desc_ini), key=f"dios_{clave}_desc",
                   disabled=baja_a is None,
                   help="Sin tocar: del 18° para abajo (según la cantidad de equipos).") if baja_a else 0
    hay = st.checkbox("Reducido por un ascenso más", value=bool(cfg["reducido"]), key=f"dios_{clave}_reducido")
    m = st.slider("Equipos en el reducido", 2, RED_MAX, int(cfg["red_equipos"]), key=f"dios_{clave}_red",
                  disabled=not hay, help="Los que siguen a los ascendidos directos en la tabla final.")
    pl = plan_simple(n, d, ds if baja_a else 0, hay, m)
    txt = f"Suben {pl['directos']} directo" + ("s" if pl["directos"] != 1 else "")
    if pl["reducido"]:
        txt += (f" y el reducido (del {pl['directos'] + 1}° al {pl['directos'] + pl['equipos']}°) da un ascenso más: "
                f"suben {pl['directos'] + 1} en total")
    st.caption(txt + (f". Bajan {pl['desc']}." if baja_a else ".") + " El tamaño de las ligas se ajusta en el pase de temporada.")
    auto = desc_auto(n)
    cambio = (d != d0 or (baja_a and ds != desc_ini) or bool(hay) != bool(cfg["reducido"])
              or int(m) != int(cfg["red_equipos"]))
    if st.button(":material/save: " + ("Guardar para la próxima temporada" if ya else "Aplicar ahora"),
                 key=f"dios_{clave}_aplicar", width="stretch", type="primary", disabled=not cambio):
        cfg["directos"], cfg["reducido"], cfg["red_equipos"] = int(d), bool(hay), int(m)
        if baja_a:
            cfg["descensos"] = None if ds == auto else int(ds)
        if not ya:
            nueva_estructura_liga(L, S["rng"], S, clave)      # la liga no empezó: se rearma ahora
        st.rerun()


def panel_dios(S):
    cfg = cfg_primera(S)
    empezo = S["fecha"] > 0 or bool(S["log"])
    if empezo:                       # equipos con los que se jugará la temporada que viene (según lo ya guardado)
        _d, _r, _ = asc_elegido(S, formato_efectivo(len(S["b"]["nombres"]), cfg_b(S)["formato"]))
        n_p = equipos_objetivo_p(S, len(S["nombres"]) + _d + int(_r) - int(cfg["descensos"]))
    else:
        n_p = len(S["nombres"])
    # el ida y vuelta sólo se puede elegir con IDA_VUELTA_MAX equipos o menos
    formatos = formatos_posibles(n_p)                      # los que se pueden jugar con esa cantidad de equipos
    b_ya = S["b"]["fecha"] > 0 or bool(S["b"]["log"])           # la B / el Federal ya jugaron fechas
    f_ya = S["f"]["fecha"] > 0 or bool(S["f"]["log"])
    txt_b = "Guardar para la próxima temporada" if b_ya else "Aplicar ahora"
    txt_f = "Guardar para la próxima temporada" if f_ya else "Aplicar ahora"
    with st.sidebar:
        st.divider()
        st.header("Modo dios")          # mismo estilo (h2) que "Parámetros de simulación", siempre desplegado
        st.caption("Cambiá los campeonatos. " + ("Primera ya empezó: lo que elijas rige desde la próxima temporada."
                                                  if empezo else "Primera no empezó: se aplica ahora mismo."))
        st.markdown("**Primera División**")
        fmt = st.selectbox("Formato", formatos, format_func=FORMATOS.get, key="dios_formato",
                           index=formatos.index(cfg["formato"] if cfg["formato"] in formatos else formato_posible(cfg["formato"], n_p)))
        k = st.slider("Descienden a la B", 0, DESCENSOS_MAX, int(cfg["descensos"]), key="dios_k",
                      help="El puesto N-k juega la promoción contra el perdedor del reducido de la B. Cuántos suben de la B "
                           "se elige en la sección de la Primera Nacional (si no coinciden con los que bajan, "
                           "cambia la cantidad de equipos de Primera).")
        pr = st.slider("Promociones", 0, PROMOS_MAX, int(cfg["promociones"]), key="dios_prom",
                       help="Series entre los de abajo de Primera y los mejores de la B: 0 (no hay), 1 o 2. "
                            "Suben los de la B que ganan, bajan los de Primera que pierden.")
        st.caption(f"Con {n_p} equipos: formato actual desde {ACTUAL_MIN}, anual una rueda desde {ANUAL_IDA_MIN} "
                   f"y anual ida y vuelta hasta {IDA_VUELTA_MAX}.")
        tp = tam_zonas_p(n_p)
        st.caption(f"Fase 2 en zonas de {tp[0]}, {tp[1]} y {tp[2]}." + (" Apertura y Clausura solo se juega con 30."
                                                                         if fmt == "apertura_clausura" and n_p != 30 else ""))
        st.caption(DETALLE[fmt])
        N = n_p
        st.caption(f"Descienden {k} directo a la B" + (f" (puestos {N - k + 1}° a {N}°)" if k else "")
                   + (f"; juegan la promoción el {N - k - pr + 1}° al {N - k}°" if pr > 1 else
                      f"; el {N - k}° juega la promoción" if pr == 1 else "; no hay promoción")
                   + ". Los ascensos desde la B se eligen en la sección de la Primera Nacional.")
        cambio = (fmt != cfg["formato"]) or (k != int(cfg["descensos"])) or (pr != int(cfg["promociones"]))
        if st.button(":material/save: " + ("Guardar para la próxima temporada" if empezo else "Aplicar ahora"),
                     key="dios_aplicar", width="stretch", type="primary", disabled=not cambio):
            cfg["formato"], cfg["descensos"], cfg["promociones"] = fmt, int(k), int(pr)
            if not empezo:
                nueva_estructura(S)                    # Primera no empezó: se rearma con el formato nuevo
                actualizar_promos_b(S)                 # y la B juega las promociones que corresponden
            st.rerun()
        if formato(S) != cfg["formato"] or descensos(S) != int(cfg["descensos"]) or promos(S) != int(cfg["promociones"]):
            st.caption(f"Esta temporada se juega con: {FORMATOS[formato(S)]}, {descensos(S)} descensos, "
                       f"{promos(S)} promoción(es).")

        # ---------------------------------------------------------------- Primera Nacional
        cfg_nac = cfg_b(S)
        objetivo = equipos_objetivo_b(S)
        st.markdown("**Primera Nacional**")
        n_b = objetivo
        # el ida y vuelta sólo se puede elegir con B_MAX_ANUAL equipos o menos (con tantos o menos se juega solo)
        opciones_b = [x for x in FORMATOS_B if x != "anual_ida_vuelta" or n_b <= B_MAX_ANUAL]
        if "anual_ida_vuelta" not in opciones_b:
            st.caption(f"El torneo anual ida y vuelta solo se puede con {B_MAX_ANUAL} equipos o menos "
                       f"(la B tiene {n_b}).")
        fmt_b = st.selectbox("Formato de la B", opciones_b, format_func=FORMATOS_B.get, key="dios_b_formato",
                             index=opciones_b.index(cfg_nac["formato"] if cfg_nac["formato"] in opciones_b else "actual"))
        auto_desc = plan_b(n_b, fmt_b)["desc"]
        desc_elegido = cfg_nac["descensos"]
        desc_b = st.slider("Descienden de la B", 0, B_DESC_MAX,
                           int(auto_desc if desc_elegido is None else desc_elegido), key="dios_b_desc",
                           help="De 0 a 8 equipos bajan de la B al Federal A o a la Primera B. Si no lo tocás, se calcula "
                                "según la cantidad de equipos (6 con 36).")
        plan_nuevo = plan_b(n_b, fmt_b, desc_b)
        if plan_nuevo["formato"] == "actual":
            tam = tam_zonas2(n_b)
            zonas = f"{tam[0]} cada una" if len(set(tam)) == 1 else f"{tam[0]}, {tam[1]} y {tam[2]}"
            st.caption(f"Formato actual: dos zonas de {n_b // 2} en la fase 1 ({plan_nuevo['f1']} fechas) y tres zonas "
                       f"de {zonas} en la fase 2 ({plan_nuevo['f2']} fechas). Bajan {plan_nuevo['desc']}.")
        else:
            st.caption(f"Torneo anual ida y vuelta: {plan_nuevo['base']} fechas, una sola tabla. "
                       f"Bajan {plan_nuevo['desc']}.")

        # ---- ascensos de la B: cuántos suben directo, si hay reducido por un ascenso más y quiénes lo juegan
        fe_b = formato_efectivo(n_b, fmt_b)                       # formato con el que se jugaría de verdad
        d_def, r_def, m_def = asc_defecto(fe_b, int(k))
        d_ini, r_ini, m_ini = (d_def if cfg_nac["directos"] is None else int(cfg_nac["directos"]),
                               r_def if cfg_nac["reducido"] is None else bool(cfg_nac["reducido"]),
                               m_def if cfg_nac["red_equipos"] is None else int(cfg_nac["red_equipos"]))
        st.caption("**Ascensos a Primera.** Elegís cuántos suben directo y si hay reducido por un ascenso más. "
                   "Pierde el reducido y hay promoción: la juega el perdedor de la final (y, si hay dos promociones, "
                   "el mejor ubicado de los demás que perdieron). Sin reducido, las promociones las juegan los que "
                   "quedaron detrás de los ascensos directos.")
        d_b = st.slider("Ascienden directo", 0, B_DIRECTOS_MAX, min(B_DIRECTOS_MAX, d_ini), key=f"dios_b_directos_{fe_b}",
                        help="Los primeros de la tabla final (en el formato actual, de la Zona Campeonato). El 1° "
                             "es el campeón.")
        hay_red_b = st.checkbox("Reducido por un ascenso más", value=r_ini, key=f"dios_b_reducido_{fe_b}")
        m_b = st.slider("Equipos en el reducido", 2, B_RED_EQUIPOS_MAX, min(B_RED_EQUIPOS_MAX, max(2, m_ini)),
                        key=f"dios_b_red_equipos_{fe_b}", disabled=not hay_red_b,
                        help="Los que siguen a los ascendidos directos en la tabla final (en el formato actual: "
                             "Campeonato, después Intermedia). Los que bajan no lo juegan.")
        pr_b = plan_reducido_b(d_b, hay_red_b, m_b, n_b, plan_nuevo["desc"])
        d_real = pr_b["directos"]
        if pr_b["reducido"]:
            st.caption(f"Reducido: del {d_real + 1}° al {d_real + pr_b['equipos']}° de la tabla "
                       f"({' → '.join(e.replace(' del reducido', '') for e in pr_b['etapas'])}). Suben "
                       f"{d_real + 1} en total (más los que ganen la promoción).")
        else:
            st.caption(f"Sin reducido. Suben {d_real} en total (más los que ganen la promoción).")
        suben_b = d_real + (1 if pr_b["reducido"] else 0)
        if int(pr) > 0:
            st.caption(f"Promoción: " + (f"el perdedor de la final del reducido" + (" y el mejor ubicado de los otros "
                       "que perdieron" if int(pr) > 1 else "") if pr_b["reducido"] else
                       f"los {int(pr)} que quedan detrás de los ascensos directos") + " juega contra el de Primera.")
        dif = suben_b - int(k)
        if dif:
            st.caption(f"Suben {suben_b} de la B y bajan {int(k)} de Primera: Primera pasa de {len(S['nombres'])} a "
                       f"{len(S['nombres']) + dif} equipos y la B de {len(S['b']['nombres'])} a "
                       f"{len(S['b']['nombres']) - dif} (rige desde la próxima temporada; las promociones no "
                       "cambian las cantidades).")
        act_d, act_r, act_m = asc_elegido(S, formato_efectivo(n_b, cfg_nac["formato"]))
        cambio_b = (fmt_b != cfg_nac["formato"]
                    or desc_b != int(plan_b(objetivo, cfg_nac["formato"], cfg_nac["descensos"])["desc"])
                    or (d_b, bool(hay_red_b), int(m_b)) != (act_d, act_r, act_m)
                    )
        if st.button(":material/save: " + txt_b, key="dios_b_aplicar", width="stretch",
                     type="primary", disabled=not cambio_b):
            cfg_nac["formato"] = fmt_b
            cfg_nac["descensos"] = None if desc_b == auto_desc else int(desc_b)   # sin tocar: automático
            cfg_nac["directos"] = None if d_b == d_def else int(d_b)             # sin tocar: automático
            cfg_nac["reducido"] = None if bool(hay_red_b) == r_def else bool(hay_red_b)
            cfg_nac["red_equipos"] = None if int(m_b) == m_def else int(m_b)
            if not b_ya:                               # la B no empezó: se rearma ahora con lo elegido
                nueva_estructura_b(S["b"], S["rng"], S)
                actualizar_promos_b(S)
            st.rerun()

        # ---------------------------------------------------------------- Federal A
        cfg_fed = cfg_federal(S)
        st.markdown("**Federal A**")
        st.caption("El formato es siempre el mismo (grupos, zonas Campeonato y Descenso). Elegís los ascensos; "
                   "rige ahora si todavía no empezó, o desde la próxima temporada.")
        d_f = st.slider("Ascienden directo", 0, F_DIRECTOS_MAX, int(cfg_fed["directos"]), key="dios_f_directos",
                        help="Los primeros de la zona Campeonato. El campeón sube siempre que haya ascensos directos.")
        hay_red = st.checkbox("Reducido por el último ascenso", value=bool(cfg_fed["reducido"]), key="dios_f_reducido")
        m_f = st.slider("Equipos en el reducido", 2, F_RED_EQUIPOS_MAX, int(cfg_fed["red_equipos"]),
                        key="dios_f_red_equipos", disabled=not hay_red,
                        help="Los que siguen a los ascendidos directos en la zona Campeonato.")
        pr_f = plan_reducido_f(d_f, hay_red, m_f, (len(S["f"]["nombres"]) + 1) // 2)
        if pr_f["reducido"]:
            st.caption(f"Reducido: del {d_f + 1}° al {d_f + pr_f['equipos']}° de la zona Campeonato "
                       f"({' → '.join(e.replace(' del reducido', '') for e in pr_f['etapas'])}). "
                       f"Ascienden {d_f + 1} en total.")
        else:
            st.caption(f"Sin reducido. Ascienden {d_f} en total.")
        cambio_f = (d_f != int(cfg_fed["directos"]) or hay_red != bool(cfg_fed["reducido"])
                    or m_f != int(cfg_fed["red_equipos"]))
        if st.button(":material/save: " + txt_f, key="dios_f_aplicar", width="stretch",
                     type="primary", disabled=not cambio_f):
            cfg_fed["directos"], cfg_fed["reducido"], cfg_fed["red_equipos"] = int(d_f), bool(hay_red), int(m_f)
            if not f_ya:                               # el Federal no empezó: se rearma ahora
                nueva_estructura_f(S["f"], S["rng"], S)
            st.rerun()

        # ---------------------------------------------------------------- Primera B y Primera C
        _panel_simple(S, "pb", "Primera B", "la Primera Nacional", "la Primera C")
        _panel_simple(S, "pc", "Primera C", "la Primera B", "el Promocional")
        _panel_simple(S, "pd", "Promocional Amateur", "la Primera C", None)

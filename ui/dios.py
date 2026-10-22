"""Modo dios del simulador (va en ui/dios.py): cambiar los campeonatos desde la barra lateral.

Por ahora: Primera División (formato, descensos y promociones), Primera Nacional (formato, descensos, ascensos
directos y reducido por el ascenso), el Federal A, el Federal B (se crea desde acá, entre el Federal A y el Regional
Amateur; ver ligas/federal_b.py), la Primera B y la Primera C (ascensos, descensos y reducido). Los ascensos de la B son independientes de los descensos de
Primera: si no coinciden, cambia la cantidad de equipos de cada categoría.
Cuando Primera todavía no empezó la temporada los cambios se aplican en el momento; si ya empezó, se guardan
para la temporada que viene. Lo que se elige queda guardado en S["cfg"]["primera"] y S["cfg"]["b"] y se usa cada
vez que se arma una temporada (ver ligas/primera.py y ligas/nacional.py). La cantidad de equipos de la B siempre
rige desde la próxima temporada (los equipos se reacomodan en el pase de temporada).
"""

import streamlit as st
from motor.nucleo import DESC_LIGA_MIN, tope_descensos
from datos.equipos import N
from ligas.federal import (F_DESC, F_DESC_MAX, F_DIRECTOS_MAX, F_RED_EQUIPOS_MAX, cfg_federal, nueva_estructura_f,
                           plan_reducido_f)
from ligas.federal_b import (FB_EQUIPOS, activo as fb_activo, cfg_federal_b, destino_descenso_federal_a,
                             pendiente as fb_pendiente)
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


def _slider_desc(label, n, tope, valor, key, **kw):
    """Slider de descensos con el límite de que la liga no quede con menos de DESC_LIGA_MIN (14) equipos: con 16 equipos
    hasta 2, con 14 ninguno, con 22 o más el tope de la liga. Si el límite es 0 no hay slider y devuelve 0."""
    lim = tope_descensos(n, tope)
    if lim <= 0:
        st.caption(f"{label}: sin descensos (con {n} equipos la liga quedaría con menos de {DESC_LIGA_MIN}).")
        return 0
    if st.session_state.get(key, 0) > lim:                  # el límite bajó: el valor guardado se ajusta
        st.session_state[key] = lim
    st.caption(f"Máximo {lim} (la liga no puede quedar con menos de {DESC_LIGA_MIN} equipos).")
    return st.slider(label, 0, lim, min(lim, int(valor)), key=key, **kw)


def _panel_simple(S, clave, nombre, sube_a, baja_a):
    """Primera B / Primera C: cuántos ascienden directo, cuántos descienden y si hay reducido por un ascenso más.
    Rige ahora si la liga no empezó; si no, desde la próxima temporada (los equipos se reacomodan en el pase)."""
    L, cfg = S[clave], cfg_simple(S, clave)
    ya = L["fecha"] > 0 or bool(L["log"])
    n = len(L["nombres"])
    _titulo(nombre)
    st.caption(f"Elegís cuántos suben a {sube_a} y cuántos bajan{' a ' + baja_a if baja_a else ''}, y si hay reducido "
               "por un ascenso más. " + ("Ya empezó: rige desde la próxima temporada." if ya else "Rige ahora mismo."))
    d0 = int(cfg["directos"])
    desc_ini = desc_auto(n) if cfg["descensos"] is None else int(cfg["descensos"])
    d = st.slider("Ascienden directo", 0, ASC_MAX, d0, key=f"dios_{clave}_directos")
    ds = _slider_desc("Descienden", n, DESC_MAX, desc_ini, f"dios_{clave}_desc",
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


def _panel_federal_b(S):
    """Federal B: crearlo (entre el Federal A y el Regional Amateur) y, una vez creado o pedido, elegir ascensos
    directos, reducido y descensos. Se arma en el pase de temporada: bajan los del Federal A y suben los mejores del
    Regional hasta completar 20 equipos."""
    cfg = cfg_federal_b(S)
    existe, pide = fb_activo(S), fb_pendiente(S)
    _titulo("Federal B")
    if not existe and not pide:
        st.caption("Categoría nueva entre el Federal A y el Regional Amateur, con el mismo formato que el Federal A. "
                   f"Se arma al terminar esta temporada: bajan al Federal B todos los que descienden del Federal A "
                   f"y suben los mejores del Regional Amateur hasta completar {FB_EQUIPOS} equipos.")
        if st.button(":material/add_circle: Crear Federal B", key="dios_fb_crear", width="stretch", type="primary"):
            cfg["crear"] = True
            st.rerun()
        return
    SFB = S.get("fb")
    ya = bool(SFB) and (SFB["fecha"] > 0 or bool(SFB["log"]))
    if pide:
        st.caption(f"Se crea al terminar esta temporada ({FB_EQUIPOS} equipos): bajan los {int(cfg_federal(S)["descensos"])} del Federal A y "
                   "suben los mejores del Regional Amateur. Elegí ahora cómo se juega su primera temporada.")
        if st.button(":material/cancel: Cancelar la creación", key="dios_fb_cancelar", width="stretch"):
            cfg["crear"] = False
            st.rerun()
    else:
        st.caption("Mismo formato que el Federal A (grupos, zonas Campeonato y Descenso). Elegís los ascensos al "
                   "Federal A, los descensos al Regional y el reducido; " +
                   ("ya empezó: rige desde la próxima temporada." if ya else "rige ahora mismo."))
    n_fb = len(SFB["nombres"]) if existe else FB_EQUIPOS
    zona = (n_fb + 1) // 2
    d_b = st.slider("Ascienden directo al Federal A", 0, F_DIRECTOS_MAX, min(F_DIRECTOS_MAX, int(cfg["directos"])),
                    key="dios_fb_directos", help="Los primeros de la zona Campeonato. El campeón sube siempre que "
                                                 "haya ascensos directos.")
    hay_red = st.checkbox("Reducido por el último ascenso", value=bool(cfg["reducido"]), key="dios_fb_reducido")
    tope_b = max(2, zona - d_b)                        # todos los que siguen a los directos en la zona Campeonato
    if st.session_state.get("dios_fb_red_equipos", 2) > tope_b:
        st.session_state["dios_fb_red_equipos"] = tope_b
    m_b = st.slider("Equipos en el reducido", 2, tope_b, min(tope_b, int(cfg["red_equipos"])),
                    key="dios_fb_red_equipos", disabled=not hay_red,
                    help=f"Los que siguen a los ascendidos directos en la zona Campeonato (hasta {tope_b}).")
    ds_b = _slider_desc("Descienden al Regional", n_fb, F_DESC_MAX, cfg["descensos"], "dios_fb_desc",
                        help="Los últimos de la zona Descenso.")
    pr = plan_reducido_f(d_b, hay_red, m_b, zona)
    suben = pr["directos"] + (1 if pr["reducido"] else 0)
    if pr["reducido"]:
        st.caption(f"Reducido: del {d_b + 1}° al {d_b + pr['equipos']}° de la zona Campeonato "
                   f"({' → '.join(e.replace(' del reducido', '') for e in pr['etapas'])}). Ascienden {suben} en total.")
    else:
        st.caption(f"Sin reducido. Ascienden {suben} en total.")
    n_a = len(S["f"]["nombres"])
    d_a = int(cfg_federal(S)["descensos"])
    if pide:
        st.caption(f"Arranca con {FB_EQUIPOS} equipos. Al terminar su primera temporada suben {suben} al Federal A y "
                   f"bajan {ds_b} al Regional (el Federal A baja {d_a} y el Regional sube 6).")
    else:
        st.caption(f"Suben {suben} al Federal A y bajan {ds_b} al Regional; del Federal A bajan {d_a} y del Regional "
                   f"suben 6. Federal A: {n_a} → {n_a - d_a + suben} equipos · Federal B: {n_fb} → "
                   f"{n_fb - suben - ds_b + d_a + 6} (rige en el pase de temporada).")
    cambio = (d_b != int(cfg["directos"]) or bool(hay_red) != bool(cfg["reducido"])
              or int(m_b) != int(cfg["red_equipos"]) or int(ds_b) != int(cfg["descensos"]))
    txt = "Guardar" if pide else ("Guardar para la próxima temporada" if ya else "Aplicar ahora")
    if st.button(":material/save: " + txt, key="dios_fb_aplicar", width="stretch", type="primary",
                 disabled=not cambio):
        cfg["directos"], cfg["reducido"], cfg["red_equipos"], cfg["descensos"] = (
            int(d_b), bool(hay_red), int(m_b), int(ds_b))
        if existe and not ya:                            # el Federal B no empezó: se rearma ahora
            nueva_estructura_f(SFB, S["rng"], S)
        st.rerun()


def _titulo(nombre, detalle=None):
    """Título de cada sección del Modo dios (mismo estilo en todas)."""
    st.markdown(f"##### {nombre}")
    if detalle:
        st.caption(detalle)


def _panel_primera(S, cfg, empezo, n_p, formatos, base_p):
    """Primera División: formato, descensos y promociones. Devuelve (descensos, promociones) elegidos."""
    with st.container(border=True):
        _titulo("Primera División")
        fmt = st.selectbox("Formato", formatos, format_func=FORMATOS.get, key="dios_formato",
                           index=formatos.index(cfg["formato"] if cfg["formato"] in formatos else formato_posible(cfg["formato"], n_p)))
        k_max = tope_descensos(base_p, DESCENSOS_MAX)      # Primera no puede quedar con menos de DESC_LIGA_MIN equipos
        if st.session_state.get("dios_k", 0) > k_max:         # el límite bajó: el valor guardado se ajusta
            st.session_state["dios_k"] = k_max
        k = st.slider("Descienden a la B", 0, max(1, k_max), min(k_max, int(cfg["descensos"])), key="dios_k",
                      disabled=k_max == 0,
                      help="El puesto N-k juega la promoción contra el perdedor del reducido de la B. Cuántos suben de la B "
                           "se elige en la sección de la Primera Nacional (si no coinciden con los que bajan, "
                           "cambia la cantidad de equipos de Primera).")
        st.caption(f"Máximo {k_max} descensos: Primera no puede quedar con menos de {DESC_LIGA_MIN} equipos.")
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
        return k, pr


def _sub(texto):
    """Subtítulo dentro de una tarjeta del Modo dios (Formato / Ascensos / Reducido / Descensos)."""
    st.markdown(f"**{texto}**")


def _panel_nacional(S, k, pr, b_ya, txt_b):
    """Primera Nacional, en orden: formato, ascensos a Primera, reducido y descensos."""
    with st.container(border=True):
        _titulo("Primera Nacional")
        cfg_nac = cfg_b(S)
        objetivo = equipos_objetivo_b(S)
        n_b = objetivo
        # ---------------------------------------------------------------- formato
        _sub("Formato")
        # el ida y vuelta sólo se puede elegir con B_MAX_ANUAL equipos o menos (con tantos o menos se juega solo)
        opciones_b = [x for x in FORMATOS_B if x != "anual_ida_vuelta" or n_b <= B_MAX_ANUAL]
        if "anual_ida_vuelta" not in opciones_b:
            st.caption(f"El torneo anual ida y vuelta solo se puede con {B_MAX_ANUAL} equipos o menos "
                       f"(la B tiene {n_b}).")
        fmt_b = st.selectbox("Formato de la B", opciones_b, format_func=FORMATOS_B.get, key="dios_b_formato",
                             label_visibility="collapsed",
                             index=opciones_b.index(cfg_nac["formato"] if cfg_nac["formato"] in opciones_b else "actual"))
        auto_desc = plan_b(n_b, fmt_b)["desc"]
        plan_fmt = plan_b(n_b, fmt_b)
        if plan_fmt["formato"] == "actual":
            tam = tam_zonas2(n_b)
            zonas = f"{tam[0]} cada una" if len(set(tam)) == 1 else f"{tam[0]}, {tam[1]} y {tam[2]}"
            st.caption(f"Dos zonas de {n_b // 2} en la fase 1 ({plan_fmt['f1']} fechas) y tres zonas de {zonas} "
                       f"en la fase 2 ({plan_fmt['f2']} fechas).")
        else:
            st.caption(f"Torneo anual ida y vuelta: {plan_fmt['base']} fechas, una sola tabla.")

        # ---------------------------------------------------------------- ascensos a Primera
        fe_b = formato_efectivo(n_b, fmt_b)                       # formato con el que se jugaría de verdad
        d_def, r_def, m_def = asc_defecto(fe_b, int(k))
        d_ini, r_ini, m_ini = (d_def if cfg_nac["directos"] is None else int(cfg_nac["directos"]),
                               r_def if cfg_nac["reducido"] is None else bool(cfg_nac["reducido"]),
                               m_def if cfg_nac["red_equipos"] is None else int(cfg_nac["red_equipos"]))
        st.divider()
        _sub("Ascensos a Primera")
        d_b = st.slider("Ascienden directo", 0, B_DIRECTOS_MAX, min(B_DIRECTOS_MAX, d_ini), key=f"dios_b_directos_{fe_b}",
                        help="Los primeros de la tabla final (en el formato actual, de la Zona Campeonato). El 1° "
                             "es el campeón.")
        ph_asc = st.empty()                                       # se completa cuando se conoce todo lo elegido

        # ---------------------------------------------------------------- reducido
        st.divider()
        _sub("Reducido")
        hay_red_b = st.checkbox("Reducido por un ascenso más", value=r_ini, key=f"dios_b_reducido_{fe_b}")
        m_b = st.slider("Equipos en el reducido", 2, B_RED_EQUIPOS_MAX, min(B_RED_EQUIPOS_MAX, max(2, m_ini)),
                        key=f"dios_b_red_equipos_{fe_b}", disabled=not hay_red_b,
                        help="Los que siguen a los ascendidos directos en la tabla final (en el formato actual: "
                             "Campeonato, después Intermedia). Los que bajan no lo juegan.")
        ph_red = st.empty()

        # ---------------------------------------------------------------- descensos
        st.divider()
        _sub("Descensos")
        desc_elegido = cfg_nac["descensos"]
        desc_b = _slider_desc("Descienden de la B", n_b, B_DESC_MAX,
                              auto_desc if desc_elegido is None else desc_elegido, "dios_b_desc",
                              help="De 0 a 8 equipos bajan de la B al Federal A o a la Primera B. Si no lo tocás, se calcula "
                                "según la cantidad de equipos (6 con 36).")
        plan_nuevo = plan_b(n_b, fmt_b, desc_b)
        st.caption(f"Bajan {plan_nuevo['desc']} al Federal A o a la Primera B.")

        # ---------------------------------------------------------------- resumen (depende de todo lo anterior)
        pr_b = plan_reducido_b(d_b, hay_red_b, m_b, n_b, plan_nuevo["desc"])
        d_real = pr_b["directos"]
        suben_b = d_real + (1 if pr_b["reducido"] else 0)
        ph_asc.caption(f"Suben {suben_b} en total" + (" (más los que ganen la promoción)." if int(pr) > 0 else "."))
        if pr_b["reducido"]:
            ph_red.caption(f"Del {d_real + 1}° al {d_real + pr_b['equipos']}° de la tabla "
                           f"({' → '.join(e.replace(' del reducido', '') for e in pr_b['etapas'])}).")
        else:
            ph_red.caption("Sin reducido: los ascensos son sólo los directos.")
        if int(pr) > 0:
            st.caption("Promoción: " + ("el perdedor de la final del reducido" + (" y el mejor ubicado de los otros "
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


def _panel_federal_a(S, f_ya, txt_f):
    """Federal A, en orden: ascensos a la Primera Nacional, reducido y descensos (al Federal B si existe, si no al
    Regional Amateur)."""
    with st.container(border=True):
        _titulo("Federal A")
        cfg_fed = cfg_federal(S)
        destino = destino_descenso_federal_a(S)                     # "Federal B" o "Regional Amateur"
        n_f = len(S["f"]["nombres"])
        zona = (n_f + 1) // 2
        st.caption("Mismo formato siempre (grupos, zonas Campeonato y Descenso). "
                   + ("Ya empezó: rige desde la próxima temporada." if f_ya else "Rige ahora mismo."))
        _sub("Ascensos a la Primera Nacional")
        d_f = st.slider("Ascienden directo", 0, F_DIRECTOS_MAX, int(cfg_fed["directos"]), key="dios_f_directos",
                        help="Los primeros de la zona Campeonato. El campeón sube siempre que haya ascensos directos.")
        ph_asc = st.empty()
        st.divider()
        _sub("Reducido")
        hay_red = st.checkbox("Reducido por el último ascenso", value=bool(cfg_fed["reducido"]), key="dios_f_reducido")
        tope_f = max(2, zona - d_f)                    # todos los que siguen a los directos en la zona Campeonato
        if st.session_state.get("dios_f_red_equipos", 2) > tope_f:      # el tope baja al subir los directos
            st.session_state["dios_f_red_equipos"] = tope_f
        m_f = st.slider("Equipos en el reducido", 2, tope_f, min(tope_f, int(cfg_fed["red_equipos"])),
                        key="dios_f_red_equipos", disabled=not hay_red,
                        help=f"Los que siguen a los ascendidos directos en la zona Campeonato (hasta {tope_f}).")
        ph_red = st.empty()
        st.divider()
        _sub("Descensos")
        ds_f = _slider_desc(f"Descienden al {destino}", n_f, F_DESC_MAX, cfg_fed["descensos"], "dios_f_desc",
                            help="Los últimos de la zona Descenso.")
        pr_f = plan_reducido_f(d_f, hay_red, m_f, zona)
        suben_f = d_f + (1 if pr_f["reducido"] else 0)
        ph_asc.caption(f"Ascienden {suben_f} en total.")
        if pr_f["reducido"]:
            ph_red.caption(f"Del {d_f + 1}° al {d_f + pr_f['equipos']}° de la zona Campeonato "
                           f"({' → '.join(e.replace(' del reducido', '') for e in pr_f['etapas'])}).")
        else:
            ph_red.caption("Sin reducido: los ascensos son sólo los directos.")
        st.caption(f"Bajan {ds_f} al {destino}.")
        cambio_f = (d_f != int(cfg_fed["directos"]) or hay_red != bool(cfg_fed["reducido"])
                    or m_f != int(cfg_fed["red_equipos"]) or int(ds_f) != int(cfg_fed["descensos"]))
        if st.button(":material/save: " + txt_f, key="dios_f_aplicar", width="stretch",
                     type="primary", disabled=not cambio_f):
            cfg_fed["directos"], cfg_fed["reducido"], cfg_fed["red_equipos"], cfg_fed["descensos"] = (
                int(d_f), bool(hay_red), int(m_f), int(ds_f))
            if not f_ya:                               # el Federal no empezó: se rearma ahora
                nueva_estructura_f(S["f"], S["rng"], S)
            st.rerun()


def panel_dios(S):
    cfg = cfg_primera(S)
    empezo = S["fecha"] > 0 or bool(S["log"])
    _d, _r, _ = asc_elegido(S, formato_efectivo(len(S["b"]["nombres"]), cfg_b(S)["formato"]))
    base_p = len(S["nombres"]) + _d + int(_r)      # equipos de Primera antes de los descensos (con los ascensos de la B)
    if empezo:                       # equipos con los que se jugará la temporada que viene (según lo ya guardado)
        n_p = equipos_objetivo_p(S, base_p - int(cfg["descensos"]))
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
        k, pr = _panel_primera(S, cfg, empezo, n_p, formatos, base_p)
        _panel_nacional(S, k, pr, b_ya, txt_b)
        _panel_federal_a(S, f_ya, txt_f)
        with st.container(border=True):
            _panel_federal_b(S)
        with st.container(border=True):
            _panel_simple(S, "pb", "Primera B", "la Primera Nacional", "la Primera C")
        with st.container(border=True):
            _panel_simple(S, "pc", "Primera C", "la Primera B", "el Promocional")
        with st.container(border=True):
            _panel_simple(S, "pd", "Promocional Amateur", "la Primera C", None)

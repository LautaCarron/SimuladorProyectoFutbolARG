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
from motor.tamanos import MAXIMO, MINIMO, NOMBRES as NOMBRES_TAM, ORDEN as ORDEN_TAM, PASO, camino, objetivos
from ligas.federal import (F_DESC_MAX, F_DIRECTOS_MAX, cfg_federal, nueva_estructura_f,
                           plan_reducido_f)
from ligas.federal_b import (FB_EQUIPOS, activo as fb_activo, cfg_federal_b, destino_descenso_federal_a,
                             pendiente as fb_pendiente)
from ligas.nacional import nueva_estructura_b
from ligas.simples import (ASC_MAX, DESC_MAX, RED_MAX, cfg_simple, desc_auto, descripcion_zonas, hay_zonas,
                           nueva_estructura_liga, plan_simple)
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


def _slider(label, lo, hi, valor, key, **kw):
    """st.slider que no se rompe cuando el mínimo y el máximo coinciden (Streamlit lo rechaza): pasa cuando una liga
    queda con muy pocos equipos. En ese caso muestra el único valor posible y lo devuelve."""
    lo, hi = int(lo), int(hi)
    if hi <= lo:
        st.session_state.pop(key, None)
        st.caption(f"{label}: {lo} (con esta cantidad de equipos no hay otra opción).")
        return lo
    if key in st.session_state:                       # ya tiene valor: se respeta (ajustado si cambió el rango)
        if not lo <= int(st.session_state[key]) <= hi:
            st.session_state[key] = max(lo, min(hi, int(st.session_state[key])))
        return st.slider(label, lo, hi, key=key, **kw)
    return st.slider(label, lo, hi, max(lo, min(hi, int(valor))), key=key, **kw)


def _slider_desc(label, n, tope, valor, key, **kw):
    """Slider de descensos con el límite de que la liga no quede con menos de DESC_LIGA_MIN (14) equipos: con 16 equipos
    hasta 2, con 14 ninguno, con 22 o más el tope de la liga. Si el límite es 0 no hay slider y devuelve 0."""
    lim = tope_descensos(n, tope)
    if lim <= 0:
        st.caption(f"{label}: sin descensos (con {n} equipos la liga quedaría con menos de {DESC_LIGA_MIN}).")
        return 0
    if st.session_state.get(key, 0) > lim:                  # el límite bajó: el valor guardado se ajusta
        st.session_state[key] = lim
    return _slider(label, 0, lim, valor, key, **kw)


def _panel_simple(S, clave, nombre, sube_a, baja_a):
    """Primera B / Primera C: cuántos ascienden directo, cuántos descienden y si hay reducido por un ascenso más.
    Rige ahora si la liga no empezó; si no, desde la próxima temporada (los equipos se reacomodan en el pase)."""
    L, cfg = S[clave], cfg_simple(S, clave)
    ya = L["fecha"] > 0 or bool(L["log"])
    n = len(L["nombres"])
    _titulo(nombre)
    # Promocional con 25 clubes o más (hoy, o por el tamaño elegido): dos zonas, sin reducido ni desempates
    zonas = hay_zonas(n, clave) or hay_zonas(objetivos(S).get(clave) or 0, clave)
    d0 = int(cfg["directos"])
    if zonas:                                           # en zonas "directos" son todos los ascensos (el reducido suma uno)
        d0 = min(ASC_MAX, d0 + int(bool(cfg["reducido"])))
    desc_ini = desc_auto(n) if cfg["descensos"] is None else int(cfg["descensos"])
    d = _slider("Ascienden en total" if zonas else "Ascienden directo", 0, ASC_MAX, d0, key=f"dios_{clave}_directos")
    ds = _slider_desc("Descienden", n, DESC_MAX, desc_ini, f"dios_{clave}_desc") if baja_a else 0
    hay = st.checkbox("Reducido por un ascenso más", value=False if zonas else bool(cfg["reducido"]),
                      key=f"dios_{clave}_reducido", disabled=zonas)
    hay = False if zonas else hay
    m = _slider("Equipos en el reducido", 2, RED_MAX, int(cfg["red_equipos"]), key=f"dios_{clave}_red",
                  disabled=not hay)
    pl = plan_simple(n, d, ds if baja_a else 0, hay, m, zonas=zonas)
    if zonas:
        txt = f"Suben {pl['directos']} en total: {descripcion_zonas(pl['directos'])}"
    else:
        txt = f"Suben {pl['directos']} directo" + ("s" if pl["directos"] != 1 else "")
    if pl["reducido"]:
        txt += (f" y el reducido (del {pl['directos'] + 1}° al {pl['directos'] + pl['equipos']}°) da un ascenso más: "
                f"suben {pl['directos'] + 1} en total")
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
        if st.button(":material/add_circle: Crear Federal B", key="dios_fb_crear", width="stretch", type="primary"):
            cfg["crear"] = True
            st.rerun()
        return
    SFB = S.get("fb")
    ya = bool(SFB) and (SFB["fecha"] > 0 or bool(SFB["log"]))
    if pide:
        if st.button(":material/cancel: Cancelar la creación", key="dios_fb_cancelar", width="stretch"):
            cfg["crear"] = False
            st.rerun()
    else:
        pass
    n_fb = len(SFB["nombres"]) if existe else FB_EQUIPOS
    zona = (n_fb + 1) // 2
    d_b = _slider("Ascienden directo al Federal A", 0, F_DIRECTOS_MAX, int(cfg["directos"]),
                    key="dios_fb_directos")
    hay_red = st.checkbox("Reducido por el último ascenso", value=bool(cfg["reducido"]), key="dios_fb_reducido")
    tope_b = max(2, zona - d_b)                        # todos los que siguen a los directos en la zona Campeonato
    m_b = _slider("Equipos en el reducido", 2, tope_b, int(cfg["red_equipos"]),
                  key="dios_fb_red_equipos", disabled=not hay_red)
    ds_b = _slider_desc("Descienden al Regional", n_fb, F_DESC_MAX, cfg["descensos"], "dios_fb_desc")
    pr = plan_reducido_f(d_b, hay_red, m_b, zona)
    suben = pr["directos"] + (1 if pr["reducido"] else 0)
    n_a = len(S["f"]["nombres"])
    d_a = int(cfg_federal(S)["descensos"])
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


def _seccion(nombre):
    """Cada sección del Modo dios es un desplegable (cerrado al principio) para comprimir la barra lateral."""
    return st.expander(nombre, expanded=False)


def _titulo(nombre, detalle=None):
    """Cabecera de cada sección del Modo dios: el nombre va en el desplegable (ver _seccion); acá sólo el detalle."""


def _panel_primera(S, cfg, empezo, n_p, formatos, base_p):
    """Primera División: formato, descensos y promociones. Devuelve (descensos, promociones) elegidos."""
    with _seccion("Primera División"):
        _titulo("Primera División")
        fmt = st.selectbox("Formato", formatos, format_func=FORMATOS.get, key="dios_formato",
                           index=formatos.index(cfg["formato"] if cfg["formato"] in formatos else formato_posible(cfg["formato"], n_p)))
        k_max = tope_descensos(base_p, DESCENSOS_MAX)      # Primera no puede quedar con menos de DESC_LIGA_MIN equipos
        if st.session_state.get("dios_k", 0) > k_max:         # el límite bajó: el valor guardado se ajusta
            st.session_state["dios_k"] = k_max
        k = _slider("Descienden a la B", 0, k_max, int(cfg["descensos"]), key="dios_k")
        pr = _slider("Promociones", 0, PROMOS_MAX, int(cfg["promociones"]), key="dios_prom")
        tp = tam_zonas_p(n_p)
        N = n_p
        cambio = (fmt != cfg["formato"]) or (k != int(cfg["descensos"])) or (pr != int(cfg["promociones"]))
        if st.button(":material/save: " + ("Guardar para la próxima temporada" if empezo else "Aplicar ahora"),
                     key="dios_aplicar", width="stretch", type="primary", disabled=not cambio):
            cfg["formato"], cfg["descensos"], cfg["promociones"] = fmt, int(k), int(pr)
            if not empezo:
                nueva_estructura(S)                    # Primera no empezó: se rearma con el formato nuevo
                actualizar_promos_b(S)                 # y la B juega las promociones que corresponden
            st.rerun()
        return k, pr


def _panel_nacional(S, k, pr, b_ya, txt_b):
    """Primera Nacional, en orden: formato, ascensos a Primera, reducido y descensos."""
    with _seccion("Primera Nacional"):
        _titulo("Primera Nacional")
        cfg_nac = cfg_b(S)
        objetivo = equipos_objetivo_b(S)
        n_b = objetivo
        # ---------------------------------------------------------------- formato
        # el ida y vuelta sólo se puede elegir con B_MAX_ANUAL equipos o menos (con tantos o menos se juega solo)
        opciones_b = [x for x in FORMATOS_B if x != "anual_ida_vuelta" or n_b <= B_MAX_ANUAL]
        fmt_b = st.selectbox("Formato de la B", opciones_b, format_func=FORMATOS_B.get, key="dios_b_formato",
                             label_visibility="collapsed",
                             index=opciones_b.index(cfg_nac["formato"] if cfg_nac["formato"] in opciones_b else "actual"))
        auto_desc = plan_b(n_b, fmt_b)["desc"]
        plan_fmt = plan_b(n_b, fmt_b)
        if plan_fmt["formato"] == "actual":
            tam = tam_zonas2(n_b)
            zonas = f"{tam[0]} cada una" if len(set(tam)) == 1 else f"{tam[0]}, {tam[1]} y {tam[2]}"
        else:
            pass

        # ---------------------------------------------------------------- ascensos a Primera
        fe_b = formato_efectivo(n_b, fmt_b)                       # formato con el que se jugaría de verdad
        d_def, r_def, m_def = asc_defecto(fe_b, int(k))
        d_ini, r_ini, m_ini = (d_def if cfg_nac["directos"] is None else int(cfg_nac["directos"]),
                               r_def if cfg_nac["reducido"] is None else bool(cfg_nac["reducido"]),
                               m_def if cfg_nac["red_equipos"] is None else int(cfg_nac["red_equipos"]))
        d_b = _slider("Ascienden directo", 0, B_DIRECTOS_MAX, d_ini, key=f"dios_b_directos_{fe_b}")

        # ---------------------------------------------------------------- reducido
        hay_red_b = st.checkbox("Reducido por un ascenso más", value=r_ini, key=f"dios_b_reducido_{fe_b}")
        m_b = _slider("Equipos en el reducido", 2, B_RED_EQUIPOS_MAX, max(2, m_ini),
                        key=f"dios_b_red_equipos_{fe_b}", disabled=not hay_red_b)

        # ---------------------------------------------------------------- descensos
        desc_elegido = cfg_nac["descensos"]
        desc_b = _slider_desc("Descienden de la B", n_b, B_DESC_MAX,
                              auto_desc if desc_elegido is None else desc_elegido, "dios_b_desc")
        plan_nuevo = plan_b(n_b, fmt_b, desc_b)

        # ---------------------------------------------------------------- resumen (depende de todo lo anterior)
        pr_b = plan_reducido_b(d_b, hay_red_b, m_b, n_b, plan_nuevo["desc"])
        d_real = pr_b["directos"]
        suben_b = d_real + (1 if pr_b["reducido"] else 0)
        dif = suben_b - int(k)
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
    with _seccion("Federal A"):
        _titulo("Federal A")
        cfg_fed = cfg_federal(S)
        destino = destino_descenso_federal_a(S)                     # "Federal B" o "Regional Amateur"
        n_f = len(S["f"]["nombres"])
        zona = (n_f + 1) // 2
        d_f = _slider("Ascienden directo", 0, F_DIRECTOS_MAX, int(cfg_fed["directos"]), key="dios_f_directos")
        hay_red = st.checkbox("Reducido por el último ascenso", value=bool(cfg_fed["reducido"]), key="dios_f_reducido")
        tope_f = max(2, zona - d_f)                    # todos los que siguen a los directos en la zona Campeonato
        m_f = _slider("Equipos en el reducido", 2, tope_f, int(cfg_fed["red_equipos"]),
                      key="dios_f_red_equipos", disabled=not hay_red)
        ds_f = _slider_desc(f"Descienden al {destino}", n_f, F_DESC_MAX, cfg_fed["descensos"], "dios_f_desc")
        pr_f = plan_reducido_f(d_f, hay_red, m_f, zona)
        suben_f = d_f + (1 if pr_f["reducido"] else 0)
        cambio_f = (d_f != int(cfg_fed["directos"]) or hay_red != bool(cfg_fed["reducido"])
                    or m_f != int(cfg_fed["red_equipos"]) or int(ds_f) != int(cfg_fed["descensos"]))
        if st.button(":material/save: " + txt_f, key="dios_f_aplicar", width="stretch",
                     type="primary", disabled=not cambio_f):
            cfg_fed["directos"], cfg_fed["reducido"], cfg_fed["red_equipos"], cfg_fed["descensos"] = (
                int(d_f), bool(hay_red), int(m_f), int(ds_f))
            if not f_ya:                               # el Federal no empezó: se rearma ahora
                nueva_estructura_f(S["f"], S["rng"], S)
            st.rerun()


def _panel_tamanos(S):
    """Tamaño objetivo de cada liga: el simulador sube y baja equipos de más (de a pocos por temporada) hasta llegar
    y después lo mantiene fijo. Ver motor/tamanos.py. Va en un formulario: los números se eligen sin que la página
    se recargue y todo se aplica junto al tocar Guardar."""
    _titulo("Tamaño de las ligas")
    obj = objetivos(S)
    actual = {"p": len(S["nombres"]), "b": len(S["b"]["nombres"]), "fa": len(S["f"]["nombres"]),
              "fb": len(S["fb"]["nombres"]) if S.get("fb") else None, "pb": len(S["pb"]["nombres"]),
              "pc": len(S["pc"]["nombres"]), "pd": len(S["pd"]["nombres"])}
    claves = [k for k in ORDEN_TAM if actual[k] is not None]        # el Federal B, sólo si ya existe
    with st.form("dios_tamanos", border=False, enter_to_submit=False):
        elegidos = {}
        for k in claves:
            v = st.number_input(f"{NOMBRES_TAM[k]} · hoy {actual[k]}", min_value=MINIMO[k], max_value=MAXIMO[k],
                                value=obj.get(k), step=1, placeholder="Automático", key=f"dios_tam_{k}")
            elegidos[k] = None if v is None else int(v)
            g = obj.get(k)                                    # lo guardado (el camino se ve después de guardar)
            if g is not None and g != actual[k]:
                c = camino(actual[k], g)
        c1, c2 = st.columns(2)
        guardar = c1.form_submit_button(":material/save: Guardar", type="primary", width="stretch")
        borrar = c2.form_submit_button(":material/restart_alt: Borrar", width="stretch")
    if guardar:
        for k, v in elegidos.items():
            if v is None:
                obj.pop(k, None)
            else:
                obj[k] = v
        st.rerun()
    if borrar and obj:
        obj.clear()
        for k in ORDEN_TAM:
            st.session_state.pop(f"dios_tam_{k}", None)
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
        k, pr = _panel_primera(S, cfg, empezo, n_p, formatos, base_p)
        _panel_nacional(S, k, pr, b_ya, txt_b)
        _panel_federal_a(S, f_ya, txt_f)
        with _seccion("Federal B"):
            _panel_federal_b(S)
        with _seccion("Primera B"):
            _panel_simple(S, "pb", "Primera B", "la Primera Nacional", "la Primera C")
        with _seccion("Primera C"):
            _panel_simple(S, "pc", "Primera C", "la Primera B", "el Promocional")
        with _seccion("Promocional Amateur"):
            _panel_simple(S, "pd", "Promocional Amateur", "la Primera C", None)
        with _seccion("Tamaño de las ligas"):
            _panel_tamanos(S)

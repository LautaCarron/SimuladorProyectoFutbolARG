"""Modo Manager (Manager Falopa): alta del manager, oficina con ofertas y simulación día por día.

Va en ui/manager.py. Usa el mismo estado S del simulador y el mismo calendario (jugar_proximo_dia),
y guarda el manager aparte, en st.session_state["manager"], para que Reiniciar / Nueva temporada
del simulador no lo borren. La lógica de ofertas está en motor/ofertas.py.

Punto de entrada: modo_manager(S, P, acumular, volatilidad)  (ver el bloque al final del archivo).

  * Sin manager cargado -> formulario de alta (datos, perfil, global y cómo arrancás).
  * Con manager         -> controles de día + pestañas Oficina (ofertas) y Carrera.
"""

import datetime as dt

import streamlit as st

from motor.calendario import jugar_proximo_dia, proximos, texto_dia
from motor.ofertas import (
    GLOBAL_MAX,
    GLOBAL_MIN,
    PRESETS,
    VIGENCIA_DIAS,
    aceptar,
    alcance,
    categoria_de,
    generar_oferta,
    info_club,
    nivel_texto,
    nuevo_dia,
    nuevo_manager_estado,
    objetivo,
    perfil_club,
    rechazar,
    renunciar,
)
from motor.temporada import nueva_temporada
from ui.vista import aviso, chip, crest, esc, norm, seccion

# ---- Opciones ---------------------------------------------------------------
NACIONALIDADES = ["Argentina", "Uruguay", "Chile", "Paraguay", "Bolivia", "Brasil", "Colombia", "Ecuador",
                  "Perú", "Venezuela", "México", "España", "Italia", "Otra"]

FORMACIONES = ["4-4-2", "4-3-3", "4-2-3-1", "3-5-2", "5-3-2", "4-1-4-1", "3-4-3"]

ESTILOS = {
    "Equilibrado": "Sin extremos: se adapta al rival.",
    "Ofensivo": "Presión alta y muchos hombres arriba.",
    "Defensivo": "Bloque bajo y orden atrás.",
    "Contraataque": "Transiciones rápidas y espacios a la espalda.",
    "Posesión": "Pelota al piso y control del partido.",
}

REPUTACIONES = {
    "Desconocido": "Sin antecedentes: arrancás desde abajo.",
    "Ex jugador de ascenso": "Hiciste carrera en el ascenso.",
    "Ex jugador profesional": "Jugaste en Primera y en la B Nacional.",
    "Ex estrella": "Fuiste figura: te llaman los grandes.",
}

DIFICULTADES = {
    "Fácil": "La directiva tiene paciencia: casi no te echan.",
    "Normal": "Te evalúan por objetivos de la temporada.",
    "Difícil": "Mala racha y te echan: la directiva no perdona.",
}

_OCULTAR_SIMULADOR = ('<style>[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] '
                      '{ display: none !important; }</style>')
TOPE_DIAS_HASTA_OFERTA = 60       # "Hasta la próxima oferta" juega como máximo estos días


# ---- Ayudas de interfaz -----------------------------------------------------
def _primer_dia(S):
    prox = proximos(S)
    return min((d for d, _ in prox.values()), default=dt.date.today())


def _volver_al_inicio():
    st.session_state.pop("afa_pantalla", None)
    if "modo" in st.query_params:
        del st.query_params["modo"]
    st.rerun()


def _chips_alcance(S, g):
    al = alcance(S, g)
    if not al:
        return chip("Los más grandes de Primera División", "#b7860b")
    return " ".join(chip(f"{cat} · {n} clubes", "#475569")
                    for cat, n in sorted(al.items(), key=lambda kv: -kv[1]))


def _tarjeta_club(S, club):
    cat, media, puesto, total = info_club(S, club)
    with st.container(border=True):
        st.markdown(
            f'<div class="team-head">{crest(club, 64)}<div><div class="tn">{esc(club)}</div>'
            f'<div style="margin-top:6px">{chip(cat)} '
            f'{chip(perfil_club(puesto, total), "#475569")}</div></div></div>',
            unsafe_allow_html=True)
        m1, m2 = st.columns(2)
        m1.metric("Media del equipo", f"{media:.1f}")
        m2.metric("Puesto por media", f"{puesto}° de {total}")


def _elegir_club(S):
    """Categoría + buscador de club. Devuelve el club elegido o None."""
    from motor.ofertas import ligas
    todas = ligas(S)
    categorias = list(todas)
    categoria = st.segmented_control("Categoría", categorias, default=categorias[0],
                                     key="mgr_cat") or categorias[0]
    L, nombres = todas[categoria]
    lista = sorted(nombres, key=norm)
    if categoria == "Regional Amateur":
        region = dict(zip(L["nombres"], L["region_de"]))
        fmt = lambda n: f"{n} · {region[n]}"
    else:
        fmt = str
    club = st.selectbox(":material/search: Club", lista, index=None, format_func=fmt,
                        placeholder="Escribí o elegí un club…", key=f"mgr_club_{categoria}")
    if club:
        _tarjeta_club(S, club)
    return club


# ---- Alta del manager -------------------------------------------------------
def alta_manager(S):
    seccion("Crear tu manager", "Cargá tus datos y elegí cómo arrancás tu carrera", "#b7860b")

    st.markdown('<div class="mlab">Datos personales</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    nombre = c1.text_input("Nombre", key="mgr_nombre", max_chars=30, placeholder="Ej: Marcelo")
    apellido = c2.text_input("Apellido", key="mgr_apellido", max_chars=30, placeholder="Ej: Gallardo")
    c3, c4 = st.columns(2)
    edad = c3.number_input("Edad", min_value=25, max_value=75, value=40, step=1, key="mgr_edad")
    nacionalidad = c4.selectbox("Nacionalidad", NACIONALIDADES, index=0, key="mgr_nac")

    st.markdown('<div class="mlab" style="margin-top:14px">Perfil de entrenador</div>',
                unsafe_allow_html=True)
    c5, c6 = st.columns(2)
    formacion = c5.selectbox("Formación preferida", FORMACIONES, index=1, key="mgr_form")
    estilo = c6.selectbox("Estilo de juego", list(ESTILOS), index=0, key="mgr_estilo")
    st.caption(ESTILOS[estilo])
    dificultad = st.segmented_control("Dificultad", list(DIFICULTADES), default="Normal",
                                      key="mgr_dif") or "Normal"
    st.caption(DIFICULTADES[dificultad])

    # ---- Global: por reputación o a mano
    st.markdown('<div class="mlab" style="margin-top:14px">Global del manager</div>', unsafe_allow_html=True)
    reputacion = st.segmented_control("Reputación", list(REPUTACIONES), default="Desconocido",
                                      key="mgr_rep") or "Desconocido"
    st.caption(REPUTACIONES[reputacion])
    modo_g = st.radio("Cómo se define el global", ["Según la reputación", "A mano"], horizontal=True,
                      key="mgr_glob_modo", label_visibility="collapsed")
    if modo_g == "A mano":
        glob = st.slider("Global", GLOBAL_MIN, GLOBAL_MAX, PRESETS[reputacion], key="mgr_glob",
                         help="Es la misma escala que la media de los clubes: cuanto más alto, "
                              "de clubes más grandes te llaman.")
    else:
        glob = PRESETS[reputacion]
    st.markdown(chip(f"Global {glob} · {nivel_texto(glob)}", "#b7860b") + " " + _chips_alcance(S, glob),
                unsafe_allow_html=True)
    st.caption("Los clubes que te llaman son los que tienen una media parecida a tu global.")

    # ---- Cómo arrancás
    st.markdown('<div class="mlab" style="margin-top:14px">Cómo arrancás</div>', unsafe_allow_html=True)
    inicio = st.radio("Modo de inicio", ["Libre · recibir ofertas", "Elegir un equipo"],
                      key="mgr_inicio", label_visibility="collapsed", horizontal=True)
    libre = inicio.startswith("Libre")
    club = None
    if libre:
        aviso("Empezás sin club. Mientras simulás día por día te van a llegar ofertas a la <b>oficina</b>, "
              "de clubes que encajen con tu global.")
    else:
        club = _elegir_club(S)

    errores = []
    if not nombre.strip():
        errores.append("Falta el nombre.")
    if not apellido.strip():
        errores.append("Falta el apellido.")
    if not libre and not club:
        errores.append("Elegí un club para arrancar.")
    for e in errores:
        st.caption(f":material/error: {e}")

    b1, b2 = st.columns([1, 2])
    if b1.button(":material/arrow_back: Volver", key="mgr_volver", width="stretch"):
        _volver_al_inicio()
    if b2.button(":material/check: Empezar carrera", key="mgr_ok", type="primary", width="stretch",
                 disabled=bool(errores)):
        M = nuevo_manager_estado(glob)
        M.update(nombre=nombre.strip(), apellido=apellido.strip(), edad=int(edad), nacionalidad=nacionalidad,
                 formacion=formacion, estilo=estilo, reputacion=reputacion, dificultad=dificultad,
                 global_a_mano=(modo_g == "A mano"), hoy=_primer_dia(S))
        if club:                                      # arranca dirigiendo
            M["club"] = club
            M["historial_clubes"].append({"club": club, "categoria": categoria_de(S, club),
                                          "temporada": S["temp"], "desde": M["hoy"], "hasta": None})
        else:                                         # libre: la oficina arranca con una primera oferta
            primera = generar_oferta(S, M, S["rng"], M["hoy"])
            if primera:
                M["ofertas"].append(primera)
        st.session_state["manager"] = M
        st.rerun()


# ---- Simulación día por día -------------------------------------------------
def _jugar_un_dia(S, M, P, acumular):
    """Juega el próximo día del calendario y actualiza la oficina. None si no queda nada por jugar."""
    prox = proximos(S)
    if not prox:
        return None
    hoy = min(d for d, _ in prox.values())
    comps = sorted(c for c, (d, _) in prox.items() if d == hoy)
    jugar_proximo_dia(S, P, acumular)
    M["registro"].append({"dia": hoy, "comps": comps})
    del M["registro"][:-40]
    nuevas, vencidas = nuevo_dia(S, M, hoy, S["rng"])
    return {"dia": hoy, "comps": comps, "nuevas": nuevas, "vencidas": vencidas}


def _mensaje_dia(r):
    partes = [f"Se jugó el {texto_dia(r['dia']).lower()}: {', '.join(r['comps'])}."]
    for o in r["nuevas"]:
        partes.append(f"📩 Nueva oferta en la oficina: <b>{esc(o['club'])}</b>.")
    for o in r["vencidas"]:
        partes.append(f"Venció la oferta de {esc(o['club'])}.")
    return " ".join(partes)


def _controles_dia(S, M, P, acumular, volatilidad):
    prox = proximos(S)
    hoy = min((d for d, _ in prox.values()), default=None)
    libre = not M["club"]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Temporada", S["temp"])
    m2.metric("Próximo día", texto_dia(hoy, False) if hoy else "—")
    m3.metric("Estado", "Libre" if libre else M["club"])
    m4.metric("Global", f"{M['global']} · {nivel_texto(M['global'])}")

    if hoy is None:
        aviso("Terminó la temporada: todas las ligas y copas están cerradas.")
        if st.button(":material/event_repeat: Pasar a la próxima temporada", key="mgr_nueva_temp",
                     type="primary", width="stretch"):
            nueva_temporada(S, volatilidad)
            st.session_state["mgr_msg"] = f"Empezó la temporada {S['temp']}."
            st.rerun()
        return

    b1, b2 = st.columns(2)
    if b1.button(":material/calendar_today: Próximo día", key="mgr_dia", type="primary", width="stretch",
                 help=f"Juega todo lo del {texto_dia(hoy)}"):
        r = _jugar_un_dia(S, M, P, acumular)
        st.session_state["mgr_msg"] = _mensaje_dia(r)
        st.rerun()
    if b2.button(":material/mark_email_unread: Hasta la próxima oferta", key="mgr_hasta_oferta",
                 width="stretch", disabled=not libre,
                 help="Simula días hasta que llegue una oferta nueva a la oficina (o termine la temporada)"):
        jugados, r = 0, None
        while jugados < TOPE_DIAS_HASTA_OFERTA:
            r = _jugar_un_dia(S, M, P, acumular)
            if r is None:
                break
            jugados += 1
            if r["nuevas"]:
                break
        if r is None or not r["nuevas"]:
            st.session_state["mgr_msg"] = f"Pasaron {jugados} días y no llegó ninguna oferta nueva."
        else:
            st.session_state["mgr_msg"] = f"Pasaron {jugados} día{'s' if jugados != 1 else ''}. " + _mensaje_dia(r)
        st.rerun()


# ---- Oficina ----------------------------------------------------------------
def _tarjeta_oferta(S, M, o):
    club = o["club"]
    cat, media, puesto, total = info_club(S, club)
    with st.container(border=True):
        st.markdown(
            f'<div class="team-head">{crest(club, 56)}<div><div class="tn">{esc(club)}</div>'
            f'<div style="margin-top:6px">{chip(cat)} {chip(perfil_club(puesto, total), "#475569")}</div>'
            f'</div></div>', unsafe_allow_html=True)
        st.write(o["mensaje"])
        c1, c2 = st.columns(2)
        c1.metric("Media del club", f"{media:.1f}", delta=f"{media - M['global']:+.1f} vs tu global",
                  delta_color="off")
        c2.metric("Puesto por media", f"{puesto}° de {total}")
        st.caption(f"Objetivo: {objetivo(cat, puesto, total)} · Vence el {texto_dia(o['vence']).lower()}")
        b1, b2 = st.columns(2)
        if b1.button(":material/check: Aceptar", key=f"of_ok_{o['id']}", type="primary", width="stretch"):
            aceptar(S, M, o)
            st.session_state["mgr_msg"] = f"Aceptaste dirigir a <b>{esc(club)}</b>."
            st.rerun()
        if b2.button(":material/close: Rechazar", key=f"of_no_{o['id']}", width="stretch"):
            rechazar(M, o)
            st.rerun()


def _oficina(S, M):
    if M["club"]:
        st.markdown('<div class="mlab">Tu club</div>', unsafe_allow_html=True)
        _tarjeta_club(S, M["club"])
        st.caption("Las ofertas de otros clubes mientras dirigís van a llegar más adelante. "
                   "Por ahora, si renunciás volvés a quedar libre y a recibir ofertas.")
        if st.button(":material/logout: Renunciar al club", key="mgr_renunciar", width="stretch"):
            renunciar(M)
            st.session_state["mgr_msg"] = "Renunciaste: volvés a estar libre."
            st.rerun()
        return
    ofertas = sorted(M["ofertas"], key=lambda o: o["vence"])
    st.markdown(f'<div class="mlab">Ofertas recibidas · {len(ofertas)}</div>', unsafe_allow_html=True)
    if not ofertas:
        aviso("No tenés ofertas por ahora. Simulá días y te van a llegar según tu global "
              f"(<b>{M['global']}</b>). Te llaman clubes de: " + _chips_alcance(S, M["global"]))
        return
    cols = st.columns(2, gap="medium") if len(ofertas) > 1 else [st.container()]
    for i, o in enumerate(ofertas):
        with cols[i % len(cols)]:
            _tarjeta_oferta(S, M, o)
    st.caption(f"Cada oferta dura {VIGENCIA_DIAS} días corridos. Si aceptás una, las demás se caen.")


# ---- Carrera ----------------------------------------------------------------
def _carrera(S, M):
    st.markdown(
        chip(f"{M['nombre']} {M['apellido']} · {M['edad']} años · {M['nacionalidad']}", "#b7860b") + " "
        + chip(f"Formación {M['formacion']}", "#475569") + " " + chip(f"Estilo {M['estilo']}", "#475569") + " "
        + chip(f"Reputación: {M['reputacion']}", "#475569") + " " + chip(f"Dificultad {M['dificultad']}", "#475569")
        + (" " + chip("Global puesto a mano", "#475569") if M.get("global_a_mano") else ""),
        unsafe_allow_html=True)

    st.markdown('<div class="mlab" style="margin-top:14px">Clubes dirigidos</div>', unsafe_allow_html=True)
    if not M["historial_clubes"]:
        st.caption("Todavía no dirigiste ningún club.")
    for h in reversed(M["historial_clubes"]):
        hasta = texto_dia(h["hasta"], False) if h["hasta"] else "hoy"
        st.markdown(f'{crest(h["club"], 22)} **{esc(h["club"])}** · {esc(h["categoria"] or "")} · '
                    f'temporada {h["temporada"]} · desde {texto_dia(h["desde"], False)} hasta {hasta}',
                    unsafe_allow_html=True)

    st.markdown('<div class="mlab" style="margin-top:14px">Últimos días jugados</div>', unsafe_allow_html=True)
    if not M["registro"]:
        st.caption("Todavía no se jugó ningún día.")
    for x in reversed(M["registro"][-10:]):
        st.caption(f"{texto_dia(x['dia'])}: {', '.join(x['comps'])}")

    b1, b2 = st.columns(2)
    if b1.button(":material/edit: Editar datos", key="mgr_editar", width="stretch"):
        del st.session_state["manager"]
        st.rerun()
    if b2.button(":material/home: Volver al inicio", key="mgr_inicio_btn", width="stretch"):
        _volver_al_inicio()


# ---- Punto de entrada -------------------------------------------------------
def modo_manager(S, P, acumular, volatilidad):
    st.markdown(_OCULTAR_SIMULADOR, unsafe_allow_html=True)
    M = st.session_state.get("manager")
    if not M:
        alta_manager(S)
        return
    seccion("Manager Falopa", f"{M['nombre']} {M['apellido']}", "#b7860b")
    msg = st.session_state.pop("mgr_msg", None)
    if msg:
        aviso(msg)
    _controles_dia(S, M, P, acumular, volatilidad)
    tab_of, tab_car = st.tabs(["Oficina", "Carrera"])
    with tab_of:
        _oficina(S, M)
    with tab_car:
        _carrera(S, M)


# En simuladorafa.py, justo después de `S = st.session_state.S` (P, acumular y volatilidad ya existen):
#
#     if st.session_state.get("afa_pantalla") == "manager" or st.query_params.get("modo") == "manager":
#         from ui.manager import modo_manager
#         modo_manager(S, P, acumular, volatilidad)
#         st.stop()

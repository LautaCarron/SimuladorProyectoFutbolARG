"""Modo Manager (Manager Falopa): alta del manager, oficina con ofertas y carrera.

Va en ui/manager.py. En modo manager se muestra el simulador COMPLETO (ligas, copas, calendario,
"Próximo día", "Simular todo"... todo funciona igual que en el modo simulación) y se suma una pestaña
"Manager" con la oficina, tu club y la carrera.

Las ofertas y los ascensos no dependen de qué botón uses: en cada ejecución se mira qué días del
calendario ya se jugaron por completo y, por cada día nuevo, se corre el motor de ofertas
(sincronizar_manager). Así andan igual con "Próximo día", con "Próxima fecha" de cada liga, con
"Simular todo" o con "Hasta la próxima novedad".

Estado: st.session_state["manager"] (aparte de S, así Reiniciar / Nueva temporada no lo borran).
Las ofertas llegan siempre; algunas son para la Reserva y el club puede subirte a DT del primer
equipo (lógica en motor/ofertas.py).

Se engancha desde simuladorafa.py (ver los bloques al final de este archivo).
"""

import datetime as dt
import uuid

import streamlit as st

from motor.calendario import jugar_proximo_dia, proximos, texto_dia
from motor.ofertas import (
    GLOBAL_MAX,
    GLOBAL_MIN,
    PRESETS,
    ROLES,
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
from ui.vista import aviso, chip, crest, esc, eventos_calendario, fila_partido_html, norm, render_ficha, seccion
from ui.vista.partidos import todos_los_partidos

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

TOPE_DIAS = 60                    # "Hasta la próxima novedad" / "hasta mi próximo partido": máximo de días


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


def _chip_rol(rol):
    return chip(ROLES[rol], "#b7860b" if rol == "primer_equipo" else "#0369a1")


def _tarjeta_club(S, club, rol=None):
    cat, media, puesto, total = info_club(S, club)
    with st.container(border=True):
        st.markdown(
            f'<div class="team-head">{crest(club, 64)}<div><div class="tn">{esc(club)}</div>'
            f'<div style="margin-top:6px">{chip(cat)} '
            f'{chip(perfil_club(puesto, total), "#475569")}'
            f'{" " + _chip_rol(rol) if rol else ""}</div></div></div>',
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
              "de clubes que encajen con tu global. Algunas son para dirigir la <b>Reserva</b>: si las "
              "aceptás, en algún momento el club echa al DT y te sube al primer equipo.")
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
        if club:                                      # arranca dirigiendo el primer equipo
            M["club"], M["rol"] = club, "primer_equipo"
            M["historial_clubes"].append({"club": club, "categoria": categoria_de(S, club),
                                          "rol": "primer_equipo", "temporada": S["temp"], "desde": M["hoy"],
                                          "hasta": None, "ascendido": None})
        else:                                         # libre: la oficina arranca con una primera oferta
            primera = generar_oferta(S, M, S["rng"], M["hoy"])
            if primera:
                M["ofertas"].append(primera)
        st.session_state["manager"] = M
        st.rerun()


# ---- Sincronización con el calendario del simulador --------------------------
def _dias_jugados(S):
    """{día: [competiciones]} de los días del calendario cuyo programa ya se jugó completo."""
    dias = {}
    for d, liga, _n, jugada in eventos_calendario(S):
        if d is None:
            continue
        r = dias.setdefault(d, {"comps": [], "todo": True})
        r["comps"].append(liga)
        r["todo"] = r["todo"] and jugada
    return {d: r["comps"] for d, r in dias.items() if r["todo"]}


def sincronizar_manager(S, M):
    """Corre el motor de ofertas por cada día que se jugó por completo desde la última vez.
    Sirve para cualquier forma de jugar. Devuelve los textos de las novedades (ofertas nuevas que
    siguen vigentes y ascensos) y los deja anotados en M["novedades"]."""
    uid = S.setdefault("_mgr_uid", uuid.uuid4().hex)       # cambia si se reinicia el simulador
    jugados = _dias_jugados(S)
    sync = M.get("sync")
    if not sync or sync["uid"] != uid:
        M["sync"] = {"uid": uid, "dias": set(jugados)}     # lo ya jugado antes no genera ofertas
        return []
    textos = []
    pendientes = []
    for d in sorted(x for x in jugados if x not in sync["dias"]):
        sync["dias"].add(d)
        M["registro"].append({"dia": d, "comps": sorted(set(jugados[d]))})
        pendientes.append((d, nuevo_dia(S, M, d, S["rng"])))
    del M["registro"][:-40]
    vigentes = {o["id"] for o in M["ofertas"]}
    for d, r in pendientes:
        for t in r["eventos"]:
            textos.append((d, f"📣 {t}"))
        for o in r["nuevas"]:
            if o["id"] in vigentes:
                textos.append((d, f"📩 Nueva oferta de {o['club']} ({ROLES[o['rol']]})."))
    M.setdefault("novedades", []).extend({"dia": d, "texto": t} for d, t in textos)
    del M["novedades"][:-30]
    return [t for _, t in textos]


def _partidos_club(club):
    return [p for p in todos_los_partidos() if club in (p["local"], p["visita"])]


def _jugar_dias(S, M, P, acumular, hasta):
    """Juega días del calendario hasta que `hasta(textos, nuevos_partidos)` sea verdadero (o no quede
    nada / se llegue al tope). Devuelve (días jugados, textos, partidos nuevos del club)."""
    antes = {id(p) for p in _partidos_club(M["club"])} if M["club"] else set()
    jugados, textos, nuevos = 0, [], []
    while jugados < TOPE_DIAS and proximos(S):
        jugar_proximo_dia(S, P, acumular)
        jugados += 1
        textos += sincronizar_manager(S, M)
        if M["club"]:
            nuevos = [p for p in _partidos_club(M["club"]) if id(p) not in antes]
        if hasta(textos, nuevos):
            break
    return jugados, textos, nuevos


# ---- Panel de la pestaña Manager ----------------------------------------------
def _controles(S, M, P, acumular):
    prox = proximos(S)
    hoy = min((d for d, _ in prox.values()), default=None)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Temporada", S["temp"])
    m2.metric("Próximo día", texto_dia(hoy, False) if hoy else "—")
    m3.metric("Estado", M["club"] or "Libre", delta=ROLES[M["rol"]] if M["club"] else None, delta_color="off")
    m4.metric("Global", f"{M['global']} · {nivel_texto(M['global'])}")
    if hoy is None:
        aviso("Terminó la temporada. Pasá a la siguiente con <b>Nueva temporada</b> (arriba).")
    if st.button(":material/mark_email_unread: Simular hasta la próxima novedad", key="mgr_hasta_oferta",
                 width="stretch", disabled=hoy is None,
                 help="Juega días hasta que llegue una oferta nueva o pase algo en tu club "
                      "(o termine la temporada). Los partidos se simulan igual que en el simulador."):
        jugados, textos, _ = _jugar_dias(S, M, P, acumular, lambda t, n: bool(t))
        st.session_state["mgr_msg"] = (f"Pasaron {jugados} día{'s' if jugados != 1 else ''}. "
                                       + (" ".join(esc(t) for t in textos) if textos else "Sin novedades."))
        st.rerun()


def _mi_club(S, M, P, acumular, abierta):
    club = M["club"]
    st.markdown(f"Dirigís a **{esc(club)}** como {ROLES[M['rol']]}. Los partidos se simulan con los botones "
                "de arriba o de cada liga; este botón avanza hasta que juegue tu club.")
    if st.button(":material/sports_soccer: Simular hasta el próximo partido de mi club", key="mgr_prox_partido",
                 type="primary", width="stretch", disabled=not proximos(S)):
        jugados, textos, nuevos = _jugar_dias(S, M, P, acumular, lambda t, n: bool(n))
        st.session_state["mgr_ultimo"] = [p for p in nuevos]
        st.session_state["mgr_msg"] = (f"Pasaron {jugados} día{'s' if jugados != 1 else ''}. "
                                       + " ".join(esc(t) for t in textos))
        st.rerun()
    ultimo = st.session_state.get("mgr_ultimo")
    if ultimo:
        st.markdown('<div class="mlab">Último partido de tu club</div>', unsafe_allow_html=True)
        for p in ultimo:
            st.markdown(fila_partido_html(p, abierto=True), unsafe_allow_html=True)
    if abierta:
        with st.container(border=True):
            render_ficha(club, "mgr")


def panel_manager(S, P, acumular):
    M = st.session_state["manager"]
    seccion("Manager Falopa", f"{M['nombre']} {M['apellido']}", "#b7860b")
    msg = st.session_state.pop("mgr_msg", None)
    if msg:
        aviso(msg)
    _controles(S, M, P, acumular)
    etiquetas = ["Oficina"] + (["Mi club"] if M["club"] else []) + ["Carrera"]
    tabs = dict(zip(etiquetas, st.tabs(etiquetas, key="tabs_mgr", on_change="rerun")))
    with tabs["Oficina"]:
        _oficina(S, M)
    if "Mi club" in tabs:
        with tabs["Mi club"]:
            _mi_club(S, M, P, acumular, tabs["Mi club"].open is not False)
    with tabs["Carrera"]:
        _carrera(S, M)


def render(ctx):
    """Pestaña "Manager" del simulador (sólo en modo manager)."""
    if getattr(ctx, "modo_mgr", False) and ctx._abierta(ctx.tab_mgr):
        with ctx.tab_mgr:
            panel_manager(ctx.S, ctx.P, ctx.acumular)


# ---- Oficina ----------------------------------------------------------------
def _tarjeta_oferta(S, M, o):
    club = o["club"]
    cat, media, puesto, total = info_club(S, club)
    with st.container(border=True):
        st.markdown(
            f'<div class="team-head">{crest(club, 56)}<div><div class="tn">{esc(club)}</div>'
            f'<div style="margin-top:6px">{chip(cat)} {chip(perfil_club(puesto, total), "#475569")} '
            f'{_chip_rol(o["rol"])}</div></div></div>', unsafe_allow_html=True)
        st.write(o["mensaje"])
        if o["rol"] == "reserva":
            st.caption("Entrás a la Reserva. Si el club hace un cambio de técnico, podés subir al primer equipo.")
        if M["club"]:
            st.caption(f"Si aceptás, dejás {M['club']}.")
        c1, c2 = st.columns(2)
        c1.metric("Media del club", f"{media:.1f}", delta=f"{media - M['global']:+.1f} vs tu global",
                  delta_color="off")
        c2.metric("Puesto por media", f"{puesto}° de {total}")
        st.caption(f"Objetivo: {objetivo(cat, puesto, total, o['rol'])} · "
                   f"Vence el {texto_dia(o['vence']).lower()}")
        b1, b2 = st.columns(2)
        if b1.button(":material/check: Aceptar", key=f"of_ok_{o['id']}", type="primary", width="stretch"):
            aceptar(S, M, o)
            st.session_state["mgr_msg"] = f"Aceptaste: {ROLES[o['rol']]} en <b>{esc(club)}</b>."
            st.rerun()
        if b2.button(":material/close: Rechazar", key=f"of_no_{o['id']}", width="stretch"):
            rechazar(M, o)
            st.rerun()


def _oficina(S, M):
    if M["club"]:
        st.markdown('<div class="mlab">Tu club</div>', unsafe_allow_html=True)
        _tarjeta_club(S, M["club"], M["rol"])
        if M["rol"] == "reserva":
            st.caption(f"Llevás {M['dias_en_rol']} días en la Reserva. Si el club hace un cambio de técnico, "
                       "te suben al primer equipo (antes, si le va mal en la liga).")
        if st.button(":material/logout: Renunciar al club", key="mgr_renunciar", width="stretch"):
            renunciar(M)
            st.session_state["mgr_msg"] = "Renunciaste: volvés a estar libre."
            st.rerun()
    ofertas = sorted(M["ofertas"], key=lambda o: o["vence"])
    titulo = "Ofertas de otros clubes" if M["club"] else "Ofertas recibidas"
    st.markdown(f'<div class="mlab" style="margin-top:14px">{titulo} · {len(ofertas)}</div>',
                unsafe_allow_html=True)
    if not ofertas:
        aviso("No tenés ofertas por ahora. Simulá días: te siguen llegando según tu global "
              f"(<b>{M['global']}</b>). Te llaman clubes de: " + _chips_alcance(S, M["global"]))
        return
    cols = st.columns(2, gap="medium") if len(ofertas) > 1 else [st.container()]
    for i, o in enumerate(ofertas):
        with cols[i % len(cols)]:
            _tarjeta_oferta(S, M, o)
    st.caption(f"Cada oferta dura {VIGENCIA_DIAS} días corridos. Si aceptás una, las demás se caen.")
    if M.get("novedades"):
        st.markdown('<div class="mlab" style="margin-top:14px">Novedades recientes</div>', unsafe_allow_html=True)
        for n in reversed(M["novedades"][-6:]):
            st.caption(f"{texto_dia(n['dia'], False)} · {n['texto']}")


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
        sube = (f' · subió a DT del primer equipo el {texto_dia(h["ascendido"], False)}'
                if h.get("ascendido") else "")
        st.markdown(f'{crest(h["club"], 22)} **{esc(h["club"])}** · {esc(h["categoria"] or "")} · '
                    f'{ROLES[h.get("rol", "primer_equipo")]} · temporada {h["temporada"]} · '
                    f'desde {texto_dia(h["desde"], False)} hasta {hasta}{sube}', unsafe_allow_html=True)

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


# ---- Cómo engancharlo en simuladorafa.py -------------------------------------------
# 1) Justo después de `S = st.session_state.S` (reemplaza el bloque anterior de modo_manager):
#
#     modo_mgr = st.session_state.get("afa_pantalla") == "manager" or st.query_params.get("modo") == "manager"
#     if modo_mgr:
#         from ui.manager import alta_manager, sincronizar_manager
#         if not st.session_state.get("manager"):
#             alta_manager(S)                      # primero se cargan los datos del manager
#             st.stop()
#         for _txt in sincronizar_manager(S, st.session_state["manager"]):
#             st.toast(_txt)
#
# 2) En las pestañas de arriba se suma "Manager" al principio cuando modo_mgr es verdadero.
# 3) Se agrega `from ui import manager as ui_manager` y `ui_manager` a la lista que recorre render(ctx).

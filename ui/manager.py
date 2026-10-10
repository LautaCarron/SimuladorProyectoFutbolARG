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

from motor.calendario import dia_partido, jugar_proximo_dia, proximos, texto_dia
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
from motor.eventos import EVENTOS, descripcion_opcion, resolver, sortear
from motor.nucleo import ESTILOS_JUEGO, TACTICAS, con_tacticas, tactica_total
from motor.relaciones import (
    CAMA_ATAQUE,
    CAMA_CONTROL,
    CAMA_DEFENSA,
    DE_CLUB,
    ETIQUETAS,
    GLOBALES,
    KARMA_DEJAR_CLUB,
    KARMA_RENUNCIAR,
    UMBRAL_CAMA,
    aplicar_partido,
    asegurar,
    cambiar,
    clave_partido,
    con_cama,
    descripcion,
    efecto_cama,
    entrar_club,
    revisar_despido,
    salir_club,
    umbral_despido,
)
from ui.vista import aviso, chip, crest, esc, eventos_calendario, fila_partido_html, norm, render_ficha, seccion
from ui.vista.calendario import _cal_partidos
from ui.vista.partidos import categoria_de as categoria_rival, todos_los_partidos

# ---- Opciones ---------------------------------------------------------------
NACIONALIDADES = ["Argentina", "Uruguay", "Chile", "Paraguay", "Bolivia", "Brasil", "Colombia", "Ecuador",
                  "Perú", "Venezuela", "México", "España", "Italia", "Otra"]

FORMACIONES = list(TACTICAS)          # cada formación es una táctica que cambia cómo se juega (motor/nucleo.py)

ESTILOS = {n: v[3] for n, v in ESTILOS_JUEGO.items()}      # estilo -> descripción (efectos en motor/nucleo.py)

REPUTACIONES = {
    "Desconocido": "Sin antecedentes: arrancás desde abajo.",
    "Ex jugador de ascenso": "Hiciste carrera en el ascenso.",
    "Ex jugador profesional": "Jugaste en Primera y en la B Nacional.",
    "Ex estrella": "Fuiste figura: te llaman los grandes.",
}

TOPE_DIAS = 60                    # "Hasta la próxima novedad" / "hasta mi próximo partido": máximo de días


# ---- Ayudas de interfaz -----------------------------------------------------
def _primer_dia(S):
    prox = proximos(S)
    return min((d for d, _ in prox.values()), default=dt.date.today())


def _pct(x):
    return f"{(x - 1) * 100:+.0f}%"


def _efectos(atk, dfn, ctl):
    mid = f"Mediocampo {ctl:+.1f}" if abs(ctl) >= 0.05 else "Mediocampo neutro"
    return f"Goles a favor {_pct(atk)} · Goles en contra {_pct(dfn)} · {mid}"


def efectos_estilo(nombre):
    atk, dfn, ctl, _ = ESTILOS_JUEGO[nombre]
    return _efectos(atk, dfn, ctl)


def efectos_tactica(nombre):
    """Resumen legible de lo que hace una táctica."""
    atk, dfn, ctl, _ = TACTICAS[nombre]
    return (f"Goles a favor {_pct(atk)} · Goles en contra {_pct(dfn)} · "
            f"Mediocampo {'+' if ctl > 0 else ''}{ctl:g}" if ctl else
            f"Goles a favor {_pct(atk)} · Goles en contra {_pct(dfn)} · Mediocampo neutro")


def aplicar_tactica(S, M):
    """Carga en el generador de azar del simulador la táctica del club del manager. Sólo juega con
    táctica si dirige al primer equipo (en la Reserva no define cómo juega el primer equipo)."""
    tab = {}
    if M.get("club") and M.get("rol") == "primer_equipo" and M.get("formacion") in TACTICAS:
        base = tactica_total(M["formacion"], M.get("estilo"))                # formación + estilo de juego
        tab = {M["club"]: con_cama(base, efecto_cama(M))}                    # el plantel puede hacerte la cama
    S["rng"] = con_tacticas(S["rng"], tab)


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
    formacion = c5.selectbox("Formación (táctica)", FORMACIONES, index=0, key="mgr_form")
    estilo = c6.selectbox("Estilo de juego", list(ESTILOS), index=0, key="mgr_estilo")
    st.caption(f"{formacion}: {TACTICAS[formacion][3]} ({efectos_tactica(formacion)}). "
               f"{estilo}: {ESTILOS[estilo]} ({efectos_estilo(estilo)}). "
               "Las dos se pueden cambiar cuando quieras desde la pestaña Mi club.")

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
                 formacion=formacion, estilo=estilo, reputacion=reputacion,
                 global_a_mano=(modo_g == "A mano"), hoy=_primer_dia(S))
        asegurar(M)                                   # relaciones iniciales (según la reputación)
        if club:                                      # arranca dirigiendo el primer equipo
            M["club"], M["rol"] = club, "primer_equipo"
            entrar_club(S, M, club)
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
    aplicar_tactica(S, M)                                   # la táctica viaja en el generador de azar
    asegurar(M)
    if M["club"] and M["rel"]["dirigencia"] is None:        # carrera empezada antes de que existieran las relaciones
        entrar_club(S, M, M["club"])
    uid = S.setdefault("_mgr_uid", uuid.uuid4().hex)       # cambia si se reinicia el simulador
    jugados = _dias_jugados(S)
    sync = M.get("sync")
    if not sync or sync["uid"] != uid:
        M["sync"] = {"uid": uid, "dias": set(jugados)}     # lo ya jugado antes no genera ofertas
        M["partidos_vistos"] = {clave_partido(p) for p in _partidos_club(M["club"])} if M["club"] else set()
        return []
    if M.get("evento") and not M["club"]:                  # el evento era de un club que ya no dirigís
        M["evento"] = None
    if M.get("evento"):                                    # evento pendiente: los días siguientes esperan
        return []
    textos = []
    pendientes = []
    for d in sorted(x for x in jugados if x not in sync["dias"]):
        sync["dias"].add(d)
        M["registro"].append({"dia": d, "comps": sorted(set(jugados[d]))})
        r = nuevo_dia(S, M, d, S["rng"])
        r["relaciones"] = _relaciones_dia(S, M, d)         # partidos del día: hinchada, dirigencia, plantel...
        pendientes.append((d, r))
        if M.get("evento"):                                # salió un evento: se frena acá; el resto espera
            break
    del M["registro"][:-40]
    vigentes = {o["id"] for o in M["ofertas"]}
    for d, r in pendientes:
        for t in r["relaciones"]:
            textos.append((d, t))
        for t in r["eventos"]:
            textos.append((d, f"📣 {t}"))
        for o in r["nuevas"]:
            if o["id"] in vigentes:
                textos.append((d, f"📩 Nueva oferta de {o['club']} ({ROLES[o['rol']]})."))
    M.setdefault("novedades", []).extend({"dia": d, "texto": t} for d, t in textos)
    del M["novedades"][:-30]
    return [t for _, t in textos]


def proximo_partido_club(S, club):
    """Próximo partido sin jugar del club en cualquier competencia (liga, Copa Argentina, Supercopa,
    copas CONMEBOL, Mundial), según el calendario. None si no hay ninguno programado todavía."""
    for _d, liga, n, jugada in eventos_calendario(S):         # ya vienen ordenados por día
        if jugada:
            continue
        try:
            partidos = _cal_partidos(S, liga, n)
        except Exception:
            continue
        for p in partidos:
            if p["gl"] is None and club in (p["local"], p["visita"]):
                return p
    return None


def _datos_rival(S, club, rival):
    partes = []
    cat = categoria_rival(rival)
    if cat:
        partes.append(cat)
    if categoria_de(S, rival) and categoria_de(S, club):
        partes.append(f"media {info_club(S, rival)[1]:.1f} (la tuya: {info_club(S, club)[1]:.1f})")
    return " · ".join(partes)


def _tarjeta_proximo(S, M):
    """Contra quién juega el club en su próximo partido."""
    club = M["club"]
    st.markdown(f'<div class="mlab">Próximo partido de {esc(club)}</div>', unsafe_allow_html=True)
    p = proximo_partido_club(S, club)
    if p is None:
        st.caption("No hay partidos programados para tu club por ahora: se conocen cuando termina "
                   "la ronda anterior o cuando arranca la próxima temporada.")
        return
    rival = p["visita"] if p["local"] == club else p["local"]
    cond = "en cancha neutral" if p["neutral"] else "de local" if p["local"] == club else "de visitante"
    st.markdown(fila_partido_html(p), unsafe_allow_html=True)
    st.markdown(f"Jugás contra **{esc(rival)}**, {cond}. " + esc(_datos_rival(S, club, rival)))
    if M["rol"] == "reserva":
        st.caption("Como DT de la Reserva no dirigís este partido: lo dirige el DT del primer equipo.")


def _relaciones_dia(S, M, d):
    """Mueve las relaciones con los partidos de mi club que ya se jugaron hasta el día `d` (sólo cuentan
    cuando sos DT del primer equipo) y revisa si te echan. Devuelve los textos de lo que pasó."""
    avisos = []
    if not M["club"]:
        return avisos
    nuevos = sorted((p for p in _partidos_club(M["club"])
                     if clave_partido(p) not in M["partidos_vistos"] and (dia_partido(S, p) or d) <= d),
                    key=lambda p: dia_partido(S, p) or d)
    for p in nuevos:
        M["partidos_vistos"].add(clave_partido(p))
        if M["rol"] == "primer_equipo":
            M["rel_log"].append({"dia": dia_partido(S, p) or d, "texto": aplicar_partido(S, M, p)})
    del M["rel_log"][:-12]
    if M["rol"] != "primer_equipo":
        return avisos
    M["dias_dt"] += 1
    plantel = M["rel"]["plantel"]
    if efecto_cama(M) > 0 and not M.get("cama_avisada"):
        M["cama_avisada"] = True
        avisos.append(f"🛏️ El plantel te está haciendo la cama: el equipo rinde peor ({plantel:.0f}% de relación).")
    elif M.get("cama_avisada") and plantel >= UMBRAL_CAMA + 10:
        M["cama_avisada"] = False
        avisos.append("🤝 El plantel volvió a bancarte.")
    despido = revisar_despido(S, M, S["rng"])
    if despido:
        M["cama_avisada"] = False
        avisos.append(f"🚨 {despido}")
    else:
        evento = sortear(S, M, S["rng"], bool(nuevos))      # a veces pasa algo que hay que decidir
        if evento:
            M["evento"] = evento
            avisos.append(f"⏸ Evento para resolver: {EVENTOS[evento['id']]['titulo']}.")
    return avisos


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
        if M.get("evento") or hasta(textos, nuevos):       # un evento pausa la simulación
            break
    return jugados, textos, nuevos


# ---- Panel de la pestaña Manager ----------------------------------------------
def _msg_dias(jugados, textos, vacio=""):
    return (f"Pasaron {jugados} día{'s' if jugados != 1 else ''}. "
            + (" ".join(esc(t) for t in textos) if textos else vacio))


def _cb_hasta_novedad(S, M, P, acumular):
    jugados, textos, _ = _jugar_dias(S, M, P, acumular, lambda t, n: bool(t))
    st.session_state["mgr_msg"] = _msg_dias(jugados, textos, "Sin novedades.")


def _cb_prox_partido(S, M, P, acumular):
    jugados, textos, nuevos = _jugar_dias(S, M, P, acumular, lambda t, n: bool(n))
    st.session_state["mgr_ultimo"] = list(nuevos)
    st.session_state["mgr_msg"] = _msg_dias(jugados, textos)


def _cb_evento(S, M, indice):
    st.session_state["mgr_msg"] = "Decidiste: " + esc(resolver(S, M, indice))


def pantalla_evento(S, M):
    """Pantalla que reemplaza a toda la app mientras hay un evento sin resolver (la simulación queda en pausa)."""
    pend = M["evento"]
    ev = EVENTOS[pend["id"]]
    rel = M["rel"]
    seccion("Evento", ev["titulo"], "#b7860b")
    st.markdown(f'<div class="mlab">{esc(texto_dia(pend["dia"]))} · {esc(M["club"])}</div>', unsafe_allow_html=True)
    st.markdown(ev["texto"](S, M))
    m = st.columns(5)
    for col, clave in zip(m, ("hinchada", "dirigencia", "plantel", "economia", "tapia")):
        col.metric(ETIQUETAS[clave], f"{rel[clave]:.0f}%")
    st.markdown('<div class="mlab" style="margin-top:12px">¿Qué hacés?</div>', unsafe_allow_html=True)
    for i, op in enumerate(ev["opciones"]):
        with st.container(border=True):
            st.markdown(f"**{op['texto']}**")
            st.caption(descripcion_opcion(op))
            st.button("Elegir esta opción", key=f"ev_op_{pend['id']}_{i}", width="stretch",
                      type="primary" if i == 0 else "secondary", on_click=_cb_evento, args=(S, M, i))
    st.caption("⏸ La simulación está en pausa hasta que decidas.")


def simular_hasta_pausa(S, P, acumular):
    """"Simular todo" del modo manager: juega día por día hasta que termina la temporada o aparece un evento
    (que hay que resolver antes de seguir)."""
    M = st.session_state["manager"]
    jugados, textos = 0, []
    while proximos(S) and jugados < 400:
        jugar_proximo_dia(S, P, acumular)
        jugados += 1
        textos += sincronizar_manager(S, M)
        if M.get("evento"):
            break
    st.session_state["mgr_msg"] = _msg_dias(jugados, textos)


def _cb_aceptar(S, M, o):
    if M["club"]:
        cambiar(M, "karma", KARMA_DEJAR_CLUB)               # dejás un club por otro
    aceptar(S, M, o)
    entrar_club(S, M, o["club"])
    M["partidos_vistos"] = set(M.get("partidos_vistos", ())) | {clave_partido(p) for p in _partidos_club(o["club"])}
    M["cama_avisada"] = False
    st.session_state["mgr_msg"] = f"Aceptaste: {ROLES[o['rol']]} en <b>{esc(o['club'])}</b>."


def _cb_rechazar(M, o):
    rechazar(M, o)


def _cb_renunciar(M):
    renunciar(M)
    salir_club(M)
    cambiar(M, "karma", KARMA_RENUNCIAR)
    M["cama_avisada"] = False
    st.session_state["mgr_msg"] = "Renunciaste: volvés a estar libre."


def _cb_editar():
    st.session_state.pop("manager", None)


def _cb_volver_inicio():
    st.session_state.pop("afa_pantalla", None)
    if "modo" in st.query_params:
        del st.query_params["modo"]


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
    st.button(":material/mark_email_unread: Simular hasta la próxima novedad", key="mgr_hasta_oferta",
              width="stretch", disabled=hoy is None, on_click=_cb_hasta_novedad, args=(S, M, P, acumular),
              help="Juega días hasta que llegue una oferta nueva o pase algo en tu club "
                   "(o termine la temporada). Los partidos se simulan igual que en el simulador.")


def _selector_tactica(S, M):
    st.markdown('<div class="mlab">Táctica y estilo de juego</div>', unsafe_allow_html=True)
    if M["rol"] != "primer_equipo":
        st.caption("Como DT de la Reserva no definís la táctica del primer equipo: la define su DT.")
        return
    actual = M["formacion"] if M["formacion"] in TACTICAS else FORMACIONES[0]
    estilos = list(ESTILOS)
    actual_e = M.get("estilo") if M.get("estilo") in ESTILOS else estilos[0]
    c1, c2 = st.columns(2)
    nueva = c1.selectbox("Formación", FORMACIONES, index=FORMACIONES.index(actual), key="mgr_tactica")
    nuevo_e = c2.selectbox("Estilo de juego", estilos, index=estilos.index(actual_e), key="mgr_estilo_sel")
    if nueva != M["formacion"] or nuevo_e != M.get("estilo"):
        M["formacion"], M["estilo"] = nueva, nuevo_e
        aplicar_tactica(S, M)
    atk, dfn, ctl = tactica_total(nueva, nuevo_e)
    st.caption(f"{nueva}: {TACTICAS[nueva][3]}  \n{nuevo_e}: {ESTILOS[nuevo_e]}  \n"
               f"**Juntas:** {_efectos(atk, dfn, ctl)}. Vale para todos los partidos de tu club (liga y copas) "
               "desde el próximo.")
    with st.expander("Comparar formaciones y estilos"):
        filas = ["| Formación | Goles a favor | Goles en contra | Mediocampo | Perfil |", "|---|---|---|---|---|"]
        for n, (a, d, c, nota) in TACTICAS.items():
            filas.append(f"| {'**' + n + '**' if n == nueva else n} | {_pct(a)} | {_pct(d)} | {c:+g} | {nota} |")
        filas += ["", "| Estilo | Goles a favor | Goles en contra | Mediocampo | Perfil |", "|---|---|---|---|---|"]
        for n, (a, d, c, nota) in ESTILOS_JUEGO.items():
            filas.append(f"| {'**' + n + '**' if n == nuevo_e else n} | {_pct(a)} | {_pct(d)} | {c:+g} | {nota} |")
        st.markdown("\n".join(filas))
        st.caption("El mediocampo es el dominio del medio: cada punto de más (o de menos) mueve el balance del "
                   "partido como si tu equipo tuviera 1 punto más (o menos) de media: alrededor de 0,04 puntos "
                   "por partido, unos 1,5 puntos en una temporada de 42 fechas, y un poco más de goles a favor "
                   "y menos en contra. Entre equipos parejos, ninguna formación ni estilo rinde más que otro "
                   "en puntos: cambia cómo se gana. Las ofensivas ayudan un poco más al favorito; las "
                   "defensivas, al más débil.")


def _mi_club(S, M, P, acumular, abierta):
    club = M["club"]
    st.markdown(f"Dirigís a **{esc(club)}** como {ROLES[M['rol']]}. Los partidos se simulan con los botones "
                "de arriba o de cada liga; este botón avanza hasta que juegue tu club.")
    _selector_tactica(S, M)
    st.button(":material/sports_soccer: Simular hasta el próximo partido de mi club", key="mgr_prox_partido",
              type="primary", width="stretch", disabled=not proximos(S), on_click=_cb_prox_partido,
              args=(S, M, P, acumular))
    ultimo = st.session_state.get("mgr_ultimo")
    if ultimo:
        st.markdown('<div class="mlab">Último partido de tu club</div>', unsafe_allow_html=True)
        for p in ultimo:
            st.markdown(fila_partido_html(p, abierto=True), unsafe_allow_html=True)
    if abierta:
        with st.container(border=True):
            render_ficha(club, "mgr")


CSS_REL = """<style>
.rel-f { margin: 10px 0 14px; }
.rel-h { display: flex; justify-content: space-between; align-items: baseline; font-weight: 600; }
.rel-h small { font-weight: 500; opacity: .65; }
.rel-b { height: 10px; border-radius: 6px; background: rgba(127,127,127,.22); overflow: hidden; margin: 5px 0 2px; }
.rel-b i { display: block; height: 100%; border-radius: 6px; }
</style>"""


def _barra_rel(clave, valor):
    """Una relación de 0 a 100 %: nombre, porcentaje, barra de color y cómo está (Pésima ... Excelente)."""
    if valor is None:
        return (f'<div class="rel-f"><div class="rel-h"><span>{ETIQUETAS[clave]}</span><b>—</b></div>'
                f'<div class="rel-b"></div></div>')
    color = "#dc2626" if valor < 30 else "#f59e0b" if valor < 50 else "#84cc16" if valor < 70 else "#16a34a"
    return (f'<div class="rel-f"><div class="rel-h"><span>{ETIQUETAS[clave]}</span>'
            f'<span><b>{valor:.0f}%</b> <small>{descripcion(valor)}</small></span></div>'
            f'<div class="rel-b"><i style="width:{valor:.0f}%;background:{color}"></i></div></div>')


def _relaciones(S, M):
    rel = asegurar(M)
    st.markdown(CSS_REL, unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown('<div class="mlab">Poder en el fútbol</div>', unsafe_allow_html=True)
        st.markdown("".join(_barra_rel(k, rel[k]) for k in GLOBALES), unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="mlab">{esc(M["club"]) if M["club"] else "Tu club"}</div>', unsafe_allow_html=True)
        if M["club"]:
            st.markdown("".join(_barra_rel(k, rel[k]) for k in DE_CLUB), unsafe_allow_html=True)
        else:
            st.caption("Estás libre: las relaciones con el club (hinchada, dirigencia, plantel y economía) "
                       "arrancan cuando aceptás una oferta.")

    if M["club"] and M["rol"] == "primer_equipo" and rel["dirigencia"] is not None:
        u = umbral_despido(M)
        if rel["dirigencia"] < u + 12:
            aviso(f"⚠ <b>La dirigencia está perdiendo la paciencia.</b> Si la relación baja de {u}% "
                  f"cada día jugado hay chance de que te echen.")
        k = efecto_cama(M)
        if k > 0:
            aviso(f"🛏️ <b>El plantel te está haciendo la cama.</b> El equipo rinde peor: "
                  f"{CAMA_ATAQUE * k * 100:.0f}% menos de goles a favor, {CAMA_DEFENSA * k * 100:.0f}% más en contra "
                  f"y {CAMA_CONTROL * k:.1f} puntos menos de mediocampo. Si los resultados no mejoran, la relación "
                  "sigue cayendo.")
    elif M["club"]:
        st.caption("Como DT de la Reserva todavía no te evalúan: las relaciones del club se mueven cuando "
                   "dirigís al primer equipo.")

    if M.get("rel_log"):
        st.markdown('<div class="mlab" style="margin-top:6px">Últimos partidos</div>', unsafe_allow_html=True)
        for x in reversed(M["rel_log"][-6:]):
            st.caption(f"{texto_dia(x['dia'], False)} · {x['texto']}")
    if M.get("eventos_hist"):
        st.markdown('<div class="mlab" style="margin-top:6px">Decisiones recientes</div>', unsafe_allow_html=True)
        for x in reversed(M["eventos_hist"][-6:]):
            st.caption(f"{texto_dia(x['dia'], False)} · {x['texto']}")
    with st.expander("Cómo funcionan las relaciones"):
        st.markdown(
            "- Van de 0 a 100 %. Después de cada partido de tu club (como DT del primer equipo) se compara el "
            "resultado con lo esperable según las medias y la localía: ganar un partido difícil sube mucho; "
            "perder uno que parecía ganado baja mucho; lo esperable casi no mueve nada.\n"
            "- **Dirigencia**: si baja de " + str(umbral_despido(M)) + "%, te pueden echar.\n"
            "- **Plantel**: por debajo de " + str(UMBRAL_CAMA) + "% te hacen la cama: el equipo rinde peor.\n"
            "- **Karma**: baja si renunciás, dejás un club por otra oferta o te echan.\n"
            "- Hinchada, Economía, Tapia, Beligoy y Toviggino se mueven pero todavía no tienen consecuencias.\n"
            "- De vez en cuando pasa un **evento** (un club te pide un jugador, la hinchada pide a un juvenil...): "
            "tenés que decidir y cada opción mueve relaciones y, a veces, la media del club.\n"
            "- Si simulás muchos días de golpe, la relación con el plantel se actualiza al final: el efecto "
            "de la cama se nota mejor yendo día por día.")


def panel_manager(S, P, acumular):
    M = st.session_state["manager"]
    seccion("Manager Falopa", f"{M['nombre']} {M['apellido']}", "#b7860b")
    lugar_msg = st.container()                       # lugar fijo del aviso: si aparece o no, nada se corre
    msg = st.session_state.pop("mgr_msg", None)
    if msg:
        with lugar_msg:
            aviso(msg)
    _controles(S, M, P, acumular)
    lugar_prox = st.container()                      # lugar fijo del próximo partido
    if M["club"]:
        with lugar_prox:
            _tarjeta_proximo(S, M)
    etiquetas = ["Oficina"] + (["Mi club"] if M["club"] else []) + ["Relaciones", "Carrera"]
    tabs = dict(zip(etiquetas, st.tabs(etiquetas, key="tabs_mgr", on_change="rerun")))
    with tabs["Oficina"]:
        _oficina(S, M)
    if "Mi club" in tabs:
        with tabs["Mi club"]:
            _mi_club(S, M, P, acumular, tabs["Mi club"].open is not False)
    with tabs["Relaciones"]:
        _relaciones(S, M)
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
        b1.button(":material/check: Aceptar", key=f"of_ok_{o['id']}", type="primary", width="stretch",
                  on_click=_cb_aceptar, args=(S, M, o))
        b2.button(":material/close: Rechazar", key=f"of_no_{o['id']}", width="stretch",
                  on_click=_cb_rechazar, args=(M, o))


def _oficina(S, M):
    if M["club"]:
        st.markdown('<div class="mlab">Tu club</div>', unsafe_allow_html=True)
        _tarjeta_club(S, M["club"], M["rol"])
        if M["rol"] == "reserva":
            st.caption(f"Llevás {M['dias_en_rol']} días en la Reserva. Si el club hace un cambio de técnico, "
                       "te suben al primer equipo (antes, si le va mal en la liga).")
        st.button(":material/logout: Renunciar al club", key="mgr_renunciar", width="stretch",
                  on_click=_cb_renunciar, args=(M,))
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
        + chip(f"Reputación: {M['reputacion']}", "#475569")
        + (" " + chip("Global puesto a mano", "#475569") if M.get("global_a_mano") else ""),
        unsafe_allow_html=True)

    st.markdown('<div class="mlab" style="margin-top:14px">Clubes dirigidos</div>', unsafe_allow_html=True)
    if not M["historial_clubes"]:
        st.caption("Todavía no dirigiste ningún club.")
    for h in reversed(M["historial_clubes"]):
        hasta = texto_dia(h["hasta"], False) if h["hasta"] else "hoy"
        sube = (f' · subió a DT del primer equipo el {texto_dia(h["ascendido"], False)}'
                if h.get("ascendido") else "") + (" · despedido" if h.get("despedido") else "")
        st.markdown(f'{crest(h["club"], 22)} **{esc(h["club"])}** · {esc(h["categoria"] or "")} · '
                    f'{ROLES[h.get("rol", "primer_equipo")]} · temporada {h["temporada"]} · '
                    f'desde {texto_dia(h["desde"], False)} hasta {hasta}{sube}', unsafe_allow_html=True)

    st.markdown('<div class="mlab" style="margin-top:14px">Últimos días jugados</div>', unsafe_allow_html=True)
    if not M["registro"]:
        st.caption("Todavía no se jugó ningún día.")
    for x in reversed(M["registro"][-10:]):
        st.caption(f"{texto_dia(x['dia'])}: {', '.join(x['comps'])}")

    b1, b2 = st.columns(2)
    b1.button(":material/edit: Editar datos", key="mgr_editar", width="stretch", on_click=_cb_editar)
    b2.button(":material/home: Volver al inicio", key="mgr_inicio_btn", width="stretch", on_click=_cb_volver_inicio)


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

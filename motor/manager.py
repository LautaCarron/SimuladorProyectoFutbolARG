"""Lógica del modo Manager que no depende de la interfaz: sincronización con el calendario, relaciones del día,
táctica y simulación día por día. Sin Streamlit (la pantalla está en ui/manager.py)."""

import datetime as dt
import uuid

from motor.calendario import dia_partido, eventos_calendario, jugar_proximo_dia, proximos
from motor.consultas import partidos_club, partidos_de_calendario
from motor.eventos import EVENTOS, sortear
from motor.nucleo import TACTICAS, con_tacticas, tactica_total
from motor.ofertas import ROLES, nuevo_dia
from motor.relaciones import (
    UMBRAL_CAMA,
    aplicar_partido,
    asegurar,
    clave_partido,
    con_cama,
    efecto_cama,
    entrar_club,
    revisar_despido,
)

TOPE_DIAS = 60                    # "Hasta la próxima novedad" / "hasta mi próximo partido": máximo de días
TOPE_DIAS_SIMULAR_TODO = 400      # "Simular todo" del modo manager (una temporada entera)


def primer_dia(S):
    prox = proximos(S)
    return min((d for d, _ in prox.values()), default=dt.date.today())


def aplicar_tactica(S, M):
    """Carga en el generador de azar del simulador la táctica del club del manager. Sólo juega con
    táctica si dirige al primer equipo (en la Reserva no define cómo juega el primer equipo)."""
    tab = {}
    if M.get("club") and M.get("rol") == "primer_equipo" and M.get("formacion") in TACTICAS:
        base = tactica_total(M["formacion"], M.get("estilo"))                # formación + estilo de juego
        tab = {M["club"]: con_cama(base, efecto_cama(M))}                    # el plantel puede hacerte la cama
    S["rng"] = con_tacticas(S["rng"], tab)


def dias_jugados(S):
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
    jugados = dias_jugados(S)
    sync = M.get("sync")
    if not sync or sync["uid"] != uid:
        M["sync"] = {"uid": uid, "dias": set(jugados)}     # lo ya jugado antes no genera ofertas
        M["partidos_vistos"] = {clave_partido(p) for p in partidos_club(S, M["club"])} if M["club"] else set()
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
        r["relaciones"] = relaciones_dia(S, M, d)         # partidos del día: hinchada, dirigencia, plantel...
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
            partidos = partidos_de_calendario(S, liga, n)
        except Exception:
            continue
        for p in partidos:
            if p["gl"] is None and club in (p["local"], p["visita"]):
                return p
    return None


def relaciones_dia(S, M, d):
    """Mueve las relaciones con los partidos de mi club que ya se jugaron hasta el día `d` (sólo cuentan
    cuando sos DT del primer equipo) y revisa si te echan. Devuelve los textos de lo que pasó."""
    avisos = []
    if not M["club"]:
        return avisos
    nuevos = sorted((p for p in partidos_club(S, M["club"])
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


def jugar_dias(S, M, P, acumular, hasta):
    """Juega días del calendario hasta que `hasta(textos, nuevos_partidos)` sea verdadero (o no quede
    nada / se llegue al tope). Devuelve (días jugados, textos, partidos nuevos del club)."""
    antes = {id(p) for p in partidos_club(S, M["club"])} if M["club"] else set()
    jugados, textos, nuevos = 0, [], []
    while jugados < TOPE_DIAS and proximos(S):
        jugar_proximo_dia(S, P, acumular)
        jugados += 1
        textos += sincronizar_manager(S, M)
        if M["club"]:
            nuevos = [p for p in partidos_club(S, M["club"]) if id(p) not in antes]
        if M.get("evento") or hasta(textos, nuevos):       # un evento pausa la simulación
            break
    return jugados, textos, nuevos


def simular_hasta_pausa(S, M, P, acumular):
    """"Simular todo" del modo manager: juega día por día hasta que termina la temporada o aparece un evento
    (que hay que resolver antes de seguir). Devuelve (días jugados, textos de novedades)."""
    jugados, textos = 0, []
    while proximos(S) and jugados < TOPE_DIAS_SIMULAR_TODO:
        jugar_proximo_dia(S, P, acumular)
        jugados += 1
        textos += sincronizar_manager(S, M)
        if M.get("evento"):
            break
    return jugados, textos

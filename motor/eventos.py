"""Eventos del modo manager (va en motor/eventos.py). Sin Streamlit.

De vez en cuando, después de un partido de tu club (sólo como DT del primer equipo), pasa algo que exige una
decisión: un club te pide un jugador, la hinchada pide a un juvenil, la dirigencia necesita plata... El evento
queda "pendiente" en M["evento"] y la interfaz frena todo hasta que elegís. Cada opción cambia relaciones
(hinchada, dirigencia, plantel, economía, karma, Tapia...) y, a veces, la MEDIA del club.

Un evento es un dict con: titulo, peso, cond(S, M) -> bool, texto(S, M) -> str y opciones: lista de
{texto, efectos}. `efectos` es {clave: delta}: las claves son las de motor/relaciones.py o "media" (cambia
la media del club en todas las competencias donde juega).
"""

from motor.nucleo import MAX_R, MIN_R
from motor.ofertas import categoria_de, ligas
from motor.relaciones import ETIQUETAS, cambiar

P_EVENTO = 0.15            # chance de evento después de cada partido de tu club...
COOLDOWN_PARTIDOS = 3      # ...pero con al menos esta cantidad de partidos desde el último evento
MIN_DIAS_DT = 6            # y recién después de estos días como DT del primer equipo
NO_REPETIR = 3             # un evento no vuelve hasta que pasaron otros tantos

ETIQUETAS_EFECTO = dict(ETIQUETAS, media="Media del club")


EVENTOS = {
    "barracas_jugador": dict(
        titulo="Barracas Central te pide un jugador", peso=3,
        cond=lambda S, M: M["club"] != "Barracas Central" and categoria_de(S, "Barracas Central") is not None,
        texto=lambda S, M: ("Desde Barracas Central piden a un jugador de tu plantel: un titular joven que la "
                            f"hinchada de {M['club']} quiere mucho. Tenés que decidir si lo cedés."),
        opciones=[
            dict(texto="Ceder al jugador", efectos=dict(media=-2, hinchada=-8, tapia=+10)),
            dict(texto="No cederlo", efectos=dict(tapia=-8, hinchada=+6)),
        ]),
    "renovacion_capitan": dict(
        titulo="El capitán pide renovar con aumento", peso=2,
        cond=lambda S, M: True,
        texto=lambda S, M: ("El capitán de tu equipo, referente del vestuario, pide renovar el contrato con un "
                            "aumento importante. Si no lo conseguís, amenaza con irse libre."),
        opciones=[
            dict(texto="Aceptar el aumento", efectos=dict(economia=-8, plantel=+10, dirigencia=-3)),
            dict(texto="Rechazar el pedido", efectos=dict(plantel=-8, dirigencia=+3)),
        ]),
    "hinchas_piden_pibe": dict(
        titulo="La hinchada pide a un pibe de inferiores", peso=2,
        cond=lambda S, M: True,
        texto=lambda S, M: ("Desde la popular piden que debute un juvenil de inferiores que viene rompiéndola. "
                            "Los más grandes del plantel no lo ven preparado."),
        opciones=[
            dict(texto="Hacerlo debutar", efectos=dict(hinchada=+8, plantel=-4)),
            dict(texto="Seguir con los de siempre", efectos=dict(hinchada=-6, plantel=+3)),
        ]),
    "vender_figura": dict(
        titulo="La dirigencia necesita plata: quieren vender a la figura", peso=2,
        cond=lambda S, M: (M["rel"]["economia"] or 50) < 45,
        texto=lambda S, M: (f"Las cuentas de {M['club']} están apretadas y la dirigencia te informa que hay una "
                            "oferta por tu mejor jugador. Quieren tu aval para venderlo."),
        opciones=[
            dict(texto="Aceptar la venta", efectos=dict(media=-2, dirigencia=+10, economia=+12, hinchada=-8)),
            dict(texto="Oponerte a la venta", efectos=dict(dirigencia=-10, hinchada=+6, plantel=+4)),
        ]),
    "fichar_refuerzo": dict(
        titulo="Te ofrecen un refuerzo con experiencia", peso=2,
        cond=lambda S, M: (M["rel"]["economia"] or 50) >= 20,
        texto=lambda S, M: ("Un representante te ofrece a un jugador de jerarquía que quedó libre. Es un "
                            "salto de calidad para el equipo, pero el sueldo no es barato."),
        opciones=[
            dict(texto="Pedir que lo contraten", efectos=dict(media=+2, economia=-10, dirigencia=-2)),
            dict(texto="Dejarlo pasar", efectos=dict(plantel=+2)),
        ]),
    "declaraciones_arbitro": dict(
        titulo="La prensa te pregunta por el arbitraje", peso=2,
        cond=lambda S, M: True,
        texto=lambda S, M: ("Después de un partido polémico, los periodistas te preguntan qué te pareció la "
                            "actuación del árbitro. Lo que digas va a repercutir."),
        opciones=[
            dict(texto="Criticar al árbitro", efectos=dict(hinchada=+6, plantel=+3, karma=-4)),
            dict(texto="Hablar de otra cosa", efectos=dict(hinchada=-2, karma=+3)),
        ]),
    "sponsor_amistoso": dict(
        titulo="Un sponsor ofrece plata por un amistoso", peso=1,
        cond=lambda S, M: True,
        texto=lambda S, M: ("Una marca quiere que el equipo juegue un amistoso en medio de la temporada y paga "
                            "muy bien. El plantel viene cargado de partidos."),
        opciones=[
            dict(texto="Aceptar el amistoso", efectos=dict(economia=+10, plantel=-4)),
            dict(texto="Rechazarlo", efectos=dict(dirigencia=-3, plantel=+2)),
        ]),
    "tension_vestuario": dict(
        titulo="Tensión en el vestuario", peso=1,
        cond=lambda S, M: True,
        texto=lambda S, M: ("Dos referentes del plantel se pelearon en la práctica y el clima se puso espeso. "
                            "Hay que actuar."),
        opciones=[
            dict(texto="Hablar con los dos y bajar los decibeles", efectos=dict(plantel=+6, karma=+2)),
            dict(texto="Sancionar públicamente a uno", efectos=dict(plantel=-8, dirigencia=+4, hinchada=+3)),
        ]),
}


# ---- Cambios que provocan los eventos ----------------------------------------------------------------
def ajustar_media(S, club, delta):
    """Suma `delta` a la media del club en la liga y en todas las competencias de la temporada donde juega
    (Copa Argentina, copas CONMEBOL, Mundial), respetando los topes de media del motor."""
    def tope(x):
        return max(MIN_R, min(MAX_R, float(x)))

    for _cat, (L, nombres) in ligas(S).items():
        if club in nombres:
            i = nombres.index(club)
            L["r"][i] = tope(L["r"][i] + delta)
    SC = S.get("copa") or {}
    if SC.get("sorteada") and club in SC.get("nombres", []):
        j = SC["nombres"].index(club)
        SC["r"][j] = tope(SC["r"][j] + delta)
    for C in (S.get("int") or {}).values():
        if club in (C.get("r") or {}):
            C["r"][club] = tope(C["r"][club] + delta)
    MU = S.get("mundial") or {}
    if club in (MU.get("r") or {}):
        MU["r"][club] = tope(MU["r"][club] + delta)


def texto_efectos(efectos):
    """"Media del club −2 · Hinchada −8 · Tapia +10" """
    return " · ".join(f"{ETIQUETAS_EFECTO[k]} {v:+d}".replace("-", "−") for k, v in efectos.items())


def resolver(S, M, indice):
    """Aplica la opción elegida del evento pendiente y lo cierra. Devuelve el texto del resultado."""
    pend = M["evento"]
    ev = EVENTOS[pend["id"]]
    op = ev["opciones"][indice]
    for clave, delta in op["efectos"].items():
        if clave == "media":
            ajustar_media(S, M["club"], delta)
            M["media_ajustada"] = M.get("media_ajustada", 0) + delta
        else:
            cambiar(M, clave, delta)
    resumen = f"{ev['titulo']} → {op['texto']} ({texto_efectos(op['efectos'])})"
    M.setdefault("eventos_hist", []).append({"dia": pend["dia"], "id": pend["id"], "opcion": op["texto"],
                                             "texto": resumen})
    del M["eventos_hist"][:-15]
    M["evento"] = None
    M["partidos_desde_evento"] = 0
    return resumen


# ---- Cuándo pasan --------------------------------------------------------------------------------------
def sortear(S, M, rng, jugo):
    """Se llama una vez por día en el que se procesan partidos de mi club. Devuelve el evento nuevo
    ({"id", "dia"}) o None. No hace nada si ya hay un evento pendiente."""
    if not jugo or M.get("evento") or not M.get("club") or M.get("rol") != "primer_equipo":
        return None
    M["partidos_desde_evento"] = M.get("partidos_desde_evento", 0) + 1
    if M.get("dias_dt", 0) < MIN_DIAS_DT or M["partidos_desde_evento"] < COOLDOWN_PARTIDOS:
        return None
    if rng.random() >= P_EVENTO:
        return None
    recientes = {h["id"] for h in M.get("eventos_hist", [])[-NO_REPETIR:]}
    cand = [(i, ev) for i, ev in EVENTOS.items() if i not in recientes and ev["cond"](S, M)]
    if not cand:
        return None
    pesos = [ev["peso"] for _, ev in cand]
    k = int(rng.choice(len(cand), p=[p / sum(pesos) for p in pesos]))
    M["partidos_desde_evento"] = 0
    return {"id": cand[k][0], "dia": M["hoy"]}

"""Eventos del modo manager (va en motor/eventos.py). Sin Streamlit.

De vez en cuando, después de un partido de tu club (sólo como DT del primer equipo), pasa algo que exige una
decisión: un club te pide un jugador, la hinchada pide a un juvenil, la dirigencia necesita plata... El evento
queda "pendiente" en M["evento"] y la interfaz frena todo hasta que elegís. Cada opción cambia relaciones
(hinchada, dirigencia, plantel, economía, karma, Tapia...) y, a veces, la MEDIA del club.

Un evento es un dict con: titulo, peso, cond(S, M) -> bool, texto(S, M) -> str y opciones: lista de
{texto, efectos, azar}. `efectos` es {clave: delta} y pasa siempre: las claves son las de motor/relaciones.py
o "media" (cambia la media del club en todas las competencias donde juega). `azar` es opcional y hace que
el resultado sea incierto: lista de (porcentaje, efectos, texto del resultado); se sortea una y se suma a
`efectos`.
"""

from motor.nucleo import MAX_R, MIN_R
from motor.ofertas import categoria_de, ligas
from motor.relaciones import ETIQUETAS, cambiar

P_EVENTO = 0.15            # chance de evento después de cada partido de tu club...
COOLDOWN_PARTIDOS = 3      # ...pero con al menos esta cantidad de partidos desde el último evento
MIN_DIAS_DT = 6            # y recién después de estos días como DT del primer equipo
NO_REPETIR = 6             # un evento no vuelve hasta que pasaron otros tantos

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
    # ---------------------------------------------------------------- humor
    "presi_quiere_jugar": dict(
        titulo="El presidente quiere jugar 10 minutos", peso=2,
        cond=lambda S, M: True,
        texto=lambda S, M: ("El presidente cumplió 62, se compró botines flúor y exige que lo pongas 10 minutos "
                            "\"para levantar la moral del grupo\". Tiene la rodilla de un jarrón y la billetera de "
                            "un sultán."),
        opciones=[
            dict(texto="Ponerlo 10 minutos (y rezar)", efectos=dict(dirigencia=+12, plantel=-5, hinchada=-4, media=-1)),
            dict(texto="Decirle que el reglamento no deja entrar a mayores de 60", efectos=dict(dirigencia=-7, plantel=+3, karma=+2)),
            dict(texto="Dejarlo patear tiros libres en el entretiempo", efectos=dict(dirigencia=+5, hinchada=+4, plantel=-2)),
        ]),
    "asado_en_llamas": dict(
        titulo="El asado del plantel salió en el noticiero", peso=2,
        cond=lambda S, M: True,
        texto=lambda S, M: ("El asado de camaradería terminó con la parrilla en llamas, dos bomberos, un perro "
                            "corriendo con un chorizo en la boca y tu volante central sin cejas. Hay video."),
        opciones=[
            dict(texto="Hacerte cargo y pagar los daños de tu bolsillo", efectos=dict(karma=+4, plantel=+8, hinchada=+2)),
            dict(texto="Pasarle la factura al club", efectos=dict(economia=-6, dirigencia=-5, plantel=+3)),
            dict(texto="Culpar al pasante de utilería", efectos=dict(karma=-6, plantel=-4, dirigencia=+2)),
        ]),
    "gallina_cabala": dict(
        titulo="El Cacho y la gallina de la suerte", peso=2,
        cond=lambda S, M: True,
        texto=lambda S, M: ("El Cacho, hincha desde la época del blanco y negro, aparece en el entrenamiento con "
                            "una gallina \"campeona\" y jura que ganan todo si la sentás en el banco. La gallina te "
                            "mira con desprecio profesional."),
        opciones=[
            dict(texto="Dejar a la gallina en el banco", efectos={}, azar=[
                (50, dict(hinchada=+8), "La gallina puso un huevo en pleno banco y la hinchada lo tomó como señal divina."),
                (50, dict(dirigencia=-6, hinchada=-2), "La gallina se escapó, picó el micrófono de la TV y el club es meme nacional."),
            ]),
            dict(texto="Agradecerle y pedirle que se la lleve", efectos=dict(hinchada=-4, karma=+2)),
        ]),
    "yuyo_abuela": dict(
        titulo="El médico y el yuyo de su abuela", peso=2,
        cond=lambda S, M: True,
        texto=lambda S, M: ("El médico del club propone curar a tu lesionado con \"un yuyito de mi abuela que "
                            "levanta muertos\". Asegura que en 48 horas corre como un rayo. O como un loro: todavía "
                            "no lo definió."),
        opciones=[
            dict(texto="Aprobar el yuyo", efectos={}, azar=[
                (45, dict(media=+1, plantel=+4), "Volvió a correr como un rayo y pidió la receta."),
                (55, dict(plantel=-4, karma=-2), "Se le pusieron los ojos verdes y el vestuario huele a menta. Nadie quiere hablar del tema."),
            ]),
            dict(texto="Mandarlo a una clínica de verdad", efectos=dict(economia=-5, plantel=+2)),
        ]),
    "coach_cuantico": dict(
        titulo="Un coach cuántico quiere alinear la energía del césped", peso=2,
        cond=lambda S, M: True,
        texto=lambda S, M: ("Un señor con túnica y siete cristales dice que la cancha tiene \"mala vibra\" y que, "
                            "por 3 mil dólares, puede reconfigurar las energías del vestuario. Tu capitán ya le "
                            "prestó el celular."),
        opciones=[
            dict(texto="Dejarlo trabajar", efectos=dict(economia=-8), azar=[
                (40, dict(media=+2, plantel=+6), "El plantel jura haber visto un duende y juega como nunca."),
                (60, dict(plantel=-6, dirigencia=-3), "Dos jugadores se fueron del vestuario por la energía \"tóxica\" del DT."),
            ]),
            dict(texto="Echarlo con un incienso de por medio", efectos=dict(plantel=+2, karma=+2)),
        ]),
    "suplente_viral": dict(
        titulo="Tu suplente se hizo viral bailando", peso=2,
        cond=lambda S, M: True,
        texto=lambda S, M: ("Tu delantero suplente subió un baile y tiene 2 millones de seguidores y 0 goles. Una "
                            "marca de gaseosas ya llamó. Tu volante dice que \"el fútbol de hoy es otra cosa\"."),
        opciones=[
            dict(texto="Ponerlo de titular por marketing", efectos=dict(media=-1, economia=+10, hinchada=+4, plantel=-5)),
            dict(texto="Que baile sólo en el entretiempo", efectos=dict(economia=+4, karma=+2)),
            dict(texto="Prohibirle el celular", efectos=dict(plantel=-4, dirigencia=+3, hinchada=-1)),
        ]),
    "micro_cumbia": dict(
        titulo="El micro volvió con DJ y cumbia a las 4 de la mañana", peso=1,
        cond=lambda S, M: True,
        texto=lambda S, M: ("A la vuelta del partido, el utilero armó una bailanta en el micro. Los vecinos de la "
                            "ruta llamaron a la policía y el chofer se sabe todas las letras."),
        opciones=[
            dict(texto="Multar a los responsables", efectos=dict(plantel=-6, karma=+2, dirigencia=+2)),
            dict(texto="Sumarte al karaoke", efectos=dict(plantel=+8, dirigencia=-4, karma=-1)),
            dict(texto="Hacerte el dormido", efectos=dict(plantel=+1)),
        ]),
    "goleador_tatuaje": dict(
        titulo="Tu goleador se tatuó su propia cara", peso=1,
        cond=lambda S, M: True,
        texto=lambda S, M: ("Tu goleador se tatuó su propio rostro en la espalda y ahora pide que le cambien el "
                            "número a \"1 de 1\". La hinchada no sabe si emocionarse o llamar al psiquiatra."),
        opciones=[
            dict(texto="Cambiarle el número", efectos=dict(plantel=+4, hinchada=-3, karma=-2)),
            dict(texto="Negarte: sigue con el 9", efectos=dict(plantel=-6, hinchada=+2)),
        ]),
    "camiseta_violeta": dict(
        titulo="Cábala: la hinchada pide la camiseta violeta flúor", peso=1,
        cond=lambda S, M: True,
        texto=lambda S, M: ("Un grupo de hinchas jura que si jugás con la camiseta violeta flúor del '94 ganan "
                            "seguro. Nadie se acuerda qué pasó en el '94, pero todos se acuerdan de que era violeta."),
        opciones=[
            dict(texto="Cambiar la camiseta", efectos=dict(hinchada=+6, economia=-6, dirigencia=-3)),
            dict(texto="Mantener la de siempre", efectos=dict(hinchada=-5, dirigencia=+2)),
        ]),
    "rifa_pretemporada": dict(
        titulo="La dirigencia rifa un jamón crudo para pagar la luz", peso=2,
        cond=lambda S, M: (M["rel"]["economia"] or 50) < 55,
        texto=lambda S, M: ("Para juntar plata, la dirigencia propone una rifa: el primer premio es un jamón crudo y "
                            "el segundo, \"una tarde con el DT lavándote el auto\". Nadie te preguntó."),
        opciones=[
            dict(texto="Aceptar y prepararte para lavar autos", efectos=dict(economia=+10, dirigencia=+6, plantel=+4, karma=+1)),
            dict(texto="Negarte con dignidad", efectos=dict(dirigencia=-6, karma=+2)),
        ]),
    "entradas_remeras": dict(
        titulo="Cuarenta señores con la misma remera piden entradas", peso=1,
        cond=lambda S, M: True,
        texto=lambda S, M: ("Cuarenta señores con remeras idénticas, mirada seria y cero ganas de pagar te piden "
                            "\"amablemente\" 40 entradas de platea. Uno te regala un alfajor. Es un alfajor muy "
                            "simbólico."),
        opciones=[
            dict(texto="Darles las entradas", efectos=dict(hinchada=+6, economia=-5, dirigencia=-4)),
            dict(texto="Negarte (y rezar)", efectos=dict(hinchada=-8, karma=+3)),
        ]),
    "utilero_empanadas": dict(
        titulo="El utilero cobra en empanadas", peso=1,
        cond=lambda S, M: True,
        texto=lambda S, M: ("Hugo, el utilero, lleva tres meses cobrando en empanadas y amenaza con no inflar las "
                            "pelotas. Ayer salió una que parecía una medialuna."),
        opciones=[
            dict(texto="Pagarle de tu bolsillo", efectos=dict(karma=+4, plantel=+3)),
            dict(texto="Reclamarle a la dirigencia", efectos=dict(dirigencia=-4, economia=-4, plantel=+2)),
            dict(texto="Darle más empanadas", efectos=dict(economia=-2, plantel=-1)),
        ]),
    "arbitro_whatsapp": dict(
        titulo="Un árbitro te escribe un WhatsApp raro", peso=1,
        cond=lambda S, M: True,
        texto=lambda S, M: ("Te llega un mensaje de un árbitro: \"Che, ¿vamos a comer unas pizzas? Lo digo para "
                            "conocernos, nada que ver con el domingo\". Adjunta un sticker de pulgar levantado."),
        opciones=[
            dict(texto="Aceptar la pizza", efectos={}, azar=[
                (50, dict(plantel=+2, karma=-3), "Nadie se enteró y la pizza estaba buenísima."),
                (50, dict(hinchada=-8, dirigencia=-8, karma=-8), "La captura llegó a un programa de TV y ahora sos tendencia."),
            ]),
            dict(texto="Bloquear y guardar la captura como prueba", efectos=dict(karma=+5, dirigencia=+2)),
        ]),
    "mascota_pinguino": dict(
        titulo="La mascota apareció cenando con la mascota del rival", peso=1,
        cond=lambda S, M: True,
        texto=lambda S, M: ("La mascota del club, un pingüino gigante, apareció en una foto cenando de la mano con la "
                            "mascota del rival y una botella de vino de por medio. La hinchada pide explicaciones; "
                            "el pingüino pide abogado."),
        opciones=[
            dict(texto="Perdonarlo públicamente", efectos=dict(hinchada=+3, karma=+3, dirigencia=-2)),
            dict(texto="Echarlo del club", efectos=dict(hinchada=-7, dirigencia=+3, plantel=-1)),
            dict(texto="Hacerle un asado de reconciliación", efectos=dict(plantel=+4, economia=-3)),
        ]),
    "guerra_playlists": dict(
        titulo="Guerra de playlists en el vestuario", peso=1,
        cond=lambda S, M: True,
        texto=lambda S, M: ("Cuatro jugadores se pelean por el parlante: el pibe quiere trap, el capitán cuarteto, el "
                            "arquero folklore y el 5 sólo escucha audios de su abuela. Hubo amenazas serias."),
        opciones=[
            dict(texto="Hacer una votación democrática", efectos=dict(plantel=+6, karma=+1)),
            dict(texto="Prohibir la música", efectos=dict(plantel=-8, dirigencia=+2)),
            dict(texto="Poner tu tango y que se banquen", efectos=dict(plantel=-3, karma=+3)),
        ]),
    "hincha_streaming": dict(
        titulo="Un hincha con 3 espectadores te destroza en vivo", peso=1,
        cond=lambda S, M: True,
        texto=lambda S, M: ("Un hincha con tres espectadores y mucho tiempo libre dedicó dos horas a analizar tu "
                            "esquema con un pizarrón. Dice que al equipo le falta \"carácter y un cuatro de "
                            "contención\". Tiene razón en lo segundo."),
        opciones=[
            dict(texto="Responderle en vivo (y hacerte viral)", efectos=dict(hinchada=+5, karma=-3, dirigencia=-3)),
            dict(texto="Ignorarlo", efectos=dict(hinchada=-1, karma=+2)),
            dict(texto="Invitarlo a un entrenamiento", efectos=dict(plantel=+3, hinchada=+4, karma=+2)),
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


def descripcion_opcion(op):
    """Lo que se le muestra al jugador de una opción: los efectos seguros y, si hay azar, los posibles resultados."""
    partes = []
    if op.get("efectos"):
        partes.append(texto_efectos(op["efectos"]))
    if op.get("azar"):
        partes.append("Resultado incierto: " + "  |  ".join(f"{p}%: {texto_efectos(ef)}" for p, ef, _ in op["azar"]))
    return " · ".join(partes) if partes else "Sin consecuencias"


def resolver(S, M, indice, rng=None):
    """Aplica la opción elegida del evento pendiente (sorteando el resultado si es incierto) y lo cierra.
    Devuelve el texto del resultado."""
    pend = M["evento"]
    ev = EVENTOS[pend["id"]]
    op = ev["opciones"][indice]
    efectos, que_paso = dict(op.get("efectos", {})), ""
    if op.get("azar"):
        rng = rng if rng is not None else S["rng"]
        k = int(rng.choice(len(op["azar"]), p=[p / sum(a[0] for a in op["azar"]) for p, _, _ in op["azar"]]))
        _, extra, que_paso = op["azar"][k]
        for clave, delta in extra.items():
            efectos[clave] = efectos.get(clave, 0) + delta
    for clave, delta in efectos.items():
        if clave == "media":
            ajustar_media(S, M["club"], delta)
            M["media_ajustada"] = M.get("media_ajustada", 0) + delta
        else:
            cambiar(M, clave, delta)
    resumen = (f"{ev['titulo']} → {op['texto']}" + (f": {que_paso}" if que_paso else "")
               + f" ({texto_efectos(efectos)})")
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

"""Incidentes: partidos suspendidos y sanciones (muy de vez en cuando, como en la vida real).

Con una probabilidad bajísima por partido (en promedio uno o dos por temporada entre todas las
categorías) puede pasar algo:
  * Suspensión por clima o por un corte de luz: el partido se termina de jugar después y el
    resultado se mantiene. Sin sanción.
  * Incidentes (hinchas, dirigentes, micro apedreado, no presentación): el Tribunal de
    Disciplina le da el partido por perdido al club responsable (en la liga, los 3 puntos van
    para el rival; en la Copa, pasa el rival). A veces, además, quita de puntos.
  * Escándalos de la dirigencia (apuestas, arreglos): quita de puntos (en la Copa, exclusión).
  * Lo gravísimo (agresión brutal al árbitro): partido perdido y descenso de categoría al
    terminar la temporada (si ya está en la última categoría, quita de 12 puntos).
Cada incidente queda en la sección de avisos (liga de la temporada: L["alertas"]).
"""

import numpy as np

PROB = 0.001              # por partido de liga o de Copa

# (clave, peso, sanción) · sanción: None (sólo suspensión), "pierde", "pierde+3", "pierde+6",
# "quita9", "gravisimo"
TIPOS = [
    ("clima", 30, None), ("luz", 9, None), ("bengalas", 13, "pierde+3"), ("invasion", 12, "pierde"),
    ("micro", 8, "pierde"), ("huelga", 6, "pierde"), ("arbitro", 9, "pierde+6"),
    ("corrupcion", 5, "quita9"), ("gravisimo", 2, "gravisimo"),
    ("doping", 3, "quita9"), ("animales", 15, None), ("cancha", 12, None), 
    ("logistica", 10, None), ("hinchada", 15, None)
]

TEXTOS = {
    "clima": [
        ("Suspendido por tormenta eléctrica",
         "Cayeron rayos cerca del estadio y el árbitro mandó a todos al vestuario a los {min}'. "
         "Se terminó de jugar el lunes: {res}."),
        ("Suspendido por diluvio",
         "La cancha quedó hecha una pileta y la pelota no picaba. Se postergó 48 horas y terminó {res}."),
        ("Suspendido por granizo",
         "Cayó granizo del tamaño de pelotas de golf y hubo que suspender a los {min}'. Se completó "
         "el miércoles: {res}."),
        ("Suspendido por niebla",
         "Una niebla cerradísima: desde un arco no se veía el otro. Se terminó de jugar al día siguiente: {res}."),
    ],
    "luz": [
        ("Se cortó la luz",
         "Apagón en el estadio a los {min}': los grupos electrógenos no arrancaron. Se completó "
         "al otro día: {res}."),
        ("Se quemó un transformador",
         "Explotó un transformador del barrio y el estadio quedó a oscuras a los {min}'. "
         "Se terminó de jugar 24 horas después: {res}."),
        ("Suspendido por falta de suministros",
         "El club local no pagó los impuestos y el árbitro suspendió el partido por falta de luz."
         " Se completó al día siguiente por la mañana: {res}."), 
    ],
    "bengalas": [
        ("Incendio en la tribuna",
         "La hinchada de {club} tiró bengalas y se prendió fuego parte de la tribuna. El árbitro "
         "suspendió el partido a los {min}'."),
        ("Pirotecnia y humo",
         "Los hinchas de {club} tiraron tanta pirotecnia que el humo tapó la cancha y hubo "
         "principio de incendio en la platea. Partido suspendido a los {min}'."),
    ],
    "invasion": [
        ("Invasión de la cancha",
         "Hinchas de {club} saltaron el alambrado y fueron a buscar a los jugadores de {rival}. "
         "El árbitro suspendió el partido a los {min}'."),
        ("Barras en el vestuario",
         "Barras de {club} entraron al vestuario visitante en el entretiempo y apretaron a los "
         "jugadores de {rival}, que se negaron a salir a jugar el segundo tiempo."),
    ],
    "micro": [
        ("Apedrearon el micro visitante",
         "El micro de {rival} fue atacado a piedrazos llegando a la cancha de {club}: dos "
         "jugadores con cortes y el partido no se jugó."),
        ("Chocó el micro local",
         "El micro de {club} chocó contra un camión en el trayecto y varios jugadores se lastimaron "
         "como Toranzo en 2016. El partido se jugó el próximo feriado nacional: {res}."), 
        ("Demoras por piquetes",
         "El micro de {rival} se demoró por un piquete del sindicato de camioneros, el partido se retrasó 3 horas: {res}."),
        ("Demoras por pinchazo",
         "El micro de {rival} se demoró por pinchar un neumático en la ruta, el partido se retrasó 1 hora: {res}.")
    ],
    "huelga": [
        ("No se presentaron",
         "Los jugadores de {club} no se presentaron: reclaman cinco meses de sueldos atrasados."),
        ("Paro del plantel",
         "El plantel de {club} hizo paro por deudas y el club no llegó a armar un equipo con juveniles."),
        ("Protesta de los jugadores", 
         "Los jugadores de {club} se manifestaron por la trata de jugadores en las divisiones inferiores."),
    ],
    "arbitro": [
        ("Agresión al árbitro",
         "Un dirigente de {club} bajó a la cancha y le pegó una trompada al árbitro a los {min}'. "
         "Partido suspendido."),
        ("Agresión al árbitro",
         "Un jugador de {club} empujó y escupió al árbitro tras un penal; se armó una batalla "
         "campal y el árbitro suspendió el partido a los {min}'."),
    ],
    "corrupcion": [
        ("Escándalo de apuestas",
         "La Justicia investiga a la dirigencia de {club} por arreglo de partidos y apuestas ilegales. "
         "Allanaron la sede del club."),
        ("Presidente detenido",
         "Detuvieron al presidente de {club} en una causa por lavado de dinero y reventa de entradas."),
        ("Irregularidades en los pases",
         "La AFA detectó contratos truchos y deudas ocultas en {club}: el Tribunal actuó de oficio."),
    ],
    "gravisimo": [
        ("Agresión brutal al árbitro",
         "Barras de {club} entraron a la cancha a los {min}' y atacaron salvajemente al árbitro, "
         "que terminó internado en terapia intensiva. Conmoción en todo el fútbol argentino."),
        ("Pelea de Hinchadas",
         "La barra de {rival} se metió en la tribuna de {club} y hubo una batalla campal con heridos graves. "
         "El árbitro suspendió el partido a los {min}'."),
        ("Incidentes en el entretiempo",
         "Los jugadores de {club} y {rival} se agarraron a trompadas en el entretiempo y el árbitro suspendió el partido."), 
    ],
    "doping": [
        ("Doping positivo",
         "Saltó la ficha en el control antidoping post partido y 3 jugadores de {rival} dieron positivo, por lo que el Tribunal intervino de oficio.")
    ],
    "animales": [
        ("Perro en la cancha",
         "Un perro se metió a la cancha durante el partido y nadie pudo sacarlo durante varios minutos. El árbitro frenó el juego a los {min}' hasta que finalmente lo retiraron: {res}."),
        ("Invasión de abejas",
         "Un enjambre de abejas apareció sobre una de las tribunas y obligó a jugadores y árbitros a salir corriendo. Partido demorado a los {min}': {res}.")
    ],
    "cancha": [
        ("Se rompió el arco",
         "Un jugador reventó el travesaño después de un disparo y terminó arrancando parte del arco. Hubo que reemplazarlo antes de continuar: {res}."),
        ("Se levantó el césped",
         "Una parte del césped se levantó durante una corrida y quedó un pozo enorme cerca del área. El árbitro pisó mal en la siguiente jugada y se lesionó, se demoró el partido a los {min}': {res}."),
        ("Aspersores activados",
         "Los aspersores del estadio se encendieron por error en pleno partido y empaparon a jugadores y árbitros. El juego se detuvo a los {min}' pero luego continuó con normalidad: {res}."),
        ("Vestuario inundado",
         "Una cañería explotó y el vestuario de {club} quedó completamente inundado antes del segundo tiempo. El partido se retrasó y terminó {res}."),
        ("Techo desprendido",
         "Una parte del techo de una tribuna se desprendió por el viento y cayó sobre un sector vacío. El partido fue suspendido por seguridad. Se postergó y se jugó en la cancha del predio: {res}.")
    ],
    "logistica": [
        ("Falta de ambulancia",
         "La policía se llevó al médico de la ambulancia del partido por presentar un título trucho. El árbitro demoró el inicio hasta resolverlo: {res}."),
        ("Se olvidaron las camisetas",
         "El plantel de {club} llegó al estadio sin su juego de camisetas y tuvo que conseguir indumentaria prestada de urgencia. El partido se retrasó: {res}."),
        ("Camisetas iguales",
         "Ambos equipos llegaron con camisetas prácticamente idénticas y ninguno tenía una alternativa disponible. El partido se retrasó hasta conseguir pecheras: {res}."),
        ("Llaves perdidas",
         "El utilero de {club} perdió las llaves del vestuario y el plantel quedó afuera durante casi una hora. El partido se retrasó: {res}.")
    ],
    "hinchada": [
        ("Papelitos por todos lados",
         "La hinchada de {club} arrojó tantos papeles que las líneas del campo quedaron completamente cubiertas. El partido se demoró mientras limpiaban: {res}.")
    ]
}


def _es_regular(p):
    """Sólo partidos de liga 'normales' (no desempates, reducidos, promoción ni finales)."""
    if p.get("neutral") or p.get("tanda"):
        return False
    t = f"{p['rotulo']} {p['comp']}"
    return not any(w in t for w in ("educido", "Promoción", "Desempate", "Final", "Eliminatoria",
                                    "Semifinal", "Octavos", "Cuartos"))


def _sumar(L, i, j, gi, gj, signo):
    for k, v in ((i, (gi, gj)), (j, (gj, gi))):
        gf, gc = v
        L["pj"][k] += signo
        L["gf"][k] += signo * gf
        L["gc"][k] += signo * gc
        L["g"][k] += signo * (gf > gc)
        L["e"][k] += signo * (gf == gc)
        L["p"][k] += signo * (gf < gc)


def _res(p):
    return f"{p['local']} {p['gl']}-{p['gv']} {p['visita']}"


def _sortear(rng):
    pesos = np.array([t[1] for t in TIPOS], dtype=float)
    return TIPOS[int(rng.choice(len(TIPOS), p=pesos / pesos.sum()))]


def _armar(rng, p, clave, club, rival):
    titulo, texto = TEXTOS[clave][int(rng.integers(len(TEXTOS[clave])))]
    return titulo, texto.format(club=club, rival=rival, min=int(rng.integers(8, 86)), res=_res(p))


def revisar_liga(L, partidos, rng):
    """Después de jugar una fecha de liga: con probabilidad bajísima, un partido tiene un
    incidente. Si el club responsable pierde el partido, se corrige la tabla (3 puntos para el
    rival). `partidos` son los recién agregados al log de la liga L."""
    for p in partidos:
        if not _es_regular(p) or rng.random() >= PROB:
            continue
        clave, _, sancion = _sortear(rng)
        # el responsable suele ser el local (su hinchada, su estadio)
        local_culpa = rng.random() < 0.7
        club, rival = (p["local"], p["visita"]) if local_culpa else (p["visita"], p["local"])
        if clave in ("clima", "luz", "animales", "cancha", "logistica", "hinchada"):
            club = rival = None
        titulo, texto = _armar(rng, p, clave, club, rival)
        aviso = {"liga": p["liga"], "fecha": p["fecha"], "rotulo": p["rotulo"], "local": p["local"],
                 "visita": p["visita"], "clave": clave, "titulo": titulo, "texto": texto, "club": club,
                 "sancion": ""}
        if sancion and sancion != "quita9":             # partido perdido para el responsable
            nom = L["nombres"]
            i, j = nom.index(p["local"]), nom.index(p["visita"])
            _sumar(L, i, j, p["gl"], p["gv"], -1)
            gana_local = rival == p["local"]
            g_riv = max(p["gl"] if gana_local else p["gv"], 1)
            g_cul = min(p["gv"] if gana_local else p["gl"], g_riv - 1)
            p["gl"], p["gv"] = (g_riv, g_cul) if gana_local else (g_cul, g_riv)
            p["gana"] = rival
            _sumar(L, i, j, p["gl"], p["gv"], 1)
            aviso["sancion"] = f"Partido perdido para {club}: el Tribunal le dio los 3 puntos a {rival} ({_res(p)})."
        quita = {"pierde+3": 3, "pierde+6": 6, "quita9": 9}.get(sancion, 0)
        if sancion == "gravisimo":
            if p["liga"] in ("Primera C", "Regional Amateur"):   # no hay categoría más abajo
                quita = 12
            else:
                L.setdefault("desc_adm", []).append(club)
                aviso["sancion"] += f" Además, {club} perderá la categoría al terminar la temporada."
        if quita:
            q = L.setdefault("quita", {})
            q[club] = q.get(club, 0) + quita
            aviso["sancion"] = (aviso["sancion"] + f" Quita de {quita} puntos para {club}.").strip()
        if not sancion:
            aviso["sancion"] = "Sin sanción: el resultado se mantiene."
        p["incidente"] = titulo
        L.setdefault("alertas", []).append(aviso)


def revisar_copa(SC, llaves, rng):
    """Copa: si hay un incidente con sanción, el responsable queda eliminado y pasa el rival.
    `llaves` son los cruces recién jugados (con 'p' y 'gana')."""
    nom = SC["nombres"]
    for m in llaves:
        p = m["p"]
        if rng.random() >= PROB:
            continue
        clave, _, sancion = _sortear(rng)
        culpa_a = rng.random() < 0.5
        i_cul, i_riv = (m["a"], m["b"]) if culpa_a else (m["b"], m["a"])
        club, rival = nom[i_cul], nom[i_riv]
        if clave in ("clima", "luz", "animales", "cancha", "logistica", "hinchada"):
            club = rival = None
        titulo, texto = _armar(rng, p, clave, club, rival)
        aviso = {"liga": p["liga"], "fecha": p["fecha"], "rotulo": p["rotulo"], "local": p["local"],
                 "visita": p["visita"], "clave": clave, "titulo": titulo, "texto": texto, "club": club,
                 "sancion": "Sin sanción: el resultado se mantiene."}
        if sancion:
            m["gana"] = i_riv
            p["gana"] = rival
            p["tanda"], p["pen"] = None, None
            if p["local"] == rival:
                p["gl"], p["gv"] = max(p["gl"], 1), min(p["gv"], max(p["gl"], 1) - 1)
            else:
                p["gv"], p["gl"] = max(p["gv"], 1), min(p["gl"], max(p["gv"], 1) - 1)
            baja = sancion == "gravisimo" and SC["origen"][i_cul] not in ("Primera C", "Regional Amateur")
            aviso["sancion"] = (f"{club} quedó eliminado de la Copa Argentina: pasa {rival}."
                                + (" Además, perderá la categoría al terminar la temporada." if baja else ""))
            if baja:
                SC.setdefault("desc_adm", []).append(club)
        p["incidente"] = titulo
        SC.setdefault("alertas", []).append(aviso)

"""Motor de carrera y ofertas del Modo Manager (va en motor/ofertas.py). Sin Streamlit: sólo numpy.

GLOBAL (20-90, la misma escala que la media de los clubes): define de qué clubes te llaman.
    global ~ 28 -> Regional, Promocional y Primera C      global ~ 58 -> Primera Nacional y piso de Primera
    global ~ 42 -> Primera B y Federal A                  global ~ 76 -> Primera División (los grandes)

OFERTAS: llegan durante toda la carrera, tanto si estás libre como si ya dirigís un club
(libre: P_OFERTA_DIA por día jugado; con club: P_OFERTA_EMPLEADO). Cada oferta trae un ROL:
    "primer_equipo" -> te contratan como DT del primer equipo.
    "reserva"       -> entrás como DT de la Reserva; el club suele ser más grande que tu global.
                       Cuanto más grande el club respecto de tu global, más probable que sea reserva.

ASCENSO A DT DEL PRIMER EQUIPO: si estás en la Reserva, pasados MIN_DIAS_RESERVA días jugados el club
puede echar al DT y subirte. La chance diaria sube si al club le va mal en su liga (puntos por partido
bajos) y a los MAX_DIAS_RESERVA días el ascenso está garantizado.

Estado del manager (dict M, lo guarda la interfaz): global, club (None = libre), rol, dias_en_rol,
ofertas, rechazos {club: fecha hasta la que no vuelve a ofrecer}, historial_clubes, registro, hoy.
"""

import datetime as dt
import math

import numpy as np

GLOBAL_MIN, GLOBAL_MAX = 20, 90

# Reputación -> global inicial (si no se pone a mano)
PRESETS = {
    "Desconocido": 28,
    "Ex jugador de ascenso": 42,
    "Ex jugador profesional": 58,
    "Ex estrella": 76,
}

ROLES = {"primer_equipo": "DT del primer equipo", "reserva": "DT de la Reserva"}

P_OFERTA_DIA = 0.30        # chance de oferta nueva cada día jugado, estando libre
P_OFERTA_EMPLEADO = 0.12   # ... y estando en un club
MAX_OFERTAS = 3            # ofertas pendientes a la vez en la oficina
VIGENCIA_DIAS = 21         # días corridos que dura una oferta
RECHAZO_DIAS = 60          # un club al que le dijiste que no (o que dejaste) no llama por un tiempo
SIGMA = 5.0                # qué tan estricto es el encaje entre el global y la media del club
VENTANA = 8                # "alcance" que se le muestra al usuario: clubes a ±8 de su global

MIN_DIAS_RESERVA = 6       # días jugados mínimos en la Reserva antes de que puedan subirte
MAX_DIAS_RESERVA = 30      # a estos días jugados el ascenso es seguro
P_ASCENSO_BASE = 0.05      # chance diaria de que echen al DT (club que va bien)
P_ASCENSO_MALA = 0.20      # ... que se suma, en escala, cuando al club le va mal

CATEGORIAS = ["Primera División", "Primera Nacional", "Federal A", "Primera B", "Primera C",
              "Promocional Amateur", "Regional Amateur"]

MENSAJES = {
    "primer_equipo": [
        "La directiva de {club} quiere que seas su nuevo entrenador.",
        "{club} necesita un cambio de rumbo y piensa en vos para el cargo.",
        "El presidente de {club} te llamó personalmente para ofrecerte el banco.",
        "{club} te sigue hace tiempo y te hace una propuesta formal.",
        "Se cayó el contrato del técnico de {club} y te quieren a vos.",
    ],
    "reserva": [
        "{club} te ofrece dirigir la Reserva: están armando un proyecto a largo plazo.",
        "En {club} te quieren en el cuerpo técnico, a cargo de la Reserva, y ven que podés llegar más arriba.",
        "{club} te propone dirigir la Reserva y trabajar pegado al primer equipo.",
        "La dirigencia de {club} te ofrece la Reserva: es la puerta de entrada al club.",
    ],
}

MENSAJES_ASCENSO = {
    "mala": [
        "{club} no levanta cabeza: la directiva echó al técnico y te subió a DT del primer equipo.",
        "Tras la racha de malos resultados, {club} despidió a su técnico y te puso a vos al mando.",
    ],
    "normal": [
        "En {club} hubo cambio de rumbo: echaron al técnico y la directiva te ascendió a DT del primer equipo.",
        "{club} se separó de su técnico y confió en vos para dirigir al primer equipo.",
    ],
}


def nivel_texto(g):
    return ("Debutante" if g <= 32 else "Del ascenso" if g <= 48 else "De categoría" if g <= 62
            else "De primer nivel" if g <= 72 else "Estrella")


# ---- Lectura del estado del simulador ---------------------------------------
def ligas(S):
    """{categoría: (estado de la liga, nombres)}."""
    out = {
        "Primera División": (S, S["nombres"]),
        "Primera Nacional": (S["b"], S["b"]["nombres"]),
        "Federal A": (S["f"], S["f"]["nombres"]),
        "Primera B": (S["pb"], S["pb"]["nombres"]),
        "Primera C": (S["pc"], S["pc"]["nombres"]),
    }
    if S.get("pd"):
        out["Promocional Amateur"] = (S["pd"], S["pd"]["nombres"])
    out["Regional Amateur"] = (S["reg"], S["reg"]["nombres"])
    return out


def medias_por_categoria(S):
    return {cat: {n: float(m) for n, m in zip(L["nombres"], L["r"])} for cat, (L, _) in ligas(S).items()}


def categoria_de(S, club):
    for cat, (_, nombres) in ligas(S).items():
        if club in nombres:
            return cat
    return None


def info_club(S, club):
    """(categoría, media, puesto por media dentro de la categoría, cantidad de clubes)."""
    cat = categoria_de(S, club)
    meds = medias_por_categoria(S)[cat]
    orden = sorted(meds, key=lambda n: -meds[n])
    return cat, meds[club], orden.index(club) + 1, len(orden)


def perfil_club(puesto, total):
    q = puesto / max(total, 1)
    return "Grande de la categoría" if q <= 0.25 else "Mitad de tabla" if q <= 0.65 else "Humilde de la categoría"


def objetivo(cat, puesto, total, rol="primer_equipo"):
    """Objetivo que le pone la directiva según qué tan grande es el club en su categoría."""
    if rol == "reserva":
        return "Trabajar con los juveniles y estar listo por si el club hace un cambio"
    q = puesto / max(total, 1)
    if q <= 0.25:
        return {"Primera División": "Pelear el título y clasificar a la Libertadores",
                "Regional Amateur": "Ganar la región y subir al Federal A"}.get(cat, "Pelear el ascenso")
    if q <= 0.65:
        return "Terminar en mitad de tabla"
    return "Hacer una campaña digna" if cat in ("Promocional Amateur", "Regional Amateur") else "Evitar el descenso"


def alcance(S, g):
    """{categoría: cantidad de clubes con media a ±VENTANA del global} (sólo las que tienen alguno)."""
    out = {}
    for cat, meds in medias_por_categoria(S).items():
        n = sum(1 for m in meds.values() if abs(m - g) <= VENTANA)
        if n:
            out[cat] = n
    return out


def rendimiento(S, club):
    """Cómo le va al club en su liga: 0 = el peor (por puntos por partido), 1 = el mejor.
    None si todavía no jugó o si la liga no expone sus estadísticas."""
    cat = categoria_de(S, club)
    if cat is None:
        return None
    L, nombres = ligas(S)[cat]
    try:
        pj, g, e = (np.asarray(L[k], float) for k in ("pj", "g", "e"))
    except (KeyError, TypeError, ValueError):
        return None
    i = nombres.index(club)
    if i >= len(pj) or pj[i] <= 0:
        return None
    jugaron = pj > 0
    ppg = (3 * g + e) / np.maximum(pj, 1)
    return float((ppg[jugaron] < ppg[i]).sum() / max(int(jugaron.sum()) - 1, 1))


# ---- Estado y ofertas -------------------------------------------------------
def nuevo_manager_estado(g):
    return {"global": int(g), "club": None, "rol": None, "dias_en_rol": 0, "ofertas": [], "rechazos": {},
            "historial_clubes": [], "registro": [], "sig_oferta": 1, "hoy": None}


def _rol_de_oferta(media, g, rng):
    """Cuanto más grande es el club respecto del global, más probable que te lo ofrezcan para la Reserva."""
    p_reserva = min(max((media - g + 2) / 10.0, 0.0), 1.0)
    return "reserva" if rng.random() < p_reserva else "primer_equipo"


def generar_oferta(S, M, rng, hoy):
    """Una oferta nueva de un club que encaje con el global del manager, o None."""
    g = M["global"]
    excluidos = {o["club"] for o in M["ofertas"]}
    if M.get("club"):
        excluidos.add(M["club"])
    excluidos |= {c for c, hasta in M.get("rechazos", {}).items() if hasta >= hoy}
    medias = medias_por_categoria(S)
    pesos = {}
    for cat, meds in medias.items():
        w = {n: math.exp(-0.5 * ((m - g) / SIGMA) ** 2) for n, m in meds.items() if n not in excluidos}
        if w:
            pesos[cat] = w
    if not pesos:
        return None
    cats = list(pesos)
    wc = np.array([max(pesos[c].values()) for c in cats])
    if wc.sum() < 1e-3:
        return None
    cat = cats[int(rng.choice(len(cats), p=wc / wc.sum()))]
    clubes = list(pesos[cat])
    wk = np.array([pesos[cat][c] for c in clubes])
    club = clubes[int(rng.choice(len(clubes), p=wk / wk.sum()))]
    rol = _rol_de_oferta(medias[cat][club], g, rng)
    oferta = {"id": M["sig_oferta"], "club": club, "rol": rol, "recibida": hoy,
              "vence": hoy + dt.timedelta(days=VIGENCIA_DIAS),
              "mensaje": MENSAJES[rol][int(rng.integers(len(MENSAJES[rol])))].format(club=club)}
    M["sig_oferta"] += 1
    return oferta


def _promover(S, M, rng):
    """El club echa al DT y te sube a DT del primer equipo. Devuelve el texto del evento."""
    club = M["club"]
    r = rendimiento(S, club)
    tono = "mala" if (r is not None and r < 0.35) else "normal"
    M["rol"] = "primer_equipo"
    M["dias_en_rol"] = 0
    for h in reversed(M["historial_clubes"]):
        if h["club"] == club and h["hasta"] is None:
            h["ascendido"] = M["hoy"]
            break
    textos = MENSAJES_ASCENSO[tono]
    return textos[int(rng.integers(len(textos)))].format(club=club)


def nuevo_dia(S, M, hoy, rng):
    """Después de jugar un día: vencen las ofertas viejas, puede llegar una nueva (estés libre o en un
    club) y, si estás en la Reserva, puede que te suban. Devuelve {"nuevas", "vencidas", "eventos"}."""
    M["hoy"] = hoy
    res = {"nuevas": [], "vencidas": [], "eventos": []}
    res["vencidas"] = [o for o in M["ofertas"] if o["vence"] < hoy]
    M["ofertas"] = [o for o in M["ofertas"] if o["vence"] >= hoy]

    if M.get("club") and M.get("rol") == "reserva":
        M["dias_en_rol"] += 1
        if M["dias_en_rol"] >= MIN_DIAS_RESERVA:
            r = rendimiento(S, M["club"])
            mala = 0.5 if r is None else 1.0 - r
            p = P_ASCENSO_BASE + P_ASCENSO_MALA * mala
            if M["dias_en_rol"] >= MAX_DIAS_RESERVA or rng.random() < p:
                res["eventos"].append(_promover(S, M, rng))

    p_oferta = P_OFERTA_EMPLEADO if M.get("club") else P_OFERTA_DIA
    if len(M["ofertas"]) < MAX_OFERTAS and rng.random() < p_oferta:
        o = generar_oferta(S, M, rng, hoy)
        if o:
            M["ofertas"].append(o)
            res["nuevas"].append(o)
    return res


def _cerrar_club_actual(M):
    club = M["club"]
    for h in reversed(M["historial_clubes"]):
        if h["club"] == club and h["hasta"] is None:
            h["hasta"] = M["hoy"]
            break
    M["rechazos"][club] = M["hoy"] + dt.timedelta(days=RECHAZO_DIAS)


def aceptar(S, M, oferta):
    """Aceptás una oferta (si ya tenías club, lo dejás). Las demás ofertas se caen."""
    if M.get("club"):
        _cerrar_club_actual(M)
    M["club"] = oferta["club"]
    M["rol"] = oferta["rol"]
    M["dias_en_rol"] = 0
    M["ofertas"] = []
    M["historial_clubes"].append({"club": oferta["club"], "categoria": categoria_de(S, oferta["club"]),
                                  "rol": oferta["rol"], "temporada": S["temp"], "desde": M["hoy"],
                                  "hasta": None, "ascendido": None})


def rechazar(M, oferta):
    M["ofertas"] = [o for o in M["ofertas"] if o["id"] != oferta["id"]]
    M["rechazos"][oferta["club"]] = M["hoy"] + dt.timedelta(days=RECHAZO_DIAS)


def renunciar(M):
    """Dejás el club y quedás libre otra vez."""
    _cerrar_club_actual(M)
    M["club"] = None
    M["rol"] = None
    M["dias_en_rol"] = 0

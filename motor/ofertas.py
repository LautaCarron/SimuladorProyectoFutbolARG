"""Motor de ofertas del Modo Manager (va en motor/ofertas.py). Sin Streamlit: sólo numpy.

Idea: el manager tiene un GLOBAL (20-90, la misma escala que la media de los clubes). Cuando está
libre, cada día que se juega puede llegarle una oferta en la oficina, y de qué club llega depende
de su global: cuanto más global, más arriba vienen las ofertas.

    global ~ 28  -> clubes del Regional, Promocional y Primera C
    global ~ 42  -> Primera B y Federal A (alguna de Primera C o de B Nacional)
    global ~ 58  -> Primera Nacional y el piso de Primera
    global ~ 76  -> Primera División (los grandes)

El global se pone a mano o sale de la reputación (PRESETS). Cómo se elige el club de una oferta:
primero una categoría (pesa por su club que mejor encaja con el global) y después un club de esa
categoría (pesa por qué tan cerca está su media del global). Así una liga con muchos clubes
(el Regional tiene 264) no se come todas las ofertas.

Estado del manager (dict M, lo guarda la interfaz): global, club (None = libre), ofertas,
rechazos {club: fecha hasta la que no vuelve a ofrecer}, historial_clubes, registro, hoy, sig_oferta.
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

P_OFERTA_DIA = 0.30        # probabilidad de que llegue una oferta nueva cada día que se juega
MAX_OFERTAS = 3            # ofertas pendientes a la vez en la oficina
VIGENCIA_DIAS = 21         # días corridos que dura una oferta
RECHAZO_DIAS = 60          # un club al que le dijiste que no, no vuelve a llamar por un tiempo
SIGMA = 5.0                # qué tan estricto es el encaje entre el global y la media del club
VENTANA = 8                # "alcance" que se le muestra al usuario: clubes a ±8 de su global

CATEGORIAS = ["Primera División", "Primera Nacional", "Federal A", "Primera B", "Primera C",
              "Promocional Amateur", "Regional Amateur"]

MENSAJES = [
    "La directiva de {club} quiere que seas su nuevo entrenador.",
    "{club} necesita un cambio de rumbo y piensa en vos para el cargo.",
    "El presidente de {club} te llamó personalmente para ofrecerte el banco.",
    "{club} te sigue hace tiempo y te hace una propuesta formal.",
    "Se cayó el contrato del técnico de {club} y te quieren a vos.",
]


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


def objetivo(cat, puesto, total):
    """Objetivo que le pone la directiva según qué tan grande es el club en su categoría."""
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


# ---- Ofertas ----------------------------------------------------------------
def nuevo_manager_estado(g):
    return {"global": int(g), "club": None, "ofertas": [], "rechazos": {}, "historial_clubes": [],
            "registro": [], "sig_oferta": 1, "hoy": None}


def generar_oferta(S, M, rng, hoy):
    """Una oferta nueva de un club que encaje con el global del manager, o None."""
    g = M["global"]
    excluidos = {o["club"] for o in M["ofertas"]}
    if M.get("club"):
        excluidos.add(M["club"])
    excluidos |= {c for c, hasta in M.get("rechazos", {}).items() if hasta >= hoy}
    pesos = {}
    for cat, meds in medias_por_categoria(S).items():
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
    oferta = {"id": M["sig_oferta"], "club": club, "recibida": hoy,
              "vence": hoy + dt.timedelta(days=VIGENCIA_DIAS),
              "mensaje": MENSAJES[int(rng.integers(len(MENSAJES)))].format(club=club)}
    M["sig_oferta"] += 1
    return oferta


def nuevo_dia(S, M, hoy, rng):
    """Después de jugar un día: vencen las ofertas viejas y puede llegar una nueva.
    Devuelve (ofertas nuevas, ofertas vencidas). Sólo si el manager está libre."""
    M["hoy"] = hoy
    if M.get("club"):
        return [], []
    vencidas = [o for o in M["ofertas"] if o["vence"] < hoy]
    M["ofertas"] = [o for o in M["ofertas"] if o["vence"] >= hoy]
    nuevas = []
    if len(M["ofertas"]) < MAX_OFERTAS and rng.random() < P_OFERTA_DIA:
        o = generar_oferta(S, M, rng, hoy)
        if o:
            M["ofertas"].append(o)
            nuevas.append(o)
    return nuevas, vencidas


def aceptar(S, M, oferta):
    hoy = M["hoy"]
    M["club"] = oferta["club"]
    M["ofertas"] = []
    M["historial_clubes"].append({"club": oferta["club"], "categoria": categoria_de(S, oferta["club"]),
                                  "temporada": S["temp"], "desde": hoy, "hasta": None})


def rechazar(M, oferta):
    M["ofertas"] = [o for o in M["ofertas"] if o["id"] != oferta["id"]]
    M["rechazos"][oferta["club"]] = M["hoy"] + dt.timedelta(days=RECHAZO_DIAS)


def renunciar(M):
    """Deja el club y queda libre otra vez (el club no vuelve a llamar por un tiempo)."""
    club = M["club"]
    for h in reversed(M["historial_clubes"]):
        if h["club"] == club and h["hasta"] is None:
            h["hasta"] = M["hoy"]
            break
    M["rechazos"][club] = M["hoy"] + dt.timedelta(days=RECHAZO_DIAS)
    M["club"] = None

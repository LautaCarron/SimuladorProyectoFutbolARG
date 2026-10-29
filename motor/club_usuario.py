"""Ciclo de vida del club propio dentro de la partida (sin Streamlit).

El club se crea desde la pestaña Partidas y vive en la partida (`S`), así que se guarda en el `.afa` y desaparece con
una partida nueva:

  S["club_pendiente"]  club creado esta temporada: entra cuando empieza la temporada que viene (el del
                       interior al Regional Amateur, el metropolitano al Promocional Amateur).
  S["club_propio"]     club que juega hoy (datos en datos/club_propio.py). Con "baja": True pierde 0-3 todo lo que le
                       queda por jugar (motor.nucleo.jugar, por su media WO_RATING) y se va al cerrar la temporada.
  S["clubes_ex"]       clubes propios que se fueron y dejaron títulos: sólo quedan nombre y escudo, para el palmarés.

Los títulos se anotan por nombre, así que un club propio nunca puede llamarse igual que otro del palmarés: si pide un
nombre ya usado se le agrega "(propio)" (datos.club_propio.nombre_unico).
"""

import numpy as np

from datos import club_propio as cp


def activar(S):
    """Deja a disposición de las funciones de datos el club de esta partida (se llama en cada pasada de la app)."""
    cp.activar(S.get("club_propio"), S.get("clubes_ex"))


def nombres_ocupados(S):
    """Nombres que un club nuevo no puede repetir: los de siempre, el propio, el pendiente y los del palmarés."""
    usados = set(cp.nombres_ocupados()) | {x["nombre"] for x in S.get("clubes_ex", [])}
    usados |= {c["nombre"] for c in (S.get("club_propio"), S.get("club_pendiente")) if c}
    return usados


def puede_crear(S):
    """Se puede crear un club si no hay otro (en juego, no dado de baja) ni uno pendiente."""
    propio = S.get("club_propio")
    return not S.get("club_pendiente") and not (propio and not propio.get("baja"))


def crear_pendiente(S, club):
    S["club_pendiente"] = dict(club)


def cancelar_pendiente(S):
    S["club_pendiente"] = None


def _tablas_con_media(S):
    """Cada liga o copa del estado que guarda un vector de medias `r` junto con sus `nombres`."""
    yield S
    for v in S.values():
        if isinstance(v, dict) and isinstance(v.get("r"), np.ndarray) and "nombres" in v:
            yield v


def dar_de_baja(S):
    """El club deja de jugar: lo que le quede por jugar este año lo pierde 3-0 y desaparece al cerrar la temporada."""
    club = S.get("club_propio")
    if not club or club.get("baja"):
        return
    club["baja"] = True
    nombre = club["nombre"]
    S["rating"][nombre] = cp.WO_RATING
    for T in _tablas_con_media(S):
        nombres = list(T["nombres"])
        if nombre in nombres:
            T["r"][nombres.index(nombre)] = cp.WO_RATING


def _en_palmares(S, nombre):
    """¿Figura con algún título? (palmarés de ligas y copas, o campeón regional en el historial)."""
    if any(nombre in d for k, d in S.items() if k.startswith("hist_") and isinstance(d, dict)):
        return True
    return any(nombre == v or (isinstance(v, dict) and nombre in v.values())
               for fila in S.get("campeones", []) for v in fila.values())


def _quitar(S, SB, nombre):
    """Saca al club de las listas de la temporada que viene. Su lugar NO se cubre solo: la liga queda con uno menos
    (si se quiere reponer, se suma un ascenso o se cambia el tamaño desde el Modo dios)."""
    for lista in (S["nombres"], SB["nombres"], S["federal"], S["primera_b"], S["primera_c"], S["promocional"],
                  S["regional"], S.get("federal_b", [])):
        if nombre in lista:
            lista.remove(nombre)


def cerrar_temporada(S, SB):
    """Entre el cierre de una temporada y el armado de la siguiente: se va el club dado de baja y entra el pendiente."""
    propio = S.get("club_propio")
    if propio and propio.get("baja"):
        _quitar(S, SB, propio["nombre"])
        S["rating"].pop(propio["nombre"], None)
        if _en_palmares(S, propio["nombre"]):          # sólo quedan su nombre y su escudo, en el palmarés
            S.setdefault("clubes_ex", []).append({"nombre": propio["nombre"], "escudo": propio.get("escudo", "")})
        S["club_propio"] = None
    nuevo = S.get("club_pendiente")
    if nuevo and not S.get("club_propio"):
        S["club_propio"] = {**nuevo, "baja": False}
        S["club_pendiente"] = None
        S["rating"][nuevo["nombre"]] = float(nuevo["media"])
        # el metropolitano arranca en el Promocional Amateur; el del interior, en el Regional
        S["promocional" if nuevo.get("origen", cp.INTERIOR) == cp.METROPOLITANA else "regional"].append(nuevo["nombre"])
    activar(S)                                         # la región y la liga del nuevo se leen al armar el Regional

"""Calendario de la temporada: qué día se juega cada fecha de cada liga y cada ronda de la
Copa Argentina, como en la vida real.

* La temporada 1 es 2026, la 2 es 2027, etc.
* Cada liga juega un día fijo del fin de semana, una fecha por semana desde su arranque.
  Si una liga tiene más fechas que fines de semana hasta mitad de diciembre, suma fechas
  entre semana (miércoles) repartidas en toda la temporada.
* Las copas por rondas (Copa Argentina, Supercopa, Mundial de Clubes) fijan sus días en
  competencias.py; acá solo se consulta el registro.
* Las fechas extra (desempates) van la semana siguiente a la última programada.
"""

import datetime as dt

from copas.registro import REGISTRO, por_nombre
from motor.fechas import INICIO, anio, desde, dia_liga, total_liga
from copas.conmebol import listo, simular_ronda_int
from ligas.federal import simular_fecha_f
from ligas.nacional import simular_fecha_b, total_b
from ligas.primera import primera_terminada, simular_fecha
from ligas.regional import simular_fecha_reg
from ligas.simples import simular_fecha_liga, tabla_pb, tabla_pc, tabla_pd

_MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
          "octubre", "noviembre", "diciembre"]
_DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
_DIAS_CORTOS = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]

# Copas CONMEBOL: (mes, a partir del día, día de la semana). Libertadores los martes,
# Sudamericana los jueves, finales únicas un sábado de noviembre, Recopa en febrero.
INT_DIAS = {
    "Copa Libertadores": [(2, 17, 1), (2, 24, 1), (3, 3, 1), (3, 10, 1), (4, 7, 1), (4, 14, 1), (4, 21, 1),
                          (5, 5, 1), (5, 19, 1), (5, 26, 1), (8, 11, 1), (8, 18, 1), (9, 15, 1), (9, 22, 1),
                          (10, 20, 1), (10, 27, 1), (11, 28, 5)],
    "Copa Sudamericana": [(4, 9, 3), (4, 16, 3), (4, 23, 3), (5, 7, 3), (5, 21, 3), (5, 28, 3), (7, 16, 3),
                          (7, 23, 3), (8, 13, 3), (8, 20, 3), (9, 17, 3), (9, 24, 3), (10, 22, 3), (10, 29, 3),
                          (11, 21, 5)],
    "Recopa Sudamericana": [(2, 19, 3), (2, 26, 3)],
}
_CLAVE_INT = {"Copa Libertadores": "lib", "Copa Sudamericana": "sud", "Recopa Sudamericana": "rec"}


def dia_de(S, liga, n):
    """Día (datetime.date) en que se juega la fecha n de una liga o la ronda n de una copa."""
    comp = por_nombre(liga)
    if comp:                                           # Copa Argentina, Supercopa, Mundial de Clubes
        return comp.dia(S, n)
    if liga in INT_DIAS:
        mes, dia, wd = INT_DIAS[liga][min(n, len(INT_DIAS[liga])) - 1]
        return desde(anio(S), mes, dia, wd)
    return dia_liga(S, liga, n)


def dia_partido(S, p):
    return dia_de(S, p["liga"], p["fecha"])


def texto_dia(d, largo=True):
    if d is None:
        return ""
    if largo:
        return f"{_DIAS[d.weekday()].capitalize()} {d.day} de {_MESES[d.month - 1]}"
    return f"{_DIAS_CORTOS[d.weekday()]} {d.day:02d}/{d.month:02d}"


def nombre_mes(m):
    return _MESES[m - 1].capitalize()


# ---------------------------------------------------------------- lo que viene en el calendario
def proximos(S):
    """Próximo evento pendiente de cada competición: {competición: (día, n)}."""
    SB = S["b"]
    pend = {}
    if not primera_terminada(S):
        pend["Primera División"] = S["fecha"] + 1
    if SB["fecha"] < total_b(SB) and not (SB["fecha"] == total_b(SB) - 1 and not primera_terminada(S)):
        pend["Primera Nacional"] = SB["fecha"] + 1
    for liga, L in (("Federal A", S["f"]), ("Primera B", S["pb"]), ("Primera C", S["pc"]),
                    ("Promocional Amateur", S["pd"]), ("Regional Amateur", S["reg"])):
        if L["fecha"] < L["total"]:
            pend[liga] = L["fecha"] + 1
    for comp in REGISTRO:
        n = comp.pendiente(S)
        if n is not None:
            pend[comp.nombre] = n
    if S.get("int"):
        for nombre, clave in _CLAVE_INT.items():
            if listo(S, clave):
                pend[nombre] = S["int"][clave]["ronda"] + 1
    return {c: (dia_de(S, c, n), n) for c, n in pend.items()}


def jugar_proximo_dia(S, P, acumular=True):
    """Juega todo lo programado para el próximo día del calendario (ligas y Copa)."""
    prox = proximos(S)
    if not prox:
        return None
    hoy = min(d for d, _ in prox.values())
    for _ in range(4):                                  # por si una liga tiene dos fechas ese día
        prox = proximos(S)
        hoy_c = [c for c, (d, _) in prox.items() if d == hoy]
        if not hoy_c:
            break
        for c in hoy_c:
            if c == "Primera División":
                simular_fecha(S, P, acumular)
            elif c == "Primera Nacional":
                simular_fecha_b(S, P)
            elif c == "Federal A":
                simular_fecha_f(S["f"], P, S["rng"])
            elif c == "Primera B":
                simular_fecha_liga(S["pb"], P, S["rng"], "Primera B", tabla_pb)
            elif c == "Primera C":
                simular_fecha_liga(S["pc"], P, S["rng"], "Primera C", tabla_pc)
            elif c == "Promocional Amateur":
                simular_fecha_liga(S["pd"], P, S["rng"], "Promocional Amateur", tabla_pd)
            elif c == "Regional Amateur":
                simular_fecha_reg(S["reg"], P, S["rng"])
            elif por_nombre(c):
                por_nombre(c).jugar(S, P, S["rng"])
            elif c in _CLAVE_INT:
                simular_ronda_int(S, _CLAVE_INT[c], P, S["rng"])
    return hoy

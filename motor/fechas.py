"""Días de juego de cada liga (calendario base de la temporada).

Cada liga juega un día fijo del fin de semana, una fecha por semana desde su arranque; si tiene más fechas
que fines de semana hasta mitad de diciembre, suma fechas entre semana (miércoles) repartidas en toda la
temporada. Las fechas extra (desempates) van la semana siguiente a la última programada.
Lo usan calendario.py y competencias.py (la Supercopa se juega después de la última fecha de Primera).
"""

import datetime as dt

from ligas.nacional import total_b
from ligas.primera import total_primera

# Arranque de cada liga: (mes, día a partir del cual, día de la semana: 0 = lunes ... 6 = domingo)
INICIO = {
    "Primera División": (1, 24, 6),     # domingos desde fines de enero
    "Primera Nacional": (2, 7, 5),      # sábados desde febrero
    "Federal A": (3, 14, 6),            # domingos desde marzo
    "Primera B": (2, 7, 5),             # sábados
    "Primera C": (2, 21, 5),            # sábados
    "Promocional Amateur": (3, 1, 5),   # sábados desde marzo
    "Regional Amateur": (6, 6, 6),      # domingos desde junio
}
FIN_TEMPORADA = (12, 13)                # las ligas terminan a más tardar a mediados de diciembre


def anio(S):
    return 2025 + S["temp"]


def desde(y, mes, dia, wd):
    d = dt.date(y, mes, dia)
    return d + dt.timedelta(days=(wd - d.weekday()) % 7)


def total_liga(S, liga):
    """Cantidad de fechas que tiene hoy la liga (con sus desempates, si los hubo)."""
    return {"Primera División": lambda: total_primera(S), "Primera Nacional": lambda: total_b(S["b"]),
            "Federal A": lambda: S["f"]["total"], "Primera B": lambda: S["pb"]["total"],
            "Primera C": lambda: S["pc"]["total"], "Promocional Amateur": lambda: S["pd"]["total"],
            "Regional Amateur": lambda: S["reg"]["total"]}[liga]()


def _dias_liga(S, liga):
    y = anio(S)
    mes, dia, wd = INICIO[liga]
    ini = desde(y, mes, dia, wd)
    fin = dt.date(y, *FIN_TEMPORADA)
    semanas = []
    d = ini
    while d <= fin:
        semanas.append(d)
        d += dt.timedelta(weeks=1)
    total = total_liga(S, liga)
    if total <= len(semanas):
        return semanas
    # más fechas que fines de semana: se suman miércoles, repartidos en toda la temporada
    todos = sorted(semanas + [s - dt.timedelta(days=(s.weekday() - 2) % 7 or 7) for s in semanas[1:]])
    if total >= len(todos):
        return todos
    return [todos[round(i * (len(todos) - 1) / (total - 1))] for i in range(total)]


def dia_liga(S, liga, n):
    """Día (datetime.date) de la fecha n de una liga."""
    if liga == "Promoción":                            # la juega el perdedor de la final de la B
        liga = "Primera Nacional"
    if liga not in INICIO:
        return None
    dias = _dias_liga(S, liga)
    if n <= len(dias):
        return dias[n - 1]
    return dias[-1] + dt.timedelta(weeks=n - len(dias))

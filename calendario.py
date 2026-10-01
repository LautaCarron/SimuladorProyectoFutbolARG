"""Calendario de la temporada: qué día se juega cada fecha de cada liga y cada ronda de la
Copa Argentina, como en la vida real.

* La temporada 1 es 2026, la 2 es 2027, etc.
* Cada liga juega un día fijo del fin de semana, una fecha por semana desde su arranque.
  Si una liga tiene más fechas que fines de semana hasta mitad de diciembre, suma fechas
  entre semana (miércoles) repartidas en toda la temporada.
* La Copa Argentina se juega los miércoles, en el medio de las ligas (de marzo a noviembre).
* La Supercopa Argentina se juega el miércoles después de la última fecha de Primera.
* Las fechas extra (desempates) van la semana siguiente a la última programada.
"""

import datetime as dt

_MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
          "octubre", "noviembre", "diciembre"]
_DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
_DIAS_CORTOS = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]

# Arranque de cada liga: (mes, día a partir del cual, día de la semana: 0 = lunes ... 6 = domingo)
INICIO = {
    "Primera División": (1, 24, 6),     # domingos desde fines de enero
    "Primera Nacional": (2, 7, 5),      # sábados desde febrero
    "Federal A": (3, 14, 6),            # domingos desde marzo
    "Primera B": (2, 7, 5),             # sábados
    "Primera C": (2, 21, 5),            # sábados
    "Regional Amateur": (6, 6, 6),      # domingos desde junio
}
FIN_TEMPORADA = (12, 13)                # las ligas terminan a más tardar a mediados de diciembre
# Copa Argentina: 64avos, 32avos, 16avos, octavos, cuartos, semifinales y final (miércoles)
COPA_DIAS = [(3, 4), (4, 8), (5, 13), (6, 24), (8, 12), (9, 23), (11, 4)]
COPA = "Copa Argentina"
SUPERCOPA = "Supercopa Argentina"
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


def anio(S):
    return 2025 + S["temp"]


def _desde(y, mes, dia, wd):
    d = dt.date(y, mes, dia)
    return d + dt.timedelta(days=(wd - d.weekday()) % 7)


def total_liga(S, liga):
    """Cantidad de fechas que tiene hoy la liga (con sus desempates, si los hubo)."""
    from torneos import total_b, total_primera
    return {"Primera División": lambda: total_primera(S), "Primera Nacional": lambda: total_b(S["b"]),
            "Federal A": lambda: S["f"]["total"], "Primera B": lambda: S["pb"]["total"],
            "Primera C": lambda: S["pc"]["total"], "Regional Amateur": lambda: S["reg"]["total"]}[liga]()


def _dias_liga(S, liga):
    y = anio(S)
    mes, dia, wd = INICIO[liga]
    ini = _desde(y, mes, dia, wd)
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


def dia_de(S, liga, n):
    """Día (datetime.date) en que se juega la fecha n de una liga o la ronda n de la Copa."""
    if liga == COPA:
        mes, dia = COPA_DIAS[min(n, len(COPA_DIAS)) - 1]
        return _desde(anio(S), mes, dia, 2)
    if liga in INT_DIAS:
        mes, dia, wd = INT_DIAS[liga][min(n, len(INT_DIAS[liga])) - 1]
        return _desde(anio(S), mes, dia, wd)
    if liga == SUPERCOPA:                              # miércoles siguiente a la última fecha de Primera
        return dia_de(S, "Primera División", total_liga(S, "Primera División")) + dt.timedelta(days=3)
    if liga == "Promoción":                            # la juega el perdedor de la final de la B
        liga = "Primera Nacional"
    if liga not in INICIO:
        return None
    dias = _dias_liga(S, liga)
    if n <= len(dias):
        return dias[n - 1]
    return dias[-1] + dt.timedelta(weeks=n - len(dias))


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
    from torneos import primera_terminada, total_b
    SB = S["b"]
    pend = {}
    if not primera_terminada(S):
        pend["Primera División"] = S["fecha"] + 1
    if SB["fecha"] < total_b(SB) and not (SB["fecha"] == total_b(SB) - 1 and not primera_terminada(S)):
        pend["Primera Nacional"] = SB["fecha"] + 1
    for liga, L in (("Federal A", S["f"]), ("Primera B", S["pb"]), ("Primera C", S["pc"]),
                    ("Regional Amateur", S["reg"])):
        if L["fecha"] < L["total"]:
            pend[liga] = L["fecha"] + 1
    SC = S.get("copa")
    if SC and SC["sorteada"] and SC["ronda"] < SC["total"]:
        pend[COPA] = SC["ronda"] + 1
    if S.get("supercopa"):
        from copas import supercopa_lista
        if supercopa_lista(S):
            pend[SUPERCOPA] = 1
    if S.get("int"):
        from internacional import listo
        for nombre, clave in _CLAVE_INT.items():
            if listo(S, clave):
                pend[nombre] = S["int"][clave]["ronda"] + 1
    return {c: (dia_de(S, c, n), n) for c, n in pend.items()}


def jugar_proximo_dia(S, P, acumular=True):
    """Juega todo lo programado para el próximo día del calendario (ligas y Copa)."""
    from copas import simular_ronda_copa, simular_supercopa
    from torneos import (simular_fecha, simular_fecha_b, simular_fecha_f, simular_fecha_liga,
                         simular_fecha_reg, tabla_pb, tabla_pc)
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
            elif c == "Regional Amateur":
                simular_fecha_reg(S["reg"], P, S["rng"])
            elif c == COPA:
                simular_ronda_copa(S["copa"], P, S["rng"])
            elif c == SUPERCOPA:
                simular_supercopa(S, P, S["rng"])
            elif c in _CLAVE_INT:
                from internacional import simular_ronda_int
                simular_ronda_int(S, _CLAVE_INT[c], P, S["rng"])
    return hoy

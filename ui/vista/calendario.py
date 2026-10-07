"""Calendario del mes: partidos y eventos de cada día.
"""

from motor.calendario import dia_de, texto_dia
from datos.logos import logo_img
from ligas.federal import rotulo_f
from ligas.nacional import rotulo_b
from ligas.primera import rotulo_p
from ligas.regional import rotulo_reg
from ui.vista.base import crest, esc
from ui.vista.copas_int import _INT_CLAVE, _int_pendientes
from ui.vista.mi_club import mi_club
from ui.vista.partidos import (
    partidos_fecha_b,
    partidos_fecha_f,
    partidos_fecha_p,
    partidos_fecha_pb,
    partidos_fecha_pc,
    partidos_fecha_pd,
    partidos_fecha_reg,
    pendiente,
)
from motor.calendario import INICIO, total_liga
from copas.registro import REGISTRO, por_nombre


# ---- Calendario del mes ----
def _cal_partidos(S, liga, n):
    """Partidos (jugados o por jugar) de la fecha n de una liga, o la ronda n de la Copa."""
    if liga in _INT_CLAVE:
        C = S["int"][_INT_CLAVE[liga]]
        return [p for p in C["log"] if p["fecha"] == n] or _int_pendientes(C, n)
    comp = por_nombre(liga)
    if comp:                                       # Copa Argentina, Supercopa, Mundial de Clubes
        hechos = [p for p in comp.log(S) if p["fecha"] == n]
        return hechos or [pendiente(liga, n, rot, cmp_, a, b) for a, b, rot, cmp_ in comp.cruces(S, n)]
    obtener = {"Primera División": partidos_fecha_p, "Primera Nacional": partidos_fecha_b,
               "Federal A": partidos_fecha_f, "Primera B": partidos_fecha_pb, "Primera C": partidos_fecha_pc,
               "Promocional Amateur": partidos_fecha_pd,
               "Regional Amateur": partidos_fecha_reg}[liga]
    try:
        return obtener(n)
    except (IndexError, KeyError, TypeError):
        return []


def _cal_rotulo(S, liga, n):
    if liga in _INT_CLAVE:
        return S["int"][_INT_CLAVE[liga]]["rondas"][n - 1]
    if por_nombre(liga):
        return por_nombre(liga).rotulo(S, n)
    return {"Primera División": lambda: rotulo_p(S, n), "Primera Nacional": lambda: rotulo_b(S["b"], n),
            "Federal A": lambda: rotulo_f(S["f"], n), "Regional Amateur": lambda: rotulo_reg(S["reg"], n)
            }.get(liga, lambda: f"Fecha {n}")()


def eventos_calendario(S):
    """Todo lo programado en la temporada: lista de (día, competición, n, jugada)."""
    ev = []
    jugadas = {"Primera División": S["fecha"], "Primera Nacional": S["b"]["fecha"], "Federal A": S["f"]["fecha"],
               "Primera B": S["pb"]["fecha"], "Primera C": S["pc"]["fecha"], "Promocional Amateur": S["pd"]["fecha"], "Regional Amateur": S["reg"]["fecha"]}
    for liga in INICIO:
        for n in range(1, total_liga(S, liga) + 1):
            ev.append((dia_de(S, liga, n), liga, n, n <= jugadas[liga]))
    for comp in REGISTRO:                      # Copa Argentina, Supercopa y Mundial de Clubes
        if comp.activa(S):
            for n in range(1, comp.total(S) + 1):
                ev.append((comp.dia(S, n), comp.nombre, n, n <= comp.hechas(S)))
    for liga, clave in _INT_CLAVE.items():
        C = S.get("int", {}).get(clave)
        if C:
            for n in range(1, C["total"] + 1):
                ev.append((dia_de(S, liga, n), liga, n, n <= C["ronda"]))
    orden = ["Recopa Sudamericana", "Copa Libertadores", "Copa Sudamericana", *[comp.nombre for comp in REGISTRO], "Primera División", "Primera Nacional", "Federal A", "Regional Amateur",
             "Primera B", "Primera C", "Promocional Amateur"]
    return sorted(ev, key=lambda e: (e[0], orden.index(e[1])))


def _cal_res(p):
    if p["gl"] is None:
        return "vs"
    pen = f"<small>({p['pen'][0]}-{p['pen'][1]})</small>" if p["pen"] else ""
    return f"{p['gl']}-{p['gv']}{pen}"


def calendario_mes_html(S, eventos, mes, proximo, solo_club=False):
    """Días del mes con lo que se juega cada uno (cada competición se despliega).
    Con `solo_club` (y un club dirigido por el manager) se ocultan los demás equipos: sólo quedan los
    días, las competencias y los partidos de ese club. Los partidos de mi club siempre se marcan."""
    club = mi_club()
    filtrar = bool(solo_club and club)
    dias = {}
    for d, liga, n, jugada in eventos:
        if d.month == mes:
            dias.setdefault(d, []).append((liga, n, jugada))
    out = ""
    for d in sorted(dias):
        comps, jugadas_dia = "", []
        for liga, n, jugada in dias[d]:
            partidos = _cal_partidos(S, liga, n)
            if filtrar:
                partidos = [p for p in partidos if club in (p["local"], p["visita"])]
                if not partidos:                  # mi club no juega en esta competición ese día
                    continue
            jugadas_dia.append(jugada)
            filas = "".join(
                f'<div class="cal-p{" mio" if club and club in (p["local"], p["visita"]) else ""}">'
                f'<span class="cl"><span class="cn">{esc(p["local"])}</span>{crest(p["local"], 16)}</span>'
                f'<span class="cs">{_cal_res(p)}'
                f'{"<i>⚠</i>" if p.get("incidente") else ""}</span>'
                f'<span class="cv">{crest(p["visita"], 16)}<span class="cn">{esc(p["visita"])}</span></span></div>'
                for p in partidos) or '<div class="cal-vacio">Los cruces se conocen más adelante.</div>'
            estado = ('<span class="cal-est ok">Jugada</span>' if jugada else '<span class="cal-est">Por jugar</span>')
            abierto = " open" if filtrar else ""      # con "sólo mi club" el partido sale desplegado
            comps += (f'<details class="cal-comp"{abierto}><summary>{logo_img(liga, 20)}<b>{esc(liga)}</b>'
                      f'<span class="cal-rot">{esc(_cal_rotulo(S, liga, n))}</span>{estado}</summary>'
                      f'<div class="cal-ps">{filas}</div></details>')
        if not jugadas_dia:                       # ese día no queda nada para mostrar
            continue
        clase = "hoy" if d == proximo else ("jugado" if all(jugadas_dia) else "")
        out += (f'<div class="cal-dia {clase}"><div class="cal-num"><b>{d.day}</b>'
                f'<span>{texto_dia(d, False)[:3]}</span></div><div class="cal-ev">{comps}</div></div>')
    return f'<div class="cal">{out}</div>'

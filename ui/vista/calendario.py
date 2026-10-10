"""Calendario del mes: partidos y eventos de cada día.
"""

import calendar as _calendar
import datetime as _dt

from motor.calendario import anio, dia_de, texto_dia
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
    resultado_para,
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


def _dia_tocable(d, proximo):
    """Se puede elegir como destino de "simular hasta esa fecha" cualquier día desde el próximo."""
    return proximo is not None and d >= proximo


CSS_SELECCION = ("<style>.cal-num[data-dia]{cursor:pointer}"
                 ".cal-dia.sel{outline:2px solid #eab308;outline-offset:-2px;border-radius:10px}</style>")


def calendario_mes_html(S, eventos, mes, proximo, solo_club=False, seleccion=None):
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
        if seleccion == d:
            clase += " sel"
        tocable = (f' data-dia="{d.isoformat()}" role="button" tabindex="0" title="Tocá para simular hasta este día"'
                   if _dia_tocable(d, proximo) else "")
        out += (f'<div class="cal-dia {clase}"><div class="cal-num"{tocable}><b>{d.day}</b>'
                f'<span>{texto_dia(d, False)[:3]}</span></div><div class="cal-ev">{comps}</div></div>')
    return f'{CSS_SELECCION}<div class="cal">{out}</div>'


# ---- Calendario en grilla (modo manager): sólo los partidos de mi club -------------------------------
_SEMANA = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]

CSS_GRILLA = """<style>
.gm-sem, .gm-grid { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 6px; }
.gm-sem span { text-align: center; opacity: .6; font-size: .8rem; padding: 6px 0; }
.gm-c { position: relative; min-height: 96px; border-radius: 10px; padding: 6px 4px 6px; box-sizing: border-box;
        display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px;
        background: rgba(127,127,127,.07); border: 1px solid rgba(127,127,127,.14); }
.gm-c.vacio { background: transparent; border-color: transparent; }
.gm-c.hoy { outline: 2px solid #6366f1; outline-offset: -2px; }
.gm-n { position: absolute; top: 5px; left: 8px; font-weight: 700; font-size: .78rem; opacity: .85; }
.gm-c.tiene { background: rgba(127,127,127,.15); }
.gm-c.copa { background: rgba(99,102,241,.18); }
.gm-c.pasado { background: rgba(100,116,139,.30); border-color: rgba(100,116,139,.40); }
.gm-c.pasado .gm-n { opacity: .5; }
.gm-c.pasado.copa { background: rgba(99,102,241,.30); }
.gm-c.g { border-color: rgba(46,125,79,.85); }
.gm-c.e { border-color: rgba(148,163,184,.8); }
.gm-c.p { border-color: rgba(184,58,46,.85); }
.gm-m { display: flex; flex-direction: column; align-items: center; gap: 3px; width: 100%; margin-top: 12px; }
.gm-m + .gm-m { margin-top: 2px; padding-top: 4px; border-top: 1px dashed rgba(127,127,127,.3); }
.gm-comp { position: absolute; top: 4px; right: 6px; line-height: 0; }
.gm-txt { font-size: .78rem; font-weight: 700; }
.gm-txt.g { color: #16a34a; } .gm-txt.p { color: #dc2626; } .gm-txt.e { color: #94a3b8; }
.gm-tit { text-align: center; font-weight: 700; font-size: 1.15rem; }
.gm-c[data-dia] { cursor: pointer; }
.gm-c[data-dia]:hover { outline: 1px solid rgba(250,204,21,.7); outline-offset: -1px; }
.gm-c.sel { outline: 2px solid #eab308; outline-offset: -2px; background: rgba(250,204,21,.16); }
@media (max-width: 640px) {
  .gm-sem, .gm-grid { gap: 3px; }
  .gm-c { min-height: 70px; padding: 4px 2px; }
  .gm-m img, .gm-m .crest { width: 24px !important; height: 26px !important; }
  .gm-txt { font-size: .62rem; } .gm-n { font-size: .68rem; left: 5px; }
  .gm-comp img { width: 12px !important; height: 12px !important; }
}
</style>"""


def _celda_partido(liga, p, club):
    """(clase del resultado o "", html) de un partido de `club`: escudo del rival, competencia y marcador
    (o Local / Visita / Neutral si todavía no se jugó)."""
    local = p["local"] == club
    rival = p["visita"] if local else p["local"]
    if p["gl"] is None:
        res = ""
        txt = "Neutral" if p.get("neutral") else ("Local" if local else "Visita")
    else:
        _, gf, gc, letra = resultado_para(p, club)
        if letra == "E" and p.get("pen"):                 # empate definido por penales
            letra = "G" if p["gana"] == club else "P"
        res = {"G": "g", "E": "e", "P": "p"}[letra]
        txt = f"{gf}-{gc}" + (" (pen.)" if p.get("pen") else "")
    titulo = f"{liga} · {p['rotulo']} · {p['local']} vs {p['visita']}" + ("" if p["gl"] is None else f" · {txt}")
    html = (f'<div class="gm-m" title="{esc(titulo)}"><span class="gm-comp">{logo_img(liga, 16)}</span>'
            f'{crest(rival, 34)}<span class="gm-txt {res}">{esc(txt)}</span></div>')
    return res, html


def calendario_grilla_html(S, eventos, mes, proximo, club, seleccion=None):
    """Mes en grilla (lun-dom), como un calendario de partidos: en cada día que juega `club`, el escudo del
    rival, el logo de la competencia y el marcador (o si es de local o de visitante). Los demás equipos no
    aparecen. Los días que ya pasaron van en gris azulado. El borde marca el resultado (verde gana, gris empata, rojo pierde) y el día de hoy va con
    un contorno violeta. Las copas se ven con un fondo más claro. Se puede tocar cualquier día desde el
    próximo: queda elegido (contorno amarillo) como destino de "simular hasta esa fecha"."""
    por_dia = {}
    for d, liga, n, _jugada in eventos:
        if d.month != mes:
            continue
        for p in _cal_partidos(S, liga, n):
            if club in (p["local"], p["visita"]):
                por_dia.setdefault(d.day, []).append((liga, p))
    celdas = ""
    for semana in _calendar.Calendar(firstweekday=0).monthdayscalendar(anio(S), mes):
        for dia in semana:
            if dia == 0:
                celdas += '<div class="gm-c vacio"></div>'
                continue
            fecha = _dt.date(anio(S), mes, dia)
            hoy = " hoy" if proximo and fecha == proximo else ""
            if proximo is None or fecha < proximo:             # día que ya pasó: se pinta de otro color
                hoy += " pasado"
            sel = " sel" if seleccion == fecha else ""
            toc = (f' data-dia="{fecha.isoformat()}" role="button" tabindex="0" title="Tocá para simular hasta este día"'
                   if _dia_tocable(fecha, proximo) else "")
            items = por_dia.get(dia, [])
            if not items:
                celdas += f'<div class="gm-c{hoy}{sel}"{toc}><span class="gm-n">{dia}</span></div>'
                continue
            partes = [_celda_partido(liga, p, club) for liga, p in items]
            copa = " copa" if any(liga not in INICIO for liga, _ in items) else ""
            res = partes[0][0] if len(partes) == 1 else ""
            celdas += (f'<div class="gm-c tiene{copa} {res}{hoy}{sel}"{toc}><span class="gm-n">{dia}</span>'
                       + "".join(h for _, h in partes) + '</div>')
    cab = "".join(f"<span>{d}</span>" for d in _SEMANA)
    return f'{CSS_GRILLA}<div class="gm-sem">{cab}</div><div class="gm-grid">{celdas}</div>'

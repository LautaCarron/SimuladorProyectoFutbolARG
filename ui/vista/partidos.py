"""Partidos jugados y por jugar de cada liga, tarjetas de partido y próximo partido de un club.
"""


from motor.calendario import dia_partido, texto_dia
from ui.vista.base import chip, crest, esc


def marcador_html(p, crests=False):
    cl = crest(p["local"], 22) if crests else ""
    cv = crest(p["visita"], 22) if crests else ""
    if p["gl"] is None:
        return f'<div class="score">{cl}<span class="vs">VS</span>{cv}</div>'
    wl = ' w' if p["gana"] == p["local"] else ''
    wv = ' w' if p["gana"] == p["visita"] else ''
    pl = pv = ""
    if p["pen"]:
        pl, pv = f"<small>({p['pen'][0]})</small>", f"<small>({p['pen'][1]})</small>"
    return (f'<div class="score">{cl}<span class="n{wl}">{p["gl"]}</span>{pl}<span class="sep">–</span>'
            f'{pv}<span class="n{wv}">{p["gv"]}</span>{cv}</div>')


def tanda_html(p, abierto=False):
    tanda = p.get("tanda")
    if not tanda or len(tanda) < 2:
        return ""
    # Compatibilidad con partidos guardados antes de que se persistiera el marcador de penales.
    pen = p.get("pen")
    if not pen or len(pen) < 2:
        pen = (sum(tanda[0]), sum(tanda[1]))
    filas = ""
    for nombre, serie, total in ((p["local"], tanda[0], pen[0]),
                                 (p["visita"], tanda[1], pen[1])):
        dots = "".join('<span class="pk ok">✓</span>' if x else '<span class="pk no">✗</span>'
                       for x in serie)
        filas += (f'<div class="trow">{crest(nombre, 18)}<span class="tn">{esc(nombre)}:</span>'
                  f'<span class="tt">{total}</span><span>{dots}</span></div>')
    return (f'<details class="tanda"{" open" if abierto else ""}><summary>Penales · '
            f'{esc(p["local"])} {pen[0]} – {pen[1]} {esc(p["visita"])}</summary>'
            f'{filas}</details>')


def fila_partido_html(S, club, p, abierto=False):
    """Partido en formato tarjeta; `club` es el club que dirige el manager (None si no hay): se marca en amarillo."""
    wl = " w" if p["gana"] == p["local"] else ""
    wv = " w" if p["gana"] == p["visita"] else ""
    dia = p.get("dia") or dia_partido(S, p)       # los de temporadas viejas guardan su día
    mio = " mio" if club and club in (p["local"], p["visita"]) else ""     # partido de mi club (amarillo)
    meta = (chip(p["liga"]) + (chip(p["comp"]) if p["comp"] != p["liga"] else "")
            + f'<span style="opacity:.7;font-weight:600">{esc(p["rotulo"])}</span>'
            + (f'<span class="m-dia">{esc(texto_dia(dia, False))}</span>' if dia else "")
            + ('<span style="opacity:.6">· cancha neutral</span>' if p["neutral"] else "")
            + (f'<span class="inc-badge">⚠ {esc(p["incidente"])}</span>' if p.get("incidente") else ""))
    return (f'<div class="mrow{mio}"><div class="meta">{meta}</div><div class="mline">'
            f'<div class="side l{wl}">{esc(p["local"])} {crest(p["local"], 26)}</div>'
            f'{marcador_html(p)}'
            f'<div class="side{wv}">{crest(p["visita"], 26)} {esc(p["visita"])}</div></div>'
            f'{tanda_html(p, abierto)}</div>')


def lista_equipos_html(items):
    """items: lista de (nombre, detalle)."""
    if not items:
        return '<div style="opacity:.6">Por definir</div>'
    return '<div class="tlist">' + "".join(
        f'<span class="tl">{crest(n, 26)}{esc(n)}{f" <small>{esc(d)}</small>" if d else ""}</span>'
        for n, d in items) + "</div>"


def resultado_para(p, nombre):
    local = p["local"] == nombre
    gf, gc = (p["gl"], p["gv"]) if local else (p["gv"], p["gl"])
    letra = "G" if gf > gc else "P" if gf < gc else "E"
    return local, gf, gc, letra

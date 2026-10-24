"""Tabla de una liguilla de desempate (partidos únicos entre varios equipos)."""

from ui.vista import club_link

_COLUMNAS = ("Pts", "PJ", "G", "P", "GF", "GC", "DG")

# (texto que identifica la competencia) -> (cuando el equipo logra el objetivo, cuando no)
_LEYENDAS = (
    ("Campeonato", "Campeón", "No sale campeón"),
    ("campeonato", "Campeón", "No sale campeón"),
    ("Ascenso", "Asciende", "No asciende"),
    ("Permanencia", "Se salva", "Desciende"),
    ("Promocion", "Se salva", "Juega la promoción"),
)


def _estadisticas(partidos):
    """Puntos y goles de cada club a partir de los partidos (gana el que pasa, sea en los 90 minutos o en penales)."""
    stats = {}
    for p in partidos:
        local = p.get("local") or p.get("l")
        visita = p.get("visita") or p.get("visitante") or p.get("v")
        gl, gv, gana = p.get("gl", 0), p.get("gv", 0), p.get("gana")
        for club in (local, visita):
            stats.setdefault(club, dict.fromkeys(_COLUMNAS, 0))
        stats[local]["PJ"] += 1
        stats[visita]["PJ"] += 1
        stats[local]["GF"] += gl
        stats[local]["GC"] += gv
        stats[visita]["GF"] += gv
        stats[visita]["GC"] += gl
        for ganador, perdedor in ((local, visita), (visita, local)):
            if gana == ganador:
                stats[ganador]["Pts"] += 3
                stats[ganador]["G"] += 1
                stats[perdedor]["P"] += 1
    filas = []
    for club, s in stats.items():
        s["DG"] = s["GF"] - s["GC"]
        filas.append({"Club": club, **s})
    filas.sort(key=lambda x: (x["Pts"], x["DG"], x["GF"]), reverse=True)
    return filas


def _leyenda(partidos):
    comp = partidos[0].get("comp", "")
    logro, no = next(((a, b) for clave, a, b in _LEYENDAS if clave in comp), ("Logra el objetivo", "No lo logra"))
    return (f'<div class="legend"><span><i style="background:var(--liga-ok)"></i>{logro}</span>'
            f'<span><i style="background:var(--liga-out)"></i>{no}</span></div>')


def html_tabla_liguilla(partidos):
    """HTML de la tabla de posiciones. Si los partidos traen el orden real del desempate (`orden`) y cuántos
    logran el objetivo (`cupos`), con 3 o más equipos se marca en verde a los que lo logran y en rojo al resto."""
    filas = _estadisticas(partidos)
    orden = next((p["orden"] for p in partidos if p.get("orden")), None)
    cupos = next((p["cupos"] for p in partidos if p.get("cupos")), None)
    if orden:
        filas.sort(key=lambda x: orden.index(x["Club"]) if x["Club"] in orden else len(orden))
    marcar = cupos is not None and len(filas) >= 3

    html = [f'<div class="liguilla-wrap"><table class="liguilla{" marcada" if marcar else ""}">',
            '<tr><th>Pos</th><th class="club">Club</th><th>Pts</th><th>PJ</th><th>G</th><th>P</th>'
            '<th>GF</th><th>GC</th><th>DG</th></tr>']
    for i, f in enumerate(filas):
        clase = ('<tr class="ok">' if i < cupos else '<tr class="out">') if marcar else "<tr>"
        html.append(f'{clase}<td class="pos">{i + 1}</td><td class="club">{club_link(f["Club"], 24)}</td>'
                    f'<td class="pts">{f["Pts"]}</td><td>{f["PJ"]}</td><td>{f["G"]}</td><td>{f["P"]}</td>'
                    f'<td>{f["GF"]}</td><td>{f["GC"]}</td><td>{f["DG"]:+d}</td></tr>')
    html.append("</table></div>")
    if marcar:
        html.append(_leyenda(partidos))
    return "".join(html)

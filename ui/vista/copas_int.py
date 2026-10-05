"""Copas CONMEBOL y Mundial de Clubes: series, grupos y cuadros.
"""

from ui.vista.base import bandera, crest, esc
from ui.vista.cuadros import _kb, _kb_col, _kb_final, _nm_club
from ui.vista.partidos import pendiente, tanda_html
from copas.conmebol import GRUPOS, _FIX4, pais_de, tabla_grupo
from copas.mundial import GRUPOS as GRUPOS_MUNDIAL, MUNDIAL, pais_club, tabla_grupo as tabla_grupo_mundial


# ---- Copas CONMEBOL ----
_INT_CLAVE = {"Copa Libertadores": "lib", "Copa Sudamericana": "sud", "Recopa Sudamericana": "rec"}


def _int_pendientes(C, n):
    """Partidos por jugar de la ronda n de una copa CONMEBOL (si ya se conocen los cruces)."""
    etapa = C["rondas"][n - 1]
    liga = C["nombre"]
    if etapa.startswith("Grupos"):
        if C["grupos"] is None:
            return []
        f = int(etapa.split()[-1]) - 1
        return [pendiente(liga, n, etapa, f"Grupo {GRUPOS[g]}", eq[i], eq[j])
                for g, eq in enumerate(C["grupos"]) for i, j in _FIX4[f]]
    fase = "Recopa" if liga == "Recopa Sudamericana" else etapa.split(" · ")[0]
    series = C["llaves"].get("Final" if liga == "Recopa Sudamericana" else fase)
    if not series:
        return []
    if etapa == "Final":
        return [dict(pendiente(liga, n, etapa, "Final", series[0]["a"], series[0]["b"]), neutral=True)]
    ida = etapa.endswith("ida") or etapa == "Ida"
    return [pendiente(liga, n, etapa, fase, x["b"], x["a"]) if ida else pendiente(liga, n, etapa, fase, x["a"], x["b"])
            for x in series]


def _club_int(n, size=26):
    e = esc(n)
    return (f'{crest(n, size)}<span class="nm" role="button" tabindex="0" data-club="{e}" '
            f'title="Ver la ficha de {e}">{e}</span>{bandera(pais_de(n), 16)}')


def serie_int_html(C, x, titulo=""):
    """Serie a ida y vuelta (o final única) de una copa CONMEBOL, en el formato de las finales
    del Regional: ida, vuelta y global de cada equipo."""
    final_unica = C["nombre"] != "Recopa Sudamericana" and x is C["llaves"].get("Final", [None])[0]
    cab = f'<div class="rf-h"><span class="rf-n">{esc(titulo)}</span><span class="rf-reg">' + (
        "Final única · cancha neutral" if final_unica else "Ida y vuelta") + '</span></div>'
    if final_unica:
        p = x["ida"]
        cab += '<div class="rf-fila rf-cab"><span></span><span></span><span></span><span>Final</span></div>'
        filas = ""
        for k, n in enumerate((x["a"], x["b"])):
            cls = "" if x["gana"] is None else ("win" if x["gana"] == n else "lose")
            g = (p["gl"] if k == 0 else p["gv"]) if p else "–"
            pk = f'<sup>({p["pen"][k]})</sup>' if p and p["pen"] else ""
            filas += (f'<div class="rf-fila {cls}"><span class="rf-eq">{crest(n, 30)}<span class="rf-nm">'
                      f'{_nm_club(n)}<small>{esc(pais_de(n))}</small></span></span><span></span><span></span>'
                      f'<span class="rf-g rf-tot">{g}{pk}</span></div>')
        pie = (f'<span class="rf-sube">🏆 Campeón</span> {_nm_club(x["gana"])}' if x["gana"] else "Se juega en noviembre")
        return f'<article class="rf">{cab}{filas}<div class="rf-f">{pie}</div>{tanda_html(p) if p else ""}</article>'
    cab += '<div class="rf-fila rf-cab"><span></span><span>Ida</span><span>Vta.</span><span>Global</span></div>'
    ida, vta = x["ida"], x["vuelta"]
    filas = ""
    for k, n in enumerate((x["a"], x["b"])):
        cls = "" if x["gana"] is None else ("win" if x["gana"] == n else "lose")
        gi = ("–" if ida is None else (ida["gv"] if k == 0 else ida["gl"]))
        gv = ("–" if vta is None else (vta["gl"] if k == 0 else vta["gv"]))
        gt = ("–" if ida is None else (x["ga"] if k == 0 else x["gb"]))
        pk = f'<sup>({x["pen"][k]})</sup>' if x["pen"] else ""
        filas += (f'<div class="rf-fila {cls}"><span class="rf-eq">{crest(n, 30)}<span class="rf-nm">'
                  f'{_nm_club(n)}<small>{esc(pais_de(n))}{" · cierra de local" if k == 0 else ""}</small></span></span>'
                  f'<span class="rf-g">{gi}</span><span class="rf-g">{gv}</span><span class="rf-g rf-tot">{gt}{pk}</span></div>')
    pie = (f'<span class="rf-sube">▲ Avanza</span> {_nm_club(x["gana"])}'
           + (f' · penales {x["pen"][0]}-{x["pen"][1]}' if x["pen"] else "")) if x["gana"] else (
        "Se jugó la ida" if ida else "Por jugar")
    return f'<article class="rf">{cab}{filas}<div class="rf-f">{pie}</div>{tanda_html(vta) if vta else ""}</article>'


def series_int_html(C, fase):
    series = C["llaves"].get(fase) or []
    if not series:
        return ""
    return '<div class="rf-grid">' + "".join(serie_int_html(C, x, f"{fase} · llave {k + 1}")
                                             for k, x in enumerate(series)) + '</div>'


def grupos_int_html(C, destinos):
    """Las 8 tablas de grupo. `destinos` = [(clase, texto)] para 1°, 2°, 3° y 4°."""
    out = ""
    for g in range(len(C["grupos"])):
        filas = ""
        for k, t in enumerate(tabla_grupo(C, g)):
            clase = destinos[k][0] if C["gstats"] and any(C["gstats"][n]["pj"] for n in C["grupos"][g]) else ""
            n = t["Equipo"]
            filas += (f'<tr class="{clase}"><td class="gp">{k + 1}</td><td class="gc"><div class="gcw">{crest(n, 20)}'
                      f'<span class="nm" role="button" tabindex="0" data-club="{esc(n)}">{esc(n)}</span>'
                      f'{bandera(pais_de(n), 14)}</div></td><td>{t["PJ"]}</td><td>{t["DG"]:+d}</td><td class="gpts">{t["Pts"]}</td></tr>')
        out += (f'<div class="grp"><div class="grp-h">Grupo {GRUPOS[g]}</div><table class="grp-t"><thead><tr><th>#</th>'
                f'<th>Club</th><th>PJ</th><th>DG</th><th>Pts</th></tr></thead><tbody>{filas}</tbody></table></div>')
    ley = "".join(f'<span><i class="{c}"></i>{esc(t)}</span>' for c, t in destinos if c)
    return f'<div class="grp-grid">{out}</div><div class="grp-ley">{ley}</div>'


def _kb_card_serie(x):
    """Serie en el cuadro: global de cada equipo (y penales)."""
    if x is None:
        fila = '<div class="kb-t tbd"><span class="kb-vacio"></span><span class="kb-n">A definir</span></div>'
        return f'<div class="kb-m">{fila}{fila}</div>'
    filas = ""
    jugada = x["ida"] is not None
    for k, n in enumerate((x["a"], x["b"])):
        cls = "" if x["gana"] is None else (" win" if x["gana"] == n else " lose")
        if x.get("vuelta") is None and jugada and x["gana"] is not None:     # final única
            g = x["ida"]["gl"] if k == 0 else x["ida"]["gv"]
            pen = x["ida"]["pen"]
        else:
            g = (x["ga"] if k == 0 else x["gb"]) if jugada else ""
            pen = x["pen"]
        pk = f'<span class="kb-p">({pen[k]})</span>' if pen else ""
        e = esc(n)
        filas += (f'<div class="kb-t{cls}">{crest(n, 20)}<span class="kb-n" role="button" tabindex="0" '
                  f'data-club="{e}" title="{e}">{e}</span>{bandera(pais_de(n), 14)}{pk}<b class="kb-g">{g}</b></div>')
    return f'<div class="kb-m">{filas}</div>'


def cuadro_int_html(C):
    """Octavos, cuartos, semis (global de cada serie), final única y campeón."""
    cols = []
    for fase, n in (("Octavos", 8), ("Cuartos", 4), ("Semifinal", 2), ("Final", 1)):
        series = C["llaves"].get(fase) or [None] * n
        if n == 1:
            cols.append(_kb_col("Final", f'<div class="kb-slot kb-solo">{_kb_card_serie(series[0])}</div>'))
        else:
            cuerpo = "".join(f'<div class="kb-pair"><div class="kb-slot">{_kb_card_serie(series[j])}</div>'
                             f'<div class="kb-slot">{_kb_card_serie(series[j + 1])}</div></div>'
                             for j in range(0, n, 2))
            cols.append(_kb_col(fase if fase != "Semifinal" else "Semis", cuerpo))
    c = C["campeon"]
    cols.append(_kb_final(f"Campeón · {C['nombre']}", "Campeón", c, pais_de(c) if c else ""))
    return _kb(cols, 8 * 74)


def grupos_mundial_html(M):
    """Las 8 tablas de grupo del Mundial de Clubes (1° y 2° pasan a octavos)."""
    out = ""
    for g in range(len(M["grupos"])):
        jugado = any(M["gstats"][n]["pj"] for n in M["grupos"][g])
        filas = ""
        for k, t in enumerate(tabla_grupo_mundial(M, g)):
            clase = "oct" if jugado and k < 2 else ""
            n = t["Equipo"]
            filas += (f'<tr class="{clase}"><td class="gp">{k + 1}</td><td class="gc"><div class="gcw">{crest(n, 20)}'
                      f'<span class="nm" role="button" tabindex="0" data-club="{esc(n)}">{esc(n)}</span>'
                      f'{bandera(pais_club(n), 14)}</div></td><td>{t["PJ"]}</td><td>{t["DG"]:+d}</td>'
                      f'<td class="gpts">{t["Pts"]}</td></tr>')
        out += (f'<div class="grp"><div class="grp-h">Grupo {GRUPOS_MUNDIAL[g]}</div><table class="grp-t"><thead><tr><th>#</th>'
                f'<th>Club</th><th>PJ</th><th>DG</th><th>Pts</th></tr></thead><tbody>{filas}</tbody></table></div>')
    return (f'<div class="grp-grid">{out}</div><div class="grp-ley"><span><i class="oct"></i>'
            f'Pasan a octavos</span></div>')


def _kb_card_mundial(m):
    """Cruce del Mundial en el cuadro: goles de cada equipo (y penales)."""
    if m is None:
        fila = '<div class="kb-t tbd"><span class="kb-vacio"></span><span class="kb-n">A definir</span></div>'
        return f'<div class="kb-m">{fila}{fila}</div>'
    p = m["p"]
    filas = ""
    for k, n in enumerate((m["a"], m["b"])):
        cls = "" if m["gana"] is None else (" win" if m["gana"] == n else " lose")
        g = (p["gl"] if k == 0 else p["gv"]) if p else ""
        pk = f'<span class="kb-p">({p["pen"][k]})</span>' if p and p.get("pen") else ""
        e = esc(n)
        filas += (f'<div class="kb-t{cls}">{crest(n, 20)}<span class="kb-n" role="button" tabindex="0" '
                  f'data-club="{e}" title="{e}">{e}</span>{bandera(pais_club(n), 14)}{pk}<b class="kb-g">{g}</b></div>')
    return f'<div class="kb-m">{filas}</div>'


def cuadro_mundial_html(M):
    """Octavos, cuartos, semis, final y campeón del Mundial de Clubes."""
    cols = []
    for k, (titulo, n) in enumerate((("Octavos", 8), ("Cuartos", 4), ("Semis", 2), ("Final", 1))):
        ronda = M["cuadro"][k] if k < len(M["cuadro"]) else [None] * n
        if n == 1:
            cols.append(_kb_col(titulo, f'<div class="kb-slot kb-solo">{_kb_card_mundial(ronda[0])}</div>'))
        else:
            cuerpo = "".join(f'<div class="kb-pair"><div class="kb-slot">{_kb_card_mundial(ronda[j])}</div>'
                             f'<div class="kb-slot">{_kb_card_mundial(ronda[j + 1])}</div></div>'
                             for j in range(0, n, 2))
            cols.append(_kb_col(titulo, cuerpo))
    c = M["campeon"]
    cols.append(_kb_final(f"Campeón · {MUNDIAL}", "Campeón", c, pais_club(c) if c else ""))
    return _kb(cols, 8 * 74)

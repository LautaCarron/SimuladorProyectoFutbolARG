"""Cuadros de eliminación: reducidos, finales del Regional, Copa Argentina y avisos del Tribunal.
"""

import streamlit as st

from motor.calendario import dia_de, texto_dia
from datos.logos import logo_img
from datos.regional import FINALES_REG
from ui.vista.base import chip, crest, esc
from ui.vista.partidos import tanda_html
from copas.argentina import COPA_CORTO, COPA_LLAVES


# ---- Cuadro del reducido ----------------------------------------------------
def bracket_card(m, final=False):
    if m is None:
        fila = '<div class="bt tbd"><span class="nm">Por definir</span></div>'
        return f'<div class="bm">{fila}{fila}</div>'
    filas = ""
    for i, (nombre, g) in enumerate(((m["local"], m["gl"]), (m["visita"], m["gv"]))):
        cls = "win" if m["gana"] == nombre else "lose"
        pk = f'<span class="p">({m["pen"][i]})</span>' if m["pen"] else ""
        lv = "N" if m["neutral"] else ("L" if i == 0 else "V")
        tit = "Neutral" if lv == "N" else "Local" if lv == "L" else "Visitante"
        filas += (f'<div class="bt {cls}">{crest(nombre, 24)}<span class="nm" title="{esc(nombre)}">'
                  f'{esc(nombre)}</span><span class="lv" title="{tit}">{lv}</span>{pk}'
                  f'<span class="g">{g}</span></div>')
    pen = f"Penales {m['pen'][0]}-{m['pen'][1]} · " if m["pen"] else ""
    que = "Campeón" if final else "Avanza"
    return (f'<div class="bm">{filas}<div class="bfoot">{pen}{que}: <b>{esc(m["gana"])}</b></div>'
            f'{tanda_html(m)}</div>')


def bracket_html(SB):
    rondas = [list(r) for r in SB["bracket"]]
    # Ordena cada ronda según la siguiente para que el cuadro se lea de izquierda a derecha
    for k in range(len(rondas) - 1, 0, -1):
        nuevo = []
        for m in rondas[k]:
            for t in (m["local"], m["visita"]):
                for pm in rondas[k - 1]:
                    if pm["gana"] == t and all(pm is not x for x in nuevo):
                        nuevo.append(pm)
        nuevo += [pm for pm in rondas[k - 1] if all(pm is not x for x in nuevo)]
        rondas[k - 1] = nuevo
    titulos = ["Octavos", "Cuartos", "Semifinal", "Final"]
    tam = [4, 4, 2, 1]
    cols = ""
    for r in range(4):
        ms = rondas[r] if r < len(rondas) else [None] * tam[r]
        cards = "".join(bracket_card(m, final=(r == 3)) for m in ms)
        cols += (f'<div class="round"><div class="round-h">{chip(titulos[r])}</div>'
                 f'<div class="round-b">{cards}</div></div>')
    if len(rondas) == 4:
        c = rondas[3][0]["gana"]
        champ = (f'<div class="champ"><div class="t">Campeón del reducido</div>'
                 f'<div style="margin-top:10px">{crest(c, 56)}</div><div class="nm">{esc(c)}</div>'
                 f'<div class="s">Asciende a Primera División</div></div>')
    else:
        champ = ('<div class="champ" style="opacity:.55"><div class="t">Campeón del reducido</div>'
                 '<div class="nm">Por definir</div><div class="s">Asciende a Primera</div></div>')
    promo = ""
    if SB["promo_partido"]:
        promo = (f'<div class="promo"><div class="round-h">{chip("Promoción")}</div>'
                 f'{bracket_card(SB["promo_partido"])}</div>')
    elif len(rondas) == 4:
        perd = SB["nombres"][SB["perdedor_final"]]
        promo = (f'<div class="promo"><div class="round-h">{chip("Promoción")}</div>'
                 f'<div class="bm"><div class="bt">{crest(perd, 24)}<span class="nm">{esc(perd)}'
                 f'</span></div><div class="bt tbd"><span class="nm">27° de Primera</span></div>'
                 f'</div></div>')
    cols += (f'<div class="round last"><div class="round-h">{chip("Campeón", "#b7860b")}</div>'
             f'<div class="round-b" style="justify-content:center">{champ}{promo}</div></div>')
    return f'<div class="bracket">{cols}</div>'


def bracket_html_f(SF):
    rondas = [list(r) for r in SF["bracket"]]
    for k in range(len(rondas) - 1, 0, -1):
        nuevo = []
        for m in rondas[k]:
            for t in (m["local"], m["visita"]):
                for pm in rondas[k - 1]:
                    if pm["gana"] == t and all(pm is not x for x in nuevo):
                        nuevo.append(pm)
        nuevo += [pm for pm in rondas[k - 1] if all(pm is not x for x in nuevo)]
        rondas[k - 1] = nuevo
    titulos = ["Eliminatoria", "Semifinal", "Final"]
    tam = [1, 2, 1]
    cols = ""
    for r in range(3):
        ms = rondas[r] if r < len(rondas) else [None] * tam[r]
        cards = "".join(bracket_card(m, final=(r == 2)) for m in ms)
        cols += (f'<div class="round"><div class="round-h">{chip(titulos[r])}</div>'
                 f'<div class="round-b">{cards}</div></div>')
    if len(rondas) == 3:
        c = rondas[2][0]["gana"]
        champ = (f'<div class="champ"><div class="t">Campeón del reducido</div>'
                 f'<div style="margin-top:10px">{crest(c, 56)}</div><div class="nm">{esc(c)}</div>'
                 f'<div class="s">Asciende a la Primera Nacional</div></div>')
    else:
        champ = ('<div class="champ" style="opacity:.55"><div class="t">Campeón del reducido</div>'
                 '<div class="nm">Por definir</div><div class="s">Asciende a la Primera Nacional'
                 '</div></div>')
    cols += (f'<div class="round last"><div class="round-h">{chip("Campeón", "#b7860b")}</div>'
             f'<div class="round-b" style="justify-content:center">{champ}</div></div>')
    return f'<div class="bracket">{cols}</div>'


# ---- Regional Amateur: series a ida y vuelta, cuadro de cada región y finales ----
def _nm_club(nombre):
    n = esc(nombre)
    return (f'<span class="nm" role="button" tabindex="0" data-club="{n}" '
            f'title="Ver la ficha de {n}">{n}</span>')


def _fila_final(SR, i, reg, goles, clase, pen=None):
    """Fila de un equipo en una final por el ascenso: escudo, nombre y región, ida, vuelta y
    global (con los penales, si hubo)."""
    if i is None:
        return (f'<div class="rf-fila tbd"><span class="rf-eq"><span class="rf-vacio"></span>'
                f'<span class="rf-nm"><b>Campeón de {esc(reg)}</b><small>Por definir</small></span></span>'
                f'<span class="rf-g">–</span><span class="rf-g">–</span><span class="rf-g rf-tot">–</span></div>')
    n = SR["nombres"][i]
    ida, vta, tot = goles
    pk = f'<sup>({pen})</sup>' if pen is not None else ""
    return (f'<div class="rf-fila {clase}"><span class="rf-eq">{crest(n, 30)}<span class="rf-nm">'
            f'{_nm_club(n)}<small>{esc(reg)}</small></span></span>'
            f'<span class="rf-g">{ida}</span><span class="rf-g">{vta}</span>'
            f'<span class="rf-g rf-tot">{tot}{pk}</span></div>')


def finales_reg_html(SR):
    """Las 6 finales por el ascenso (de a pares de regiones, según el JSON): cada tarjeta
    muestra ida, vuelta y global de cada campeón y quién asciende al Federal A."""
    tarjetas = ""
    for k, (ra, rb) in enumerate(FINALES_REG):
        x = SR["finales"][k] if k < len(SR["finales"]) else None
        cab = (f'<div class="rf-h"><span class="rf-n">Final {k + 1}</span>'
               f'<span class="rf-reg">{esc(ra)} <i>vs.</i> {esc(rb)}</span></div>'
               '<div class="rf-fila rf-cab"><span></span><span>Ida</span><span>Vta.</span>'
               '<span>Global</span></div>')
        tanda = ""
        if x is None:                                  # todavía no se armó el cruce
            filas = "".join(_fila_final(SR, SR["campeones"].get(reg), reg, ("–", "–", "–"), "")
                            for reg in (ra, rb))
            listos = sum(SR["campeones"].get(reg) is not None for reg in (ra, rb))
            pie = ("Ida y vuelta · cierra de local el de mejor campaña" if listos == 2 else
                   "Se completa con los campeones de cada región")
        elif x["a"] is None:                           # las dos regiones sin clubes
            filas = "".join(_fila_final(SR, None, reg, ("–", "–", "–"), "") for reg in (ra, rb))
            pie = "Final desierta: ninguna de las dos regiones tiene clubes"
        elif x["b"] is None:                           # la otra región no tiene campeón
            reg_a = SR["region_de"][x["a"]]
            filas = _fila_final(SR, x["a"], reg_a, ("–", "–", "–"), "win")
            pie = f'<span class="rf-sube">▲ Asciende</span> {_nm_club(SR["nombres"][x["a"]])} · sin rival'
        else:
            ida, vta = x["ida"], x["vuelta"]
            # ida: local el de peor campaña (b) · vuelta: cierra de local el mejor ubicado (a)
            g_a = (ida["gv"] if ida else "–", vta["gl"] if vta else "–", x["ga"] if ida else "–")
            g_b = (ida["gl"] if ida else "–", vta["gv"] if vta else "–", x["gb"] if ida else "–")
            filas = ""
            for k2, (i, g) in enumerate(((x["a"], g_a), (x["b"], g_b))):
                clase = "" if x["gana"] is None else ("win" if x["gana"] == i else "lose")
                filas += _fila_final(SR, i, SR["region_de"][i], g, clase,
                                     x["pen"][k2] if x["pen"] else None)
            if x["gana"] is not None:
                pie = (f'<span class="rf-sube">▲ Asciende al Federal A</span> '
                       f'{_nm_club(SR["nombres"][x["gana"]])}'
                       + (f' · penales {x["pen"][0]}-{x["pen"][1]}' if x["pen"] else ""))
                tanda = tanda_html(vta) if vta is not None else ""
            elif ida:
                pie = "Se jugó la ida · falta la vuelta"
            else:
                pie = "Ida y vuelta · cierra de local el de mejor campaña (arriba)"
        tarjetas += (f'<article class="rf{" hecha" if x is not None and x["gana"] is not None else ""}">'
                     f'{cab}{filas}<div class="rf-f">{pie}</div>{tanda}</article>')
    return f'<div class="rf-grid">{tarjetas}</div>'


# ---- Copa Argentina: cuadro por llaves (A-H) y fase final ----
def _kb_card(SC, m):
    """Cruce de la Copa en el cuadro: dos renglones iguales (escudo, club, logo de su liga,
    penales y goles). El que pasa, resaltado."""
    if m is None:
        fila = '<div class="kb-t tbd"><span class="kb-vacio"></span><span class="kb-n">A definir</span></div>'
        return f'<div class="kb-m">{fila}{fila}</div>'
    nom, p = SC["nombres"], m["p"]
    filas = ""
    for k, i in enumerate((m["a"], m["b"])):
        cls = "" if m["gana"] is None else (" win" if m["gana"] == i else " lose")
        g = (p["gl"] if k == 0 else p["gv"]) if p else ""
        pk = f'<span class="kb-p">({p["pen"][k]})</span>' if p and p["pen"] else ""
        n = esc(nom[i])
        filas += (f'<div class="kb-t{cls}">{crest(nom[i], 20)}'
                  f'<span class="kb-n" role="button" tabindex="0" data-club="{n}" title="{n}">{n}</span>'
                  f'{logo_img(SC["origen"][i], 14, "logo-mini")}{pk}<b class="kb-g">{g}</b></div>')
    alerta = ' <span class="kb-inc" title="{}">⚠</span>'.format(esc(p["incidente"])) if p and p.get("incidente") else ""
    return f'<div class="kb-m">{filas}{alerta}</div>'


def _kb_col(titulo, cuerpo):
    return f'<div class="kb-col"><div class="kb-h">{chip(titulo, "#1e5aa8")}</div><div class="kb-body">{cuerpo}</div></div>'


def _kb_ronda(SC, titulo, cruces):
    """Una ronda: los cruces van de a pares (una línea une a los dos que se enfrentan después)."""
    if len(cruces) == 1:
        return _kb_col(titulo, f'<div class="kb-slot kb-solo">{_kb_card(SC, cruces[0])}</div>')
    cuerpo = "".join(f'<div class="kb-pair"><div class="kb-slot">{_kb_card(SC, cruces[j])}</div>'
                     f'<div class="kb-slot">{_kb_card(SC, cruces[j + 1])}</div></div>'
                     for j in range(0, len(cruces), 2))
    return _kb_col(titulo, cuerpo)


def _kb_final(titulo, sub, nombre, origen):
    if nombre is None:
        inner = f'<div class="kb-champ vacio"><div class="t">{esc(titulo)}</div><div class="nm">A definir</div></div>'
    else:
        inner = (f'<div class="kb-champ"><div class="t">{esc(titulo)}</div>{crest(nombre, 46)}'
                 f'<div class="nm">{esc(nombre)}</div><div class="s">{esc(origen)}</div></div>')
    return _kb_col(sub, f'<div class="kb-slot">{inner}</div>')


def _kb(cols, alto):
    return (f'<div class="kb-wrap"><div class="kb" style="--cols:{len(cols)};--alto:{alto}px">'
            f'{"".join(cols)}</div></div>')


def cuadro_llave_html(SC, letra):
    """Una llave (16 equipos): 64avos, 32avos, 16avos y octavos; el ganador va a cuartos."""
    li = COPA_LLAVES.index(letra)
    cols = []
    for k in range(4):
        n = 8 >> k
        ronda = SC["cuadro"][k][li * n:(li + 1) * n] if k < len(SC["cuadro"]) else [None] * n
        cols.append(_kb_ronda(SC, COPA_CORTO[k], ronda))
    octavos = SC["cuadro"][3][li] if len(SC["cuadro"]) > 3 else None
    g = octavos["gana"] if octavos is not None else None
    cols.append(_kb_final(f"Llave {letra}", "A cuartos", SC["nombres"][g] if g is not None else None,
                          SC["origen"][g] if g is not None else ""))
    return _kb(cols, 8 * 74)


def cuadro_final_copa_html(SC):
    """Fase final: cuartos (ganadores de las llaves A-H), semifinales, final y campeón."""
    cols = []
    for k, n in ((4, 4), (5, 2), (6, 1)):
        if k < len(SC["cuadro"]):
            cols.append(_kb_ronda(SC, COPA_CORTO[k], SC["cuadro"][k]))
        elif k == 4:                                    # qué llaves se cruzan en cuartos
            vacias = "".join(
                f'<div class="kb-pair">' + "".join(
                    f'<div class="kb-slot"><div class="kb-m">'
                    f'<div class="kb-t tbd"><span class="kb-vacio"></span><span class="kb-n">Ganador llave '
                    f'{COPA_LLAVES[2 * j2]}</span></div><div class="kb-t tbd"><span class="kb-vacio"></span>'
                    f'<span class="kb-n">Ganador llave {COPA_LLAVES[2 * j2 + 1]}</span></div></div></div>'
                    for j2 in (2 * j, 2 * j + 1)) + '</div>' for j in range(2))
            cols.append(_kb_col(COPA_CORTO[k], vacias))
        else:
            cols.append(_kb_ronda(SC, COPA_CORTO[k], [None] * n))
    c = SC["campeon"]
    cols.append(_kb_final("Campeón · Copa Argentina", "Campeón", SC["nombres"][c] if c is not None else None,
                          SC["origen"][c] if c is not None else ""))
    return _kb(cols, 4 * 84)


# ---- Avisos (Tribunal de Disciplina, suspensiones) ----
_ICONO_AVISO = {"clima": "⛈", "luz": "💡", "bengalas": "🔥", "invasion": "🏃", "micro": "🚌",
                "huelga": "✋", "arbitro": "🟥", "corrupcion": "⚖", "gravisimo": "🚨",
                "doping": "💊", "animales": "🐕", "cancha": "🏟️", "logistica": "👕", "hinchada": "🎊"}


def avisos_html(avisos, con_temporada=False):
    """Tarjetas de los avisos (lo más nuevo primero)."""
    S = st.session_state.S
    out = ""
    for a in reversed(avisos):
        grave = a["clave"] not in ("clima", "luz")
        dia = dia_de(S, a["liga"], a["fecha"]) if not con_temporada else None
        cuando = (f'Temporada {a["temp"]}' if con_temporada else texto_dia(dia) if dia else "")
        out += (f'<div class="aviso{" grave" if grave else ""}{" gravisimo" if a["clave"] == "gravisimo" else ""}">'
                f'<div class="av-ico">{_ICONO_AVISO.get(a["clave"], "⚠")}</div><div class="av-cuerpo">'
                f'<div class="av-meta">{logo_img(a["liga"], 16)} {esc(a["liga"])} · {esc(a["rotulo"])}'
                f'{" · " + esc(cuando) if cuando else ""}</div>'
                f'<div class="av-tit">{esc(a["titulo"])}</div>'
                f'<div class="av-partido">{crest(a["local"], 18)} {esc(a["local"])} <span>vs.</span> '
                f'{crest(a["visita"], 18)} {esc(a["visita"])}</div>'
                f'<div class="av-txt">{esc(a["texto"])}</div>'
                f'<div class="av-sancion">{esc(a["sancion"])}</div></div></div>')
    return f'<div class="avisos">{out}</div>'

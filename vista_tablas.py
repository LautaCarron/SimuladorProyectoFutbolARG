"""Tablas de posiciones (HTML), colores por destino, movimientos y el puente para abrir la ficha de un club.
"""

import numpy as np
import streamlit as st

from torneos import ZONA_TAM, destino
from vista_base import (
    COLORES_B,
    COLORES_DESTINO,
    COLORES_F,
    COLORES_ZONA,
    COLOR_ORO,
    crest,
    esc,
    seccion,
)
from vista_partidos import resultado_para


# ---- Tablas -----------------------------------------------------------------
def ultimos_movs(hist):
    if len(hist) < 2 or hist[-1][0] != hist[-2][0]:
        return None
    return hist[-2][1] - hist[-1][1], hist[-1][1]


def color_mov(v):
    if str(v).startswith("▲"):
        return "color: #16a34a; font-weight: 700"
    if str(v).startswith("▼"):
        return "color: #dc2626; font-weight: 700"
    return "color: #94a3b8"


# ---- Tabla HTML (integrada a la página; en mobile se desliza con el club fijo) ----
_COL_NUM = {"Pos", "Pts", "PJ", "G", "E", "P", "GF", "GC", "DG", "Media", "Fecha", "Mérito", "Resultado",
            "Temporada"}


_TITULOS = {"Pos": "#", "Equipo": "Club"}


_AYUDAS = {"±": "Puestos ganados o perdidos en la última fecha", "Media": "Fuerza interna del equipo",
           "Pts": "Puntos", "PJ": "Partidos jugados", "G": "Ganados", "E": "Empatados",
           "P": "Perdidos", "GF": "Goles a favor", "GC": "Goles en contra", "DG": "Diferencia de gol"}


def _valor(v, formato):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "–"
    return formato.format(v) if formato else esc(str(v))


def club_link(nombre, size=22):
    """Escudo + nombre de un club que al tocarlo abre su ficha (la misma de la sección Clubes).
    El click lo recibe el puente de `puente_clubes()`."""
    n = esc(nombre)
    return (f'<span class="tb-cl" role="button" tabindex="0" data-club="{n}" '
            f'title="Ver la ficha de {n}">{crest(nombre, size)}<span class="tb-nm">{n}</span></span>')


def _th(c, clase=""):
    ayuda = f' title="{esc(_AYUDAS[c])}"' if c in _AYUDAS else ""
    return f'<th class="{clase}"{ayuda}>{esc(_TITULOS.get(c, c))}</th>'


def tabla_html(df, estilo=None, clubes=("Equipo",), formatos=None, fija=None, clic=True):
    """Dibuja un DataFrame como tabla HTML con el estilo del sitio.
    - `estilo(fila)` devuelve una lista de CSS por celda (como pandas Styler).
    - Las columnas de `clubes` llevan escudo y (con `clic`) abren la ficha del club.
    - `fija`: esa columna y las anteriores (#, ±, Club) forman un solo bloque que queda quieto
      al deslizar la tabla en pantallas chicas."""
    formatos = formatos or {}
    cols = list(df.columns)
    n_fijas = cols.index(fija) + 1 if fija in cols else 0
    fijas, resto = cols[:n_fijas], cols[n_fijas:]

    def clase(c):
        if c in clubes:
            return "tb-club"
        k = "tb-num" if c in _COL_NUM else "tb-txt"
        return k + (" tb-pts" if c == "Pts" else "")

    def contenido(c, v):
        if c in clubes and isinstance(v, str) and v:
            return club_link(v) if clic else (f'<span class="tb-cl">{crest(v, 22)}'
                                              f'<span class="tb-nm">{esc(v)}</span></span>')
        return _valor(v, formatos.get(c))

    def parte_fija(c, v, e=""):
        cls = {"Pos": "tb-pos", "±": "tb-mov"}.get(c)
        if cls is None:                       # la columna del club ocupa el resto del bloque
            return f'<span class="tb-fc">{contenido(c, v)}</span>'
        e = ";".join(x for x in (e or "").split(";") if x.strip() and "background" not in x)
        return f'<span class="{cls}"' + (f' style="{e}"' if e else "") + f'>{_valor(v, None)}</span>'

    th = ""
    if fijas:
        th += ('<th class="tb-fija"><div class="tb-f">'
               + "".join(f'<span class="{ {"Pos": "tb-pos", "±": "tb-mov"}.get(c, "tb-fc") }"'
                         + (f' title="{esc(_AYUDAS[c])}"' if c in _AYUDAS else "")
                         + f'>{esc(_TITULOS.get(c, c))}</span>' for c in fijas)
               + '</div></th>')
    th += "".join(_th(c, clase(c)) for c in resto)

    filas = []
    for _, fila in df.iterrows():
        css = list(estilo(fila)) if estilo else [""] * len(cols)
        css = [(e or "").replace("background-color", "--rc").strip() for e in css]
        tds = ""
        if fijas:
            fondo = css[n_fijas - 1]                     # color de la fila (el de la celda del club)
            fondo = ";".join(x for x in fondo.split(";") if "--rc" in x)
            tds += (f'<td class="tb-fija"' + (f' style="{fondo}"' if fondo else "") + '><div class="tb-f">'
                    + "".join(parte_fija(c, fila[c], css[i]) for i, c in enumerate(fijas))
                    + '</div></td>')
        for i, c in enumerate(resto, start=n_fijas):
            e = css[i]
            tds += (f'<td class="{clase(c)}"' + (f' style="{e}"' if e else "")
                    + f'>{contenido(c, fila[c])}</td>')
        filas.append("<tr>" + tds + "</tr>")
    return (f'<div class="tabla-wrap"><table class="tabla{" con-fija" if fijas else ""}">'
            f'<thead><tr>{th}</tr></thead><tbody>{"".join(filas)}</tbody></table></div>')


def mostrar_tabla(df, fn_color, hist=None):
    df = df.copy()
    mov = ultimos_movs(hist) if hist is not None else None
    if hist is not None:
        if mov:
            d = [int(x) for x in mov[0][df["id"].to_numpy()]]
            df.insert(1, "±", [f"▲{x}" if x > 0 else f"▼{-x}" if x < 0 else "=" for x in d])
        else:
            df.insert(1, "±", ["–"] * len(df))
    df = df.drop(columns="id")
    orden = [c for c in ["Pos", "±", "Equipo", "Región", "Pts", "PJ", "G", "E", "P", "GF", "GC",
                         "DG", "Destino", "Media"] if c in df.columns]
    df = df[orden]
    cols = list(df.columns)

    def estilo(fila):
        css = list(fn_color(fila))
        if "±" in cols:
            i = cols.index("±")
            css[i] = "; ".join(x for x in (css[i], color_mov(fila["±"])) if x)
        return css

    st.markdown(tabla_html(df, estilo, formatos={"Media": "{:.1f}"}, fija="Equipo"),
                unsafe_allow_html=True)


def colorear_fase1(fila):
    """Pinta según la zona a la que pasa (o pasaría) cada equipo de Primera."""
    c = COLORES_ZONA[(fila["Pos"] - 1) // ZONA_TAM]
    return [f"background-color: {c}"] * len(fila)


def colorear_destino(fila):
    """Pinta según el destino (copas / promoción / descenso); dorado para el líder."""
    pos = fila["Pos"]
    d = fila.get("Destino", "")
    if "Desempate" in d:
        if "Campeonato" in d:
            c = "rgba(249, 115, 22, 0.3)"
        else:
            c = "rgba(147, 51, 234, 0.3)"
        return [f"background-color: {c}"] * len(fila)
        
    c = COLOR_ORO if pos == 1 else COLORES_DESTINO.get(destino(pos), "")
    return [f"background-color: {c}" if c else ""] * len(fila)


def colorear_b(fila):
    d = fila["Destino"]
    c = COLORES_B.get(d, "")
    if "Desempate" in d:
        c = "rgba(147, 51, 234, 0.3)"
    return [f"background-color: {c}" if c else ""] * len(fila)


def colorear_f(fila):
    c = COLORES_F.get(fila["Destino"], "")
    return [f"background-color: {c}" if c else ""] * len(fila)


def colorear_pb(fila):
    d = fila["Destino"]
    c = COLORES_B["Ascenso directo"] if d == "Ascenso directo" else (
        COLORES_B["Desciende"] if d == "Desciende" else (
        "rgba(147, 51, 234, 0.3)" if d == "Desempate Permanencia" else (
        "rgba(249, 115, 22, 0.3)" if d in ("Desempate Campeonato", "Desempate Ascenso") else ""
        )))
    return [f"background-color: {c}" if c else ""] * len(fila)


def colorear_reg(fila):
    d = fila["Destino"]
    c = (COLOR_ORO if d == "Campeón regional" else
         "rgba(249, 115, 22, 0.3)" if d == "Desempate Campeonato" else "")
    return [f"background-color: {c}" if c else ""] * len(fila)


def colorear_pc(fila):
    d = fila["Destino"]
    c = COLORES_B["Ascenso directo"] if d == "Ascenso directo" else (
        COLORES_B["Desciende"] if d == "Desciende" else (
        "rgba(147, 51, 234, 0.3)" if d == "Desempate Permanencia" else (
        "rgba(249, 115, 22, 0.3)" if d in ("Desempate Campeonato", "Desempate Ascenso") else ""
        )))
    return [f"background-color: {c}" if c else ""] * len(fila)


def colorear_pd(fila):
    d = fila["Destino"]
    c = COLORES_B["Ascenso directo"] if d == "Ascenso directo" else (
        "rgba(249, 115, 22, 0.3)" if d in ("Desempate Campeonato", "Desempate Ascenso") else ""
    )
    return [f"background-color: {c}" if c else ""] * len(fila)


# ---- Movimientos de la temporada -------------------------------------------
def rachas(log, nombres):
    seq = {n: [] for n in nombres}
    for p in log:
        for eq in (p["local"], p["visita"]):
            if eq in seq:
                seq[eq].append(resultado_para(p, eq)[3])

    def cola(lst, ok):
        n = 0
        for x in reversed(lst):
            if x not in ok:
                break
            n += 1
        return n

    invicto = max(nombres, key=lambda n: cola(seq[n], "GE"))
    sin_ganar = max(nombres, key=lambda n: cola(seq[n], "EP"))
    ganando = max(nombres, key=lambda n: cola(seq[n], "G"))
    return ((invicto, cola(seq[invicto], "GE")), (sin_ganar, cola(seq[sin_ganar], "EP")),
            (ganando, cola(seq[ganando], "G")))


def card(k, v, s="", color="#2f7fd0", big=False):
    return (f'<div class="card" style="--c:{color}"><div class="k">{k}</div>'
            f'<div class="v{" big" if big else ""}">{v}</div><div class="s">{s}</div></div>')


def eq_html(n, size=26):
    return f'{crest(n, size)}<span>{esc(n)}</span>'


def partido_corto(p):
    pen = f" ({p['pen'][0]}-{p['pen'][1]} pen.)" if p["pen"] else ""
    return (f'{crest(p["local"], 22)}<span>{esc(p["local"])} <b>{p["gl"]}-{p["gv"]}</b>'
            f'{pen} {esc(p["visita"])}</span>{crest(p["visita"], 22)}')


def render_movimientos(log, hist, nombres, color):
    seccion("Movimientos de la temporada", "Cambios en la tabla, rachas y partidos destacados",
            color)
    log = [p for p in log if p["local"] in nombres or p["visita"] in nombres]
    if not log:
        st.info("Simulá una fecha para ver los movimientos de la temporada.")
        return
    cards = ""
    mov = ultimos_movs(hist)
    if mov:
        d, cur = mov
        iu, idn = int(np.argmax(d)), int(np.argmin(d))
        if d[iu] > 0:
            cards += card("▲ Mayor subida · última fecha", eq_html(nombres[iu]),
                          f"Ganó {d[iu]} puesto{'s' if d[iu] > 1 else ''}: del "
                          f"{cur[iu] + d[iu]}° al {cur[iu]}°", "#16a34a")
        if d[idn] < 0:
            cards += card("▼ Mayor caída · última fecha", eq_html(nombres[idn]),
                          f"Perdió {-d[idn]} puesto{'s' if d[idn] < -1 else ''}: del "
                          f"{cur[idn] + d[idn]}° al {cur[idn]}°", "#dc2626")
    gole = max(log, key=lambda p: (abs(p["gl"] - p["gv"]), p["gl"] + p["gv"]))
    if gole["gl"] != gole["gv"]:
        cards += card("Mayor goleada", partido_corto(gole),
                      f"{gole['rotulo']} · {gole['comp']}", "#ea580c")
    mas = max(log, key=lambda p: (p["gl"] + p["gv"], -abs(p["gl"] - p["gv"])))
    cards += card("Partido con más goles", partido_corto(mas),
                  f"{mas['gl'] + mas['gv']} goles · {mas['rotulo']}", "#0891b2")
    (inv, n_inv), (sg, n_sg), (gan, n_gan) = rachas(log, nombres)
    if n_gan >= 2:
        cards += card("Racha ganadora", eq_html(gan), f"{n_gan} victorias seguidas", "#16a34a")
    cards += card("Racha invicta", eq_html(inv), f"{n_inv} partidos sin perder", "#2f7fd0")
    cards += card("Racha sin ganar", eq_html(sg), f"{n_sg} partidos sin ganar", "#64748b")
    goles = sum(p["gl"] + p["gv"] for p in log)
    emp = sum(p["gl"] == p["gv"] for p in log)
    cards += card("Goles por partido", f"{goles / len(log):.2f}",
                  f"{goles} goles en {len(log)} partidos · {100 * emp / len(log):.0f}% empates",
                  "#7c3aed", big=True)
    st.markdown(f'<div class="cards">{cards}</div>', unsafe_allow_html=True)

    if mov:
        d, cur = mov
        orden = np.argsort(-d)
        suben = [i for i in orden if d[i] > 0][:8]
        bajan = [i for i in orden[::-1] if d[i] < 0][:8]

        def lista(ids, cls, signo):
            return "".join(f'<span class="mv">{crest(nombres[i], 20)}{esc(nombres[i])}'
                           f'<span class="d {cls}">{signo}{abs(d[i])}</span>'
                           f'<span style="opacity:.6">{cur[i]}°</span></span>' for i in ids) or "—"

        c1, c2 = st.columns(2)
        c1.markdown('<div class="mlab up">▲ Subieron en la última fecha</div><div class="movlist">'
                    + lista(suben, "up", "+") + "</div>", unsafe_allow_html=True)
        c2.markdown('<div class="mlab down">▼ Bajaron en la última fecha</div><div class="movlist">'
                    + lista(bajan, "down", "−") + "</div>", unsafe_allow_html=True)

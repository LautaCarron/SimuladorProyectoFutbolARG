"""Piezas básicas de la interfaz: colores, etiquetas, escudos, banderas y el estado compartido.
"""

import hashlib
import html
import re
import streamlit as st
import unicodedata

from datos.equipos import ESCUDOS, ESCUDOS_OSCUROS


def _estado():
    """Estado de la sesión actual: Primera, B Nacional, Federal A, Primera B y Primera C."""
    S = st.session_state.S
    return S, S["b"], S["f"], S["pb"], S["pc"]


COLOR_ORO = "rgba(227, 162, 26, 0.30)"


COLORES_DESTINO = {
    "Libertadores": "rgba(116, 172, 223, 0.36)",
    "Fase previa Libertadores": "rgba(116, 172, 223, 0.18)",
    "Sudamericana": "rgba(224, 138, 40, 0.20)",
    "Promoción": "rgba(109, 63, 192, 0.16)",
    "Desciende": "rgba(184, 58, 46, 0.17)",
}


COLORES_ZONA = ["rgba(46, 125, 79, 0.15)", "rgba(227, 162, 26, 0.15)", "rgba(184, 58, 46, 0.13)"]


COLORES_B = {
    "Campeón · Ascenso": COLOR_ORO,
    "Ascenso directo": "rgba(46, 125, 79, 0.22)",
    "Cuartos del reducido": "rgba(116, 172, 223, 0.36)",
    "Octavos del reducido": "rgba(116, 172, 223, 0.18)",
    "Desciende": "rgba(184, 58, 46, 0.17)",
    "→ Zona Campeonato": COLORES_ZONA[0],
    "→ Zona Intermedia": COLORES_ZONA[1],
    "→ Zona Descenso": COLORES_ZONA[2],
}


COLORES_F = {
    "Campeón · Ascenso": COLOR_ORO,
    "Ascenso directo": "rgba(46, 125, 79, 0.22)",
    "Reducido": "rgba(116, 172, 223, 0.30)",
    "→ Fase 2": "rgba(46, 125, 79, 0.15)",
    "→ Zona Campeonato": "rgba(46, 125, 79, 0.15)",
    "Desciende": "rgba(184, 58, 46, 0.17)",
}


COLOR_COMP = [
    ("Mundial de Clubes", "#be185d"),
    ("Campeonato", "#16a34a"), ("Intermedia", "#d97706"), ("Descenso", "#dc2626"),
    ("Zona A", "#4f46e5"), ("Zona B", "#0891b2"), ("Octavos", "#2563eb"),
    ("Cuartos", "#1d4ed8"), ("Semifinal", "#7c3aed"), ("Final", "#b7860b"),
    ("Promoción", "#9333ea"), ("Fase 1", "#475569"), ("Federal A", "#b45309"),
    ("Primera B", "#0369a1"),
    ("Primera División", "#1e5aa8"), ("Primera Nacional", "#0f766e"),
    ("Regional Amateur", "#0e7490"), ("Región", "#0e7490"),
]


esc = html.escape


def color_de(txt):
    for k, c in COLOR_COMP:
        if k in txt:
            return c
    return "#64748b"


def chip(txt, color=None):
    return f'<span class="chip" style="--c:{color or color_de(txt)}">{esc(txt)}</span>'


def seccion(titulo, sub="", color="#2f7fd0"):
    sub = f'<span class="sub">{esc(sub)}</span>' if sub else ""
    st.markdown(f'<div class="sec" style="--c:{color}"><span class="tt">{titulo}</span>{sub}</div>',
                unsafe_allow_html=True)


def aviso(txt):
    st.markdown(f'<div class="aviso">{txt}</div>', unsafe_allow_html=True)


def leyenda(items):
    st.markdown('<div class="legend">' + "".join(
        f'<span><i style="background:{c}"></i>{esc(t)}</span>' for t, c in items) + "</div>",
        unsafe_allow_html=True)


def iniciales(nombre):
    base = nombre.split("(")[0].replace("'", "").strip()
    w = base.split()
    return (w[0][0] + w[1][0]).upper() if len(w) >= 2 else base[:3].upper()


def crest(nombre, size=26):
    """Escudo real del club (o un distintivo con sus iniciales si no hay imagen)."""
    url = ESCUDOS.get(nombre)
    if url:
        osc = " crest-osc" if nombre in ESCUDOS_OSCUROS else ""
        return (f'<img class="crest-img{osc}" src="{esc(url)}" width="{size}" height="{size}" '
                f'alt="" loading="lazy" title="{esc(nombre)}">')
    h = int(hashlib.md5(nombre.encode("utf-8")).hexdigest()[:6], 16)
    return (f'<span class="crest" style="width:{size}px;height:{size + 2}px;'
            f'font-size:{max(8, round(size * 0.36))}px;background:linear-gradient(160deg,'
            f'hsl({h % 360},62%,44%),hsl({(h // 360 + 25) % 360},58%,28%))">'
            f'{esc(iniciales(nombre))}</span>')


def norm(s):
    s = unicodedata.normalize("NFKD", str(s).lower())
    return "".join(c for c in s if not unicodedata.combining(c))


_STOP = {"fecha", "vs", "contra", "de", "del", "la", "el", "y", "-", "fch", "f"}


def coincide(consulta, texto, fecha, marcadores):
    """Cada palabra de la búsqueda tiene que aparecer. Un número = número de fecha;
    algo como 2-1 = resultado (en cualquier orden)."""
    for t in norm(consulta).replace("–", "-").split():
        if t in _STOP:
            continue
        if t.isdigit():
            if int(t) != fecha:
                return False
        elif re.fullmatch(r"\d+-\d+", t):
            if t not in marcadores:
                return False
        elif t not in texto:
            return False
    return True


LEY_ZONAS = [("Pasa a Zona Campeonato", COLORES_ZONA[0]), ("Zona Intermedia", COLORES_ZONA[1]),
             ("Zona Descenso", COLORES_ZONA[2])]


LEY_DESTINOS = [("Líder", COLOR_ORO), ("Libertadores", COLORES_DESTINO["Libertadores"]),
                ("Fase previa Libertadores", COLORES_DESTINO["Fase previa Libertadores"]),
                ("Sudamericana", COLORES_DESTINO["Sudamericana"]),
                ("Promoción", COLORES_DESTINO["Promoción"]), ("Descenso", COLORES_DESTINO["Desciende"])]


LEY_B = [("Campeón", COLOR_ORO), ("Ascenso directo", COLORES_B["Ascenso directo"]),
         ("Cuartos del reducido", COLORES_B["Cuartos del reducido"]),
         ("Octavos del reducido", COLORES_B["Octavos del reducido"]),
         ("Desciende", COLORES_B["Desciende"])]


LEY_F = [("Campeón", COLOR_ORO), ("Ascenso directo", COLORES_F["Ascenso directo"]),
         ("Juega el reducido", COLORES_F["Reducido"]),
         ("Desciende al Regional", COLORES_F["Desciende"])]


_ISO = {"Argentina": "ar", "Brasil": "br", "Colombia": "co", "Paraguay": "py", "Perú": "pe", "Chile": "cl",
        "Uruguay": "uy", "Ecuador": "ec", "Bolivia": "bo", "Venezuela": "ve",
        "Francia": "fr", "España": "es", "Inglaterra": "gb-eng", "Alemania": "de", "Italia": "it",
        "Portugal": "pt", "Países Bajos": "nl", "Arabia Saudita": "sa", "Japón": "jp",
        "Corea del Sur": "kr", "Qatar": "qa", "Emiratos Árabes Unidos": "ae", "Egipto": "eg",
        "Sudáfrica": "za", "Marruecos": "ma", "Túnez": "tn", "RD Congo": "cd", "México": "mx",
        "Estados Unidos": "us", "Canadá": "ca", "Nueva Zelanda": "nz"}


def bandera(pais, ancho=18):
    iso = _ISO.get(pais)
    if not iso:
        return ""
    return (f'<img class="bandera" src="https://flagcdn.com/w40/{iso}.png" width="{ancho}" '
            f'height="{round(ancho * 2 / 3)}" alt="{esc(pais)}" title="{esc(pais)}" loading="lazy">')


def barra_estado(items, progreso):
    celdas = "".join(f'<div class="stc"><span>{esc(k)}</span><b>{esc(str(v))}</b></div>'
                     for k, v in items)
    celdas += (f'<div class="stc"><span>Progreso</span><b>{progreso:.0f}%</b>'
               f'<div class="bar"><i style="width:{progreso:.1f}%"></i></div></div>')
    st.markdown(f'<div class="status">{celdas}</div>', unsafe_allow_html=True)

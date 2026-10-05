"""
Simulador del fútbol argentino: Primera División + Categorías de Ascenso
-------------------------------------------------------------------------------
Ejecutar con:
    python -m pip install streamlit numpy pandas
    python -m streamlit run simuladorafa.py

PRIMERA DIVISIÓN (30 equipos)
  * Fase 1: todos contra todos, 29 fechas (una vuelta).
  * Fase 2: tres zonas de 10 según la tabla (Campeonato 1-10, Intermedia 11-20,
    Descenso 21-30), 9 fechas dentro de la zona con localía invertida.
  * Destinos: 1-5 Libertadores · 6-8 Sudamericana · 11 Fase previa Libertadores
    · 12-13 Sudamericana · 28-30 descienden · 27° juega la PROMOCIÓN.

PRIMERA NACIONAL (36 equipos)
  * Fase 1: 2 zonas de 18 (A y B), una sola rueda (17 fechas) + 8 fechas
    interzonales cruzadas entre ambas zonas antes de pasar a la fase 2.
  * Se reparten en 3 zonas de 12 y CONSERVAN los puntos acumulados:
      Campeonato: 1°-6° de cada zona · Intermedia: 7°-12° de cada zona
      Descenso: 13°-18° de cada zona.  Una sola rueda en cada una.
  * Campeonato: 1° campeón + ascenso · 2° ascenso · 3°-4° a cuartos del reducido
    · 5°-12° a octavos.   Intermedia: 1°-4° a octavos.
    Descenso: los 6 últimos descienden (al Federal A o Primera B según afiliación).
  * Reducido (14 equipos): a partido único. Localía y ventaja para el mejor
    ubicado. Final en cancha neutral con penales.
  * El campeón del reducido asciende. El perdedor de la final juega la PROMOCIÓN
    contra el 27° de Primera.

FEDERAL A (Equipos indirectamente afiliados)
  * Fase 1: 5 grupos por cercanía geográfica (Norte, Centro, Buenos Aires,
    Patagonia y Cuyo), ida y vuelta.
  * Fase 2: Pasan los 4 primeros de cada grupo a la Zona Campeonato (20 equipos).
    El resto a Zona Descenso. Puntos de vuelta a 0, una sola rueda.
  * Ascensos: 1°, 2° y 3° de la Zona Campeonato ascienden directo.
  * Reducido: Del 4° al 8° juegan eliminatorias a partido único por el cuarto
    ascenso a la Primera Nacional.
  * Descenso: los 6 últimos de la Zona Descenso bajan al Regional Amateur (a la
    región de su provincia). Si hay igualdad en puntos en el límite, desempate.

PRIMERA B (Equipos directamente afiliados)
  * Formato de liga tradicional: Todos contra todos, ida y vuelta.
  * Ascensos: Campeón y subcampeón (1° y 2°) ascienden de forma directa a la 
    Primera Nacional.
  * del 18 al ultimo bajan a la Primera C, si el campeonato son menos de
    18 equipos no hay descensos.

PRIMERA C (Equipos directamente afiliados)
  * Formato de liga tradicional: Todos contra todos, ida y vuelta.
  * Ascensos: Campeón y subcampeón (1° y 2°) ascienden de forma directa a la 
    Primera B.

Cada equipo tiene una "media interna" (fuerza) que cambia cada temporada.
Los partidos se simulan con goles Poisson y cada equipo tiene una "forma del
día" aleatoria: cuanto mayor es el nivel de sorpresas, más seguido gana el
que tiene menos media.
"""

import streamlit as st

st.set_page_config(page_title="Proyecto AFA · Simulador Fútbol Argentino", page_icon="⚽", layout="wide",
                   initial_sidebar_state="collapsed")

import os
import sys
from types import SimpleNamespace

import numpy as np
import pandas as pd


from datos import (
    ERROR_DATOS,
    ESCUDOS,
    F_GRUPOS_NOMBRES,
    N,
    origen,
    region_regional,
)

if ERROR_DATOS:                 # datos.py ya no depende de Streamlit: el aviso lo muestra la interfaz
    st.error(ERROR_DATOS)
    st.stop()
from motor import (
    MAX_R,
    MIN_R,
)
from torneos import (
    B_F1,
    B_F2,
    B_RED,
    B_TOTAL,
    B_ZONAS2,
    FECHAS_F1,
    TOTAL_FECHAS,
    VERSION_ESTADO,
    ZONAS,
    crear_estado,
    nueva_temporada,
    primera_terminada,
    simular_fecha,
    simular_fecha_b,
    simular_fecha_f,
    simular_fecha_liga,
    tabla_b_f1,
    tabla_b_f2,
    tabla_f_f2,
    tabla_f_grupo,
    tabla_final,
    tabla_general,
    tabla_pb,
    tabla_pc,
    tabla_pd,
    tabla_zona,
    total_b,
    total_primera,
    simular_fecha_reg,
    tabla_reg_region,
)
from regional import FINALES_REG, REGIONES_REG
from copas import (
    COPA_CORTO,
    COPA_LLAVES,
    COPA_RONDAS,
    ligas_terminadas,
    rivales_supercopa,
    simular_ronda_copa,
    simular_supercopa,
    sortear_copa,
    supercopa_lista,
)
from competencias import REGISTRO
from logos import LOGOS, LOGOS_CSS, logo_img
from internacional import fase_actual, listo, pais_de, simular_ronda_int, terminadas
from mundial import (
    RONDAS as MUNDIAL_RONDAS,
    anio_de as anio_mundial,
    calcular_clasificados,
    fase_actual as fase_mundial,
    hay_mundial,
    medias as medias_mundial,
    mundial_terminado,
    pais_club,
    proxima_temporada,
    simular_ronda_mundial,
)
from calendario import anio, jugar_proximo_dia, nombre_mes, proximos, texto_dia
from vista import (
    COLOR_ORO,
    COLORES_B,
    COLORES_F,
    COLORES_ZONA,
    CSS,
    LEY_B,
    LEY_DESTINOS,
    LEY_F,
    LEY_ZONAS,
    aviso,
    barra_estado,
    bracket_html,
    bracket_html_f,
    chip,
    colorear_b,
    colorear_destino,
    colorear_f,
    colorear_fase1,
    colorear_pb,
    colorear_pc,
    colorear_reg,
    avisos_html,
    bandera,
    cuadro_int_html,
    grupos_int_html,
    grupos_mundial_html,
    cuadro_mundial_html,
    series_int_html,
    serie_int_html,
    calendario_mes_html,
    eventos_calendario,
    cuadro_final_copa_html,
    cuadro_llave_html,
    finales_reg_html,
    crest,
    esc,
    fila_partido_html,
    leyenda,
    lista_equipos_html,
    mostrar_tabla,
    tabla_html,
    club_link,
    puente_clubes,
    norm,
    render_ficha,
    render_movimientos,
    seccion,
    ver_equipo,
    vista_fixture,
)


def editar_medias(nombres, r, clave):
    """Editor de medias internas. En la versión web (stlite, corre en el navegador)
    st.data_editor no funciona, así que ahí se edita club por club."""
    if sys.platform != "emscripten":
        ed = st.data_editor(pd.DataFrame({"Equipo": nombres, "Media": r}),
                            disabled=["Equipo"], hide_index=True, width="stretch", key=clave)
        return np.clip(ed["Media"].to_numpy(float), MIN_R, MAX_R)
    r = np.array(r, dtype=float)
    c1, c2 = st.columns([3, 2], vertical_alignment="bottom")
    i = c1.selectbox("Club", range(len(nombres)), format_func=lambda k: nombres[k],
                     key=f"{clave}_club")
    r[i] = c2.number_input("Media", MIN_R, MAX_R, float(round(r[i], 1)), 0.5,
                           key=f"{clave}_media_{i}")
    return r


# ----------------------------------------------------------------------------
# INTERFAZ
# ----------------------------------------------------------------------------
st.markdown(CSS, unsafe_allow_html=True)
st.markdown(LOGOS_CSS, unsafe_allow_html=True)   # logos de ligas y copas (una sola vez)
puente_clubes()     # tocar un club en cualquier tabla abre su ficha

with st.sidebar:
    st.header("Parámetros de simulación")
    sorpresa = st.slider("Nivel de sorpresas", 0.0, 15.0, 6.0, 0.5,
                         help="Qué tanto varía la 'forma del día' de cada equipo. "
                              "Más alto = más partidos donde gana el que tiene menos media.")
    volatilidad = st.slider("Volatilidad entre temporadas", 0.0, 10.0, 2.5, 0.5,
                            help="Qué tanto cambia la media de cada equipo al pasar de temporada.")
    acumular = st.checkbox("Arrastrar puntos de la fase 1 a las zonas (Primera)", value=True,
                           help="Solo Primera. Si está activado, las zonas parten con lo sumado en "
                                "las 29 fechas. Si no, cada zona arranca de cero. Se fija al "
                                "terminar la fase 1. (En la B Nacional ahora los puntos se conservan siempre).")
    st.caption("En cada partido, cada equipo rinde un poco mejor o peor que su "
               "media habitual. Los partidos del reducido y la promoción son a un solo "
               "partido y, si empatan, se definen por penales.")

P = dict(sorpresa=sorpresa)


if "S" not in st.session_state or st.session_state.S.get("version") != VERSION_ESTADO:
    st.session_state.S = crear_estado()
S = st.session_state.S
SB, SF, SPB, SPC, SR, SC = S["b"], S["f"], S["pb"], S["pc"], S["reg"], S["copa"]
SPD = S.get("pd", SPC)
SS = S["supercopa"]
SM = S["mundial"]

terminada = primera_terminada(S)            # incluye las fechas de desempate
terminada_b = SB["fecha"] >= total_b(SB)
terminada_f = SF["fecha"] >= SF["total"]
terminada_pb = SPB["fecha"] >= SPB["total"]
terminada_pc = SPC["fecha"] >= SPC["total"]
terminada_pd = SPD["fecha"] >= SPD["total"]
terminada_reg = SR["fecha"] >= SR["total"]
terminada_copa = SC["sorteada"] and SC["ronda"] >= SC["total"]
terminadas_extra = all(comp.terminada(S) for comp in REGISTRO)       # Copa, Supercopa y Mundial (si hay)
terminadas_int = terminadas(S)
ambas = (terminada and terminada_b and terminada_f and terminada_pb and terminada_pc and terminada_reg
         and terminada_copa and terminadas_extra and terminadas_int)
b_espera_primera = SB["fecha"] == total_b(SB) - 1 and not terminada

pct_p = 100 * S["fecha"] / total_primera(S)
pct_b = 100 * SB["fecha"] / total_b(SB)
pct_f = 100 * SF["fecha"] / SF["total"]
pct_pb = 100 * SPB["fecha"] / SPB["total"] if SPB["total"] else 0
pct_pc = 100 * SPC["fecha"] / SPC["total"] if SPC["total"] else 0
pct_reg = 100 * SR["fecha"] / SR["total"] if SR["total"] else 0
pct_copa = 100 * SC["ronda"] / SC["total"]

# ---- Cabecera (masthead) · Proyecto AFA
# Sol de Mayo geométrico: 16 rayos alternando largo (mismo dibujo que la intro)
_RAYOS = "".join(
    f'<polygon points="-3.2,-21 0,-{36 if k % 2 else 47} 3.2,-21" transform="rotate({k * 22.5})"/>'
    for k in range(16))
SOL_SVG = (f'<svg viewBox="-50 -50 100 100" aria-hidden="true"><g fill="currentColor">{_RAYOS}'
           f'<circle r="16.5"/></g></svg>')


def _celda(nombre, fecha, total, pct):
    return (f'<div class="mh-c"><span>{nombre}</span><b>{fecha}/{total}</b>'
            f'<div class="bar"><i style="width:{pct:.1f}%"></i></div></div>')


# En la web el tema claro/oscuro lo maneja la intro (index.html): este botón le avisa.
_BOTON_TEMA = (
    '<a class="mh-tema" href="#tema" title="Cambiar entre modo claro y oscuro" '
    'aria-label="Cambiar entre modo claro y oscuro">'
    '<svg class="sol-ico" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5">'
    '<circle cx="8" cy="8" r="3"/><path d="M8 1v2M8 13v2M1 8h2M13 8h2M3 3l1.4 1.4M11.6 11.6L13 13'
    'M3 13l1.4-1.4M11.6 4.4L13 3"/></svg>'
    '<svg class="luna" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5">'
    '<path d="M13.5 9.8A6 6 0 0 1 6.2 2.5a6 6 0 1 0 7.3 7.3z"/></svg></a>')

# En la web (stlite) la marca vuelve a la intro de Proyecto AFA; en la PC no hay intro
_web = sys.platform == "emscripten"
_marca_tag = ('a class="mh-marca" href="#inicio" title="Volver al inicio de Proyecto AFA"'
              if _web else 'div class="mh-marca"')
_jugados = (len(S["log"]) + len(SB["log"]) + len(SF["log"]) + len(SPB["log"]) + len(SPC["log"])
            + len(SR["log"]) + sum(len(comp.log(S)) for comp in REGISTRO))
_prox = proximos(S)
_hoy = min((d for d, _ in _prox.values()), default=None)       # próximo día con partidos
st.markdown(
    f'<header class="masthead"><{_marca_tag}>{SOL_SVG}<div><b>Proyecto AFA</b>'
    f'<span>Simulador Fútbol Argentino</span></div></{"a" if _web else "div"}>'
    f'<div class="mh-der"><div class="mh-tabla">'
    f'<div class="mh-c temp"><span>Temporada</span><b>{S["temp"]}</b></div>'
    + _celda("Primera", S["fecha"], total_primera(S), pct_p)
    + _celda("B Nacional", SB["fecha"], total_b(SB), pct_b)
    + _celda("Federal A", SF["fecha"], SF["total"], pct_f)
    + _celda("Primera B", SPB["fecha"], SPB["total"], pct_pb)
    + _celda("Primera C", SPC["fecha"], SPC["total"], pct_pc)
    + _celda("Regional", SR["fecha"], SR["total"], pct_reg)
    + _celda("Copa Arg.", SC["ronda"], SC["total"], pct_copa)
    + f'<div class="mh-c"><span>Partidos</span><b>{_jugados}</b></div>'
    + f'<div class="mh-c"><span>Próximo día</span><b>{texto_dia(_hoy, False) if _hoy else "—"}</b></div></div>'
    + (_BOTON_TEMA if _web else "")
    + '</div></header>', unsafe_allow_html=True)

g0, gd, g1, g2, g3 = st.container(key="acciones").columns([1.6, 1.4, 1.3, 1.5, 1.1],
                                                          vertical_alignment="center")
g0.caption("Jugá día por día del calendario, fecha por fecha en cada categoría, o simulá todo junto.")
if gd.button(":material/calendar_today: Próximo día", disabled=_hoy is None, width="stretch",
             help=f"Juega todo lo del {texto_dia(_hoy)}" if _hoy else None):
    jugar_proximo_dia(S, P, acumular)
    st.rerun()
if g1.button(":material/fast_forward: Simular todo", disabled=ambas, width="stretch", type="primary"):
    # 1. Primero terminar Primera División, desempates incluidos
    #    (la B necesita saber el 27° definitivo para la Promoción)
    while not primera_terminada(S):
        simular_fecha(S, P, acumular)
        
    # 2. Ahora sí corre la B Nacional hasta el final sin trabarse
    while SB["fecha"] < total_b(SB) and not (SB["fecha"] == total_b(SB) - 1 and not primera_terminada(S)):
        simular_fecha_b(S, P)
        
    # 3. Resto de las categorías
    while SF["fecha"] < SF["total"]: 
        simular_fecha_f(SF, P, S["rng"])
    while SPB["fecha"] < SPB["total"]: 
        simular_fecha_liga(SPB, P, S["rng"], "Primera B", tabla_pb)
    while SPC["fecha"] < SPC["total"]: 
        simular_fecha_liga(SPC, P, S["rng"], "Primera C", tabla_pc)
    while SPD["fecha"] < SPD["total"]:
        simular_fecha_liga(SPD, P, S["rng"], "Promocional Amateur", tabla_pc)
    while SR["fecha"] < SR["total"]:
        simular_fecha_reg(SR, P, S["rng"])
    # 4. Copa Argentina (se juega en el medio de las ligas; acá se completa lo que falte)
    while S["copa"]["ronda"] < S["copa"]["total"]:
        simular_ronda_copa(S["copa"], P, S["rng"])
    # 4b. Copas del registro (Supercopa y Mundial de Clubes): cada una sabe si le toca jugar ahora
    for comp in REGISTRO:
        comp.jugar_todo(S, P, S["rng"])
    # 5. Copas CONMEBOL (la Sudamericana espera lo que necesita de la Libertadores)
    while not terminadas(S):
        for clave in ("rec", "lib", "sud"):
            simular_ronda_int(S, clave, P, S["rng"])
    st.rerun()
if g2.button(":material/event_repeat: Nueva temporada", disabled=not ambas, width="stretch"):
    nueva_temporada(S, volatilidad)
    st.rerun()
if g3.button(":material/restart_alt: Reiniciar", width="stretch"):
    st.session_state.S = crear_estado()
    st.rerun()

# Avisos (suspensiones y sanciones): los de esta temporada y los anteriores. Los nuevos (sin leer)
# se cuentan en la pestaña Avisos.
_avisos = [a for L in (S, SB, SF, SPB, SPC, SR, SC) for a in L.get("alertas", [])]
_total_avisos = len(S.get("alertas_hist", [])) + len(_avisos)
_sin_leer = max(0, _total_avisos - S.get("avisos_leidos", 0))


def _con_logo(liga, texto):
    return f"![]({LOGOS[liga]}) {texto}" if liga in LOGOS else texto


# Sólo se dibuja la pestaña abierta (on_change="rerun" + .open): antes se armaban las 6 ligas y
# todas las copas en cada clic, la página pesaba más de 1 MB y el navegador se quedaba trabado.
with st.container(key="menu_top"):
    tab_ligas, tab_copas, tab_cal, tab_c, tab_av, tab_h = st.tabs(
        ["Ligas", "Copas", "Calendario", "Clubes", "Avisos", "Historial"], key="tabs_top", on_change="rerun")
if _sin_leer:                          # contador de avisos nuevos (globito rojo en la pestaña)
    st.markdown(f'<style>.st-key-menu_top>[data-testid="stTabs"]>div>[role="tablist"]>[role="tab"]:nth-child(5)'
                f'::after{{content:"{_sin_leer}";margin-left:6px;background:var(--lose);color:#fff;font-size:.66rem;'
                f'font-weight:800;border-radius:9px;padding:1px 7px;line-height:1.4;}}</style>', unsafe_allow_html=True)
with tab_ligas:
    with st.container(key="menu_ligas"):
        tab_p, tab_b, tab_f, tab_reg, tab_pb, tab_pc, tab_pd = st.tabs([
            _con_logo("Primera División", "Primera"), _con_logo("Primera Nacional", "B Nacional"),
            _con_logo("Federal A", "Federal A"), _con_logo("Regional Amateur", "Regional"),
            _con_logo("Primera B", "Primera B"), _con_logo("Primera C", "Primera C"),
            _con_logo("Promocional Amateur", "Promocional"),
        ], key="tabs_ligas", on_change="rerun")
with tab_copas:
    with st.container(key="menu_copas"):
        tab_ca, tab_sup, tab_lib, tab_sud, tab_rec, tab_mun = st.tabs([
            _con_logo("Copa Argentina", "Copa Argentina"), 
            _con_logo("Supercopa Argentina", "Supercopa"),
            _con_logo("Copa Libertadores", "Libertadores"),
            _con_logo("Copa Sudamericana", "Sudamericana"), 
            _con_logo("Recopa Sudamericana", "Recopa"),
            _con_logo("Mundial de Clubes", "Mundial de Clubes")
            ],
            key="tabs_copas", on_change="rerun")


_TODAS = os.environ.get("AFA_TODAS_LAS_PESTANAS") == "1"   # sólo para las pruebas automáticas


def _abierta(*tabs):
    """¿Está a la vista? (la pestaña y sus pestañas madre abiertas)."""
    return _TODAS or all(t.open is not False for t in tabs)

# (Esto va debajo de los imports y la configuración inicial de streamlit)

def html_tabla_liguilla(partidos):
    stats = {}
    for p in partidos:
        # Atrapamos "local" o "l", y "visita" o "v"
        l = p.get("local") or p.get("l")
        v = p.get("visita") or p.get("visitante") or p.get("v")
        gl = p.get("gl", 0)
        gv = p.get("gv", 0)
        gana = p.get("gana")
        
        # Inicializa los equipos si no existen
        for eq in (l, v):
            if eq not in stats: stats[eq] = {"Pts": 0, "PJ": 0, "G": 0, "P": 0, "GF": 0, "GC": 0, "DG": 0}
        
        stats[l]["PJ"] += 1; stats[v]["PJ"] += 1
        stats[l]["GF"] += gl; stats[l]["GC"] += gv
        stats[v]["GF"] += gv; stats[v]["GC"] += gl
        
        # Asigna los 3 puntos al que ganó (sea en 90 mins o penales)
        if gana == l: stats[l]["Pts"] += 3; stats[l]["G"] += 1; stats[v]["P"] += 1
        elif gana == v: stats[v]["Pts"] += 3; stats[v]["G"] += 1; stats[l]["P"] += 1
        
        stats[l]["DG"] = stats[l]["GF"] - stats[l]["GC"]
        stats[v]["DG"] = stats[v]["GF"] - stats[v]["GC"]
        
    # Convertimos a lista y ordenamos por Pts, DG y GF
    lista = [{"Club": k, **v} for k, v in stats.items()]
    lista.sort(key=lambda x: (x["Pts"], x["DG"], x["GF"]), reverse=True)
    # Orden real con el que se resolvió el desempate (incluye definiciones extra) y cuántos
    # logran el objetivo de la tabla: verde los que lo logran, rojo los que no (3 o más equipos)
    orden = next((p["orden"] for p in partidos if p.get("orden")), None)
    cupos = next((p["cupos"] for p in partidos if p.get("cupos")), None)
    if orden:
        lista.sort(key=lambda x: orden.index(x["Club"]) if x["Club"] in orden else len(orden))
    marcar = cupos is not None and len(lista) >= 3

    # Construimos el HTML visual (colores del tema: se lee bien en claro y en oscuro)
    html = f'<div class="liguilla-wrap"><table class="liguilla{" marcada" if marcar else ""}">'
    html += ('<tr><th>Pos</th><th class="club">Club</th><th>Pts</th><th>PJ</th><th>G</th><th>P</th>'
             '<th>GF</th><th>GC</th><th>DG</th></tr>')
    for i, row in enumerate(lista):
        html += ('<tr class="ok">' if i < cupos else '<tr class="out">') if marcar else '<tr>'
        html += f'<td class="pos">{i+1}</td>'
        html += f'<td class="club">{club_link(row["Club"], 24)}</td>'
        html += f'<td class="pts">{row["Pts"]}</td>'
        html += f'<td>{row["PJ"]}</td><td>{row["G"]}</td><td>{row["P"]}</td>'
        html += f'<td>{row["GF"]}</td><td>{row["GC"]}</td><td>{row["DG"]:+d}</td>'
        html += '</tr>'
    html += '</table></div>'
    if marcar:
        comp = partidos[0].get("comp", "")
        logro, no = next(((a, b) for k, a, b in (
            ("Campeonato", "Campeón", "No sale campeón"), ("campeonato", "Campeón", "No sale campeón"),
            ("Ascenso", "Asciende", "No asciende"), ("Permanencia", "Se salva", "Desciende"),
            ("Promocion", "Se salva", "Juega la promoción")) if k in comp), ("Logra el objetivo", "No lo logra"))
        html += (f'<div class="legend"><span><i style="background:var(--liga-ok)"></i>{logro}</span>'
                 f'<span><i style="background:var(--liga-out)"></i>{no}</span></div>')
    return html


# ============================================================================
# PESTAÑAS · cada una vive en su propio módulo ui_*.py y recibe en `ctx` el estado compartido
# (S, P, las pestañas, las banderas terminada_*, los ayudantes). El orden es el de la pantalla.
# ============================================================================
import ui_primera
import ui_nacional
import ui_federal
import ui_ligas_simples
import ui_regional
import ui_copa_argentina
import ui_supercopa
import ui_conmebol
import ui_mundial
import ui_calendario
import ui_clubes
import ui_avisos
import ui_historial

ctx = SimpleNamespace(**{k: v for k, v in globals().items() if not k.startswith("__")})
for _modulo in (ui_primera, ui_nacional, ui_federal, ui_ligas_simples, ui_regional, ui_copa_argentina, ui_supercopa, ui_conmebol, ui_mundial, ui_calendario, ui_clubes, ui_avisos, ui_historial):
    _modulo.render(ctx)

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

import numpy as np
import pandas as pd


from datos import (
    ESCUDOS,
    F_GRUPOS_NOMBRES,
    N,
    origen,
    region_regional,
)
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
terminada_supercopa = SS["jugada"]
terminada_mundial = mundial_terminado(S)
terminadas_int = terminadas(S)
ambas = (terminada and terminada_b and terminada_f and terminada_pb and terminada_pc and terminada_reg
         and terminada_copa and terminada_supercopa and terminada_mundial and terminadas_int)
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
            + len(SR["log"]) + len(SC["log"]) + len(SS["log"]) + len(SM["log"]))
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
    # 4b. Supercopa Argentina (campeón de Primera vs. campeón de la Copa; necesita las dos terminadas)
    simular_supercopa(S, P, S["rng"])
    # 4c. Mundial de Clubes (solo en las temporadas que corresponde: 4, 8, 12...)
    while not mundial_terminado(S):
        simular_ronda_mundial(S, P, S["rng"])
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
# PRIMERA DIVISIÓN
# ============================================================================
if _abierta(tab_ligas, tab_p):
    with tab_p:
        c1, c2, c3 = st.columns([3, 1.4, 1.4], vertical_alignment="center")
        c1.markdown(chip("Liga Profesional · 30 equipos", "#1e5aa8") + " " +
                    chip("Fase 1 · todos contra todos" if S["fase"] == 1 else "Fase 2 · zonas"),
                    unsafe_allow_html=True)
                
        extra_p = S.get("extra_f2", 0)
        terminada_p_dyn = S["fecha"] >= TOTAL_FECHAS + extra_p
    
        if c2.button(":material/skip_next: Próxima fecha", key="p_next", disabled=terminada_p_dyn, width="stretch",
                     type="primary"):
            simular_fecha(S, P, acumular)
            st.rerun()
        if c3.button(":material/fast_forward: Hasta el final", key="p_all", disabled=terminada_p_dyn, width="stretch"):
            while S["fecha"] < TOTAL_FECHAS + S.get("extra_f2", 0):
                simular_fecha(S, P, acumular)
            st.rerun()

        jugados = int(S["pj"].sum() // 2)
        pct = 100 * S["sorpresas"] / jugados if jugados else 0
        pct_p = 100 * S["fecha"] / (TOTAL_FECHAS + extra_p) if (TOTAL_FECHAS + extra_p) else 0
    
        barra_estado([("Fase", "1 · Todos contra todos" if S["fase"] == 1 else "2 · Zonas"),
                      ("Fecha", f"{S['fecha']} / {TOTAL_FECHAS + extra_p}"),
                      ("Sorpresas", f"{S['sorpresas']} ({pct:.0f}%)")], pct_p)
                  
        if S["fase"] == 2 and S["fecha"] == FECHAS_F1:
            aviso("Terminó la fase 1: se armaron las zonas Campeonato, Intermedia y Descenso. "
                  "Las 9 fechas siguientes se juegan dentro de cada zona, con la localía invertida.")

        desempates_p = [p for p in S["log"] if p["rotulo"] == "Desempate"]
        mostrar_desempate_p = S.get("desempate_pendiente") or len(desempates_p) > 0
    
        titulos_p = ["Posiciones", "Fixture y resultados"]
        if mostrar_desempate_p: titulos_p.append("Desempate")
        titulos_p.extend(["Movimientos", "Definiciones"])
    
        sp = st.tabs(titulos_p)
        idx_p = 0
    
        with sp[idx_p]:
            if S["fase"] == 1:
                seccion("Tabla de posiciones", "Fase 1 · 29 fechas, todos contra todos", "#475569")
                mostrar_tabla(tabla_general(S), colorear_fase1, S["pos_hist"])
                leyenda(LEY_ZONAS)
            else:
                seccion("Fase 2 · Zonas", "9 fechas dentro de cada zona, localía invertida", "#16a34a")
                tabs = st.tabs([f"Zona {n}" for n in ZONAS] + ["Tabla fase 1"])
                for z, tab in enumerate(tabs[:3]):
                    with tab:
                        mostrar_tabla(tabla_zona(S, z), colorear_destino, S["pos_hist"])
                with tabs[3]:
                    mostrar_tabla(S["tabla_f1"], colorear_fase1)
                    st.caption("Tabla final de las 29 fechas de la fase 1.")
                leyenda(LEY_DESTINOS + [("Desempate Campeonato", "rgba(249, 115, 22, 0.3)"), ("Desempate Permanencia/Promoción", "rgba(147, 51, 234, 0.3)")])
            
            if S["fecha"] == 0:
                with st.expander(":material/tune: Editar medias internas de esta temporada"):
                    S["r"] = editar_medias(S["nombres"], S["r"], f"editor_p_{S['temp']}")
        idx_p += 1
    
        with sp[idx_p]:
            vista_fixture("p")
        idx_p += 1
    
        if mostrar_desempate_p:
            with sp[idx_p]:
                if S.get("desempate_pendiente"):
                    seccion("Desempate en Primera", "Están empatados en puntos críticos. Jugarán un desempate.", "#9333ea")
                    for z in [0, 2]:
                        df_des = tabla_zona(S, z)
                        df_des = df_des[df_des["id"].isin(S.get("ids_desempate", []))]
                        if not df_des.empty:
                            mostrar_tabla(df_des, colorear_destino)
                else:
                    grupos = {}
                    for p in desempates_p:
                        m = p["comp"]
                        if m not in grupos: grupos[m] = []
                        grupos[m].append(p)
                
                    for motivo, parts in grupos.items():
                        if "Liguilla" in motivo:
                            seccion(f"Tabla final: {motivo}", "Posiciones del mini-torneo a partido único", "#9333ea")
                            st.markdown(html_tabla_liguilla(parts), unsafe_allow_html=True)
                            with st.expander(f":material/visibility: Ver los {len(parts)} enfrentamientos", expanded=False):
                                for p in parts:
                                    st.markdown(fila_partido_html(p), unsafe_allow_html=True)
                        else:
                            seccion(f"Desempate: {motivo}", "Partido único definitorio", "#dc2626")
                            for p in parts:
                                st.markdown(fila_partido_html(p, abierto=True), unsafe_allow_html=True)
            idx_p += 1
        
        with sp[idx_p]:
            render_movimientos(S["log"], S["pos_hist"], S["nombres"], "#1e5aa8")
        idx_p += 1
    
        with sp[idx_p]:
            seccion("Definiciones de la temporada", "Campeón, copas, promoción y descensos", "#b7860b")
            if not terminada_p_dyn:
                aviso("Las definiciones aparecen acá cuando termina la temporada de Primera. "
                      "Destinos: 1°-5° Libertadores · 6°-8° y 12°-13° Sudamericana · 11° fase previa "
                      "de Libertadores · 27° Promoción · 28°-30° descienden.")
            else:
                final = tabla_final(S)
                def equipos(posiciones):
                    sel = final[final["Pos"].isin(list(posiciones))]
                    return lista_equipos_html([(r.Equipo, f"{r.Pos}°") for r in sel.itertuples()])

                st.caption("Están cerradas para no spoilear: tocá cada una para verla.")
                e1, e2 = st.columns(2)
                with e1:
                    with st.expander(":material/emoji_events: Campeón de Primera División", expanded=False):
                        campeon = final.iloc[0]["Equipo"]
                        st.markdown(f'<div class="champ"><div class="t">Campeón · Temporada {S["temp"]}'
                                    f'</div><div style="margin-top:10px">{crest(campeon, 64)}</div>'
                                    f'<div class="nm">{esc(campeon)}</div></div>', unsafe_allow_html=True)
                    with st.expander(":material/public: Clasificados · Copa Libertadores", expanded=False):
                        st.markdown('<div class="mlab">Fase de grupos (1° al 5°)</div>'
                                    + equipos(range(1, 6)) + '<div class="mlab">Fase previa (11°)</div>'
                                    + equipos([11]), unsafe_allow_html=True)
                    with st.expander(":material/public: Copa Sudamericana", expanded=False):
                        st.markdown('<div class="mlab">6° al 8° y 12°-13°</div>'
                                    + equipos(list(range(6, 9)) + [12, 13]), unsafe_allow_html=True)
                with e2:
                    with st.expander(":material/swap_vert: Promoción", expanded=False):
                        txt = ('<div class="mlab">Juega la Promoción contra el perdedor de la final '
                               'del reducido (27°)</div>' + equipos([N - 3]))
                        if SB["promo_partido"]:
                            txt += fila_partido_html(SB["promo_partido"])
                        st.markdown(txt, unsafe_allow_html=True)
                    with st.expander(":material/south: Descensos", expanded=False):
                        st.markdown('<div class="mlab">Descienden a la Primera Nacional (28° al 30°)</div>'
                                    + equipos(range(N - 2, N + 1)), unsafe_allow_html=True)

# -----------------
# Recordá que, ARRIBA DE TODO, el botón general ("Simular todo") 
# debe arrancar así para leer el alargue:
# while S["fecha"] < TOTAL_FECHAS + S.get("extra_f2", 0): 
#     simular_fecha(S, P, acumular)

# ============================================================================
# PRIMERA NACIONAL
# ============================================================================
if _abierta(tab_ligas, tab_b):
    with tab_b:
        fb = SB["fecha"]
        nom_b = SB["nombres"]
        extra = SB.get("extra_f2", 0)  # Offset dinámico por si se alarga con un desempate
    
        if fb < B_F1:
            fase_txt = "1 · Zonas A y B"
        elif fb < B_F1 + B_F2 + extra:
            if fb < B_F1 + B_F2:
                fase_txt = "2 · Tres zonas"
            else:
                fase_txt = "Desempate"
        elif fb < B_F1 + B_F2 + extra + B_RED:
            fase_txt = "Reducido"
        elif fb < B_TOTAL + extra:
            fase_txt = "Promoción"
        else:
            fase_txt = "Terminada"

        c1, c2, c3 = st.columns([3, 1.4, 1.4], vertical_alignment="center")
        c1.markdown(chip("Primera Nacional · 36 equipos") + " " + chip(f"Fase {fase_txt}", "#475569"),
                    unsafe_allow_html=True)
    
        if c2.button(":material/skip_next: Próxima fecha", key="b_next", width="stretch", type="primary",
                     disabled=terminada_b or b_espera_primera):
            simular_fecha_b(S, P)
            st.rerun()
        
        if c3.button(":material/fast_forward: Hasta el final", key="b_all", width="stretch",
                     disabled=terminada_b or b_espera_primera):
            while SB["fecha"] < total_b(SB) and not (SB["fecha"] == total_b(SB) - 1 and not primera_terminada(S)):
                simular_fecha_b(S, P)
            st.rerun()

        pct_b_dyn = 100 * fb / (B_TOTAL + extra) if (B_TOTAL + extra) else 0
        barra_estado([("Fase", fase_txt), ("Fecha", f"{fb} / {B_TOTAL + extra}"),
                      ("Partidos jugados", len(SB["log"]))], pct_b_dyn)
                  
        if b_espera_primera:
            aviso("La Promoción se juega contra el 27° de Primera: terminá primero la temporada "
                  "de Primera División.")
        if fb == B_F1:
            aviso("Terminó la fase 1: se repartieron los equipos en las zonas Campeonato, "
                  "Intermedia y Descenso y <b>se conservan todos los puntos acumulados</b>.")
        if fb == B_F1 + B_F2 + extra:
            aviso("Terminó la fase 2 y sus definiciones: quedaron definidos los 12 clasificados al reducido. "
                  "Mirá el cuadro en la pestaña <b>Reducido</b>.")

        # ------------------ SISTEMA DE PESTAÑAS DINÁMICAS ------------------
        desempates_b = [p for p in SB["log"] if p["rotulo"] == "Desempate"]
        mostrar_desempate_b = SB.get("desempate_pendiente") or len(desempates_b) > 0
    
        titulos_b = ["Posiciones", "Fixture y resultados"]
        if mostrar_desempate_b: titulos_b.append("Desempate")
        titulos_b.extend(["Reducido", "Movimientos", "Definiciones"])
    
        sb = st.tabs(titulos_b)
        idx_b = 0
    
        with sb[idx_b]:
            if fb < B_F1:
                seccion("Fase 1 · Zonas A y B", "Una rueda + 8 fechas interzonales · 18 equipos por zona", "#4f46e5")
                tabs_b = st.tabs(["Zona A", "Zona B"])
                for z, tab in enumerate(tabs_b):
                    with tab:
                        mostrar_tabla(tabla_b_f1(SB, z), colorear_b, SB["pos_hist"])
                leyenda([("1°-6° → Zona Campeonato", COLORES_ZONA[0]),
                         ("7°-12° → Zona Intermedia", COLORES_ZONA[1]),
                         ("13°-18° → Zona Descenso", COLORES_ZONA[2])])
            else:
                seccion("Fase 2 · Zonas", "Arrastran los puntos de la Fase 1 · una rueda por zona", "#16a34a")
                tabs_b = st.tabs([f"Zona {n}" for n in B_ZONAS2] + ["Fase 1"])
                for z in range(3):
                    with tabs_b[z]:
                        mostrar_tabla(tabla_b_f2(SB, z), colorear_b, SB["pos_hist"])
                with tabs_b[3]:
                    for z, nz in enumerate(["Zona A", "Zona B"]):
                        st.markdown(chip(nz), unsafe_allow_html=True)
                        mostrar_tabla(SB["tablas_f1"][z], colorear_b)
                    st.caption("Posiciones finales de la fase 1 (sus puntos ya no cuentan).")
                leyenda(LEY_B + [("Desempate Permanencia", "rgba(147, 51, 234, 0.3)")])
            
            with st.expander(":material/info: Formato de la Primera Nacional"):
                st.markdown(
                    "Fase 1: dos zonas de 18, una rueda, más 8 fechas interzonales (localía fija "
                    "4 y 4) cruzando ambas zonas. "
                    "Después, conservando los puntos acumulados, se arman "
                    "Campeonato, Intermedia y Descenso (12 cada una), una rueda cada una "
                    "(si dos equipos ya se cruzaron en la fase 1, la revancha es con la localía "
                    "invertida). Campeonato: 1° campeón y ascenso, 2° ascenso, 3°-4° a cuartos, "
                    "5°-12° a octavos. Intermedia: 1°-4° a octavos. Descenso: bajan los 6 últimos. "
                    "Reducido a partido único con penales directos; el campeón asciende y el perdedor "
                    "de la final juega la promoción contra el 27° de Primera.")
                
            if fb == 0:
                with st.expander(":material/tune: Editar medias internas de esta temporada (Primera Nacional)"):
                    SB["r"] = editar_medias(SB["nombres"], SB["r"], f"editor_b_{S['temp']}")
        idx_b += 1
    
        with sb[idx_b]: 
            vista_fixture("b")
        idx_b += 1
    
        if mostrar_desempate_b:
            with sb[idx_b]:
                if SB.get("desempate_pendiente"):
                    seccion("Desempates en la Primera Nacional", "Están empatados en puntos. Jugarán un desempate.", "#9333ea")
                    for z_des in (0, 2):
                        df_des = tabla_b_f2(SB, z_des)
                        df_des = df_des[df_des["id"].isin(SB["ids_desempate"])]
                        if len(df_des):
                            mostrar_tabla(df_des, colorear_b)
                else:
                    grupos = {}
                    for p in desempates_b:
                        m = p["comp"]
                        if m not in grupos: grupos[m] = []
                        grupos[m].append(p)
                
                    for motivo, parts in grupos.items():
                        if "Liguilla" in motivo:
                            seccion(f"Tabla final: {motivo}", "Posiciones del mini-torneo a partido único", "#9333ea")
                            st.markdown(html_tabla_liguilla(parts), unsafe_allow_html=True)
                            with st.expander(f":material/visibility: Ver los {len(parts)} enfrentamientos", expanded=False):
                                for p in parts:
                                    st.markdown(fila_partido_html(p), unsafe_allow_html=True)
                        else:
                            seccion(f"Desempate: {motivo}", "Partido único definitorio", "#dc2626")
                            for p in parts:
                                st.markdown(fila_partido_html(p, abierto=True), unsafe_allow_html=True)
            idx_b += 1

        with sb[idx_b]:
            seccion("Reducido por el tercer ascenso",
                    "Octavos → Cuartos → Semifinal → Final · partido único, penales si empatan · "
                    "L = local, V = visitante, N = neutral", "#2563eb")
            if fb < B_F1 + B_F2 + extra:
                aviso("El cuadro se completa al terminar la fase 2 y sus posibles desempates. Entran 3°-4° de Zona Campeonato "
                      "(directo a cuartos), 5°-12° de Campeonato y 1°-4° de Intermedia (octavos).")
            st.markdown(bracket_html(SB), unsafe_allow_html=True)
            if SB["entrantes"] is not None:
                with st.expander("Clasificados al reducido (orden de mérito)"):
                    st.markdown(tabla_html(SB["entrantes"]), unsafe_allow_html=True)
        idx_b += 1
    
        with sb[idx_b]:
            render_movimientos(SB["log"], SB["pos_hist"], nom_b, "#0f766e")
        idx_b += 1
        
        with sb[idx_b]:
            seccion("Definiciones de la temporada", "Campeón, ascensos, promoción y descensos",
                    "#b7860b")
            if SB["campeon"] is None:
                aviso("Las definiciones aparecen acá cuando termina la fase 2 de la Primera Nacional.")
            else:
                st.caption("Están cerradas para no spoilear: tocá cada una para verla.")
                e1, e2 = st.columns(2)
                with e1:
                    with st.expander(":material/emoji_events: Campeón de la Primera Nacional", expanded=False):
                        cb = nom_b[SB["campeon"]]
                        st.markdown(f'<div class="champ"><div class="t">Campeón · Temporada {S["temp"]}'
                                    f'</div><div style="margin-top:10px">{crest(cb, 64)}</div>'
                                    f'<div class="nm">{esc(cb)}</div><div class="s">Asciende a Primera'
                                    f'</div></div>', unsafe_allow_html=True)
                    with st.expander(":material/north: Clasificados · Ascensos", expanded=False):
                        asc = [(nom_b[SB["asc_directo"][0]], "campeón"), (nom_b[SB["asc_directo"][1]], "2°")]
                        if SB["asc_reducido"] is not None:
                            asc.append((nom_b[SB["asc_reducido"]], "reducido"))
                        if SB["promo"] and SB["promo"]["gana_b"]:
                            asc.append((nom_b[SB["promo"]["b_id"]], "promoción"))
                        st.markdown(lista_equipos_html(asc) + (
                            '' if SB["asc_reducido"] is not None else
                            '<div style="font-size:.8rem;opacity:.65">El tercer ascenso sale del '
                            'reducido.</div>'), unsafe_allow_html=True)
                with e2:
                    with st.expander(":material/swap_vert: Promoción", expanded=False):
                        if SB["promo_partido"]:
                            st.markdown(fila_partido_html(SB["promo_partido"], abierto=True),
                                        unsafe_allow_html=True)
                        elif SB["perdedor_final"] is not None:
                            st.markdown('<div class="mlab">Juega la promoción (perdedor de la final)</div>'
                                        + lista_equipos_html([(nom_b[SB["perdedor_final"]], "")]),
                                        unsafe_allow_html=True)
                        else:
                            st.caption("La juega el perdedor de la final del reducido contra el 27° "
                                       "de Primera.")
                    with st.expander(":material/south: Descensos", expanded=False):
                        st.markdown(
                            '<div class="mlab">Descienden (7° al 12° de Zona Descenso): al Federal '
                            'A los del interior, a la Primera B los metropolitanos</div>'
                            + lista_equipos_html([
                                (nom_b[i], "Federal A" if origen(nom_b[i]) == "Interior" else "Primera B")
                                for i in SB["desc_b"]
                            ]), unsafe_allow_html=True)

# ============================================================================
# FEDERAL A
# ============================================================================
if _abierta(tab_ligas, tab_f):
    with tab_f:
        ff = SF["fecha"]
        nom_f = SF["nombres"]
        if ff < SF["f1_rondas"]:
            fase_txt_f = "1 · Grupos por cercanía"
        elif ff < SF["f1_rondas"] + SF.get("f2_rondas", 0):
            fase_txt_f = "2 · Campeonato y Descenso"
        elif ff < SF["total"]:
            fase_txt_f = "Reducido"
        else:
            fase_txt_f = "Terminada"

        c1, c2, c3 = st.columns([3, 1.4, 1.4], vertical_alignment="center")
        c1.markdown(chip(f"Federal A · {len(nom_f)} equipos") + " " +
                    chip(f"Fase {fase_txt_f}", "#475569"), unsafe_allow_html=True)
        if c2.button(":material/skip_next: Próxima fecha", key="f_next", width="stretch", type="primary",
                     disabled=terminada_f):
            simular_fecha_f(SF, P, S["rng"])
            st.rerun()
        if c3.button(":material/fast_forward: Hasta el final", key="f_all", width="stretch", disabled=terminada_f):
            while SF["fecha"] < SF["total"]:
                simular_fecha_f(SF, P, S["rng"])
            st.rerun()

        barra_estado([("Fase", fase_txt_f), ("Fecha", f"{ff} / {SF['total']}"),
                      ("Partidos jugados", len(SF["log"]))], pct_f)
                  
        if ff == SF["f1_rondas"]:
            aviso("Terminó la fase 1: clasificaron los 4 primeros de cada grupo (20 equipos) a Zona Campeonato, "
                  "el resto a Zona Descenso, y <b>todos los puntos se reiniciaron a 0</b>.")
        if ff == SF["f1_rondas"] + SF.get("f2_rondas", 0):
            aviso("Terminó la fase 2: 1°, 2° y 3° ascendieron directo a la B Nacional y los 6 últimos "
                  "de Zona Descenso bajan al Regional Amateur. "
                  "El reducido arranca con el 7° y 8°. Mirá el cuadro en la pestaña <b>Reducido</b>.")

        # ------------------ SISTEMA DE PESTAÑAS DINÁMICAS ------------------
        desempate_f = SF.get("desempate_camp")
        desempate_fd = SF.get("desempate_desc")
        titulos_f = ["Posiciones", "Fixture y resultados"]
        if desempate_f or desempate_fd: titulos_f.append("Desempate")
        titulos_f.extend(["Reducido", "Movimientos", "Definiciones"])
        tab_f = dict(zip(titulos_f, st.tabs(titulos_f)))
                       
        with tab_f["Posiciones"]:
            if ff < SF["f1_rondas"]:
                seccion("Fase 1 · Grupos por cercanía", "Ida y vuelta · pasan los 4 primeros de "
                        "cada grupo", "#4f46e5")
                tabs_f = st.tabs(F_GRUPOS_NOMBRES)
                for g, tab in enumerate(tabs_f):
                    with tab:
                        mostrar_tabla(tabla_f_grupo(SF, g), colorear_f, SF["pos_hist"])
                leyenda([("1°-4° → Zona Campeonato", COLORES_F["→ Zona Campeonato"])])
            else:
                seccion("Fase 2 · Zonas", "Puntos reiniciados a 0 · una rueda por zona", "#16a34a")
                tabs_f = st.tabs(["Campeonato", "Descenso", "Fase 1"])
                with tabs_f[0]:
                    mostrar_tabla(tabla_f_f2(SF, 0), colorear_f, SF["pos_hist"])
                with tabs_f[1]:
                    mostrar_tabla(tabla_f_f2(SF, 1), colorear_f, SF["pos_hist"])
                with tabs_f[2]:
                    for g, dfg in zip(F_GRUPOS_NOMBRES, SF["tablas_f1"]):
                        st.markdown(chip(g), unsafe_allow_html=True)
                        mostrar_tabla(dfg, colorear_f)
                    st.caption("Posiciones finales de la fase 1 (sus puntos ya no cuentan).")
                leyenda(LEY_F)
            
            if ff == 0:
                with st.expander(":material/tune: Editar medias internas de esta temporada (Federal A)"):
                    SF["r"] = editar_medias(nom_f, SF["r"], f"editor_f_{S['temp']}")
                
        with tab_f["Fixture y resultados"]:
            vista_fixture("f")
        
        def partidos_desempate_f(info):
            grupos_f = {}
            for p in info["partidos"]:
                grupos_f.setdefault(p["comp"], []).append(p)
            for comp_f, partes in grupos_f.items():
                if "Liguilla" in comp_f:
                    seccion(f"Tabla final: {comp_f}", "Posiciones del mini-torneo a partido único", "#9333ea")
                    st.markdown(html_tabla_liguilla(partes), unsafe_allow_html=True)
                    with st.expander(f":material/visibility: Ver los {len(partes)} enfrentamientos",
                                     expanded=False):
                        for p in partes:
                            st.markdown(fila_partido_html(p), unsafe_allow_html=True)
                else:
                    if len(grupos_f) > 1:
                        seccion(comp_f, "Partido único definitorio", "#dc2626")
                    for p in partes:
                        st.markdown(fila_partido_html(p, abierto=True), unsafe_allow_html=True)

        if desempate_f or desempate_fd:
            with tab_f["Desempate"]:
                if desempate_f:
                    seccion("Desempate por el campeonato",
                            f"Igualaron en puntos en el 1° puesto: {', '.join(desempate_f['equipos'])}",
                            "#9333ea")
                    partidos_desempate_f(desempate_f)
                    st.caption("El título se define con desempate en cancha neutral (penales si empatan). "
                               "El resto de las posiciones se ordena por diferencia de gol.")
                if desempate_fd:
                    seccion("Desempate por la permanencia",
                            f"Igualaron en puntos en el límite del descenso (Zona Descenso): "
                            f"{', '.join(desempate_fd['equipos'])} · se salva"
                            f"{'n' if desempate_fd['salvados'] > 1 else ''} {desempate_fd['salvados']}",
                            "#9333ea")
                    partidos_desempate_f(desempate_fd)
                    st.caption("Partido único en cancha neutral (penales si empatan). Los 6 últimos bajan "
                               "al Regional Amateur.")

        with tab_f["Reducido"]:
            seccion("Reducido por el cuarto ascenso",
                    "Eliminatoria → Semifinal → Final · partido único · gana el mejor ubicado si "
                    "empatan, menos en la final (cancha neutral, penales) · L = local, V = "
                    "visitante, N = neutral", "#2563eb")
            if ff < SF["f1_rondas"] + SF.get("f2_rondas", 0):
                aviso("El cuadro se completa al terminar la fase 2. Entran del 4° al 8° de Zona "
                      "Campeonato.")
            st.markdown(bracket_html_f(SF), unsafe_allow_html=True)
            if SF["entrantes"] is not None:
                with st.expander("Clasificados al reducido (orden de mérito)"):
                    st.markdown(tabla_html(SF["entrantes"]), unsafe_allow_html=True)
                             
        with tab_f["Movimientos"]:
            render_movimientos(SF["log"], SF["pos_hist"], nom_f, "#0f766e")
        
        with tab_f["Definiciones"]:
            seccion("Definiciones de la temporada", "Campeón y ascensos a la Primera Nacional",
                    "#b7860b")
            if SF["campeon"] is None:
                aviso("Las definiciones aparecen acá cuando termina la fase 2 del Federal A.")
            else:
                st.caption("Están cerradas para no spoilear: tocá cada una para verla.")
                with st.expander(":material/emoji_events: Campeón del Federal A", expanded=False):
                    cf = nom_f[SF["campeon"]]
                    st.markdown(f'<div class="champ"><div class="t">Campeón · Temporada {S["temp"]}'
                                f'</div><div style="margin-top:10px">{crest(cf, 64)}</div>'
                                f'<div class="nm">{esc(cf)}</div><div class="s">Asciende a la Primera'
                                f' Nacional</div></div>', unsafe_allow_html=True)
                    if SF.get("desempate_camp"):
                        dc = SF["desempate_camp"]
                        st.markdown(f'<div class="mlab" style="margin-top:14px">Título definido por '
                                    f'desempate · igualaron en puntos: {esc(", ".join(dc["equipos"]))}'
                                    f'</div>' + "".join(fila_partido_html(p) for p in dc["partidos"]),
                                    unsafe_allow_html=True)
                with st.expander(":material/north: Clasificados · Ascensos", expanded=False):
                    asc_f = [(nom_f[SF["asc_directo"][0]], "campeón"), 
                             (nom_f[SF["asc_directo"][1]], "2°"), 
                             (nom_f[SF["asc_directo"][2]], "3°")]
                    if SF["asc_reducido"] is not None:
                        asc_f.append((nom_f[SF["asc_reducido"]], "reducido"))
                    st.markdown(lista_equipos_html(asc_f) + (
                        '' if SF["asc_reducido"] is not None else
                        '<div style="font-size:.8rem;opacity:.65">El cuarto ascenso sale del '
                        'reducido.</div>'), unsafe_allow_html=True)
                with st.expander(":material/south: Descensos al Regional Amateur", expanded=False):
                    st.markdown('<div class="mlab">Descienden los 6 últimos de Zona Descenso (a la región '
                                'de su provincia)</div>'
                                + lista_equipos_html([(nom_f[i], region_regional(nom_f[i]))
                                                      for i in SF["descendidos"]]), unsafe_allow_html=True)


# ============================================================================
# PRIMERA B
# ============================================================================
if _abierta(tab_ligas, tab_pb):
    with tab_pb:
        c1, c2, c3 = st.columns([3, 1.4, 1.4], vertical_alignment="center")
        c1.markdown(chip(f"Primera B · {len(SPB['nombres'])} equipos") + " " + chip("Todos contra todos", "#475569"), unsafe_allow_html=True)
    
        if c2.button(":material/skip_next: Próxima fecha", key="pb_next", width="stretch", type="primary", disabled=terminada_pb):
            simular_fecha_liga(SPB, P, S["rng"], "Primera B", tabla_pb)
            st.rerun()
        if c3.button(":material/fast_forward: Hasta el final", key="pb_all", width="stretch", disabled=terminada_pb):
            while SPB["fecha"] < SPB["total"]: 
                simular_fecha_liga(SPB, P, S["rng"], "Primera B", tabla_pb)
            st.rerun()
        
        barra_estado([("Fase", "Liga ida y vuelta"), ("Fecha", f"{SPB['fecha']} / {SPB['total']}"), ("Partidos jugados", len(SPB["log"]))], pct_pb)
    
        desempates = [p for p in SPB["log"] if p["rotulo"] == "Desempate"]
        mostrar_desempate = SPB.get("desempate_pendiente") or len(desempates) > 0
    
        titulos = ["Posiciones", "Fixture y resultados"]
        if mostrar_desempate: titulos.append("Desempate")
        titulos.extend(["Movimientos", "Definiciones"])
    
        spb_tabs = st.tabs(titulos)
        idx = 0
    
        with spb_tabs[idx]:
            seccion("Tabla de posiciones", "Ida y vuelta · ascienden los 2 primeros, del 18° para abajo descienden", "#4f46e5")
            mostrar_tabla(tabla_pb(SPB), colorear_pb, SPB["pos_hist"])
            leyenda([("1°-2° Ascenso a Primera Nacional", COLORES_B["Ascenso directo"]), 
                     ("Desempate Campeonato / Ascenso", "rgba(249, 115, 22, 0.3)"),
                     ("Desempate Permanencia", "rgba(147, 51, 234, 0.3)"),
                     ("18° o peor Descenso a Primera C", COLORES_B["Desciende"])])
            if SPB["fecha"] == 0:
                with st.expander(":material/tune: Editar medias internas de esta temporada (Primera B)"):
                    SPB["r"] = editar_medias(SPB["nombres"], SPB["r"], f"editor_pb_{S['temp']}")
        idx += 1
            
        with spb_tabs[idx]: vista_fixture("pb")
        idx += 1
    
        if mostrar_desempate:
            with spb_tabs[idx]:
                if SPB.get("desempate_pendiente"):
                    seccion("Desempates por Posiciones", "Están empatados en puntos. Jugarán un partido único.", "#9333ea")
                    df_des = tabla_pb(SPB)
                    df_des = df_des[df_des["id"].isin(SPB["ids_desempate"])]
                    mostrar_tabla(df_des, colorear_pb)
                else:
                    grupos = {}
                    for p in desempates:
                        m = p["comp"]
                        if m not in grupos: grupos[m] = []
                        grupos[m].append(p)
                
                    for motivo, parts in grupos.items():
                        if "Liguilla" in motivo:
                            seccion(f"Tabla final: {motivo}", "Posiciones del mini-torneo a partido único", "#9333ea")
                            st.markdown(html_tabla_liguilla(parts), unsafe_allow_html=True)
                            with st.expander(f":material/visibility: Ver los {len(parts)} enfrentamientos", expanded=False):
                                for p in parts:
                                    st.markdown(fila_partido_html(p), unsafe_allow_html=True)
                        else:
                            seccion(f"Desempate: {motivo}", "Partido único definitorio", "#dc2626")
                            for p in parts:
                                st.markdown(fila_partido_html(p, abierto=True), unsafe_allow_html=True)
            idx += 1
            
        with spb_tabs[idx]: render_movimientos(SPB["log"], SPB["pos_hist"], SPB["nombres"], "#0f766e")
        idx += 1
        
        with spb_tabs[idx]:
            seccion("Definiciones de la temporada", "Campeón, ascensos y descensos", "#b7860b")
            if SPB["campeon"] is None: aviso("Las definiciones aparecen acá cuando termina la liga.")
            else:
                with st.expander(":material/emoji_events: Campeón de la Primera B", expanded=False):
                    cpb = SPB["nombres"][SPB["campeon"]]
                    st.markdown(f'<div class="champ"><div class="t">Campeón</div><div style="margin-top:10px">{crest(cpb, 64)}</div><div class="nm">{esc(cpb)}</div></div>', unsafe_allow_html=True)
                

# ============================================================================
# PRIMERA C
# ============================================================================
if _abierta(tab_ligas, tab_pc):
    with tab_pc:
        c1, c2, c3 = st.columns([3, 1.4, 1.4], vertical_alignment="center")
        c1.markdown(chip(f"Primera C · {len(SPC['nombres'])} equipos") + " " + chip("Todos contra todos", "#475569"), unsafe_allow_html=True)
    
        if c2.button(":material/skip_next: Próxima fecha", key="pc_next", width="stretch", type="primary", disabled=terminada_pc):
            simular_fecha_liga(SPC, P, S["rng"], "Primera C", tabla_pc)
            st.rerun()
        if c3.button(":material/fast_forward: Hasta el final", key="pc_all", width="stretch", disabled=terminada_pc):
            while SPC["fecha"] < SPC["total"]: 
                simular_fecha_liga(SPC, P, S["rng"], "Primera C", tabla_pc)
            st.rerun()
        
        barra_estado([("Fase", "Liga ida y vuelta"), ("Fecha", f"{SPC['fecha']} / {SPC['total']}"), ("Partidos jugados", len(SPC["log"]))], pct_pc)
    
        desempates_c = [p for p in SPC["log"] if p["rotulo"] == "Desempate"]
        mostrar_desempate_c = SPC.get("desempate_pendiente") or len(desempates_c) > 0
    
        titulos_c = ["Posiciones", "Fixture y resultados"]
        if mostrar_desempate_c: titulos_c.append("Desempate")
        titulos_c.extend(["Movimientos", "Definiciones"])
    
        spc_tabs = st.tabs(titulos_c)
        idx_c = 0
    
        with spc_tabs[idx_c]:
            seccion("Tabla de posiciones", "Ida y vuelta · ascienden los 2 primeros", "#4f46e5")
            mostrar_tabla(tabla_pc(SPC), colorear_pc, SPC["pos_hist"])
            leyenda([("1°-2° Ascenso a Primera B", COLORES_B["Ascenso directo"]), 
                 ("Desempate Campeonato / Ascenso", "rgba(249, 115, 22, 0.3)"),
                 ("Desempate Permanencia", "rgba(147, 51, 234, 0.3)"),
                 ("18° o peor Descenso al Promocional", COLORES_B["Desciende"])])
            if SPC["fecha"] == 0:
                with st.expander(":material/tune: Editar medias internas de esta temporada (Primera C)"):
                    SPC["r"] = editar_medias(SPC["nombres"], SPC["r"], f"editor_pc_{S['temp']}")
        idx_c += 1
            
        with spc_tabs[idx_c]: vista_fixture("pc")
        idx_c += 1
    
        if mostrar_desempate_c:
            with spc_tabs[idx_c]:
                if SPC.get("desempate_pendiente"):
                    seccion("Desempates por Posiciones", "Están empatados en puntos. Jugarán un partido único.", "#9333ea")
                    df_des = tabla_pc(SPC)
                    df_des = df_des[df_des["id"].isin(SPC["ids_desempate"])]
                    mostrar_tabla(df_des, colorear_pc)
                else:
                    grupos = {}
                    for p in desempates_c:
                        m = p["comp"]
                        if m not in grupos: grupos[m] = []
                        grupos[m].append(p)
                
                    for motivo, parts in grupos.items():
                        if "Liguilla" in motivo:
                            seccion(f"Tabla final: {motivo}", "Posiciones del mini-torneo a partido único", "#9333ea")
                            st.markdown(html_tabla_liguilla(parts), unsafe_allow_html=True)
                            with st.expander(f":material/visibility: Ver los {len(parts)} enfrentamientos", expanded=False):
                                for p in parts:
                                    st.markdown(fila_partido_html(p), unsafe_allow_html=True)
                        else:
                            seccion(f"Desempate: {motivo}", "Partido único definitorio", "#dc2626")
                            for p in parts:
                                st.markdown(fila_partido_html(p, abierto=True), unsafe_allow_html=True)
            idx_c += 1
            
        with spc_tabs[idx_c]: render_movimientos(SPC["log"], SPC["pos_hist"], SPC["nombres"], "#0f766e")
        idx_c += 1
        
        with spc_tabs[idx_c]:
            seccion("Definiciones de la temporada", "Campeón y ascensos", "#b7860b")
            if SPC["campeon"] is None: aviso("Las definiciones aparecen acá cuando termina la liga.")
            else:
                with st.expander(":material/emoji_events: Campeón de la Primera C", expanded=False):
                    cpc = SPC["nombres"][SPC["campeon"]]
                    st.markdown(f'<div class="champ"><div class="t">Campeón</div><div style="margin-top:10px">{crest(cpc, 64)}</div><div class="nm">{esc(cpc)}</div></div>', unsafe_allow_html=True)


# ============================================================================
# PROMOCIONAL AMATEUR
# ============================================================================
if _abierta(tab_ligas, tab_pd):
    with tab_pd:
        c1, c2, c3 = st.columns([3, 1.4, 1.4], vertical_alignment="center")
        c1.markdown(chip(f"Promocional Amateur · {len(SPD['nombres'])} equipos", "#0369a1") + " " + chip("Todos contra todos", "#475569"), unsafe_allow_html=True)
    
        if c2.button(":material/skip_next: Próxima fecha", key="pd_next", width="stretch", type="primary", disabled=terminada_pd):
            simular_fecha_liga(SPD, P, S["rng"], "Promocional Amateur", tabla_pd)
            st.rerun()
        if c3.button(":material/fast_forward: Hasta el final", key="pd_all", width="stretch", disabled=terminada_pd):
            while SPD["fecha"] < SPD["total"]: 
                simular_fecha_liga(SPD, P, S["rng"], "Promocional Amateur", tabla_pd)
            st.rerun()
        
        pct_pd = 100 * SPD["fecha"] / SPD["total"] if SPD["total"] else 0
        barra_estado([("Fase", "Liga ida y vuelta"), ("Fecha", f"{SPD['fecha']} / {SPD['total']}"), ("Partidos jugados", len(SPD["log"]))], pct_pd)
    
        desempates_d = [p for p in SPD["log"] if p["rotulo"] == "Desempate"]
        mostrar_desempate_d = SPD.get("desempate_pendiente") or len(desempates_d) > 0
    
        titulos_d = ["Posiciones", "Fixture y resultados", "Movimientos", "Definiciones"]
        if mostrar_desempate_d: titulos_d.insert(2, "Desempate")
    
        spd_tabs = st.tabs(titulos_d)
        idx_d = 0
    
        with spd_tabs[idx_d]:
            seccion("Tabla de posiciones", "Ida y vuelta · ascienden los 2 primeros", "#4f46e5")
            from vista import colorear_pd
            mostrar_tabla(tabla_pd(SPD), colorear_pd, SPD["pos_hist"])
            leyenda([("1°-2° Ascenso a Primera C", COLORES_B["Ascenso directo"]), 
                     ("Desempate Campeonato / Ascenso", "rgba(249, 115, 22, 0.3)")])
            if SPD["fecha"] == 0:
                with st.expander(":material/tune: Editar medias internas de esta temporada (Promocional Amateur)"):
                    SPD["r"] = editar_medias(SPD["nombres"], SPD["r"], f"editor_pd_{S['temp']}")
        idx_d += 1
            
        with spd_tabs[idx_d]: vista_fixture("pd")
        idx_d += 1
    
        if mostrar_desempate_d:
            with spd_tabs[idx_d]:
                if SPD.get("desempate_pendiente"):
                    seccion("Desempates por Posiciones", "Están empatados en puntos. Jugarán un partido único.", "#9333ea")
                    df_des = tabla_pd(SPD)
                    df_des = df_des[df_des["id"].isin(SPD["ids_desempate"])]
                    mostrar_tabla(df_des, colorear_pd)
                else:
                    grupos = {}
                    for p in desempates_d:
                        m = p["comp"]
                        if m not in grupos: grupos[m] = []
                        grupos[m].append(p)
                    for motivo, parts in grupos.items():
                        seccion(f"Desempate: {motivo}", "Partido único definitorio", "#dc2626")
                        for p in parts:
                            st.markdown(fila_partido_html(p, abierto=True), unsafe_allow_html=True)
            idx_d += 1
            
        with spd_tabs[idx_d]: render_movimientos(SPD["log"], SPD["pos_hist"], SPD["nombres"], "#0f766e")
        idx_d += 1
        
        with spd_tabs[idx_d]:
            seccion("Definiciones de la temporada", "Campeón y ascensos", "#b7860b")
            if SPD["campeon"] is None: aviso("Las definiciones aparecen acá cuando termina la liga.")
            else:
                with st.expander(":material/emoji_events: Campeón del Promocional Amateur", expanded=False):
                    cpd = SPD["nombres"][SPD["campeon"]]
                    st.markdown(f'<div class="champ"><div class="t">Campeón</div><div style="margin-top:10px">{crest(cpd, 64)}</div><div class="nm">{esc(cpd)}</div></div>', unsafe_allow_html=True)


# ============================================================================
# TORNEO REGIONAL AMATEUR
# ============================================================================
if _abierta(tab_ligas, tab_reg):
    with tab_reg:
        c1, c2, c3 = st.columns([3, 1.4, 1.4], vertical_alignment="center")
        c1.markdown(chip(f"Regional Amateur · {len(SR['nombres'])} clubes", "#0e7490") + " "
                    + chip("12 regiones · 6 ascensos al Federal A", "#475569"), unsafe_allow_html=True)
        if c2.button(":material/skip_next: Próxima fecha", key="reg_next", width="stretch", type="primary",
                     disabled=terminada_reg):
            simular_fecha_reg(SR, P, S["rng"])
            st.rerun()
        if c3.button(":material/fast_forward: Hasta el final", key="reg_all", width="stretch",
                     disabled=terminada_reg):
            while SR["fecha"] < SR["total"]:
                simular_fecha_reg(SR, P, S["rng"])
            st.rerun()

        fase_reg = ("Ligas regionales" if SR["fecha"] < SR["f_liga"] else
                    "Desempate por el campeonato" if SR["fecha"] < SR["f_final0"] else
                    "Terminado" if terminada_reg else "Final por el ascenso")
        barra_estado([("Fase", fase_reg), ("Fecha", f"{SR['fecha']} / {SR['total']}"),
                      ("Partidos jugados", len(SR["log"]))], pct_reg)

        desempates_r = [p for p in SR["log"] if p["rotulo"] == "Desempate"]
        titulos_r = ["Regiones", "Fixture y resultados"]
        if SR["desempate_pendiente"] or desempates_r:
            titulos_r.append("Desempate")
        titulos_r += ["Final por el ascenso", "Movimientos", "Definiciones"]
        tab_r = dict(zip(titulos_r, st.tabs(titulos_r)))

        with tab_r["Regiones"]:
            seccion("Regiones", "Cada región es una liga de todos contra todos a una sola vuelta · "
                    "el 1° es el campeón regional", "#0e7490")
            region = st.pills("Región", REGIONES_REG, default=REGIONES_REG[0], key="reg_region",
                              label_visibility="collapsed") or REGIONES_REG[0]
            n_final, rival = next((k + 1, b if a == region else a) for k, (a, b) in enumerate(FINALES_REG)
                                  if region in (a, b))
            st.markdown(chip(f"{len(SR['grupos'][region])} clubes", "#0e7490") + " "
                        + chip(f"Final {n_final} por el ascenso vs. {rival}", "#b7860b"),
                        unsafe_allow_html=True)
            seccion(f"Región {region}", "Si hay igualdad en puntos en el 1° puesto, el título se define "
                    "con un desempate (nunca por diferencia de gol)", "#16a34a")
            mostrar_tabla(tabla_reg_region(SR, region), colorear_reg)
            leyenda([("Campeón regional", COLOR_ORO), ("Desempate Campeonato", "rgba(249, 115, 22, 0.3)")])
            if SR["fecha"] == 0:
                nom_reg_ed = [f"{n} · {rg}" for n, rg in zip(SR["nombres"], SR["region_de"])]
                with st.expander(":material/tune: Editar medias internas de esta temporada (Regional Amateur)"):
                    SR["r"] = editar_medias(nom_reg_ed, SR["r"], f"editor_reg_{S['temp']}")

        if "Desempate" in tab_r:
            with tab_r["Desempate"]:
                seccion("Desempates por el campeonato", "Igualdad en puntos en el 1° puesto de la región · "
                        "partido único en cancha neutral, penales si empatan", "#9333ea")
                for reg in REGIONES_REG:
                    if SR["desempate_pendiente"] and reg in SR["motivos_desempate"]:
                        st.markdown(f'<div class="mlab" style="margin-top:14px">Región {esc(reg)}</div>',
                                    unsafe_allow_html=True)
                        df_des = tabla_reg_region(SR, reg).head(SR["motivos_desempate"][reg])
                        mostrar_tabla(df_des, colorear_reg)
                        continue
                    grupos_r = {}
                    for p in desempates_r:
                        if p["region"] == reg:
                            grupos_r.setdefault(p["comp"], []).append(p)
                    for comp_r, partes in grupos_r.items():
                        if "Liguilla" in comp_r:
                            seccion(f"Tabla final: {comp_r}", "Posiciones del mini-torneo a partido único", "#9333ea")
                            st.markdown(html_tabla_liguilla(partes), unsafe_allow_html=True)
                            with st.expander(f":material/visibility: Ver los {len(partes)} enfrentamientos",
                                             expanded=False):
                                for p in partes:
                                    st.markdown(fila_partido_html(p), unsafe_allow_html=True)
                        else:
                            seccion(f"Desempate: {comp_r}", "Partido único definitorio", "#dc2626")
                            for p in partes:
                                st.markdown(fila_partido_html(p, abierto=True), unsafe_allow_html=True)

        with tab_r["Fixture y resultados"]:
            region_fx = st.selectbox(":material/map: Región", REGIONES_REG, key="reg_fx_region")
            vista_fixture("reg", region_fx)

        with tab_r["Final por el ascenso"]:
            seccion("Final por el ascenso", "Los 12 campeones regionales se cruzan de a pares, a ida y "
                    "vuelta · los 6 ganadores ascienden al Federal A", "#b7860b")
            campeones_ya = [(SR["nombres"][c], reg) for reg, c in SR["campeones"].items() if c is not None]
            if not campeones_ya:
                aviso("Los cruces se completan con los campeones de cada región.")
            st.markdown(finales_reg_html(SR), unsafe_allow_html=True)
            if SR["ascendidos"]:
                st.markdown('<div class="mlab up">▲ Ascienden al Federal A</div>'
                            + lista_equipos_html([(SR["nombres"][i], SR["region_de"][i])
                                                  for i in SR["ascendidos"]]), unsafe_allow_html=True)

        with tab_r["Movimientos"]:
            render_movimientos(SR["log"], SR["pos_hist"], SR["nombres"], "#0f766e")

        with tab_r["Definiciones"]:
            seccion("Definiciones de la temporada", "Campeones regionales y ascensos al Federal A", "#b7860b")
            if not any(c is not None for c in SR["campeones"].values()):
                aviso("Las definiciones aparecen acá cuando termina la liga de cada región.")
            else:
                with st.expander(":material/emoji_events: Campeones regionales", expanded=False):
                    st.markdown(lista_equipos_html([(SR["nombres"][c], reg) for reg, c in
                                                    SR["campeones"].items() if c is not None]),
                                unsafe_allow_html=True)
                if SR["ascendidos"]:
                    with st.expander(":material/arrow_upward: Ascensos al Federal A", expanded=False):
                        st.markdown(lista_equipos_html([(SR["nombres"][i], SR["region_de"][i])
                                                        for i in SR["ascendidos"]]), unsafe_allow_html=True)


# ============================================================================
# COPA ARGENTINA
# ============================================================================
if _abierta(tab_copas, tab_ca):
    with tab_ca:
        c1, c2, c3 = st.columns([3, 1.4, 1.4], vertical_alignment="center")
        c1.markdown(logo_img("Copa Argentina", 30) + " " + chip("Copa Argentina · 128 equipos", "#1e5aa8") + " "
                    + chip("Partido único · cancha neutral", "#475569"), unsafe_allow_html=True)
        if c2.button(":material/skip_next: Próxima ronda", key="ca_next", width="stretch", type="primary",
                     disabled=not SC["sorteada"] or terminada_copa):
            simular_ronda_copa(SC, P, S["rng"])
            st.rerun()
        if c3.button(":material/fast_forward: Hasta el final", key="ca_all", width="stretch",
                     disabled=not SC["sorteada"] or terminada_copa):
            while SC["ronda"] < SC["total"]:
                simular_ronda_copa(SC, P, S["rng"])
            st.rerun()
        ronda_txt = ("Sin sortear" if not SC["sorteada"] else "Terminada" if terminada_copa
                     else COPA_RONDAS[SC["ronda"]])
        barra_estado([("Próxima ronda" if SC["sorteada"] and not terminada_copa else "Estado", ronda_txt),
                      ("Rondas", f"{SC['ronda']} / {SC['total']}"), ("Partidos jugados", len(SC["log"]))],
                     pct_copa)

        if not SC["sorteada"]:
            seccion("Copa Argentina", "128 equipos · desde 64avos de final · partido único en cancha "
                    "neutral, penales si empatan", "#1e5aa8")
            aviso("La Copa se sortea al empezar la temporada.")
            cupos = pd.DataFrame([
                ("Primera División", "Los 30 equipos", 30), ("Primera Nacional", "Los 36 equipos", 36),
                ("Federal A", "Los 20 de Zona Campeonato y los 8 mejores de Zona Descenso", 28),
                ("Primera B", "Los 12 primeros", 12), ("Primera C", "Los 10 primeros", 10),
                ("Regional Amateur", "El campeón de cada una de las 12 regiones", 12)],
                columns=["Liga", "Clasifican", "Cupos"])
            st.markdown(tabla_html(cupos, clubes=()), unsafe_allow_html=True)
            pendientes = [n for n, t in (("Primera", terminada), ("B Nacional", terminada_b),
                                         ("Federal A", terminada_f), ("Primera B", terminada_pb),
                                         ("Primera C", terminada_pc), ("Regional", terminada_reg)) if not t]
            st.caption("Faltan terminar: " + ", ".join(pendientes))
        else:
            titulos_ca = ["Cuadro", "Partidos", "Clasificados", "Definiciones"]
            tab_ca_t = dict(zip(titulos_ca, st.tabs(titulos_ca)))
            with tab_ca_t["Cuadro"]:
                seccion("Cuadro de la Copa Argentina", "8 llaves de 16 equipos (64avos a octavos) · el ganador "
                        "de cada llave juega los cuartos · todo en cancha neutral · (n) = penales", "#1e5aa8")
                st.caption("64avos por categoría: Primera vs. Regional Amateur, B Nacional vs. Primera C, "
                           "Federal A vs. Primera B; los que sobran se cruzan con la misma regla. Se juega "
                           "los miércoles, en el medio de las ligas (ver Calendario).")
                opciones = [f"Llave {x}" for x in COPA_LLAVES] + ["Fase final"]
                vista_llave = st.segmented_control("Llave", opciones, default="Llave A", key="ca_llave",
                                                   label_visibility="collapsed") or "Llave A"
                if vista_llave == "Fase final":
                    st.markdown(cuadro_final_copa_html(SC), unsafe_allow_html=True)
                else:
                    st.markdown(cuadro_llave_html(SC, vista_llave[-1]), unsafe_allow_html=True)
            with tab_ca_t["Partidos"]:
                if not SC["log"]:
                    aviso("Todavía no se jugó ninguna ronda. Los cruces de 64avos están en el <b>Cuadro</b>.")
                else:
                    jugadas = SC["ronda"]
                    ronda_sel = st.selectbox(":material/event: Ronda", range(jugadas), index=jugadas - 1,
                                             format_func=lambda k: COPA_RONDAS[k], key=f"ca_ronda_{S['temp']}")
                    for m in SC["cuadro"][ronda_sel]:
                        st.markdown(fila_partido_html(m["p"]), unsafe_allow_html=True)
            with tab_ca_t["Clasificados"]:
                seccion("Clasificados", "Los 128 equipos y por qué entraron (por la temporada anterior; "
                        "en la temporada 1, por media)", "#1e5aa8")
                df_cl = pd.DataFrame({"Equipo": SC["nombres"], "Liga": SC["origen"],
                                      "Clasificó como": SC["criterio"],
                                      "Media": np.round(SC["r"], 1)})
                df_cl["_o"] = df_cl["Liga"].map({x: k for k, x in enumerate(
                    ["Primera División", "Primera Nacional", "Federal A", "Primera B", "Primera C",
                     "Regional Amateur"])})
                df_cl = df_cl.sort_values(["_o", "Media"], ascending=[True, False]).drop(columns="_o")
                st.markdown(tabla_html(df_cl, formatos={"Media": "{:.1f}"}), unsafe_allow_html=True)
            with tab_ca_t["Definiciones"]:
                seccion("Definiciones", "Campeón y finalista de la Copa Argentina", "#b7860b")
                if SC["campeon"] is None:
                    aviso("El campeón aparece acá cuando se juega la final.")
                else:
                    fin = SC["cuadro"][-1][0]
                    sub = fin["b"] if fin["gana"] == fin["a"] else fin["a"]
                    cc = SC["nombres"][SC["campeon"]]
                    st.markdown(f'<div class="champ"><div class="t">Campeón · Copa Argentina · Temporada {S["temp"]}'
                                f'</div><div style="margin-top:10px">{crest(cc, 64)}</div>'
                                f'<div class="nm">{esc(cc)}</div><div class="s">{esc(SC["origen"][SC["campeon"]])}'
                                f' · finalista: {esc(SC["nombres"][sub])}</div></div>', unsafe_allow_html=True)
                    st.markdown(fila_partido_html(fin["p"], abierto=True), unsafe_allow_html=True)


# ============================================================================
# SUPERCOPA ARGENTINA
# ============================================================================
if _abierta(tab_copas, tab_sup):
    with tab_sup:
        listo_sup = supercopa_lista(S)
        c1, c2 = st.columns([4, 1.6], vertical_alignment="center")
        c1.markdown(logo_img("Supercopa Argentina", 30) + " " + chip("Supercopa Argentina", "#b7860b") + " "
                    + chip("Partido único · cancha neutral", "#475569"), unsafe_allow_html=True)
        if c2.button(":material/sports_soccer: Jugar la Supercopa", key="sup_jugar", width="stretch",
                     type="primary", disabled=not listo_sup):
            simular_supercopa(S, P, S["rng"])
            st.rerun()
        estado_sup = ("Terminada" if SS["jugada"] else "Lista para jugar" if listo_sup
                      else "Esperando a Primera y a la Copa")
        barra_estado([("Estado", estado_sup), ("Partidos jugados", len(SS["log"]))],
                     100 if SS["jugada"] else 0)
        seccion("Supercopa Argentina", "Campeón de Primera vs. campeón de la Copa Argentina · partido único "
                "en cancha neutral, penales si empatan", "#b7860b")
        if SS["jugada"]:
            cc = SS["campeon"]
            sub = SS["b"] if cc == SS["a"] else SS["a"]
            st.markdown(f'<div class="champ"><div class="t">Campeón · Supercopa Argentina · Temporada {S["temp"]}'
                        f'</div><div style="margin-top:10px">{crest(cc, 64)}</div>'
                        f'<div class="nm">{esc(cc)}</div><div class="s">finalista: {esc(sub)}</div></div>',
                        unsafe_allow_html=True)
            st.markdown(fila_partido_html(SS["p"], abierto=True), unsafe_allow_html=True)
            st.caption(f"{esc(SS['a'])}: {SS['crit_a']} · {esc(SS['b'])}: {SS['crit_b']}")
        elif listo_sup:
            a_s, _, ca_s, b_s, _, cb_s = rivales_supercopa(S)
            st.markdown(lista_equipos_html([(a_s, ca_s), (b_s, cb_s)]), unsafe_allow_html=True)
            st.caption("Se juega el miércoles siguiente a la última fecha de Primera (ver Calendario).")
        else:
            aviso("Se juega cuando terminan Primera División y la Copa Argentina. Si el mismo club gana las "
                  "dos, el rival es el subcampeón de Primera.")
            faltan_sup = [n for n, ok in (("Primera División", terminada), ("Copa Argentina", terminada_copa))
                          if not ok]
            st.caption("Faltan terminar: " + ", ".join(faltan_sup))


# ============================================================================
# COPAS CONMEBOL: LIBERTADORES, SUDAMERICANA Y RECOPA
# ============================================================================
def pestaña_int(clave, color):
    C = S["int"][clave]
    nombre = C["nombre"]
    terminada_c = C["ronda"] >= C["total"]
    c1, c2, c3 = st.columns([3, 1.4, 1.4], vertical_alignment="center")
    c1.markdown(logo_img(nombre, 30) + " " + chip(f"{nombre} · {len(C['via'])} equipos", color),
                unsafe_allow_html=True)
    espera = not terminada_c and not listo(S, clave)
    if c2.button(":material/skip_next: Próxima ronda", key=f"{clave}_next", width="stretch", type="primary",
                 disabled=terminada_c or espera):
        simular_ronda_int(S, clave, P, S["rng"])
        st.rerun()
    if c3.button(":material/fast_forward: Hasta el final", key=f"{clave}_all", width="stretch",
                 disabled=terminada_c or espera):
        while listo(S, clave):
            simular_ronda_int(S, clave, P, S["rng"])
        st.rerun()
    barra_estado([("Próxima ronda" if not terminada_c else "Estado", fase_actual(C)),
                  ("Rondas", f"{C['ronda']} / {C['total']}"), ("Partidos jugados", len(C["log"]))],
                 100 * C["ronda"] / max(C["total"], 1))
    if espera:
        aviso("La Sudamericana espera a la Libertadores: sus grupos se arman con los que pierden la Fase 3 "
              "y los playoffs, con los terceros de los grupos. Avanzá la Libertadores (o usá Próximo día).")
    if clave == "rec":
        seccion("Recopa Sudamericana", "Campeón de la Libertadores vs. campeón de la Sudamericana · ida y "
                "vuelta (si el global empata, penales)", color)
        if not C["llaves"].get("Final"):
            aviso("Esta temporada no hay Recopa.")
        else:
            st.markdown('<div class="rf-grid">' + serie_int_html(C, C["llaves"]["Final"][0], "Recopa")
                        + '</div>', unsafe_allow_html=True)
        return
    es_lib = clave == "lib"
    titulos = (["Fase previa"] if es_lib else []) + ["Grupos"] + ([] if es_lib else ["Playoffs"]) + [
        "Eliminatorias", "Partidos", "Clasificados", "Definiciones"]
    t = dict(zip(titulos, st.tabs(titulos)))
    if es_lib:
        with t["Fase previa"]:
            seccion("Fase previa", "Fase 2 (16 equipos) y Fase 3 (8) a ida y vuelta · los 4 que ganan la Fase 3 "
                    "van a los grupos; los 4 que pierden, a la Sudamericana", color)
            for fase in ("Fase 2", "Fase 3"):
                if C["llaves"].get(fase):
                    st.markdown(f'<div class="mlab" style="margin-top:10px">{fase}</div>'
                                + series_int_html(C, fase), unsafe_allow_html=True)
    with t["Grupos"]:
        seccion("Fase de grupos", "8 grupos de 4 · ida y vuelta · " + (
            "1° y 2° a octavos, 3° a la Sudamericana" if es_lib else "1° a octavos, 2° a los playoffs"), color)
        if C["grupos"] is None:
            aviso("Los grupos se sortean cuando termina la fase previa de la Libertadores.")
        else:
            destinos = ([("oct", "Octavos"), ("oct", ""), ("sud", "Pasa a la Sudamericana"), ("", "")] if es_lib
                        else [("oct", "Octavos"), ("sud", "Playoffs"), ("", ""), ("", "")])
            st.markdown(grupos_int_html(C, destinos), unsafe_allow_html=True)
    if not es_lib:
        with t["Playoffs"]:
            seccion("Playoffs", "2° de cada grupo vs. los 3° de la Libertadores (cierran de local) · ida y vuelta",
                    color)
            if C["llaves"].get("Playoffs"):
                st.markdown(series_int_html(C, "Playoffs"), unsafe_allow_html=True)
            else:
                aviso("Se arman cuando terminan los grupos de las dos copas.")
    with t["Eliminatorias"]:
        seccion("Eliminatorias", "Octavos, cuartos y semis a ida y vuelta (cierra de local el de mejor campaña) · "
                "final única en cancha neutral · se ve el global de cada serie", color)
        st.markdown(cuadro_int_html(C), unsafe_allow_html=True)
        fases = [f for f in ("Octavos", "Cuartos", "Semifinal") if C["llaves"].get(f)]
        if fases:
            with st.expander(":material/visibility: Ver ida y vuelta de cada serie"):
                for f in fases:
                    st.markdown(f'<div class="mlab" style="margin-top:10px">{f}</div>' + series_int_html(C, f),
                                unsafe_allow_html=True)
    with t["Partidos"]:
        if not C["log"]:
            aviso("Todavía no se jugó ninguna ronda.")
        else:
            rondas = sorted({p["fecha"] for p in C["log"]})
            r_sel = st.selectbox(":material/event: Ronda", rondas, index=len(rondas) - 1,
                                 format_func=lambda n: C["rondas"][n - 1], key=f"{clave}_ronda_{S['temp']}")
            for p in [p for p in C["log"] if p["fecha"] == r_sel]:
                st.markdown(fila_partido_html(p, abierto=p["comp"] == "Final"), unsafe_allow_html=True)
    with t["Clasificados"]:
        seccion("Clasificados", "Argentina: por la tabla de Primera, la Copa Argentina y los campeones · "
                "los otros países: cupos por país, los clubes se sortean cada año", color)
        filas = [{"Equipo": n, "País": pais_de(n), "Cómo clasificó": v, "Media": round(C["r"][n], 1)}
                 for n, v in C["via"].items()]
        filas.sort(key=lambda x: (x["País"] != "Argentina", x["País"], -x["Media"]))
        df_i = pd.DataFrame(filas)
        st.markdown(tabla_html(df_i, formatos={"Media": "{:.1f}"}), unsafe_allow_html=True)
    with t["Definiciones"]:
        seccion("Definiciones", f"Campeón de la {nombre}", "#b7860b")
        if C["campeon"] is None:
            aviso("El campeón aparece acá cuando se juega la final.")
        else:
            cc = C["campeon"]
            st.markdown(f'<div class="champ"><div class="t">Campeón · {esc(nombre)} {anio(S)}</div>'
                        f'<div style="margin-top:10px">{crest(cc, 64)}</div><div class="nm">{esc(cc)}</div>'
                        f'<div class="s">{bandera(pais_de(cc), 18)} {esc(pais_de(cc))} · finalista: '
                        f'{esc(C["subcampeon"])}</div></div>', unsafe_allow_html=True)
            st.caption("Clasifica a la Recopa y a la próxima Libertadores.")


if _abierta(tab_copas, tab_lib):
    with tab_lib:
        pestaña_int("lib", "#8a6d1e")
if _abierta(tab_copas, tab_sud):
    with tab_sud:
        pestaña_int("sud", "#1e5aa8")
if _abierta(tab_copas, tab_rec):
    with tab_rec:
        pestaña_int("rec", "#475569")


# ============================================================================
# MUNDIAL DE CLUBES (cada 4 temporadas: 2029, 2033...)
# ============================================================================
def pestaña_mundial(color):
    M = S["mundial"]
    if not hay_mundial(S):
        prox = proxima_temporada(S["temp"])
        c1 = st.columns(1)[0]
        c1.markdown(chip("Mundial de Clubes · 32 equipos", color) + " " + chip(
            f"Próxima edición: {anio_mundial(prox)} (temporada {prox})", "#475569"), unsafe_allow_html=True)
        seccion("Camino al Mundial", "Los campeones continentales de los 4 años anteriores clasifican directo; "
                "el resto de cada cupo sale del ranking (máximo 2 clubes por país)", color)
        aviso("Esta temporada no hay Mundial de Clubes. Se sortea al empezar la temporada de la edición, con "
              "lo que haya pasado en las copas hasta entonces. Abajo, los clasificados hasta ahora.")
        med = medias_mundial(S)
        filas = [{"Equipo": x["club"], "País": pais_club(x["club"]), "Confederación": x["conf"],
                  "Cómo clasifica": x["via"], "Media": round(med.get(x["club"], 0.0), 1)}
                 for x in calcular_clasificados(S, prox)]
        st.markdown(tabla_html(pd.DataFrame(filas), formatos={"Media": "{:.1f}"}), unsafe_allow_html=True)
        return
    terminado = M["ronda"] >= M["total"]
    c1, c2, c3 = st.columns([3, 1.4, 1.4], vertical_alignment="center")
    c1.markdown(chip(f"Mundial de Clubes {M['anio']} · 32 equipos", color), unsafe_allow_html=True)
    if c2.button(":material/skip_next: Próxima ronda", key="mun_next", width="stretch", type="primary",
                 disabled=terminado):
        simular_ronda_mundial(S, P, S["rng"])
        st.rerun()
    if c3.button(":material/fast_forward: Hasta el final", key="mun_all", width="stretch", disabled=terminado):
        while not mundial_terminado(S):
            simular_ronda_mundial(S, P, S["rng"])
        st.rerun()
    barra_estado([("Próxima ronda" if not terminado else "Estado", fase_mundial(M)),
                  ("Rondas", f"{M['ronda']} / {M['total']}"), ("Partidos jugados", len(M["log"]))],
                 100 * M["ronda"] / max(M["total"], 1))
    titulos = ["Grupos", "Eliminatorias", "Partidos", "Clasificados", "Definiciones"]
    t = dict(zip(titulos, st.tabs(titulos)))
    with t["Grupos"]:
        seccion("Fase de grupos", "8 grupos de 4 · una rueda en cancha neutral · 1° y 2° a octavos", color)
        st.markdown(grupos_mundial_html(M), unsafe_allow_html=True)
    with t["Eliminatorias"]:
        seccion("Eliminatorias", "Octavos, cuartos, semifinales y final en cancha neutral · si empatan, penales",
                color)
        st.markdown(cuadro_mundial_html(M), unsafe_allow_html=True)
    with t["Partidos"]:
        if not M["log"]:
            aviso("Todavía no se jugó ninguna ronda.")
        else:
            rondas = sorted({p["fecha"] for p in M["log"]})
            r_sel = st.selectbox(":material/event: Ronda", rondas, index=len(rondas) - 1,
                                 format_func=lambda n: MUNDIAL_RONDAS[n - 1], key=f"mun_ronda_{S['temp']}")
            for p in [p for p in M["log"] if p["fecha"] == r_sel]:
                st.markdown(fila_partido_html(p, abierto=p["comp"] == "Final"), unsafe_allow_html=True)
    with t["Clasificados"]:
        seccion("Clasificados", "UEFA 12 · CONMEBOL 6 · AFC 4 · CAF 4 · Concacaf 4 · OFC 1 · anfitrión 1", color)
        orden_conf = ["UEFA", "CONMEBOL", "AFC", "CAF", "CONCACAF", "OFC"]
        filas = [{"Equipo": n, "País": pais_club(n), "Confederación": M["conf"][n], "Cómo clasificó": M["via"][n],
                  "Media": round(M["r"][n], 1)} for n in M["nombres"]]
        filas.sort(key=lambda x: (orden_conf.index(x["Confederación"]), -x["Media"]))
        st.markdown(tabla_html(pd.DataFrame(filas), formatos={"Media": "{:.1f}"}), unsafe_allow_html=True)
    with t["Definiciones"]:
        seccion("Definiciones", "Campeón del Mundial de Clubes", "#b7860b")
        if M["campeon"] is None:
            aviso("El campeón aparece acá cuando se juega la final.")
        else:
            cc = M["campeon"]
            st.markdown(f'<div class="champ"><div class="t">Campeón · Mundial de Clubes {M["anio"]}</div>'
                        f'<div style="margin-top:10px">{crest(cc, 64)}</div><div class="nm">{esc(cc)}</div>'
                        f'<div class="s">{bandera(pais_club(cc), 18)} {esc(pais_club(cc))} · finalista: '
                        f'{esc(M["subcampeon"])}</div></div>', unsafe_allow_html=True)


if _abierta(tab_copas, tab_mun):
    with tab_mun:
        pestaña_mundial("#be185d")


# ============================================================================
# CALENDARIO
# ============================================================================
if _abierta(tab_cal):
    with tab_cal:
        seccion(f"Calendario {anio(S)}", "Cuándo se juega cada fecha de cada liga y cada ronda de la Copa "
                "Argentina (los miércoles, en el medio de las ligas)", "#1e5aa8")
        c1, c2 = st.columns([3, 1.4], vertical_alignment="center")
        c1.markdown((f'Próximo día: <b>{esc(texto_dia(_hoy))}</b> · ' + " ".join(
            logo_img(c, 18) for c, (d, _) in _prox.items() if d == _hoy)) if _hoy else
            "Terminó la temporada: pasá a la siguiente desde <b>Nueva temporada</b>.", unsafe_allow_html=True)
        if c2.button(":material/calendar_today: Jugar ese día", key="cal_next", width="stretch", type="primary",
                     disabled=_hoy is None):
            jugar_proximo_dia(S, P, acumular)
            st.rerun()
        eventos = eventos_calendario(S)
        meses = sorted({d.month for d, *_ in eventos})
        mes_def = (_hoy or eventos[-1][0]).month
        clave_mes = f"cal_mes_{S['temp']}"
        # el mes elegido sigue al próximo día (cuando avanza el calendario, se mueve solo)
        if st.session_state.get(f"{clave_mes}_sigue") != mes_def or clave_mes not in st.session_state:
            st.session_state[clave_mes] = mes_def if mes_def in meses else meses[0]
            st.session_state[f"{clave_mes}_sigue"] = mes_def
        mes = st.segmented_control("Mes", meses, format_func=lambda m: nombre_mes(m)[:3], key=clave_mes,
                                   label_visibility="collapsed") or mes_def
        st.markdown(calendario_mes_html(S, eventos, mes, _hoy), unsafe_allow_html=True)
        st.caption("Tocá cada competición para ver sus partidos. ⚠ = partido con incidente (ver Avisos).")


# ============================================================================
# CLUBES
# ============================================================================
if _abierta(tab_c):
    with tab_c:
        seccion("Clubes", "Elegí un club para ver su ficha y buscar sus partidos", "#1e5aa8")
        cat = st.segmented_control("Categoría",
                                   ["Primera División", "Primera Nacional", "Federal A", "Primera B", "Primera C",
                                    "Regional Amateur"],
                                   default="Primera División", key="cat_clubes")
        cat = cat or "Primera División"
        if cat == "Regional Amateur":            # 245 clubes: se elige la región
            region_c = st.pills("Región", REGIONES_REG, default=REGIONES_REG[0], key="club_reg_region",
                                label_visibility="collapsed") or REGIONES_REG[0]
            lista = sorted([n for n, r in zip(SR["nombres"], SR["region_de"]) if r == region_c], key=norm)
            region_club = dict(zip(SR["nombres"], SR["region_de"]))
            buscables = sorted(SR["nombres"], key=norm)          # el buscador: todas las regiones
        else:
            lista = sorted({"Primera División": S["nombres"], "Primera Nacional": SB["nombres"],
                            "Federal A": S["federal"], "Primera B": S["primera_b"], "Primera C": S["primera_c"]}[cat],
                           key=norm)
            buscables = lista
        elegido = st.selectbox(":material/search: Buscar club", buscables, index=None,
                               placeholder=("Escribí un club de cualquier región…" if cat == "Regional Amateur"
                                            else "Escribí o elegí un club…"),
                               format_func=(lambda n: f"{n} · {region_club[n]}") if cat == "Regional Amateur"
                               else str, key=f"club_sel_{cat}")
        if elegido:
            with st.container(border=True):
                render_ficha(elegido, "clubes")
        st.markdown(f'<div class="mlab" style="margin-top:14px">{esc(cat if cat != "Regional Amateur" else f"Regional · {region_c}")} · {len(lista)} clubes · '
                    f'tocá uno para ver su ficha</div>', unsafe_allow_html=True)
        # Grilla de clubes: cada casilla es un botón (invisible, ocupa toda la casilla) que abre la ficha
        slug = norm(cat if cat != "Regional Amateur" else f"reg {region_c}").replace(" ", "_")
        with st.container(key=f"cgrid_{slug}"):
            for i, n in enumerate(lista):
                with st.container(key=f"ctile_{slug}_{i}"):
                    st.markdown(f'<div class="ct-in">{crest(n, 52)}<span>{esc(n)}</span></div>',
                                unsafe_allow_html=True)
                    if st.button(n, key=f"clubbtn_{slug}_{i}"):
                        ver_equipo(n)


# ============================================================================
# AVISOS
# ============================================================================
if _abierta(tab_av):
    with tab_av:
        seccion("Avisos", "Partidos suspendidos y sanciones del Tribunal de Disciplina", "#b83a2e")
        if _sin_leer:
            c1, c2 = st.columns([3, 1.4], vertical_alignment="center")
            c1.markdown(f'<div class="aviso-banner">🚨 <span><b>{_sin_leer} aviso{"s" if _sin_leer > 1 else ""} '
                        f'nuevo{"s" if _sin_leer > 1 else ""}</b></span></div>', unsafe_allow_html=True)
            if c2.button(":material/done_all: Marcar como leídos", key="avisos_leidos_btn", width="stretch"):
                S["avisos_leidos"] = _total_avisos
                st.rerun()
        if _avisos:
            st.markdown(f'<div class="mlab" style="margin-top:8px">Temporada {S["temp"]}</div>', unsafe_allow_html=True)
            st.markdown(avisos_html(_avisos), unsafe_allow_html=True)
        else:
            aviso("Esta temporada, por ahora, no hubo partidos suspendidos ni sanciones.")
        if S.get("alertas_hist"):
            st.markdown('<div class="mlab" style="margin-top:18px">Temporadas anteriores</div>', unsafe_allow_html=True)
            st.markdown(avisos_html(S["alertas_hist"], con_temporada=True), unsafe_allow_html=True)


# ============================================================================
# HISTORIAL
# ============================================================================

def tabla_ranking_html(titulo, logo, actual, base):
    """Tarjeta de palmarés de una liga o copa: posición, escudo, club y títulos. Los ganados
    en las temporadas simuladas se marcan aparte (+n)."""
    lista = sorted(((n, t) for n, t in actual.items() if t > 0), key=lambda x: (-x[1], x[0]))
    total = sum(t for _, t in lista)
    filas, pos, previo = "", 0, None
    for k, (n, t) in enumerate(lista):
        if t != previo:
            pos, previo = k + 1, t
        extra = t - base.get(n, 0)
        clase = " oro" if pos == 1 else ""
        filas += (f'<div class="pal-f{clase}"><span class="pal-pos">{pos}</span>{crest(n, 22)}'
                  f'<span class="pal-nm" role="button" tabindex="0" data-club="{esc(n)}" title="{esc(n)}">{esc(n)}</span>'
                  + (f'<span class="pal-mas" title="Ganados en las temporadas simuladas">+{extra}</span>' if extra > 0 else "")
                  + f'<b class="pal-t">{t}</b></div>')
    if not filas:
        filas = '<div class="pal-vacio">Todavía no hay campeones.</div>'
    return (f'<div class="pal"><div class="pal-h">{logo_img(logo, 26)}<span class="pal-tit">{esc(titulo)}</span>'
            f'<span class="pal-tot">{total} títulos</span></div><div class="pal-lista">{filas}</div></div>')


if _abierta(tab_h):
    with tab_h:
        seccion("Historial", "Campeones de cada temporada y rankings históricos", "#b7860b")

        if S["campeones"]:
            ligas_c = ["Primera División", "Primera Nacional", "Federal A", "Primera B", "Primera C",
                       "Copa Argentina", "Supercopa", "Libertadores", "Sudamericana", "Recopa", "Mundial"]
            with st.expander(":material/emoji_events: Campeones por temporada", expanded=False):
                df_c = pd.DataFrame([{k: x.get(k) or None for k in ["Temporada"] + ligas_c} for x in S["campeones"]])
                st.markdown(tabla_html(df_c, clubes=tuple(ligas_c)), unsafe_allow_html=True)
            with st.expander(":material/emoji_events: Campeones del Regional Amateur (por región)", expanded=False):
                df_r = pd.DataFrame([{"Temporada": x["Temporada"],
                                      **{reg: x.get("Regional", {}).get(reg) or None for reg in REGIONES_REG}}
                                     for x in S["campeones"]])
                st.markdown(tabla_html(df_r, clubes=tuple(REGIONES_REG)), unsafe_allow_html=True)
        else:
            aviso("Los campeones de cada liga aparecen acá al pasar a la temporada siguiente.")

        # Palmarés histórico: títulos oficiales hasta 2025 (palmares.py) + los de las temporadas simuladas
        from palmares import PALMARES
        st.markdown('<div class="mlab" style="margin-top:20px">Palmarés histórico · ligas</div>', unsafe_allow_html=True)
        st.markdown('<div class="pal-grid">' + "".join(
            tabla_ranking_html(titulo, logo, S.get(clave, {}), PALMARES.get(clave, {}))
            for titulo, logo, clave in (("Primera División", "Primera División", "hist_primera"),
                                        ("Primera Nacional", "Primera Nacional", "hist_nacional"),
                                        ("Federal A", "Federal A", "hist_federal"),
                                        ("Primera B Metropolitana", "Primera B", "hist_pb"),
                                        ("Primera C Metropolitana", "Primera C", "hist_pc"))) + '</div>',
                    unsafe_allow_html=True)
        st.markdown('<div class="mlab" style="margin-top:18px">Palmarés histórico · copas</div>', unsafe_allow_html=True)
        st.markdown('<div class="pal-grid">' + "".join(
            tabla_ranking_html(titulo, logo, S.get(clave, {}), PALMARES.get(clave, {}))
            for titulo, logo, clave in (("Copa Argentina", "Copa Argentina", "hist_copa"),
                                        ("Supercopa Argentina", "Supercopa Argentina", "hist_super"),
                                        ("Mundial de Clubes", "Mundial de Clubes", "hist_mundial"),
                                        ("Copa Libertadores", "Copa Libertadores", "hist_lib"),
                                        ("Copa Sudamericana", "Copa Sudamericana", "hist_sud"),
                                        ("Recopa Sudamericana", "Recopa Sudamericana", "hist_rec"))) + '</div>',
                    unsafe_allow_html=True)
        st.caption("Títulos oficiales hasta 2025 (AFA / CONMEBOL): Primera, era amateur y profesional; "
                   "B Nacional, Primera B Metropolitana y Primera C, desde 1986-87; Federal A, desde 2014. "
                   "En verde (+n), los ganados en las temporadas simuladas. Tocá un club para ver su ficha.")

        if S["movimientos"]:
            mv = S["movimientos"]
            with st.expander(f":material/swap_vert: Cambios de categoría para la temporada {S['temp']}", expanded=False):
                st.markdown(
                    '<div class="catgrid">'
                    f'<div><div class="mlab up">▲ Ascendieron a Primera</div>'
                    f'{lista_equipos_html([(n, "directo") for n in mv["directos"]] + ([(mv["reducido"], "reducido")] if mv["reducido"] else []))}</div>'
                    f'<div><div class="mlab down">▼ Descendieron a B Nacional</div>'
                    f'{lista_equipos_html([(n, "") for n in mv["bajan_p"]])}</div>'
                
                    f'<div><div class="mlab up">▲ Ascendieron a B Nacional</div>'
                    f'{lista_equipos_html([(n, "del Federal A") for n in mv.get("suben_f_b", [])] + [(n, "de la B Metro") for n in mv.get("suben_pb_b", [])])}</div>'
                    f'<div><div class="mlab down">▼ Descendieron al Federal A</div>'
                    f'{lista_equipos_html([(n, "") for n in mv.get("bajan_b_fed", [])])}</div>'
                
                    f'<div><div class="mlab down">▼ Descendieron a la B Metro</div>'
                    f'{lista_equipos_html([(n, "") for n in mv.get("bajan_b_pb", [])])}</div>'
                    f'<div><div class="mlab up">▲ Ascendieron a la B Metro</div>'
                    f'{lista_equipos_html([(n, "de la C") for n in mv.get("suben_pc_pb", [])])}</div>'
                
                    f'<div><div class="mlab down">▼ Descendieron a Primera C</div>'
                    f'{lista_equipos_html([(n, "") for n in mv.get("bajan_pb_pc", [])])}</div>'
                    f'<div><div class="mlab up">▲ Ascendieron al Federal A</div>'
                    f'{lista_equipos_html([(n, "del Regional") for n in mv.get("suben_reg_fed", [])] + [(n, "reubicación") for n in mv.get("suben_reg_fed_extra", [])])}</div>'
                    
                    f'<div><div class="mlab down">▼ Descendieron al Promocional Amateur</div>'
                    f'{lista_equipos_html([(n, "") for n in mv.get("bajan_pc_pd", [])])}</div>'
                    f'<div><div class="mlab up">▲ Ascendieron a Primera C</div>'
                    f'{lista_equipos_html([(n, "del Promocional") for n in mv.get("suben_pd_pc", [])])}</div>'
                    
                    f'<div><div class="mlab down">▼ Descendieron al Regional</div>'
                    f'{lista_equipos_html([(n, region_regional(n)) for n in mv.get("bajan_fed_reg", [])])}</div>'
                    + (f'<div><div class="mlab down">▼ Descenso administrativo (Tribunal de Disciplina)</div>'
                       f'{lista_equipos_html([(n, "sanción") for n in mv.get("descenso_adm", [])])}</div>'
                       if mv.get("descenso_adm") else "") +
                    f'</div>', unsafe_allow_html=True)
"""Pestañas de la página: las de arriba (Ligas, Copas, Calendario...) y las de cada liga y copa."""

from dataclasses import dataclass

import streamlit as st

from datos.ligas_ext import LIGAS_EXT
from datos.logos import LOGOS
from datos import paises
from datos.paises import PAIS_BASE
from ui.vista.mi_club import tabs_con_default


@dataclass
class Pestanas:
    """Los contenedores donde dibuja cada módulo de ui/. `tab_mgr` y `tab_fb` son None si ese modo / categoría no existe.
    Las pestañas de Ligas y Copas que no son del país activo también son None: ctx.abierta() las salta."""
    tab_ligas: object
    tab_copas: object
    tab_cal: object
    tab_c: object
    tab_av: object
    tab_h: object
    tab_pa: object
    tab_p: object
    tab_b: object
    tab_f: object
    tab_reg: object
    tab_pb: object
    tab_pc: object
    tab_pd: object
    tab_ca: object
    tab_sup: object
    tab_rgs: object
    tab_lib: object
    tab_sud: object
    tab_rec: object
    tab_mun: object
    tab_mgr: object = None
    tab_scuy: object = None            # Supercopa Uruguaya (sólo si el país activo es Uruguay)
    tab_cuy: object = None             # Copa AUF Uruguay (sólo si el país activo es Uruguay)
    tab_cbr: object = None             # Copa do Brasil (sólo si el país activo es Brasil)
    tab_sbr: object = None             # Supercopa do Brasil (sólo si el país activo es Brasil)
    tab_fb: object = None
    tab_mundo: object = None            # selector de país (pestaña madre)
    tabs_ligas_ext: dict = None         # {clave de la liga: su pestaña} (las ligas del país activo si no es Argentina)


def _con_logo(liga, texto):
    return f"![]({LOGOS[liga]}) {texto}" if liga in LOGOS else texto


def _etiqueta(liga, texto, clave, competencias):
    """Etiqueta de pestaña; en modo manager marca con ⭐ las competencias donde juega mi club."""
    return _con_logo(liga, texto) + (" ⭐" if clave in competencias else "")


def _inicial(etiquetas, claves, competencias):
    """Pestaña que se abre sola: la primera donde juega mi club (None si no hay)."""
    return next((e for e, c in zip(etiquetas, claves) if c in competencias), None)


def _globito_avisos(sin_leer, posicion):
    """Contador de avisos nuevos (globito rojo en la pestaña Avisos, la número `posicion` del menú de arriba)."""
    if sin_leer:
        st.markdown(f'<style>.st-key-menu_top>[data-testid="stTabs"]>div>[role="tablist"]>[role="tab"]:nth-child({posicion})'
                    f'::after{{content:"{sin_leer}";margin-left:6px;background:var(--lose);color:#fff;font-size:.66rem;'
                    f'font-weight:800;border-radius:9px;padding:1px 7px;line-height:1.4;}}</style>', unsafe_allow_html=True)


CLAVES_INTERNACIONALES = ("lib", "sud", "rec", "mun")
CLAVE_COPA_EXT = {"Copa AUF Uruguay": "cuy", "Supercopa Uruguaya": "scuy", "Copa do Brasil": "cbr", "Supercopa do Brasil": "sbr"}   # copas nacionales de otros países


def _sufijo(pais):
    """Sufijo de la key de las pestañas: con otro país cambia la key, así que cada país abre sus pestañas desde cero
    (y Argentina conserva las keys de siempre)."""
    return "" if pais == PAIS_BASE else "_" + "".join(c if c.isalnum() else "_" for c in pais)


def _pestanas_de_ligas_ext(pais):
    """Ligas de un país que no es Argentina (hoy una por país): {clave de la liga: pestaña}."""
    cfgs = [c for c in LIGAS_EXT if c["pais"] == pais]
    etiquetas = [_con_logo(c["nombre"], c["nombre"]) for c in cfgs]
    return dict(zip([c["clave"] for c in cfgs],
                    tabs_con_default(etiquetas, None, key=f"tabs_ligas{_sufijo(pais)}", on_change="rerun")))


def _pestanas_de_ligas(S, competencias, kclub):
    """El Federal B (se crea desde el Modo dios) va entre el Federal A y el Regional; hasta entonces no hay pestaña."""
    hay_fb = bool(S.get("fb"))
    claves = ["p", "b", "f"] + (["fb"] if hay_fb else []) + ["reg", "pb", "pc", "pd"]
    etiquetas = [_etiqueta("Primera División", "Primera", "p", competencias),
                 _etiqueta("Primera Nacional", "B Nacional", "b", competencias),
                 _etiqueta("Federal A", "Federal A", "f", competencias)]
    if hay_fb:
        etiquetas.append(_etiqueta("Federal B", "Federal B", "fb", competencias))
    etiquetas += [_etiqueta("Regional Amateur", "Regional", "reg", competencias),
                  _etiqueta("Primera B", "Primera B", "pb", competencias),
                  _etiqueta("Primera C", "Primera C", "pc", competencias),
                  _etiqueta("Promocional Amateur", "Promocional", "pd", competencias)]
    # la key lleva el club: si cambiás de club, la pestaña se vuelve a abrir en su competencia
    return dict(zip(claves, tabs_con_default(
        etiquetas, _inicial(etiquetas, claves, competencias),
        key=f"tabs_ligas{kclub}{'_fb' if hay_fb else ''}", on_change="rerun")))


def _pestanas_de_copas(competencias, kclub, pais):
    """Copas del país activo (las nacionales) y las internacionales donde puede jugar. Devuelve {clave: pestaña}."""
    todas = [("ca", _etiqueta("Copa Argentina", "Copa Argentina", "ca", competencias)),
             ("sup", _etiqueta("Supercopa Argentina", "Supercopa", "sup", competencias)),
             ("rgs", _etiqueta("Regionales", "Regionales", "rgs", competencias)),
             ("cuy", _etiqueta("Copa AUF Uruguay", "Copa AUF Uruguay", "cuy", competencias)),
             ("scuy", _etiqueta("Supercopa Uruguaya", "Supercopa Uruguaya", "scuy", competencias)),
             ("cbr", _etiqueta("Copa do Brasil", "Copa do Brasil", "cbr", competencias)),
             ("sbr", _etiqueta("Supercopa do Brasil", "Supercopa do Brasil", "sbr", competencias)),
             ("lib", _etiqueta("Copa Libertadores", "Libertadores", "lib", competencias)),
             ("sud", _etiqueta("Copa Sudamericana", "Sudamericana", "sud", competencias)),
             ("rec", _etiqueta("Recopa Sudamericana", "Recopa", "rec", competencias)),
             ("mun", _etiqueta("Mundial de Clubes", "Mundial de Clubes", "mun", competencias))]
    propias = tuple(CLAVE_COPA_EXT[c] for c in paises.copas_nacionales_de(pais) if c in CLAVE_COPA_EXT)
    ajenas = set(CLAVE_COPA_EXT.values()) - set(propias)
    todas = [(c, e) for c, e in todas if c not in ajenas]
    if pais != PAIS_BASE:           # las de su país (si simula alguna) y las internacionales
        todas = [(c, e) for c, e in todas if c in CLAVES_INTERNACIONALES + propias]
    claves, etiquetas = [c for c, _ in todas], [e for _, e in todas]
    return dict(zip(claves, tabs_con_default(
        etiquetas, _inicial(etiquetas, claves, competencias), key=f"tabs_copas{kclub}{_sufijo(pais)}",
        on_change="rerun")))


def crear_pestanas(S, modo_mgr, competencias, kclub, sin_leer, pestana_inicial=None, pais=PAIS_BASE):
    """Arma todas las pestañas. Sólo se dibuja la pestaña abierta (on_change="rerun" + .open): antes se armaban
    las 6 ligas y todas las copas en cada clic, la página pesaba más de 1 MB y el navegador se quedaba trabado.

    competencias: claves de las competencias donde juega mi club (vacío si no dirijo a ninguno).
    pestana_inicial: "Partidas" si se llegó con "Cargar partida" desde la pantalla de inicio.
    pais: país activo (se elige en Mundo). Ligas y Copas arman sólo las pestañas de ese país."""
    nombres = ["Ligas", "Copas", "Mundo", "Calendario", "Clubes", "Avisos", "Historial", "Partidas"]
    with st.container(key="menu_top"):
        if modo_mgr:
            tab_mgr, *arriba = tabs_con_default(["Manager", *nombres], pestana_inicial, key="tabs_top", on_change="rerun")
        else:
            tab_mgr, arriba = None, tabs_con_default(nombres, pestana_inicial, key="tabs_top", on_change="rerun")
    tab_ligas, tab_copas, tab_mundo, tab_cal, tab_c, tab_av, tab_h, tab_pa = arriba
    _globito_avisos(sin_leer, nombres.index("Avisos") + 1 + bool(modo_mgr))
    ligas, ligas_ext = {}, {}
    with tab_ligas, st.container(key="menu_ligas"):
        if pais == PAIS_BASE:
            ligas = _pestanas_de_ligas(S, competencias, kclub)
        else:
            ligas_ext = _pestanas_de_ligas_ext(pais)
    with tab_copas, st.container(key="menu_copas"):
        copas = _pestanas_de_copas(competencias, kclub, pais)
    return Pestanas(
        tab_ligas=tab_ligas, tab_copas=tab_copas, tab_cal=tab_cal, tab_c=tab_c, tab_av=tab_av, tab_h=tab_h,
        tab_pa=tab_pa, tab_p=ligas.get("p"), tab_b=ligas.get("b"), tab_f=ligas.get("f"), tab_reg=ligas.get("reg"),
        tab_pb=ligas.get("pb"), tab_pc=ligas.get("pc"), tab_pd=ligas.get("pd"), tab_ca=copas.get("ca"),
        tab_sup=copas.get("sup"), tab_rgs=copas.get("rgs"), tab_lib=copas.get("lib"), tab_sud=copas.get("sud"),
        tab_rec=copas.get("rec"), tab_mun=copas.get("mun"), tab_cuy=copas.get("cuy"), tab_scuy=copas.get("scuy"),
        tab_cbr=copas.get("cbr"), tab_sbr=copas.get("sbr"),
        tab_mgr=tab_mgr, tab_fb=ligas.get("fb"), tab_mundo=tab_mundo, tabs_ligas_ext=ligas_ext)

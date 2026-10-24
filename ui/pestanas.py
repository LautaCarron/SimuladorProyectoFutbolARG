"""Pestañas de la página: las de arriba (Ligas, Copas, Calendario...) y las de cada liga y copa."""

from dataclasses import dataclass

import streamlit as st

from datos.logos import LOGOS
from ui.vista.mi_club import tabs_con_default


@dataclass
class Pestanas:
    """Los contenedores donde dibuja cada módulo de ui/. `tab_mgr` y `tab_fb` son None si ese modo / categoría no existe."""
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
    tab_lib: object
    tab_sud: object
    tab_rec: object
    tab_mun: object
    tab_mgr: object = None
    tab_fb: object = None


def _con_logo(liga, texto):
    return f"![]({LOGOS[liga]}) {texto}" if liga in LOGOS else texto


def _etiqueta(liga, texto, clave, competencias):
    """Etiqueta de pestaña; en modo manager marca con ⭐ las competencias donde juega mi club."""
    return _con_logo(liga, texto) + (" ⭐" if clave in competencias else "")


def _inicial(etiquetas, claves, competencias):
    """Pestaña que se abre sola: la primera donde juega mi club (None si no hay)."""
    return next((e for e, c in zip(etiquetas, claves) if c in competencias), None)


def _globito_avisos(sin_leer, modo_mgr):
    """Contador de avisos nuevos (globito rojo en la pestaña Avisos)."""
    if sin_leer:
        posicion = 6 if modo_mgr else 5
        st.markdown(f'<style>.st-key-menu_top>[data-testid="stTabs"]>div>[role="tablist"]>[role="tab"]:nth-child({posicion})'
                    f'::after{{content:"{sin_leer}";margin-left:6px;background:var(--lose);color:#fff;font-size:.66rem;'
                    f'font-weight:800;border-radius:9px;padding:1px 7px;line-height:1.4;}}</style>', unsafe_allow_html=True)


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


def _pestanas_de_copas(competencias, kclub):
    claves = ["ca", "sup", "lib", "sud", "rec", "mun"]
    etiquetas = [_etiqueta("Copa Argentina", "Copa Argentina", "ca", competencias),
                 _etiqueta("Supercopa Argentina", "Supercopa", "sup", competencias),
                 _etiqueta("Copa Libertadores", "Libertadores", "lib", competencias),
                 _etiqueta("Copa Sudamericana", "Sudamericana", "sud", competencias),
                 _etiqueta("Recopa Sudamericana", "Recopa", "rec", competencias),
                 _etiqueta("Mundial de Clubes", "Mundial de Clubes", "mun", competencias)]
    return tabs_con_default(etiquetas, _inicial(etiquetas, claves, competencias), key=f"tabs_copas{kclub}",
                            on_change="rerun")


def crear_pestanas(S, modo_mgr, competencias, kclub, sin_leer, pestana_inicial=None):
    """Arma todas las pestañas. Sólo se dibuja la pestaña abierta (on_change="rerun" + .open): antes se armaban
    las 6 ligas y todas las copas en cada clic, la página pesaba más de 1 MB y el navegador se quedaba trabado.

    competencias: claves de las competencias donde juega mi club (vacío si no dirijo a ninguno).
    pestana_inicial: "Partidas" si se llegó con "Cargar partida" desde la pantalla de inicio."""
    nombres = ["Ligas", "Copas", "Calendario", "Clubes", "Avisos", "Historial", "Partidas"]
    with st.container(key="menu_top"):
        if modo_mgr:
            tab_mgr, *arriba = tabs_con_default(["Manager", *nombres], pestana_inicial, key="tabs_top", on_change="rerun")
        else:
            tab_mgr, arriba = None, tabs_con_default(nombres, pestana_inicial, key="tabs_top", on_change="rerun")
    tab_ligas, tab_copas, tab_cal, tab_c, tab_av, tab_h, tab_pa = arriba
    _globito_avisos(sin_leer, modo_mgr)
    with tab_ligas, st.container(key="menu_ligas"):
        ligas = _pestanas_de_ligas(S, competencias, kclub)
    with tab_copas, st.container(key="menu_copas"):
        tab_ca, tab_sup, tab_lib, tab_sud, tab_rec, tab_mun = _pestanas_de_copas(competencias, kclub)
    return Pestanas(
        tab_ligas=tab_ligas, tab_copas=tab_copas, tab_cal=tab_cal, tab_c=tab_c, tab_av=tab_av, tab_h=tab_h,
        tab_pa=tab_pa, tab_p=ligas["p"], tab_b=ligas["b"], tab_f=ligas["f"], tab_reg=ligas["reg"],
        tab_pb=ligas["pb"], tab_pc=ligas["pc"], tab_pd=ligas["pd"], tab_ca=tab_ca, tab_sup=tab_sup,
        tab_lib=tab_lib, tab_sud=tab_sud, tab_rec=tab_rec, tab_mun=tab_mun,
        tab_mgr=tab_mgr, tab_fb=ligas.get("fb"))

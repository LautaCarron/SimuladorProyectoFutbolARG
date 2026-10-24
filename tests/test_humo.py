"""Pruebas de humo: no verifican resultados de partidos (son al azar), sólo que nada se rompe."""

import os

import pytest

from config import VOLATILIDAD, parametros_partido
from motor.calendario import jugar_proximo_dia, proximos
from motor.progreso import Progreso
from motor.simulacion import jugar_competencia, simular_todo
from motor.temporada import crear_estado, nueva_temporada

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_una_temporada_completa():
    S, P = crear_estado(), parametros_partido()
    assert not Progreso.desde_estado(S).todas
    jugar_proximo_dia(S, P)
    simular_todo(S, P)
    assert Progreso.desde_estado(S).todas
    assert not proximos(S)
    nueva_temporada(S, VOLATILIDAD)
    assert S["temp"] == 2


def test_competencia_desconocida():
    with pytest.raises(ValueError):
        jugar_competencia(crear_estado(), parametros_partido(), "Liga de la Quimera")


def _app(modo="simulador"):
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(os.path.join(RAIZ, "simuladorafa.py"), default_timeout=240)
    at.session_state["afa_pantalla"] = modo
    return at


def _boton(at, texto):
    return next(b for b in at.button if texto in (b.label or ""))


def test_app_simulador():
    at = _app()
    at.run()
    assert not at.exception
    for paso in ("Próximo día", "Simular todo", "Nueva temporada"):
        _boton(at, paso).click()
        at.run()
        assert not at.exception, paso
    assert at.session_state["S"]["temp"] == 2


def test_app_manager():
    from motor.manager import primer_dia
    from motor.ofertas import categoria_de, nuevo_manager_estado
    from motor.relaciones import asegurar, entrar_club

    S = crear_estado()
    club = S["nombres"][0]
    M = nuevo_manager_estado(70)
    M.update(nombre="Test", apellido="Manager", edad=40, nacionalidad="Argentina", formacion="4-4-2", estilo=None,
             reputacion="Desconocido", global_a_mano=True, hoy=primer_dia(S))
    asegurar(M)
    M["club"], M["rol"] = club, "primer_equipo"
    entrar_club(S, M, club)
    M["historial_clubes"].append({"club": club, "categoria": categoria_de(S, club), "rol": "primer_equipo",
                                  "temporada": 1, "desde": M["hoy"], "hasta": None, "ascendido": None})
    at = _app("manager")
    at.session_state["S"], at.session_state["manager"] = S, M
    at.run()
    assert not at.exception
    _boton(at, "Simular hasta el próximo partido").click()
    at.run()
    assert not at.exception
    assert any("mrow mio" in m.value for m in at.markdown), "el partido de mi club debe marcarse"
    for paso in ("Próximo día", "Simular todo"):
        _boton(at, paso).click()
        at.run()
        assert not at.exception, paso


def test_vista_recibe_el_estado_por_parametro():
    """Ficha, avisos, finales y fixture reciben S explícito (no leen st.session_state.S)."""
    from streamlit.testing.v1 import AppTest

    def app():
        import streamlit as st

        from config import parametros_partido
        from motor.simulacion import simular_todo
        from motor.temporada import crear_estado
        from ui.vista import render_ficha
        from ui.vista.cuadros import avisos_html, finales_reg_html
        from ui.vista.fixture import vista_fixture

        S = crear_estado()
        simular_todo(S, parametros_partido())
        render_ficha(S, None, S["nombres"][0], "t1")
        st.markdown(avisos_html(S, S.get("alertas", [])), unsafe_allow_html=True)
        st.markdown(finales_reg_html(S), unsafe_allow_html=True)
        for liga in ("p", "b", "f", "pb", "pc", "pd", "reg"):
            vista_fixture(S, None, liga)

    at = AppTest.from_function(app, default_timeout=120).run()
    assert not at.exception


def test_regional_regiones_de_mas_de_24_clubes_se_dividen_en_dos_zonas():
    from datos.datos_regional import FINALES_REG, REGIONES_REG
    from ligas.regional import REG_CRUCE, REG_MAX_LIGA, simular_fecha_reg, tabla_reg_region

    S, P = crear_estado(), parametros_partido()
    SR = S["reg"]
    divididas = [r for r in REGIONES_REG if len(SR["grupos"][r]) > REG_MAX_LIGA]
    assert divididas, "con los datos actuales hay regiones con más de 24 clubes"
    for reg in REGIONES_REG:
        claves = SR["zonas_de"][reg]
        assert len(claves) == (2 if reg in divididas else 1)
        tamanos = sorted(len(SR["zonas"][c]) for c in claves)
        assert sum(tamanos) == len(SR["grupos"][reg])
        assert tamanos[-1] - tamanos[0] <= 1                       # zonas parejas
        assert set(SR["zonas"][claves[0]]).isdisjoint(SR["zonas"][claves[-1]]) or len(claves) == 1
    assert SR["f_cruce"] == 1 and SR["f_liga"] <= REG_MAX_LIGA - 1       # la liga más larga es la de 24 clubes

    while SR["fecha"] < SR["total"]:
        simular_fecha_reg(SR, P, S["rng"])

    cruces = [p for p in SR["log"] if p["rotulo"] == REG_CRUCE]
    assert sorted(p["region"] for p in cruces) == sorted(divididas)         # uno por cada región dividida
    assert all(p["neutral"] and p["fecha"] == SR["f_final0"] for p in cruces)
    finales = [p for p in SR["log"] if p["liga"] == "Regional Amateur" and p["comp"] == "Final por el ascenso"]
    assert finales and min(p["fecha"] for p in finales) > SR["f_final0"]    # el cruce va antes de las finales
    for reg in divididas:
        zona_a, zona_b = (SR["campeones_zona"][c] for c in SR["zonas_de"][reg])
        campeon, finalista = SR["cruces"][reg]
        assert SR["campeones"][reg] == campeon and {campeon, finalista} == {zona_a, zona_b}
        tabla = tabla_reg_region(SR, reg)
        assert len(tabla) == len(SR["grupos"][reg]) and sorted(tabla["Puesto"]) == list(range(1, len(tabla) + 1))
        assert int(tabla.sort_values("Puesto")["id"].iloc[0]) == campeon
    assert all(SR["campeones"][r] is not None for r in REGIONES_REG) and len(SR["ascendidos"]) == len(FINALES_REG)


def test_vista_de_la_region_dividida():
    """La tabla de una región dividida se dibuja con los componentes de siempre."""
    from streamlit.testing.v1 import AppTest

    def app():
        from config import parametros_partido
        from ligas.regional import simular_fecha_reg, tabla_reg_region
        from motor.temporada import crear_estado
        from ui.vista.tablas import colorear_reg, mostrar_tabla

        S, P = crear_estado(), parametros_partido()
        SR = S["reg"]
        while SR["fecha"] < SR["total"]:
            simular_fecha_reg(SR, P, S["rng"])
        for reg in ("Centro", "NOA Sur"):
            mostrar_tabla(tabla_reg_region(SR, reg), colorear_reg)

    at = AppTest.from_function(app, default_timeout=120).run()
    assert not at.exception


def test_regional_el_limite_de_24_se_reevalua_en_cada_temporada(monkeypatch):
    """Una región que baja de 24 deja de dividirse y otra que lo supera empieza a dividirse (y al revés)."""
    import ligas.regional as regional
    from ligas.regional import REG_MAX_LIGA, nueva_estructura_reg, simular_fecha_reg, tabla_reg_region

    S, P = crear_estado(), parametros_partido()
    SR = S["reg"]
    original = regional.region_reg
    assert len(SR["zonas_de"]["Centro"]) == 2 and len(SR["zonas_de"]["NEA Este"]) == 1

    def jugar_regional():
        while SR["fecha"] < SR["total"]:
            simular_fecha_reg(SR, P, S["rng"])
        assert all(c is not None for c in SR["campeones"].values())

    jugar_regional()
    # Temporada siguiente: Centro baja a REG_MAX_LIGA clubes y los que salen pasan a NEA Este, que supera el límite
    sobran = len(SR["grupos"]["Centro"]) - REG_MAX_LIGA
    movidos = [n for n, r in zip(SR["nombres"], SR["region_de"]) if r == "Centro"][:sobran]
    monkeypatch.setattr(regional, "region_reg", lambda nm: "NEA Este" if nm in movidos else original(nm))
    nueva_estructura_reg(SR, S["rng"])
    assert len(SR["grupos"]["Centro"]) <= REG_MAX_LIGA < len(SR["grupos"]["NEA Este"])
    assert SR["zonas_de"]["Centro"] == ["Centro"] and len(SR["zonas_de"]["NEA Este"]) == 2
    assert not any(c.startswith("Centro · Zona") for c in SR["zonas"])       # no queda nada de la división anterior
    jugar_regional()
    assert SR["campeones"]["NEA Este"] in SR["cruces"]["NEA Este"] and "Centro" not in SR["cruces"]
    assert len(tabla_reg_region(SR, "Centro")) == len(SR["grupos"]["Centro"])

    # y de vuelta: cada club vuelve a su región
    monkeypatch.setattr(regional, "region_reg", original)
    nueva_estructura_reg(SR, S["rng"])
    assert len(SR["zonas_de"]["Centro"]) == 2 and SR["zonas_de"]["NEA Este"] == ["NEA Este"]
    jugar_regional()

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


def _jugar_regional(SR, P, rng):
    from ligas.regional import simular_fecha_reg

    while SR["fecha"] < SR["total"]:
        simular_fecha_reg(SR, P, rng)


def test_regional_fase_1_en_subgrupos_y_fase_2_en_la_zona_regional():
    import numpy as np

    from datos.datos_regional import FINALES_REG, REGIONES_REG
    from ligas.regional import (
        REG_FASE1,
        REG_GRUPO_MIN,
        REG_PASAN,
        simular_fecha_reg,
        tabla_reg_region,
        tabla_subgrupo_reg,
    )

    S, P = crear_estado(), parametros_partido()
    SR = S["reg"]
    for reg in REGIONES_REG:                                    # los subgrupos parten la región sin repetir a nadie
        claves = SR["subgrupos_de"][reg]
        if claves:
            todos = np.concatenate([SR["subgrupos"][c] for c in claves])
            assert sorted(todos) == sorted(SR["grupos"][reg])
            assert all(len(SR["subgrupos"][c]) >= REG_GRUPO_MIN for c in claves)
        else:
            assert len(SR["zona2"][reg]) == len(SR["grupos"][reg])
    assert SR["f_fase1"] > 0 and SR["f_liga"] == SR["f_fase1"] + SR["f_fase2"]

    for _ in range(SR["f_fase1"]):
        simular_fecha_reg(SR, P, S["rng"])
    assert SR["f1_cerrada"] and not SR["pj"].any()              # la zona regional arranca con las tablas en cero
    partidos_f1 = [p for p in SR["log"] if p["rotulo"].startswith(REG_FASE1)]
    assert len(partidos_f1) == sum(len(v) * (len(v) - 1) for v in SR["subgrupos"].values())    # ida y vuelta
    for reg in REGIONES_REG:
        claves = SR["subgrupos_de"][reg]
        if not claves:
            continue
        esperados = {int(i) for c in claves for i in tabla_subgrupo_reg(SR, c)["id"].iloc[:REG_PASAN]}
        assert {int(i) for i in SR["zona2"][reg]} == esperados and len(esperados) == REG_PASAN * len(claves)
        for c in claves:                                        # todos jugaron contra todos dos veces
            assert all(SR["stats_f1"]["pj"][i] == 2 * (len(SR["subgrupos"][c]) - 1) for i in SR["subgrupos"][c])

    _jugar_regional(SR, P, S["rng"])
    for reg in REGIONES_REG:
        zona = SR["zona2"][reg]
        assert all(SR["pj"][i] == 2 * (len(zona) - 1) for i in zona)
        tabla = tabla_reg_region(SR, reg)
        assert len(tabla) == len(SR["grupos"][reg]) and sorted(tabla["Puesto"]) == list(range(1, len(tabla) + 1))
        assert int(tabla.sort_values("Puesto")["id"].iloc[0]) == SR["campeones"][reg]
        assert set(tabla["id"].iloc[: len(zona)]) == {int(i) for i in zona}     # los eliminados quedan abajo
    assert all(SR["campeones"][r] is not None for r in REGIONES_REG) and len(SR["ascendidos"]) == len(FINALES_REG)


def test_vista_de_las_tablas_del_regional():
    """Los subgrupos y la zona regional se dibujan con los componentes de siempre."""
    from streamlit.testing.v1 import AppTest

    def app():
        from config import parametros_partido
        from ligas.regional import simular_fecha_reg, tabla_subgrupo_reg, tabla_zona_reg
        from motor.temporada import crear_estado
        from ui.vista.tablas import colorear_reg, mostrar_tabla

        S, P = crear_estado(), parametros_partido()
        SR = S["reg"]
        while SR["fecha"] < SR["total"]:
            simular_fecha_reg(SR, P, S["rng"])
        for reg in ("Centro", "NOA Sur"):
            for clave in SR["subgrupos_de"][reg]:
                mostrar_tabla(tabla_subgrupo_reg(SR, clave), colorear_reg)
            mostrar_tabla(tabla_zona_reg(SR, reg), colorear_reg)

    at = AppTest.from_function(app, default_timeout=120).run()
    assert not at.exception


def test_regional_los_subgrupos_se_rearman_en_cada_temporada(monkeypatch):
    """Una región que se achica deja de dividirse y juega directo la zona; una que crece pasa a dividirse (y al revés)."""
    import ligas.regional as regional
    from ligas.regional import REG_MAX_GRUPOS, REG_PASAN, nueva_estructura_reg, tabla_reg_region

    S, P = crear_estado(), parametros_partido()
    SR = S["reg"]
    original = regional.region_reg
    assert len(SR["subgrupos_de"]["Centro"]) > 1
    _jugar_regional(SR, P, S["rng"])
    assert all(c is not None for c in SR["campeones"].values())

    # Temporada siguiente: Centro queda con 6 clubes y el resto pasa a NEA Este
    centro = [n for n, r in zip(SR["nombres"], SR["region_de"]) if r == "Centro"]
    movidos = set(centro[6:])
    monkeypatch.setattr(regional, "region_reg", lambda nm: "NEA Este" if nm in movidos else original(nm))
    nueva_estructura_reg(SR, S["rng"])
    assert SR["subgrupos_de"]["Centro"] == [] and len(SR["zona2"]["Centro"]) == 6   # juega directo la zona
    assert len(SR["subgrupos_de"]["NEA Este"]) == REG_MAX_GRUPOS                    # tope de subgrupos
    assert not any(c.startswith("Centro · Grupo") for c in SR["subgrupos"])          # nada de la división anterior
    _jugar_regional(SR, P, S["rng"])
    assert all(c is not None for c in SR["campeones"].values())
    assert len(SR["zona2"]["NEA Este"]) == REG_PASAN * REG_MAX_GRUPOS
    assert len(tabla_reg_region(SR, "Centro")) == 6

    # y de vuelta: cada club vuelve a su región
    monkeypatch.setattr(regional, "region_reg", original)
    nueva_estructura_reg(SR, S["rng"])
    assert len(SR["subgrupos_de"]["Centro"]) > 1 and len(SR["subgrupos_de"]["NEA Este"]) > 1
    _jugar_regional(SR, P, S["rng"])

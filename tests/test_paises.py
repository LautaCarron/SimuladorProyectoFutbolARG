"""Países (Argentina y Uruguay): qué competencias son de cada uno y cómo se filtran Calendario y Avisos."""

import pytest

from config import VOLATILIDAD, parametros_partido
from copas.registro import LIGAS_EXTERIOR, REGISTRO
from datos import paises
from datos.ligas_ext import LIGAS_EXT
from motor.calendario import eventos_calendario, jugar_proximo_dia
from motor.progreso import avisos_del_pais_en, marcar_avisos_leidos
from motor.simulacion import simular_todo
from motor.temporada import crear_estado, nueva_temporada


def test_paises_con_argentina_primero():
    assert paises.PAISES[0] == paises.PAIS_BASE == "Argentina"
    assert "Uruguay" in paises.PAISES
    assert paises.PAISES == list(dict.fromkeys(paises.PAISES))


def test_ligas_de_cada_pais():
    assert "Primera División" in paises.ligas_de("Argentina")
    assert "Liga AUF Uruguaya" not in paises.ligas_de("Argentina")
    assert paises.ligas_de("Uruguay") == ["Liga AUF Uruguaya", "Segunda División Profesional"]
    assert paises.ligas_de("Atlántida") == []
    for cfg in LIGAS_EXT:       # cada liga cargada por datos queda en su país
        assert cfg["nombre"] in paises.ligas_de(cfg["pais"])


def test_competencias_propias_sin_internacionales():
    for pais in paises.PAISES:
        assert not paises.competencias_de(pais) & set(paises.COPAS_INTERNACIONALES)
    assert "Copa Argentina" in paises.competencias_de("Argentina")
    assert "Copa Argentina" not in paises.competencias_de("Uruguay")


def test_pais_de_competencia():
    assert paises.pais_de_competencia("Primera Nacional") == "Argentina"
    assert paises.pais_de_competencia("Liga AUF Uruguaya") == "Uruguay"
    assert paises.pais_de_competencia("Copa Libertadores") is None


def test_pais_invalido_vuelve_a_argentina():
    assert paises.validar("Narnia") == "Argentina"
    assert paises.validar("Uruguay") == "Uruguay"


def test_toda_competencia_del_calendario_tiene_pais_o_es_internacional():
    """Si se suma una competencia nueva y no se la asigna a un país, no aparecería en ningún Calendario."""
    S = crear_estado()
    nombres = {liga for _, liga, _, _ in eventos_calendario(S)} | {c.nombre for c in REGISTRO}
    for n in nombres:
        assert n in paises.COPAS_INTERNACIONALES or paises.pais_de_competencia(n), n


def test_calendario_de_cada_pais():
    S = crear_estado()
    eventos = eventos_calendario(S)
    for pais in paises.PAISES:
        assert [e for e in eventos if e[1] in paises.competencias_de(pais)], pais
    uy = {e[1] for e in eventos if e[1] in paises.competencias_de("Uruguay")}
    assert uy == {c.nombre for c in LIGAS_EXTERIOR if c.cfg["pais"] == "Uruguay"}


def _aviso(liga, i=0):
    return {"liga": liga, "fecha": 1, "clave": "clima", "titulo": f"t{i}", "texto": "", "sancion": "", "local": "A",
            "visita": "B", "rotulo": "Fecha 1"}


def test_avisos_por_pais_y_leidos_independientes():
    S = crear_estado()
    S["alertas_hist"] = [dict(_aviso("Primera División"), temp=1), dict(_aviso("Liga AUF Uruguaya", 1), temp=1)]
    actuales = [_aviso("Primera Nacional"), _aviso("Copa Argentina", 2), _aviso("Liga AUF Uruguaya", 3)]
    arg, arg_hist, arg_sin = avisos_del_pais_en(S, actuales, "Argentina")
    uy, uy_hist, uy_sin = avisos_del_pais_en(S, actuales, "Uruguay")
    assert (len(arg), len(arg_hist), arg_sin) == (2, 1, 3)
    assert (len(uy), len(uy_hist), uy_sin) == (1, 1, 2)
    marcar_avisos_leidos(S, "Argentina", 3)           # leer los de un país no toca los del otro
    assert avisos_del_pais_en(S, actuales, "Argentina")[2] == 0
    assert avisos_del_pais_en(S, actuales, "Uruguay")[2] == 2
    marcar_avisos_leidos(S, "Uruguay", 2)
    assert avisos_del_pais_en(S, actuales, "Uruguay")[2] == 0
    assert S["avisos_leidos"] == 3                    # Argentina sigue en la clave de siempre (partidas guardadas)


def test_avisos_de_competencia_desconocida_son_argentinos():
    assert paises.pais_del_aviso({"liga": "Liga de la Quimera"}) == "Argentina"
    assert paises.pais_del_aviso({}) == "Argentina"


@pytest.mark.parametrize("pais", paises.PAISES)
def test_temporada_completa_no_depende_del_pais(pais):
    """El país activo es sólo de pantalla: el motor juega todo igual (y el calendario de cada país sigue completo)."""
    S, P = crear_estado(), parametros_partido()
    jugar_proximo_dia(S, P)
    simular_todo(S, P)
    nueva_temporada(S, VOLATILIDAD)
    assert S["temp"] == 2
    propios = [e for e in eventos_calendario(S) if e[1] in paises.competencias_de(pais)]
    assert propios and not any(e[3] for e in propios)      # temporada nueva: nada jugado todavía

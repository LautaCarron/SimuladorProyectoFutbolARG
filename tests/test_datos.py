"""Pruebas de los datos: que los JSON de datos/json/ estén bien armados y que la web estática los cargue."""

import json
import os
import re

from datos import equipos
from datos.cargador import CARPETA, cargar
from datos.datos_regional import FINALES_REG, REGIONAL, REGIONES_REG

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSONS = sorted(f[:-5] for f in os.listdir(CARPETA) if f.endswith(".json"))


def test_todos_los_json_se_leen():
    assert JSONS
    for nombre in JSONS:
        cargar(nombre)


def test_datos_de_equipos_cierran():
    assert equipos.ERROR_DATOS is None, equipos.ERROR_DATOS


def test_medias_son_numeros():
    for nombre in ("equipos",):
        for categoria, clubes in cargar(nombre).items():
            for club, media in clubes.items():
                assert isinstance(media, (int, float)) and 0 <= media <= 100, f"{categoria}: {club} -> {media!r}"
    assert all(isinstance(x["media"], (int, float)) for x in REGIONAL)


def test_regional_clubes_completos():
    claves = {"nombre", "region", "zona", "final", "provincia", "ciudad", "liga", "escudo", "media"}
    nombres = [x["nombre"] for x in REGIONAL]
    assert len(nombres) == len(set(nombres)), "hay clubes del Regional repetidos"
    for x in REGIONAL:
        assert claves <= set(x), f"{x['nombre']}: faltan {claves - set(x)}"
        assert x["region"] in REGIONES_REG, f"{x['nombre']}: región desconocida {x['region']!r}"
    assert sorted(r for par in FINALES_REG for r in par) == sorted(REGIONES_REG)


def test_la_web_estatica_carga_todos_los_archivos_de_datos():
    """Si se suma un JSON y no está en ARCHIVOS de index.html, la web estática se rompe."""
    html = open(os.path.join(RAIZ, "index.html"), encoding="utf-8").read()
    listados = set(re.findall(r'"(datos/[\w/]+\.(?:py|json))"', html))
    existentes = {"datos/json/" + n + ".json" for n in JSONS} | {"datos/cargador.py"}
    assert existentes <= listados, f"faltan en index.html: {sorted(existentes - listados)}"


def test_json_con_formato_valido():
    for nombre in JSONS:
        with open(os.path.join(CARPETA, nombre + ".json"), encoding="utf-8") as f:
            json.load(f)

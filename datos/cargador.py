"""Lectura de los archivos de datos (datos/json/*.json).

Los datos (equipos, medias, escudos, palmarés, regional...) viven en JSON y no en código Python: se editan
sin tocar la lógica. Cada módulo de `datos/` los lee con `cargar("nombre")` y los expone con los mismos nombres
de siempre, así que el resto del proyecto no se entera.
"""

import json
import os

CARPETA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "json")


def cargar(nombre):
    """Contenido de datos/json/<nombre>.json. Si el archivo está mal escrito, el error dice cuál y en qué línea."""
    ruta = os.path.join(CARPETA, nombre + ".json")
    with open(ruta, encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"datos/json/{nombre}.json está mal escrito (línea {e.lineno}, columna {e.colno}): {e.msg}") from e

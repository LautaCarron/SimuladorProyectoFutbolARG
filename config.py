"""Configuración global: parámetros fijos de la simulación y detección del entorno.

Antes estos valores vivían sueltos en simuladorafa.py. Acá hay un único lugar donde cambiarlos.
"""

import os
import sys

# Entorno -----------------------------------------------------------------------------------------------
ES_WEB = sys.platform == "emscripten"      # versión estática (stlite) que corre en el navegador
TODAS_LAS_PESTANAS = os.environ.get("AFA_TODAS_LAS_PESTANAS") == "1"   # sólo para las pruebas automáticas

# Parámetros de la simulación (ya no se editan desde la barra lateral) --------------------------------
SORPRESA = 6.0            # nivel de sorpresas de los partidos
VOLATILIDAD = 2.5         # cuánto cambia la media de cada equipo al pasar de temporada
ACUMULAR_PUNTOS = True    # Primera arrastra los puntos de la fase 1 a las zonas


def parametros_partido():
    """Diccionario `P` que reciben las funciones de simulación de partidos."""
    return {"sorpresa": SORPRESA}

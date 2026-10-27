"""Palmarés histórico oficial de cada liga y copa, hasta 2025 inclusive (la temporada 1 del
simulador es 2026, así que lo que se gana desde ahí lo suman las temporadas simuladas).
"""

import copy

from datos.cargador import cargar

# Cada palmarés tiene su descripción (de dónde sale y hasta qué año llega) en datos/json/palmares.json
PALMARES = {k: v["titulos"] for k, v in cargar("palmares").items()}


def palmares_inicial():
    """Copia del palmarés histórico para una partida nueva (cada partida suma sus títulos)."""
    return copy.deepcopy(PALMARES)
"""Contexto que reciben las pestañas: `render(ctx)`.

Antes `ctx` era un SimpleNamespace armado con TODAS las variables globales de simuladorafa.py (más de 150 nombres,
varios "privados"). Ahora es un objeto con los campos que las pestañas realmente usan.
"""

import datetime as dt
from dataclasses import dataclass

from config import TODAS_LAS_PESTANAS
from motor.progreso import Progreso
from ui.pestanas import Pestanas


@dataclass
class Contexto:
    S: dict                         # estado de la partida
    P: dict                         # parámetros de los partidos
    acumular: bool                  # Primera arrastra los puntos de la fase 1 a las zonas
    modo_mgr: bool
    manager: dict | None            # estado del manager (st.session_state["manager"]); None en modo simulación
    progreso: Progreso
    pestanas: Pestanas
    avisos: list                    # avisos de esta temporada
    total_avisos: int
    sin_leer: int
    prox: dict                      # próximo evento de cada competencia: {competición: (día, n)}
    hoy: dt.date | None             # próximo día con partidos
    todas_pestanas: bool = TODAS_LAS_PESTANAS

    # Atajos al estado de cada competencia (siempre salen de S: no quedan desactualizados)
    @property
    def club(self):
        """Club que dirige el manager (None si está libre o en modo simulación)."""
        return self.manager.get("club") if self.manager else None

    @property
    def SB(self):
        return self.S["b"]

    @property
    def SF(self):
        return self.S["f"]

    @property
    def SR(self):
        return self.S["reg"]

    @property
    def SC(self):
        return self.S["copa"]

    @property
    def SS(self):
        return self.S["supercopa"]

    def abierta(self, *tabs):
        """¿Está a la vista? (la pestaña y sus pestañas madre abiertas)."""
        return self.todas_pestanas or all(t.open is not False for t in tabs)

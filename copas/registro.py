"""Registro de competencias por rondas: Copa Argentina, Supercopa Argentina y Mundial de Clubes.

Cada competencia declara en UN solo lugar cómo se juega: cuál es su estado en S, qué ronda toca,
cómo se juega, qué día cae cada ronda, qué partidos muestra el calendario y cómo se cierra la
temporada. El calendario, "Simular todo", "Nueva temporada", el historial y el palmarés recorren
REGISTRO en vez de nombrar cada competencia a mano.

Para sumar una competencia nueva: escribir su lógica en un módulo propio, agregar acá una clase
(heredando de PorRondas o de Competencia) y sumarla a REGISTRO. Sin Streamlit: es motor puro.
Importa copas, mundial y fechas_ligas (que no dependen de él): no hay importaciones circulares.
"""

import datetime as dt

from copas.argentina import (COPA_RONDAS, nueva_supercopa, rivales_supercopa, simular_ronda_copa, simular_supercopa,
                   supercopa_lista)
from motor.fechas import desde as _desde, dia_liga, total_liga
from copas.mundial import (RONDAS as RONDAS_MUNDIAL, actualizar_ratings, cerrar_temporada, es_temporada_mundial,
                     nuevo_mundial, partidos_ronda, simular_ronda_mundial, sortear_mundial)


def _anio(S):
    return 2025 + S["temp"]        # la temporada 1 del simulador es 2026


class Competencia:
    """Interfaz que cumple cada competencia del registro."""
    nombre = ""            # nombre en el calendario y en los partidos (campo "liga")
    clave = ""             # clave de S donde vive su estado
    col_historial = None   # columna de campeones del Historial (None: la maneja otro código)
    hist = None            # clave de S con el palmarés acumulado (None: la maneja otro código)
    crea_estado = False    # True: Nueva temporada (y la partida nueva) arman S[clave] con nueva()

    def estado(self, S):
        return S[self.clave]

    def nueva(self, S, rng):
        """Estado de la temporada nueva (se asigna a S[clave])."""
        raise NotImplementedError

    def activa(self, S):
        """Falso si esta temporada no se juega (p. ej. el Mundial fuera de su año)."""
        return True

    def total(self, S):
        raise NotImplementedError

    def hechas(self, S):
        """Rondas ya jugadas."""
        raise NotImplementedError

    def pendiente(self, S):
        """Número de la próxima ronda que se puede jugar, o None si no hay ninguna."""
        raise NotImplementedError

    def jugar(self, S, P, rng):
        """Juega la próxima ronda pendiente."""
        raise NotImplementedError

    def jugar_todo(self, S, P, rng):
        """Juega todo lo que se pueda jugar ahora (con tope por seguridad)."""
        for _ in range(100):
            if self.pendiente(S) is None:
                return
            self.jugar(S, P, rng)

    def terminada(self, S):
        return self.hechas(S) >= self.total(S)

    def log(self, S):
        return S.get(self.clave, {}).get("log", [])

    def cruces(self, S, n):
        """Partidos aún no jugados de la ronda n: [(local, visita, rótulo, competencia)]."""
        return []

    def rotulo(self, S, n):
        return f"Ronda {n}"

    def dia(self, S, n):
        raise NotImplementedError

    def campeon(self, S):
        return None

    def cerrar(self, S, rng):
        """Al terminar la temporada (antes de armar la siguiente)."""


class PorRondas(Competencia):
    """Competencia cuyo estado tiene "ronda", "total" y "log" (Copa Argentina, Mundial)."""

    def total(self, S):
        return self.estado(S)["total"]

    def hechas(self, S):
        return self.estado(S)["ronda"]

    def pendiente(self, S):
        E = self.estado(S)
        return E["ronda"] + 1 if self.activa(S) and E["ronda"] < E["total"] else None

    def terminada(self, S):
        E = self.estado(S)
        return (not self.activa(S)) or E["ronda"] >= E["total"]


# ----------------------------------------------------------------------------
class CopaArgentina(PorRondas):
    nombre = "Copa Argentina"
    clave = "copa"
    DIAS = [(3, 4), (4, 8), (5, 13), (6, 24), (8, 12), (9, 23), (11, 4)]     # miércoles

    def activa(self, S):
        return bool(S["copa"]["sorteada"])

    def jugar(self, S, P, rng):
        simular_ronda_copa(S["copa"], P, rng)

    def cruces(self, S, n):
        SC = S["copa"]
        if n - 1 >= len(SC["cuadro"]):
            return []
        nom = SC["nombres"]
        return [(nom[m["a"]], nom[m["b"]], "", "") for m in SC["cuadro"][n - 1]]

    def rotulo(self, S, n):
        return COPA_RONDAS[n - 1]

    def dia(self, S, n):
        mes, dia = self.DIAS[min(n, len(self.DIAS)) - 1]
        return _desde(_anio(S), mes, dia, 2)

    def campeon(self, S):
        SC = S["copa"]
        return SC["nombres"][SC["campeon"]] if SC["campeon"] is not None else None


class SupercopaArgentina(Competencia):
    nombre = "Supercopa Argentina"
    clave = "supercopa"
    col_historial = "Supercopa"
    hist = "hist_super"
    crea_estado = True

    def nueva(self, S, rng):
        return nueva_supercopa()

    def total(self, S):
        return 1

    def hechas(self, S):
        return 1 if S["supercopa"]["jugada"] else 0

    def pendiente(self, S):
        return 1 if supercopa_lista(S) else None

    def jugar(self, S, P, rng):
        simular_supercopa(S, P, rng)

    def terminada(self, S):
        return bool(S["supercopa"]["jugada"])

    def cruces(self, S, n):
        if not supercopa_lista(S):
            return []
        a, _, _, b, _, _ = rivales_supercopa(S)
        return [(a, b, "Final", "Final")]

    def rotulo(self, S, n):
        return "Final"

    def dia(self, S, n):
        """Miércoles siguiente a la última fecha de Primera."""
        return dia_liga(S, "Primera División", total_liga(S, "Primera División")) + dt.timedelta(days=3)

    def campeon(self, S):
        return S["supercopa"]["campeon"]


class MundialDeClubes(PorRondas):
    nombre = "Mundial de Clubes"
    clave = "mundial"
    col_historial = "Mundial"
    hist = "hist_mundial"
    crea_estado = True
    DIAS = [(6, 15), (6, 19), (6, 23), (6, 28), (7, 4), (7, 8), (7, 13)]     # 3 de grupos y 4 eliminatorias

    def nueva(self, S, rng):
        """Cada 4 temporadas (2029 = temporada 4) se arman clasificados y grupos."""
        if S["temp"] > 1:
            actualizar_ratings(S, rng)
        return sortear_mundial(S, rng) if es_temporada_mundial(S["temp"]) else nuevo_mundial()

    def activa(self, S):
        return bool(S.get("mundial", {}).get("sorteado"))

    def jugar(self, S, P, rng):
        simular_ronda_mundial(S, P, rng)

    def cruces(self, S, n):
        return partidos_ronda(S["mundial"], n)

    def rotulo(self, S, n):
        return RONDAS_MUNDIAL[n - 1]

    def dia(self, S, n):
        mes, dia = self.DIAS[min(n, len(self.DIAS)) - 1]
        return dt.date(_anio(S), mes, dia)

    def campeon(self, S):
        return S.get("mundial", {}).get("campeon")

    def cerrar(self, S, rng):
        """Registra los campeones continentales del año y los puntos del ranking CONMEBOL."""
        cerrar_temporada(S, rng)


# El orden importa: es el orden en que "Simular todo" las juega y en que el calendario las lista.
REGISTRO = [CopaArgentina(), SupercopaArgentina(), MundialDeClubes()]
_POR_NOMBRE = {c.nombre: c for c in REGISTRO}


def por_nombre(nombre):
    """La competencia del registro con ese nombre (o None si es una liga u otra copa)."""
    return _POR_NOMBRE.get(nombre)

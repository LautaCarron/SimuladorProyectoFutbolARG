"""Países del simulador y qué competencias pertenece a cada uno. Sin Streamlit.

Argentina es el país base (todo el fútbol argentino vive en `S` desde siempre); los demás (hoy Uruguay) salen de sus
archivos de liga (datos/ligas_ext.py). La pestaña Mundo elige un "país activo" y Ligas, Copas, Calendario, Historial
y Avisos muestran sólo lo de ese país, más las copas internacionales donde puede jugar.

Para sumar un país: crear su liga (docs/LIGAS_EXTERIOR.md). Acá aparece solo: no hay nada que tocar.

  PAISES                       ["Argentina", "Uruguay", ...] (Argentina siempre primero)
  ligas_de(pais)               nombres de sus ligas ("Primera División", "Liga AUF Uruguaya"...)
  copas_nacionales_de(pais)    sus copas propias ("Copa Argentina"..., "Copa AUF Uruguay")
  COPAS_INTERNACIONALES        las que pueden jugar clubes de cualquier país (CONMEBOL y Mundial de Clubes)
  competencias_de(pais)        ligas + copas propias (lo que muestra el Calendario)
  pais_de_competencia(nombre)  a qué país pertenece una competencia (None si es internacional)
"""

from datos.clubes_int import BANDERA
from datos.ligas_ext import LIGAS_EXT

PAIS_BASE = "Argentina"

LIGAS_ARGENTINA = ("Primera División", "Primera Nacional", "Federal A", "Federal B", "Primera B", "Primera C",
                   "Promocional Amateur", "Regional Amateur")
COPAS_ARGENTINA = ("Copa Argentina", "Supercopa Argentina", "Regionales")
COPAS_EXTERIOR = {"Uruguay": ("Copa AUF Uruguay", "Supercopa Uruguaya")}        # copas nacionales de los países con liga simulada
COPAS_INTERNACIONALES = ("Copa Libertadores", "Copa Sudamericana", "Recopa Sudamericana", "Mundial de Clubes")

PAISES = [PAIS_BASE, *dict.fromkeys(c["pais"] for c in LIGAS_EXT)]

_LIGAS_EXT_DE = {}
for _c in LIGAS_EXT:
    _LIGAS_EXT_DE.setdefault(_c["pais"], []).append(_c["nombre"])
_PAIS_DE = {**{n: PAIS_BASE for n in (*LIGAS_ARGENTINA, *COPAS_ARGENTINA)},
            **{c["nombre"]: c["pais"] for c in LIGAS_EXT},
            **{n: pais for pais, copas in COPAS_EXTERIOR.items() for n in copas}}


def bandera(pais):
    return BANDERA.get(pais, "")


def etiqueta(pais):
    """Texto del país con su bandera: "🇺🇾 Uruguay"."""
    return f"{bandera(pais)} {pais}".strip()


def ligas_de(pais):
    """Nombres de las ligas del país (el Federal B figura aunque todavía no se haya creado en el Modo dios)."""
    return list(LIGAS_ARGENTINA) if pais == PAIS_BASE else list(_LIGAS_EXT_DE.get(pais, []))


def copas_nacionales_de(pais):
    return list(COPAS_ARGENTINA) if pais == PAIS_BASE else list(COPAS_EXTERIOR.get(pais, ()))


def competencias_de(pais):
    """Ligas y copas propias del país, sin las internacionales (es lo que lista el Calendario)."""
    return {*ligas_de(pais), *copas_nacionales_de(pais)}


def pais_de_competencia(nombre):
    """País dueño de la competencia, o None si es internacional (Libertadores, Sudamericana, Recopa, Mundial)."""
    return _PAIS_DE.get(nombre)


def pais_del_aviso(aviso):
    """País al que pertenece un aviso del Tribunal de Disciplina (por su competencia; lo desconocido es argentino)."""
    return pais_de_competencia(aviso.get("liga")) or PAIS_BASE


def avisos_del_pais(avisos, pais):
    return [a for a in avisos if pais_del_aviso(a) == pais]


def validar(pais):
    """País válido (si llega algo raro, por ejemplo de una partida vieja, se vuelve al país base)."""
    return pais if pais in PAISES else PAIS_BASE

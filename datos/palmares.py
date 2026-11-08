"""Palmarés históricos por competencia.

Los registros argentinos se mantienen en palmares.json. Cada país extranjero puede
agregar datos en palmares_<clave>.json (por ejemplo, palmares_uy.json). Las claves
son las mismas que usa cada competencia en el estado de la partida (hist_ext_uy,
hist_copa_uy, etc.). Si el archivo no existe, el país empieza con palmarés vacío.
"""

import copy

from datos.cargador import cargar
from datos.ligas_ext import LIGAS_EXT


def _leer(nombre):
    """Carga un archivo de palmarés; permite que países nuevos todavía no tengan archivo."""
    try:
        return cargar(nombre)
    except FileNotFoundError:
        return {}


# Datos históricos argentinos.
PALMARES = {k: v.get("titulos", {}) for k, v in _leer("palmares").items()}

# Datos históricos de países extranjeros. Se carga una sola vez por país (no por división).
for _cfg in LIGAS_EXT:
    if int(_cfg.get("divisional", 1)) != 1:
        continue
    _historicos = _leer(f"palmares_{_cfg['clave']}")
    for _clave, _datos in _historicos.items():
        PALMARES[_clave] = _datos.get("titulos", {})


def palmares_inicial():
    """Copia independiente del palmarés histórico para una partida nueva."""
    return copy.deepcopy(PALMARES)

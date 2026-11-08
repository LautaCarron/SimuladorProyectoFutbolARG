"""Clubes de primera división de los otros países de la CONMEBOL (con licencia para las copas
internacionales): nombre, país, media inicial y escudo (ESPN). Cada temporada los cupos de
cada país se reparten al azar entre sus clubes (los más fuertes entran más seguido)."""

from datos.cargador import cargar
from datos.ligas_ext import CLUBES_LIGAS, OSCUROS_LIGAS


_D = cargar("clubes_int")     # datos/json/clubes_int.json
CLUBES_INT = [(c["nombre"], c["pais"], c["media"], c["escudo"]) for c in _D["clubes"]] + CLUBES_LIGAS
# (los países con liga propia, como Uruguay, vienen de su archivo: datos/ligas_ext.py)
PAISES = _D["paises"]
BANDERA = _D["bandera"]
# escudos de borde oscuro (contorno claro en modo oscuro)
OSCUROS_INT = _D["oscuros"] + OSCUROS_LIGAS

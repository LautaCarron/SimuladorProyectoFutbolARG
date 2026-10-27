"""Torneo Regional Amateur: clubes, zonas, regiones y cruces por el ascenso.

Los datos están en datos/json/:
  regional.json        clubes con zona (generado del JSON oficial del torneo), regiones, finales y grupo del Federal A
  regional_extra.json  clubes sueltos que se suman a mano (sin zona, media 10): nombre, region, provincia, ciudad,
                       liga y, si hay, escudo
"""

from datos.cargador import cargar

_R = cargar("regional")

# Cada club: nombre, región (de las 12), zona de la fase de zonas (región original + número),
# final por el ascenso que juega su región, datos del club, escudo y media inicial.
REGIONAL = list(_R["clubes"])

# Clubes sumados a mano, sin zona todavía: van a "<región> · Sin zona", con la final de su región y media 10.
_FINAL_REG = _R["final_de_region"]
REGIONAL += [{"nombre": x["nombre"], "region": x["region"], "zona": x["region"] + " · Sin zona",
              "final": _FINAL_REG[x["region"]], "provincia": x["provincia"], "ciudad": x["ciudad"],
              "liga": x["liga"], "escudo": x.get("escudo", ""), "media": 10.0}
             for x in cargar("regional_extra")]

# Las 12 regiones, ordenadas de a pares: cada par juega una de las 6 finales por el ascenso
REGIONES_REG = _R["regiones"]
FINALES_REG = [tuple(par) for par in _R["finales"]]
# Grupo del Federal A al que va cada región cuando uno de sus clubes asciende
GRUPO_FEDERAL_REG = _R["grupo_federal"]

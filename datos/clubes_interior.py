"""Ciudad, provincia y liga local de los clubes del interior que juegan en Primera, Primera Nacional
y Federal A (los del Regional Amateur ya traen estos datos en datos/datos_regional.py).

Formato: nombre del club -> (ciudad, provincia, liga). Los nombres de las ligas siguen el mismo criterio
que el JSON del Regional ("Liga Cordobesa", "Liga de Pergamino"...), así que si un club desciende hasta
el Regional se queda en su misma liga. Los de la lista "revisar" son los que conviene revisar.
"""

from datos.cargador import cargar


_D = cargar("clubes_interior")      # datos/json/clubes_interior.json
DATOS_INTERIOR = {n: tuple(v) for seccion in _D["secciones"].values() for n, v in seccion.items()}
REVISAR = set(_D["revisar"])           # los que conviene revisar


_REG = None


def datos_club(nombre):
    """{'ciudad', 'provincia', 'liga'} del club, o None si no es del interior.

    Sirve para cualquier club del interior: Primera, Primera Nacional, Federal A y Regional Amateur."""
    global _REG
    from datos import club_propio
    if (propio := club_propio.datos(nombre)):          # el club que creó la persona (ver datos/club_propio.py)
        return propio
    if nombre in DATOS_INTERIOR:
        c, p, lg = DATOS_INTERIOR[nombre]
        return {"ciudad": c, "provincia": p, "liga": lg}
    if _REG is None:
        from datos.datos_regional import REGIONAL
        _REG = {x["nombre"]: {"ciudad": x["ciudad"], "provincia": x["provincia"], "liga": x["liga"]}
                for x in REGIONAL}
    return _REG.get(nombre)

"""Ligas de primera división de otros países (Uruguay, y más adelante Brasil y las demás).

Un archivo por país en datos/json/liga_<país>.json con TODO lo de esa liga: el formato, cuántos suben y bajan, el
calendario y los clubes de primera y de segunda con su media y su escudo. Para sumar un país: crear su archivo, agregar
su nombre a ARCHIVOS (acá) y a ARCHIVOS de index.html. Ver docs/LIGAS_EXTERIOR.md.

Los clubes de estos archivos se suman a CLUBES_INT (datos/clubes_int.py) para que sigan jugando las copas CONMEBOL con
la misma media, así que un club tiene una sola media en toda la partida.

La segunda división puede ser de dos maneras:
  * Sólo una lista de clubes (la "reserva"): no se juega; de ahí suben los ascendidos (al azar, con más chances los de
    mejor media) y ahí van los que descienden.
  * Una liga simulada: si el archivo trae `segunda_liga` ({nombre, formato, descensos, calendario}), la segunda se
    juega como una liga más (su entrada en LIGAS_EXT lleva `divisional` = 2 y `superior` = la clave de la primera) y los
    que suben salen de su tabla. Uruguay es el primer caso (ligas/uruguay_segunda.py).
"""

from datos.cargador import cargar

ARCHIVOS = ["liga_uruguay", "liga_brasil"]          # un archivo por país (datos/json/<nombre>.json)

LIGAS_EXT = []                       # configuración de cada liga; "clubes" = los que la juegan, "reserva" = segunda sin simular
CLUBES_LIGAS = []                    # (nombre, país, media, escudo) de todos los clubes de estos archivos
OSCUROS_LIGAS = []                   # escudos de borde oscuro
for _nombre in ARCHIVOS:
    _d = cargar(_nombre)
    _cfg = {k: v for k, v in _d.items() if k not in ("primera", "segunda", "tercera", "segunda_liga", "oscuros")}
    _cfg["clubes"] = [c["nombre"] for c in _d["primera"]]
    _cfg["reserva"] = [c["nombre"] for c in _d["segunda"]]
    _cfg["tercera"] = [c["nombre"] for c in _d.get("tercera", [])]      # tercera división falsa: no se simula (ver abajo)
    _cfg["divisional"] = 1
    LIGAS_EXT.append(_cfg)
    if _d.get("segunda_liga"):       # segunda simulada: una liga más, que cuelga de la primera
        _seg = {"clave": _cfg["clave"] + "2", "pais": _d["pais"], "ascensos": int(_cfg.get("ascensos", 0)),
                **_d["segunda_liga"], "clubes": list(_cfg["reserva"]), "reserva": [], "divisional": 2,
                "superior": _cfg["clave"], "tercera": list(_cfg["tercera"])}
        _cfg["inferior"] = _seg["clave"]
        LIGAS_EXT.append(_seg)
    CLUBES_LIGAS += [(c["nombre"], _d["pais"], c["media"], c["escudo"])
                     for c in _d["primera"] + _d["segunda"] + _d.get("tercera", [])]
    OSCUROS_LIGAS += _d.get("oscuros", [])

CONFIG = {c["clave"]: c for c in LIGAS_EXT}
CONFIG_POR_CLAVE = CONFIG
MEDIA_CLUB = {n: float(m) for n, _, m, _ in CLUBES_LIGAS}


def clubes_de_la_liga(cfg):
    """Todos los clubes de la liga de `cfg`, de su reserva (si la segunda no se juega, los de segunda) y de su tercera
    división falsa (si la tiene)."""
    return list(cfg["clubes"]) + list(cfg["reserva"]) + list(cfg.get("tercera", []))


def clave_clubes(cfg):
    """Clave con la que S["ext_clubes"] guarda quién juega esta liga: el país para la primera ("Uruguay") y
    "<país>|<divisional>" para las de abajo ("Uruguay|2")."""
    return cfg["pais"] if cfg.get("divisional", 1) == 1 else f"{cfg['pais']}|{cfg['divisional']}"


def clave_tercera(cfg):
    """Clave de S["ext_clubes"] con los clubes de la tercera división falsa del país ("Uruguay|3")."""
    return f"{cfg['pais']}|3"


def errores():
    """Problemas de los archivos de liga (lista vacía si todo cierra); los muestra la prueba de datos."""
    out, vistos = [], {}
    for cfg in LIGAS_EXT:
        k = cfg["clave"]
        if cfg.get("divisional", 1) > 1:             # liga de abajo: sus clubes ya se contaron en la de arriba
            arriba = CONFIG_POR_CLAVE.get(cfg.get("superior"))
            if arriba is None:
                out.append(f"{k}: su liga de arriba ('{cfg.get('superior')}') no existe")
            elif set(cfg["clubes"]) != set(arriba["reserva"]):
                out.append(f"{k}: sus clubes no son los de la segunda de '{arriba['clave']}'")
            if cfg.get("ascensos", 0) > len(cfg["clubes"]):
                out.append(f"{k}: suben más clubes de los que hay en la liga")
            if cfg.get("descensos", 0) > len(cfg["clubes"]):
                out.append(f"{k}: bajan más clubes de los que hay en la liga")
            if cfg.get("descensos", 0) > len(cfg.get("tercera", [])):
                out.append(f"{k}: bajan {cfg['descensos']} pero la tercera división tiene {len(cfg.get('tercera', []))} clubes")
            continue
        for n in clubes_de_la_liga(cfg):
            if n in vistos:
                out.append(f"{k}: '{n}' también está en '{vistos[n]}'")
            vistos[n] = k
        if cfg.get("ascensos", 0) > len(cfg["reserva"]):
            out.append(f"{k}: suben {cfg['ascensos']} pero la segunda tiene {len(cfg['reserva'])} clubes")
        if cfg.get("descensos", 0) > len(cfg["clubes"]):
            out.append(f"{k}: bajan más clubes de los que hay en primera")
        if cfg.get("inferior") and cfg.get("ascensos", 0) != cfg.get("descensos", 0):
            out.append(f"{k}: con segunda simulada tienen que subir y bajar la misma cantidad "
                       f"({cfg.get('ascensos', 0)} y {cfg.get('descensos', 0)})")
    claves = [c["clave"] for c in LIGAS_EXT]
    if len(set(claves)) != len(claves):
        out.append("hay claves de liga repetidas")
    return out

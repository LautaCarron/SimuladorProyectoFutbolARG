import numpy as np
import pytest

from copas import conmebol
from datos.clubes_int import CLUBES_INT, PAISES


def _estado_prueba(pais_campeon):
    argentinos = [f"Club argentino {i}" for i in range(1, 21)]
    clubes_por_pais = {
        pais: [nombre for nombre, p, _, _ in CLUBES_INT if p == pais]
        for pais in PAISES
    }
    campeon_externo = clubes_por_pais[pais_campeon][0]
    clasif = {
        "grupos": [(n, f"Primera 2026: {i}°") for i, n in enumerate(argentinos[:5], 1)],
        "previa": [(argentinos[10], "Primera 2026: 11°")],
        "sud": [(n, f"Primera 2026: {i}°") for i, n in enumerate(argentinos[5:10], 6)]
               + [(argentinos[12], "Campeón Copa Argentina")],
        "orden": argentinos,
        "temp_tabla": 2026,
        "campeon_lib": argentinos[0],
        "campeon_sud": campeon_externo,
    }
    vacia = {"nombres": [], "r": []}
    return {
        "int_clasif": clasif,
        "rating_int": {n: float(m) for n, _, m, _ in CLUBES_INT},
        "ext_mov": {p: {"orden": clubes_por_pais[p]} for p in PAISES},
        "ext_clubes": clubes_por_pais,
        "ext_copa": {},
        "ext_copa_sub": {},
        "nombres": [],
        "r": [],
        "b": dict(vacia),
        "f": dict(vacia),
        "pb": dict(vacia),
        "pc": dict(vacia),
        "reg": dict(vacia),
        "fb": None,
    }, argentinos, campeon_externo, clubes_por_pais


@pytest.mark.parametrize("pais", PAISES)
def test_campeon_sudamericana_recibe_plaza_y_su_cupo_se_reasigna(pais):
    S, argentinos, campeon, clubes_por_pais = _estado_prueba(pais)
    conmebol.nuevas_internacionales(S, np.random.default_rng(17))

    lib = S["int"]["lib"]
    sud = S["int"]["sud"]
    cupos_base = conmebol.CUPOS_LIB_GRUPOS[pais]

    assert campeon in lib["directos"]
    assert len([n for n in lib["directos"] if n in clubes_por_pais[pais]]) == cupos_base + 1
    assert len(lib["via"]) == 47
    assert len(lib["directos"]) == 28
    assert len(lib["f2_directos"]) == 13
    assert len(sud["via"]) == 44
    assert len(set(lib["via"])) == len(lib["via"])
    assert set(lib["via"]).isdisjoint(set(sud["via"]))

    # El campeón argentino que ya tenía plaza doméstica también se promueve y su vacante se repone.
    assert argentinos[0] in lib["directos"]
    assert argentinos[11] in lib["directos"]
    assert argentinos[0] not in sud["via"]

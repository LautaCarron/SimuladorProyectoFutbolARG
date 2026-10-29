"""Promocional Amateur con 25 equipos o más: dos zonas, ida y vuelta, sin desempates y con los ascensos que salen de
cada zona (ver ligas/simples.py). Con 24 o menos sigue siendo una sola liga ida y vuelta."""

import numpy as np
import pytest

from config import VOLATILIDAD, parametros_partido
from ligas.simples import (
    ASC_MAX,
    cfg_simple,
    hay_zonas,
    nueva_estructura_liga,
    simular_fecha_liga,
    tabla_pd,
    tablas_zonas,
)
from motor.simulacion import simular_todo
from motor.temporada import crear_estado, nueva_temporada

NOMBRE = "Promocional Amateur"


def _promocional(n, ascensos, semilla=1):
    """Estado con el Promocional de `n` equipos y `ascensos` elegidos en el Modo dios, sin jugar."""
    S = crear_estado()
    S["rng"] = np.random.default_rng(semilla)
    L = S["pd"]
    L["nombres"] = [f"Club {i}" for i in range(n)]
    L["r"] = np.random.default_rng(semilla).uniform(15, 35, n)
    cfg = cfg_simple(S, "pd")
    cfg["directos"], cfg["reducido"] = ascensos, False
    nueva_estructura_liga(L, S["rng"], S, "pd")
    return S, L


def _jugar(S, L):
    P = parametros_partido()
    while L["fecha"] < L["total"]:
        simular_fecha_liga(L, P, S["rng"], NOMBRE, tabla_pd)


def test_con_24_equipos_o_menos_es_una_sola_liga_ida_y_vuelta():
    S, L = _promocional(24, 2)
    assert not hay_zonas(24, "pd") and L["zonas"] is None
    assert L["total"] == 2 * 23
    _jugar(S, L)
    assert all(L["pj"] == 46)


@pytest.mark.parametrize("n", [25, 26, 31, 40])
def test_con_25_o_mas_hay_dos_zonas_ida_y_vuelta(n):
    S, L = _promocional(n, 2)
    za, zb = L["zonas"]
    assert sorted(za + zb) == list(range(n)) and (len(za), len(zb)) == ((n + 1) // 2, n // 2)
    _jugar(S, L)
    for zona in (za, zb):
        assert all(L["pj"][i] == 2 * (len(zona) - 1) for i in zona)        # ida y vuelta dentro de la zona
    # nadie juega contra el de la otra zona en la liga regular
    otra = {i: set(zb) if i in za else set(za) for i in range(n)}
    assert all(p["visita"] not in {f"Club {j}" for j in otra[int(p["local"].split()[1])]}
               for p in L["log"] if not p["neutral"])


def test_sin_desempates_solo_una_fecha_mas_con_las_finales():
    S, L = _promocional(26, 3)
    _jugar(S, L)
    assert L["total"] == L["fechas_zona"] + 1
    assert not any("Desempate" in p["rotulo"] for p in L["log"])
    assert not L["desempate_pendiente"]


@pytest.mark.parametrize("k", range(0, ASC_MAX + 1))
def test_ascensos_segun_la_cantidad_elegida(k):
    S, L = _promocional(27, k, semilla=10 + k)
    _jugar(S, L)
    orden, final = L["orden_zonas"], L["playoffs"][0]
    assert (final["a"], final["b"]) == (orden[0][0], orden[1][0])            # la final es entre los ganadores de zona
    assert L["campeon"] in (final["a"], final["b"])
    assert len(L["ascendidos"]) == len(set(L["ascendidos"])) == k
    if k == 1:                                                              # sube el campeón de esa final
        assert L["ascendidos"] == [L["campeon"]]
    if k >= 2:                                                              # los k // 2 primeros de cada zona
        p = k // 2
        assert set(orden[0][:p]) | set(orden[1][:p]) <= set(L["ascendidos"])
    if k >= 3 and k % 2:                                                    # el último sube por un partido entre los que siguen
        cruce = L["playoffs"][1]
        assert (cruce["a"], cruce["b"]) == (orden[0][k // 2], orden[1][k // 2])
        assert L["ascendidos"][-1] == cruce["gana"]
    else:
        assert len(L["playoffs"]) == 1


def test_pasa_el_mejor_de_la_zona_por_diferencia_de_gol_si_empatan_en_puntos():
    S, L = _promocional(26, 2, semilla=5)
    _jugar(S, L)
    for dfz, orden in zip(tablas_zonas(L), L["orden_zonas"]):
        esperado = dfz.sort_values(["Pts", "DG", "GF"], ascending=False)["id"].tolist()
        assert orden == esperado


def test_temporada_completa_y_pase_con_el_promocional_en_zonas():
    """El Promocional llega a 25 o más desde el Modo dios (la C baja de más y el Promocional no sube a nadie) y las
    temporadas siguen con las zonas, el calendario, los ascensos y el pase sin duplicar clubes."""
    S, P = crear_estado(), parametros_partido()
    cfg_simple(S, "pc")["descensos"], cfg_simple(S, "pd")["directos"] = 8, 0
    con_zonas = 0
    for _ in range(4):
        simular_todo(S, P)
        L = S["pd"]
        if L["zonas"] is not None:
            con_zonas += 1
            assert len(L["ascendidos"]) == L["plan"]["directos"]
        campeon = L["nombres"][L["campeon"]]
        nueva_temporada(S, VOLATILIDAD)
        assert S["campeones"][-1][NOMBRE] == campeon
        todos = [n for lig in (S, S["b"], S["f"], S["pb"], S["pc"], S["pd"], S["reg"]) for n in lig["nombres"]]
        assert len(todos) == len(set(todos))
    assert con_zonas >= 1

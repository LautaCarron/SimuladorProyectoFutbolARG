"""Regionales: copa opcional con torneos por zona (copas/regionales.py)."""

from config import VOLATILIDAD, parametros_partido
from copas import regionales as RG
from motor.calendario import eventos_calendario
from motor.progreso import Progreso
from motor.simulacion import simular_todo
from motor.temporada import crear_estado, nueva_temporada


def test_desactivados_por_defecto_no_cambian_nada():
    S = crear_estado()
    assert not S["regionales"]["activo"] and not S["regionales_on"]
    assert not [e for e in eventos_calendario(S) if e[1] == "Regionales"]
    simular_todo(S, parametros_partido())
    assert Progreso.desde_estado(S).todas and not S["regionales"]["log"]


def test_temporada_completa_con_campeones_y_palmares():
    S, P = crear_estado(), parametros_partido()
    assert RG.cambiar_activacion(S, S["rng"], True, False)
    R = S["regionales"]
    juegan = {c for t in R["torneos"] for c in (R["nombres"][i] for i in t["ids"])}
    cats = {c for c in R["cat"]}
    assert cats <= set(RG.CATEGORIAS) and not (juegan & set(S["promocional"]) | juegan & set(S["regional"]))
    simular_todo(S, P)
    assert Progreso.desde_estado(S).todas
    assert len(RG.campeones(S)) == len(R["torneos"])
    nueva_temporada(S, VOLATILIDAD)
    assert S["campeones"][-1]["Regionales"]
    assert S["regionales"]["activo"] and S["regionales"]["ronda"] == 0


def test_activar_con_la_temporada_empezada_rige_desde_la_proxima():
    S, P = crear_estado(), parametros_partido()
    assert not RG.cambiar_activacion(S, S["rng"], True, True)
    assert RG.pendiente_de_aplicar(S) and not S["regionales"]["activo"]
    simular_todo(S, P)
    nueva_temporada(S, VOLATILIDAD)
    assert S["regionales"]["activo"] and not RG.pendiente_de_aplicar(S)


def test_formato_de_grupos_y_llaves():
    assert [RG.n_grupos(n) for n in (4, 8, 9, 16, 17, 24, 25, 40)] == [1, 1, 2, 2, 3, 3, 4, 4]
    assert [RG.tam_llave(n) for n in (4, 5, 6, 8, 9, 13, 14, 20, 31)] == [2, 2, 4, 4, 4, 4, 8, 8, 8]

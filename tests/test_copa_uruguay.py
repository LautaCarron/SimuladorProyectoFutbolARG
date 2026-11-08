"""Pruebas de la Copa AUF Uruguay y de la tercera división falsa (la reserva de la que suben y a la que bajan clubes de
la Segunda División)."""

import numpy as np
import pytest

from config import VOLATILIDAD, parametros_partido
from copas import uruguay as copa_uy
from copas.registro import REGISTRO, CopaUruguay
from datos import ligas_ext, paises
from motor.calendario import eventos_calendario, jugar_proximo_dia
from motor.guardado import desempaquetar, empaquetar
from motor.simulacion import simular_todo
from motor.temporada import crear_estado, nueva_temporada

P = parametros_partido()
COPA = next(c for c in REGISTRO if isinstance(c, CopaUruguay))
PARTIDOS_POR_RONDA = [12, 12, 12, 16, 8, 4, 2, 1]


def _estado(semilla):
    S = crear_estado()
    S["rng"] = np.random.default_rng(semilla)
    return S


def _fase(L, rotulo):
    return [p for p in L["log"] if p["rotulo"] == rotulo]


@pytest.mark.parametrize("semilla", range(8))
def test_copa_se_juega_completa_y_define_campeon(semilla):
    S = _estado(semilla)
    assert not COPA.activa(S)                                # todavía no se sorteó: falta el Torneo Competencia
    simular_todo(S, P)
    L = S[COPA.clave]
    assert L["sorteada"] and COPA.terminada(S) and L["fecha"] == 8
    assert L["campeon"] in L["nombres"] and L["subcampeon"] in L["nombres"] and L["campeon"] != L["subcampeon"]
    for n, esperados in enumerate(PARTIDOS_POR_RONDA, start=1):
        jugaron = [x for p in L["log"] if p["fecha"] == n for x in (p["local"], p["visita"])]
        assert len(jugaron) == len(set(jugaron)) == 2 * esperados, f"ronda {n}"
    final = _fase(L, "Final")[0]
    assert final["gana"] == L["campeon"] and final["neutral"]


def test_copa_arma_40_clubes_y_6_grupos():
    S = _estado(1)
    simular_todo(S, P)
    L = S[COPA.clave]
    pro = [n for n, o in zip(L["nombres"], L["origen"]) if o == "Profesional"]
    amateurs = [n for n, o in zip(L["nombres"], L["origen"]) if o == "Amateur"]
    assert len(L["nombres"]) == len(set(L["nombres"])) == 40 and len(pro) == 24 and len(amateurs) == 16
    assert set(pro[:16]) == set(S["ext_uy"]["nombres"])                  # los 16 de la Liga AUF
    assert len(set(pro[16:]) & set(S["ext_uy2"]["nombres"])) == 8        # 8 de la Segunda
    assert set(amateurs) <= set(ligas_ext.CONFIG["uy"]["tercera"])      # los amateurs salen de la tercera división
    assert len(L["grupos"]) == 6 and all(len(g) == 4 for g in L["grupos"])
    assert sorted(i for g in L["grupos"] for i in g) == list(range(24))
    for p in L["log"]:                                       # los amateurs no juegan grupos y no se cruzan con profesionales hasta octavos
        o = {L["nombres"][i]: L["origen"][i] for i in range(40)}
        if p["rotulo"].startswith("Fase de grupos"):
            assert o[p["local"]] == o[p["visita"]] == "Profesional"
        if p["rotulo"] == "Dieciseisavos de final":
            assert o[p["local"]] == o[p["visita"]]


def test_dieciseisavos_pasan_16_profesionales_por_siembra():
    S = _estado(2)
    simular_todo(S, P)
    L = S[COPA.clave]
    nom = L["nombres"]
    pasan = copa_uy.clasificados_grupos(L)
    assert len(pasan) == len(set(pasan)) == 16
    for t in (t for _, t in copa_uy.tablas_grupos(L)):
        assert set(t["id"][:2]) <= set(pasan)                # los 2 primeros de cada grupo siempre pasan
    pros = [(p["local"], p["visita"]) for p in _fase(L, "Dieciseisavos de final")
            if L["origen"][nom.index(p["local"])] == "Profesional"]
    assert len(pros) == 8
    assert {nom[i] for i in pasan} == {x for par in pros for x in par}
    assert pros[0] == (nom[pasan[0]], nom[pasan[15]])        # 1° contra 16°


def test_campeon_de_la_copa_juega_la_libertadores_siguiente():
    S = _estado(3)
    simular_todo(S, P)
    campeon = S[COPA.clave]["campeon"]
    nueva_temporada(S, VOLATILIDAD)
    assert S["ext_copa"]["Uruguay"] == campeon
    assert campeon in S["int"]["lib"]["r"]                   # Uruguay 4 (o ya había clasificado por la liga)
    assert S["hist_copa_uy"] == {campeon: 1}
    assert S["campeones"][-1]["Copa AUF Uruguay"] == campeon
    assert S["ext_def"]["copa_uy"][0]["campeon"] == campeon
    assert not S[COPA.clave]["sorteada"] and S[COPA.clave]["campeon"] is None     # copa nueva, sin sortear


def test_uruguay_4_pasa_a_la_tabla_si_el_campeon_ya_clasifico():
    from copas.conmebol import _sortear_pais
    S = {"ext_mov": {"Uruguay": {"orden": ["A", "B", "C", "D", "E"]}}}
    rng = np.random.default_rng(0)
    assert _sortear_pais(rng, S, "Uruguay", 1, {"A"}, primero="Z") == ["Z"]           # el campeón se queda el cupo
    assert _sortear_pais(rng, S, "Uruguay", 1, {"A", "Z"}, primero="Z") == ["B"]      # ya clasificó: sigue la Anual
    assert _sortear_pais(rng, S, "Uruguay", 2, {"A"}, primero="Z") == ["Z", "B"]


def test_copa_aparece_en_el_calendario_recien_con_el_sorteo_y_se_guarda_y_carga():
    S = _estado(4)
    assert COPA.nombre not in {e[1] for e in eventos_calendario(S)}
    for _ in range(400):                                     # día por día hasta que se sortea
        if COPA.activa(S):
            break
        jugar_proximo_dia(S, P)
    assert COPA.activa(S) and not S["ext_uy2"]["hecho"]["Regular"]
    ev = [e for e in eventos_calendario(S) if e[1] == COPA.nombre]
    assert len(ev) == 8 and all(e[0].weekday() == 2 for e in ev) and [e[0] for e in ev] == sorted(e[0] for e in ev)
    assert all(e[0].month >= 8 for e in ev)
    for _ in range(600):                                     # y a mitad de la copa se guarda y se carga
        jugar_proximo_dia(S, P)
        if S[COPA.clave]["fecha"] >= 4:
            break
    assert 0 < S[COPA.clave]["fecha"] < 8
    S2 = desempaquetar(empaquetar(S))["S"]
    assert S2[COPA.clave]["fecha"] == S[COPA.clave]["fecha"] and S2[COPA.clave]["grupos"] == S[COPA.clave]["grupos"]
    simular_todo(S2, P)
    assert S2[COPA.clave]["campeon"] and COPA.terminada(S2)


def test_copa_es_de_uruguay():
    assert paises.copas_nacionales_de("Uruguay") == ["Copa AUF Uruguay"]
    assert paises.pais_de_competencia("Copa AUF Uruguay") == "Uruguay"
    assert "Copa AUF Uruguay" in paises.competencias_de("Uruguay")
    assert "Copa AUF Uruguay" not in paises.competencias_de("Argentina")


def test_tercera_division_falsa_bajan_los_ultimos_y_suben_al_azar():
    cfg = ligas_ext.CONFIG["uy"]
    assert len(cfg["tercera"]) == 20 and ligas_ext.CONFIG["uy2"]["descensos"] == 2
    S = _estado(5)
    for _ in range(3):
        L2 = S["ext_uy2"]
        previa3 = set(S["ext_clubes"]["Uruguay|3"])
        simular_todo(S, P)
        ultimos = list(S["ext_uy2"]["nombres"][int(i)] for i in
                       __import__("ligas.uruguay_segunda", fromlist=["x"])._tabla_anual(S["ext_uy2"])["id"])[-2:]
        nueva_temporada(S, VOLATILIDAD)
        tercera = set(S["ext_clubes"]["Uruguay|3"])
        assert len(tercera) == 20 and set(ultimos) <= tercera                   # los últimos de la Segunda bajan
        assert len(previa3 - tercera) == 2 == len(set(S["ext_uy2"]["nombres"]) & previa3)    # y suben 2 de la tercera
        mov = S["ext_mov3"]["Uruguay"]
        assert set(mov["bajan"]) == set(ultimos) and set(mov["suben"]) == previa3 - tercera
    assert not (set(S["ext_clubes"]["Uruguay|3"]) & set(S["ext_uy"]["nombres"]))

"""Pruebas de las ligas de otros países: datos, formato uruguayo, formato genérico y conexión con el simulador."""

import numpy as np
import pytest

from config import VOLATILIDAD, parametros_partido
from copas.registro import LIGAS_EXTERIOR
from datos import equipos, ligas_ext
from datos.clubes_int import CLUBES_INT
from ligas.exterior import FORMATOS, TodosContraTodos, formato_de, jugar_ronda
from motor.calendario import eventos_calendario, jugar_proximo_dia
from motor.guardado import desempaquetar, empaquetar
from motor.progreso import Progreso
from motor.simulacion import simular_todo
from motor.temporada import crear_estado, nueva_temporada

P = parametros_partido()
MEDIA = {n: float(m) for n, _, m, _ in CLUBES_INT}


def test_datos_de_las_ligas_cierran():
    assert ligas_ext.errores() == []
    uy, uy2 = ligas_ext.CONFIG["uy"], ligas_ext.CONFIG["uy2"]
    assert len(uy["clubes"]) == 16 and len(uy["reserva"]) >= uy["ascensos"]
    assert uy["inferior"] == "uy2" and uy2["superior"] == "uy" and uy2["divisional"] == 2
    assert len(uy2["clubes"]) == 14 and uy2["clubes"] == uy["reserva"] and uy["ascensos"] == uy["descensos"] == 3
    en_int = {n for n, p, *_ in CLUBES_INT if p == "Uruguay"}
    assert en_int == set(ligas_ext.clubes_de_la_liga(uy))        # CLUBES_INT los suma desde el archivo de la liga


def test_nombres_de_clubes_no_chocan_con_los_argentinos():
    argentinos = set(equipos._todos)
    repetidos = [n for n, *_ in CLUBES_INT if n in argentinos]
    assert not repetidos, f"clubes del exterior con el mismo nombre que uno argentino: {repetidos}"
    todos = [n for n, *_ in CLUBES_INT]
    assert len(todos) == len(set(todos))


def _temporada(cfg, semilla, previo=None):
    fmt, rng = formato_de(cfg), np.random.default_rng(semilla)
    nombres = list(cfg["clubes"])
    L = fmt.nueva(cfg, nombres, [MEDIA[n] for n in nombres], previo or {}, 2026, rng)
    fmt.avanzar(L, rng)
    for _ in range(100):
        if L["fecha"] >= len(L["rondas"]):
            break
        assert L["rondas"][L["fecha"]]["pares"], "una ronda sin cruces quedó por jugar"
        jugar_ronda(L, P, rng)
        fmt.avanzar(L, rng)
    return fmt, L


@pytest.mark.parametrize("semilla", range(25))
def test_uruguay_siempre_define_campeon(semilla):
    fmt, L = _temporada(ligas_ext.CONFIG["uy"], semilla)
    assert L["campeon"] and L["subcampeon"] and L["campeon"] != L["subcampeon"]
    anual = next(t for t in fmt.tablas(L) if t["titulo"] == "Tabla Anual")["df"]
    assert (anual["PJ"] == 37).all()                     # 15 + 7 + 15: las finales y los desempates no suman
    c = fmt.cierre(L)
    assert len(c["descienden"]) == ligas_ext.CONFIG["uy"]["descensos"] and c["orden"][:2] == [L["campeon"], L["subcampeon"]] and len(set(c["orden"])) == 16
    for n in range(1, L["fecha"] + 1):                   # nadie juega dos veces la misma fecha
        jugaron = [x for p in L["log"] if p["fecha"] == n for x in (p["local"], p["visita"])]
        assert len(jugaron) == len(set(jugaron))


def test_uruguay_descenso_usa_la_temporada_anterior():
    cfg = ligas_ext.CONFIG["uy"]
    previo = {n: (0, 37) for n in cfg["clubes"]}
    previo["Peñarol"] = (0, 37)                          # el peor promedio de dos temporadas, gane lo que gane ahora
    fmt, L = _temporada(cfg, 3, previo)
    prom = fmt._promedios(L)
    assert len(prom) == 16 and (prom["PJ"] == 74).all()


def test_formato_generico_todos_contra_todos():
    """El formato de Brasil (cuando se sume) ya funciona con sólo agregar una entrada de datos."""
    cfg = {"clave": "xx", "nombre": "Liga de prueba", "pais": "Brasil", "formato": "todos_contra_todos", "descensos": 4,
           "calendario": {"Liga": [1, 31, 6]},
           "clubes": [n for n, p, *_ in CLUBES_INT if p == "Brasil"][:20]}
    fmt, L = _temporada(cfg, 1)
    assert isinstance(fmt, TodosContraTodos) and len(L["rondas"]) == 38 and L["campeon"]
    c = fmt.cierre(L)
    assert len(c["descienden"]) == 4 and c["orden"][0] == L["campeon"]


def test_formato_desconocido():
    with pytest.raises(ValueError):
        formato_de({"clave": "zz", "formato": "inventado"})
    assert {"uruguay", "todos_contra_todos"} <= set(FORMATOS)


def test_liga_conectada_al_simulador():
    S = crear_estado()
    assert LIGAS_EXTERIOR and S["ext_uy"]["fecha"] == 0
    assert any(e[1] == "Liga AUF Uruguaya" for e in eventos_calendario(S))
    for _ in range(30):
        jugar_proximo_dia(S, P)
    assert S["ext_uy"]["fecha"] > 0
    simular_todo(S, P)
    assert Progreso.desde_estado(S).todas
    campeon = S["ext_uy"]["campeon"]
    S2 = desempaquetar(empaquetar(S))["S"]               # se guarda y se carga
    assert S2["ext_uy"]["campeon"] == campeon
    suben_segunda = S["ext_uy2"]["suben"]
    nueva_temporada(S, VOLATILIDAD)
    mov = S["ext_mov"]["Uruguay"]
    assert S["campeones"][-1]["Uruguay"] == campeon and S["hist_ext_uy"][campeon] == 1
    assert len(S["ext_uy"]["nombres"]) == 16 and set(mov["suben"]) <= set(S["ext_uy"]["nombres"])
    assert all(n not in S["ext_uy"]["nombres"] for n in mov["bajan"])
    assert S["ext_uy"]["fecha"] == 0 and S["temp"] == 2
    # la Segunda: suben exactamente los que ascendieron en su tabla y ocupan su lugar los que bajaron
    assert mov["suben"] == suben_segunda and len(mov["bajan"]) == len(suben_segunda) == 3
    assert len(S["ext_uy2"]["nombres"]) == 14 and S["ext_uy2"]["fecha"] == 0
    assert set(mov["bajan"]) <= set(S["ext_uy2"]["nombres"]) and not set(suben_segunda) & set(S["ext_uy2"]["nombres"])
    assert not set(S["ext_uy"]["nombres"]) & set(S["ext_uy2"]["nombres"])
    assert S["campeones"][-1]["Uruguay · D2"] == S["ext_mov"]["Uruguay|2"]["orden"][0]


def test_cupos_internacionales_de_uruguay():
    """La Tabla Anual muestra los cupos y las copas CONMEBOL de la temporada siguiente los respetan."""
    S = crear_estado()
    L = S["ext_uy"]
    assert [k for _, k in L["cupos"]] == [2, 1, 1, 4]       # Libertadores: grupos, Fase 2, Fase 1; Sudamericana
    simular_todo(S, P)
    anual = next(t for t in formato_de(ligas_ext.CONFIG["uy"]).tablas(L) if t["titulo"] == "Tabla Anual")
    destinos = [d for d in anual["df"]["Destino"] if d]
    assert sum("Libertadores" in d for d in destinos) == 4 and sum("Sudamericana" in d for d in destinos) == 4
    campeon, sub = L["campeon"], L["subcampeon"]
    fila = anual["df"].set_index("Equipo")["Destino"]
    assert fila[campeon].startswith("Campeón") and fila[campeon].endswith("Libertadores")
    assert fila[sub] == "Libertadores"
    nueva_temporada(S, VOLATILIDAD)
    lib = S["int"]["lib"]
    assert campeon in lib["directos"] and sub in lib["directos"]      # Uruguay 1 y 2 van directo a los grupos
    uy = [n for n, v in lib["via"].items() if v.startswith("Uruguay")]
    assert len(uy) == 4
    sud = [n for n, v in S["int"]["sud"]["via"].items() if v.startswith("Uruguay")]
    assert len(sud) == 4 and not set(sud) & set(uy)


# ---------------------------------------------------------------------------------------- Segunda de Uruguay
@pytest.mark.parametrize("semilla", range(25))
def test_segunda_uruguay_define_tres_ascensos(semilla):
    cfg = ligas_ext.CONFIG["uy2"]
    fmt, L = _temporada(cfg, semilla)
    nom = L["nombres"]
    assert L["campeon"] and L["campeon"] != L["subcampeon"] and len(L["suben"]) == 3 == len(set(L["suben"]))
    anual = next(t for t in fmt.tablas(L) if t["titulo"] == "Tabla Anual")["df"]
    assert (anual["PJ"] == 32).all()                     # 6 de la Competencia + 26 de la fase regular
    assert anual.iloc[0]["Equipo"] == L["campeon"] and anual.iloc[1]["Equipo"] == L["subcampeon"]
    assert L["suben"][:2] == [nom[i] for i in L["directos"]] == list(anual["Equipo"][:2])
    P = L["playoff"]
    assert len(P["cupos"]) == 4 == len(set(P["cupos"])) and not set(P["cupos"]) & set(L["directos"])
    assert nom[P["ganador"]] == L["suben"][2] and P["ganador"] in P["cupos"]
    gc = L["ganadores"]["Competencia"]                  # el campeón de la Competencia asciende o juega el playoff
    assert gc in L["directos"] or gc in P["cupos"]
    for n in range(1, L["fecha"] + 1):                   # nadie juega dos veces la misma fecha
        jugaron = [x for p in L["log"] if p["fecha"] == n for x in (p["local"], p["visita"])]
        assert len(jugaron) == len(set(jugaron))
    c = fmt.cierre(L)
    assert c["suben"] == L["suben"] and len(set(c["orden"])) == 14
    assert len(c["descienden"]) == cfg["descensos"] == 2 and c["descienden"] == c["orden"][-2:]     # bajan a la tercera


def test_segunda_uruguay_el_de_la_competencia_entra_al_playoff():
    """Si el campeón de la Competencia termina lejos de los puestos de ascenso, ocupa el lugar del 6° en el playoff."""
    cfg = ligas_ext.CONFIG["uy2"]
    visto = False
    for semilla in range(60):
        _, L = _temporada(cfg, semilla)
        gc, P = L["ganadores"]["Competencia"], L["playoff"]
        ids = [int(i) for i in tabla_anual_ids(L)]
        if gc in ids[6:]:
            visto = True
            assert P["cupos"] == ids[2:5] + [gc]
        else:
            assert P["cupos"] == ids[2:6]
    assert visto, "en 60 temporadas el de la Competencia nunca quedó fuera de los seis primeros: revisar la prueba"


def tabla_anual_ids(L):
    from ligas.uruguay_segunda import _tabla_anual
    return list(_tabla_anual(L)["id"])


def test_uruguay_dos_divisiones_tres_temporadas():
    """Suben y bajan los mismos clubes, las dos ligas conservan su tamaño y nadie juega en las dos a la vez."""
    S = crear_estado()
    todos = set(S["ext_uy"]["nombres"]) | set(S["ext_uy2"]["nombres"]) | set(S["ext_clubes"]["Uruguay|3"])
    assert len(todos) == 50                                  # 16 + 14 + la tercera división falsa (20)
    for _ in range(3):
        simular_todo(S, P)
        nueva_temporada(S, VOLATILIDAD)
        a, b, c = set(S["ext_uy"]["nombres"]), set(S["ext_uy2"]["nombres"]), set(S["ext_clubes"]["Uruguay|3"])
        assert len(a) == 16 and len(b) == 14 and len(c) == 20 and not a & b and not a & c and not b & c
        assert a | b | c == todos
    assert S["temp"] == 4 and len(S["campeones"]) == 3
    assert all(x["Uruguay"] and x["Uruguay · D2"] for x in S["campeones"])


def test_segunda_uruguay_se_guarda_y_se_carga_a_mitad_de_temporada():
    S = crear_estado()
    for _ in range(60):
        jugar_proximo_dia(S, P)
    assert 0 < S["ext_uy2"]["fecha"] < len(S["ext_uy2"]["rondas"])
    S2 = desempaquetar(empaquetar(S))["S"]
    assert S2["ext_uy2"]["fecha"] == S["ext_uy2"]["fecha"] and S2["ext_clubes"]["Uruguay|2"] == S["ext_clubes"]["Uruguay|2"]
    simular_todo(S2, P)
    assert S2["ext_uy2"]["campeon"] and len(S2["ext_uy2"]["suben"]) == 3


def test_campeones_con_semifinales_y_finales_quedan_registrados():
    """Cada temporada cerrada anota quién ganó, cómo y los partidos decisivos (sección Campeones de la liga)."""
    S = crear_estado()
    comp = next(c for c in LIGAS_EXTERIOR if c.cfg["clave"] == "uy")
    for _ in range(4):
        simular_todo(S, P)
        actual = comp.definiciones(S, S["ext_uy"])
        assert actual["campeon"] == S["ext_uy"]["campeon"]
        nueva_temporada(S, VOLATILIDAD)
    regs = S["ext_def"]["ext_uy"]
    assert [r["temp"] for r in regs] == [1, 2, 3, 4]
    assert [r["campeon"] for r in regs] == [x["Uruguay"] for x in S["campeones"]]
    etapas = set(comp.formato.etapas_definicion)
    for r in regs:
        assert r["subcampeon"] and r["via"] and set(r["ganadores"]) <= {"Apertura", "Intermedio", "Clausura", "Anual"}
        assert all(p["dia"] and p["comp"] for p in r["partidos"])
        assert r["partidos"] and {p["rotulo"] for p in r["partidos"]} <= {p["rotulo"] for p in r["partidos"]}
        assert len(r["partidos"]) <= 8
    assert len(S["ext_def"]["ext_uy2"]) == 4


def test_medias_del_exterior_vuelven_un_15_por_ciento():
    from motor import temporada
    assert temporada.REVERSION_EXT == 0.15


def test_brasil_serie_a_cupos_y_descensos():
    """Brasileirão Série A pinta Libertadores, Libertadores Fase 2, Sudamericana y descensos."""
    from ui.ui_ligas_ext import _color_destino
    from ui.vista import COLOR_ORO, COLORES_B, COLORES_DESTINO

    cfg = ligas_ext.CONFIG["br"]
    fmt = formato_de(cfg)
    rng = np.random.default_rng(42)
    nombres = list(cfg["clubes"])
    L = fmt.nueva(cfg, nombres, [MEDIA[n] for n in nombres], {}, 2026, rng)
    fmt.avanzar(L, rng)

    # Con la liga en curso (fecha 0): 1° al 5° directos, 6° fase previa, 7° al 12° Sudamericana
    tablas = fmt.tablas(L)
    df = tablas[0]["df"]
    assert len(df) == 20
    destinos = list(df["Destino"])

    assert destinos[0].startswith("Líder") and destinos[0].endswith("Libertadores")
    assert _color_destino(destinos[0]) == COLOR_ORO

    for d in destinos[1:5]:
        assert d == "Libertadores"
        assert _color_destino(d) == COLORES_DESTINO["Libertadores"]

    assert destinos[5] == "Libertadores · Fase 2"
    assert _color_destino(destinos[5]) == COLORES_DESTINO["Fase previa Libertadores"]

    for d in destinos[6:12]:
        assert d == "Sudamericana"
        assert _color_destino(d) == COLORES_DESTINO["Sudamericana"]

    for d in destinos[12:16]:
        assert d == ""
        assert _color_destino(d) == ""

    for d in destinos[16:20]:
        assert d == "Desciende"
        assert _color_destino(d) == COLORES_B["Desciende"]

    # Al simular toda la temporada
    fmt, L = _temporada(cfg, 42)
    assert L["campeon"]
    df_fin = fmt.tablas(L)[0]["df"]
    destinos_fin = list(df_fin["Destino"])
    assert destinos_fin[0] == "Campeón · Libertadores"
    assert _color_destino(destinos_fin[0]) == COLOR_ORO


def test_brasil_serie_b_ascensos():
    """Brasileirão Série B pinta el campeón/líder y los que ascienden directo (2° al 4°)."""
    from ui.ui_ligas_ext import _color_destino
    from ui.vista import COLOR_ORO, COLORES_B

    cfg = ligas_ext.CONFIG["br2"]
    fmt = formato_de(cfg)
    rng = np.random.default_rng(42)
    nombres = list(cfg["clubes"])
    L = fmt.nueva(cfg, nombres, [MEDIA[n] for n in nombres], {}, 2026, rng)
    fmt.avanzar(L, rng)

    # Con la liga en curso (fecha 0)
    df = fmt.tablas(L)[0]["df"]
    assert len(df) == 20
    destinos = list(df["Destino"])

    assert destinos[0] == "Líder · Asciende"
    assert _color_destino(destinos[0]) == COLOR_ORO

    for d in destinos[1:4]:
        assert d == "Asciende"
        assert _color_destino(d) == COLORES_B["Ascenso directo"]

    for d in destinos[4:20]:
        assert d == ""
        assert _color_destino(d) == ""

    # Al simular toda la temporada
    fmt, L = _temporada(cfg, 42)
    assert L["campeon"]
    df_fin = fmt.tablas(L)[0]["df"]
    destinos_fin = list(df_fin["Destino"])
    assert destinos_fin[0] == "Campeón · Asciende"
    assert _color_destino(destinos_fin[0]) == COLOR_ORO
    for d in destinos_fin[1:4]:
        assert d == "Asciende"
        assert _color_destino(d) == COLORES_B["Ascenso directo"]

    c = fmt.cierre(L)
    assert len(c["suben"]) == 4
    assert c["suben"] == list(df_fin["Equipo"][:4])
    assert c["descienden"] == []

"""Club propio (datos/club_propio.py y motor/club_usuario.py): se crea en la pestaña Partidas y entra al Regional."""

import io

import numpy as np

from config import VOLATILIDAD, parametros_partido
from datos import club_propio as cp
from datos.equipos import datos_club, origen, region_regional
from motor import club_usuario as cu
from motor.nucleo import jugar
from motor.simulacion import simular_todo
from motor.temporada import crear_estado, nueva_temporada


def _club(S, nombre="Los Pinos FC", **kw):
    datos = dict(provincia="Buenos Aires", liga="Liga Marplatense", ciudad="Mar del Plata")
    datos.update(kw)
    return cp.crear(nombre, ocupados=cu.nombres_ocupados(S), **datos)


def _entra(S, **kw):
    """Crea el club y pasa de temporada: así entra al Regional."""
    cu.crear_pendiente(S, _club(S, **kw))
    simular_todo(S, parametros_partido())
    nueva_temporada(S, VOLATILIDAD)


def test_region_por_liga():
    assert cp.region_de_liga("Buenos Aires", "Liga Marplatense") == "Pampeana Sur"
    assert cp.region_de_liga("Tucumán", "Liga Tucumana") == "NOA Sur"
    assert all(cp.region_de_liga(p, lg) for p, ligas in cp.LIGAS_POR_PROVINCIA.items() for lg in ligas)


def test_nombre_repetido_se_diferencia():
    S = crear_estado()
    assert _club(S, "Aldosivi")["nombre"] == "Aldosivi (propio)"
    assert _club(S, "aldosivi")["nombre"] == "aldosivi (propio)"
    assert _club(S, "Los Pinos FC")["nombre"] == "Los Pinos FC"
    assert cp.nombre_valido("") and cp.nombre_valido("x" * 41) and cp.nombre_valido("a<b")


def _imagen(formato="PNG", lado=600):
    from PIL import Image
    salida = io.BytesIO()
    Image.new("RGB", (lado, lado), (200, 30, 30)).save(salida, formato)
    return salida.getvalue()


def test_escudo():
    uri, err = cp.procesar_escudo(_imagen())
    assert err is None and uri.startswith("data:image/png;base64,")
    assert cp.procesar_escudo(_imagen("JPEG"))[1] is None
    assert cp.procesar_escudo(b"x" * (cp.MAX_ESCUDO + 1))[0] is None            # pasa de 1 MB
    assert cp.procesar_escudo(b"no es una imagen")[0] is None


def test_entra_en_la_temporada_siguiente_y_partida_nueva_lo_borra():
    S = crear_estado()
    cu.crear_pendiente(S, _club(S))
    assert "Los Pinos FC" not in S["reg"]["nombres"]                   # esta temporada no juega
    simular_todo(S, parametros_partido())
    nueva_temporada(S, VOLATILIDAD)
    try:
        assert S["club_propio"]["region"] == "Pampeana Sur" and not S["club_pendiente"]
        SR = S["reg"]
        assert SR["region_de"][SR["nombres"].index("Los Pinos FC")] == "Pampeana Sur"
        assert datos_club("Los Pinos FC")["liga"] == "Liga Marplatense"
        assert region_regional("Los Pinos FC") == "Pampeana Sur"
        assert not cu.puede_crear(S)                                    # uno solo
        S2 = crear_estado()                                             # partida nueva: sin club
        assert "club_propio" not in S2 and datos_club("Los Pinos FC") is None
    finally:
        cp.activar(None)


def test_baja_pierde_3_a_0_y_desaparece_dejando_palmares():
    S, P = crear_estado(), parametros_partido()
    _entra(S)
    try:
        nombre = "Los Pinos FC"
        i = S["reg"]["nombres"].index(nombre)
        S["reg"]["r"][i] = 90                                          # sería el campeón de la región
        S.setdefault("hist_federal", {})[nombre] = 1                    # y ya tiene un título en el palmarés
        cu.dar_de_baja(S)
        simular_todo(S, P)
        jugados = [p for p in S["reg"]["log"] if nombre in (p["local"], p["visita"])] if "log" in S["reg"] else []
        for p in jugados:
            assert (p["local"] == nombre and (p["gl"], p["gv"]) == (0, 3)) or \
                   (p["visita"] == nombre and (p["gl"], p["gv"]) == (3, 0))
        nueva_temporada(S, VOLATILIDAD)
        assert S["club_propio"] is None and nombre not in S["rating"]
        todos = [n for lig in (S, S["b"], S["f"], S["pb"], S["pc"], S["pd"], S["reg"]) for n in lig["nombres"]]
        assert nombre not in todos
        assert S["clubes_ex"] == [{"nombre": nombre, "escudo": ""}]    # queda para el palmarés
        assert cu.puede_crear(S)
        assert _club(S)["nombre"] == "Los Pinos FC (propio)"           # un club nuevo no pisa ese palmarés
    finally:
        cp.activar(None)


def test_jugar_con_media_de_baja():
    rng = np.random.default_rng(1)
    gl, gv = jugar(rng, np.array([cp.WO_RATING, 50.0, 50.0]), np.array([50.0, cp.WO_RATING, 50.0]), 6.0)
    assert list(gl[:2]) == [0, 3] and list(gv[:2]) == [3, 0]


def test_sin_club_no_cambia_nada():
    S = crear_estado()
    assert "club_propio" not in S and datos_club("Los Pinos FC") is None


def test_media_minima_es_10():
    assert cp.MEDIA_MIN == 10
    assert cp.crear("Los Pinos FC", "Buenos Aires", "Liga Marplatense", "Mar del Plata", media=3)["media"] == 10.0
    assert cp.crear("Los Pinos FC", "Buenos Aires", "Liga Marplatense", "Mar del Plata", media=10)["media"] == 10.0


def test_metropolitano_entra_al_promocional_sin_datos_extra():
    S = crear_estado()
    club = cp.crear("Los Pinos FC", media=12, ocupados=cu.nombres_ocupados(S), origen=cp.METROPOLITANA)
    assert club["origen"] == cp.METROPOLITANA and club["region"] == "" and club["liga"] == ""
    cu.crear_pendiente(S, club)
    assert "Los Pinos FC" not in S["promocional"]                       # esta temporada no juega
    simular_todo(S, parametros_partido())
    nueva_temporada(S, VOLATILIDAD)
    try:
        assert "Los Pinos FC" in S["promocional"] and "Los Pinos FC" in S["pd"]["nombres"]
        assert "Los Pinos FC" not in S["regional"] and "Los Pinos FC" not in S["reg"]["nombres"]
        assert S["rating"]["Los Pinos FC"] >= 10 and S["club_propio"]["origen"] == cp.METROPOLITANA
        assert datos_club("Los Pinos FC") is None and cp.region("Los Pinos FC") is None
        assert origen("Los Pinos FC") == "Metropolitana"
        simular_todo(S, parametros_partido())                           # la temporada se juega completa
        cu.dar_de_baja(S)
        nueva_temporada(S, VOLATILIDAD)
        assert "Los Pinos FC" not in S["promocional"] and S["club_propio"] is None
    finally:
        cp.activar(None)

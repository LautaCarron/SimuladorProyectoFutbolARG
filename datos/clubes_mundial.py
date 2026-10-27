"""Clubes que podrían clasificar al Mundial de Clubes (próxima edición: 2029, 32 equipos).

Solo datos, sin lógica de simulación ni Streamlit (lo consumen datos/equipos.py y
copas/mundial.py). CONMEBOL no figura acá: sus clubes ya están en datos/equipos.py (Argentina) y en
datos/clubes_int.py (resto de la CONMEBOL).

Cupos del formato vigente (ciclo 2025-2028): los campeones continentales de los cuatro años
clasifican directo y el resto de los lugares sale del ranking de cada confederación, con
máximo de 2 clubes por país salvo que haya más campeones del mismo país.

Medias: orientativas, en la misma escala que EQUIPOS (Primera argentina 63-80). Tope 90.
Escudos: todavía no hay; crest() (ui/vista/base.py) dibuja un distintivo con las iniciales si falta la URL.
Para sumarlos después: ESCUDOS.update({nombre: url}) en datos/equipos.py.

Los nombres evitan chocar con los de clubes argentinos o sudamericanos (p. ej. "Arsenal (ING)",
porque en Primera B ya existe "Arsenal").
"""

from datos.cargador import cargar


_D = cargar("clubes_mundial")      # datos/json/clubes_mundial.json
CUPOS_2029 = _D["cupos_2029"]

# Clasificados por título continental (al 1/10/2026, según las notas de junio de 2026 de TUDN,
# El Universal y 365Scores: Paris Saint-Germain (Champions 2025 y 2026), Al-Ahli (AFC 2025), Pyramids 
# y Mamelodi Sundowns (CAF 2025 y 2026), Cruz Azul (Concacaf 2025) y Toluca (Concacaf 2026). Flamengo (Libertadores 2025) es CONMEBOL.
CLASIFICADOS_2029 = set(_D["clasificados_2029"])

# (nombre, país, confederación, media)
MUNDIAL_CLUBES = [(c["nombre"], c["pais"], c["confederacion"], c["media"],
                  *([c["escudo"]] if c.get("escudo") else []))
                 for c in _D["clubes"]]

# Usamos índices (x[0] es Nombre, x[1] País, x[2] Conf, x[3] Media) 
# Esto evita que el programa explote si algún club tiene 4 datos y otro tiene 5.
MEDIA_MUNDIAL = {x[0]: x[3] for x in MUNDIAL_CLUBES}
PAIS_MUNDIAL = {x[0]: x[1] for x in MUNDIAL_CLUBES}
CONF_MUNDIAL = {x[0]: x[2] for x in MUNDIAL_CLUBES}


def clubes_de(confederacion):
    """Nombres de los clubes de una confederación, de mayor a menor media."""
    return sorted((x[0] for x in MUNDIAL_CLUBES if x[2] == confederacion),
                  key=lambda n: -MEDIA_MUNDIAL[n])


assert len(MEDIA_MUNDIAL) == len(MUNDIAL_CLUBES), "Hay clubes del Mundial con nombre repetido"
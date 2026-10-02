"""Clubes que podrían clasificar al Mundial de Clubes (próxima edición: 2029, 32 equipos).

Solo datos, sin lógica de simulación ni Streamlit (por ahora no está conectado a ningún otro
archivo). CONMEBOL no figura acá: sus clubes ya están en datos.py (Argentina) y en
clubes_int.py (resto de la CONMEBOL).

Cupos del formato vigente (ciclo 2025-2028): los campeones continentales de los cuatro años
clasifican directo y el resto de los lugares sale del ranking de cada confederación, con
máximo de 2 clubes por país salvo que haya más campeones del mismo país.

Medias: orientativas, en la misma escala que EQUIPOS (Primera argentina 63-80). Tope 90.
Escudos: todavía no hay; vista.crest() dibuja un distintivo con las iniciales si falta la URL.
Para sumarlos después: ESCUDOS.update({nombre: url}) en datos.py.

Los nombres evitan chocar con los de clubes argentinos o sudamericanos (p. ej. "Arsenal (ING)",
porque en Primera B ya existe "Arsenal").
"""

CUPOS_2029 = {"UEFA": 12, "CONMEBOL": 6, "AFC": 4, "CAF": 4, "CONCACAF": 4, "OFC": 1, "Anfitrión": 1}

# Clasificados por título continental (al 1/10/2026, según las notas de junio de 2026 de TUDN,
# El Universal y 365Scores; conviene revisarlo antes de usarlo): Paris Saint-Germain (Champions
# 2025 y 2026), Al-Ahli (AFC 2025), Pyramids y Mamelodi Sundowns (CAF 2025 y 2026), Cruz Azul
# (Concacaf 2025) y Toluca (Concacaf 2026). Flamengo (Libertadores 2025) es CONMEBOL.
CLASIFICADOS_2029 = {
    "Paris Saint-Germain", "Al-Ahli", "Pyramids", "Mamelodi Sundowns", "Cruz Azul", "Toluca",
}

# (nombre, país, confederación, media)
MUNDIAL_CLUBES = [
    # UEFA
    ("Paris Saint-Germain", "Francia", "UEFA", 90),
    ("Real Madrid", "España", "UEFA", 90),
    ("Manchester City", "Inglaterra", "UEFA", 90),
    ("Bayern Múnich", "Alemania", "UEFA", 90),
    ("Arsenal (ING)", "Inglaterra", "UEFA", 90),
    ("Liverpool (ING)", "Inglaterra", "UEFA", 90),
    ("FC Barcelona", "España", "UEFA", 90),
    ("Inter de Milán", "Italia", "UEFA", 88),
    ("Chelsea", "Inglaterra", "UEFA", 90),
    ("Atlético Madrid", "España", "UEFA", 88),
    ("Borussia Dortmund", "Alemania", "UEFA", 86),
    ("Bayer Leverkusen", "Alemania", "UEFA", 85),
    ("Juventus", "Italia", "UEFA", 83),
    ("Napoli", "Italia", "UEFA", 83),
    ("Tottenham", "Inglaterra", "UEFA", 83),
    ("Milan", "Italia", "UEFA", 82),
    ("Atalanta", "Italia", "UEFA", 82),
    ("Benfica", "Portugal", "UEFA", 80),
    ("Sporting CP", "Portugal", "UEFA", 80),
    ("Newcastle United", "Inglaterra", "UEFA", 80),
    ("Aston Villa", "Inglaterra", "UEFA", 83),
    ("Manchester United", "Inglaterra", "UEFA", 84),
    ("Porto", "Portugal", "UEFA", 80),
    ("Roma", "Italia", "UEFA", 81),
    ("Olympique de Marsella", "Francia", "UEFA", 79),
    ("Sevilla", "España", "UEFA", 79),
    ("RB Leipzig", "Alemania", "UEFA", 82),
    ("Monaco", "Francia", "UEFA", 79),
    ("Lyon", "Francia", "UEFA", 79),
    ("Ajax", "Países Bajos", "UEFA", 76),
    # AFC
    ("Al-Hilal", "Arabia Saudita", "AFC", 80),
    ("Al-Ahli", "Arabia Saudita", "AFC", 78),
    ("Al-Nassr", "Arabia Saudita", "AFC", 77),
    ("Al-Ittihad", "Arabia Saudita", "AFC", 76),
    ("Vissel Kobe", "Japón", "AFC", 71),
    ("Urawa Reds", "Japón", "AFC", 70),
    ("Kawasaki Frontale", "Japón", "AFC", 68),
    ("Ulsan HD", "Corea del Sur", "AFC", 68),
    ("Al-Sadd", "Qatar", "AFC", 67),
    ("Al-Duhail", "Qatar", "AFC", 66),
    ("Shabab Al-Ahli", "Emiratos Árabes Unidos", "AFC", 66),
    ("Al-Ain", "Emiratos Árabes Unidos", "AFC", 66),
    # CAF
    ("Al Ahly", "Egipto", "CAF", 75),
    ("Pyramids", "Egipto", "CAF", 74),
    ("Mamelodi Sundowns", "Sudáfrica", "CAF", 72),
    ("Wydad Casablanca", "Marruecos", "CAF", 70),
    ("Espérance de Tunis", "Túnez", "CAF", 70),
    ("Zamalek", "Egipto", "CAF", 68),
    ("RS Berkane", "Marruecos", "CAF", 66),
    ("Orlando Pirates", "Sudáfrica", "CAF", 66),
    ("Raja Casablanca", "Marruecos", "CAF", 64),
    ("TP Mazembe", "RD Congo", "CAF", 62),
    # CONCACAF
    ("Club América", "México", "CONCACAF", 77),
    ("Monterrey", "México", "CONCACAF", 77),
    ("Cruz Azul", "México", "CONCACAF", 75),
    ("Toluca", "México", "CONCACAF", 74),
    ("Tigres", "México", "CONCACAF", 74),
    ("León", "México", "CONCACAF", 74),
    ("Pachuca", "México", "CONCACAF", 72),
    ("Guadalajara", "México", "CONCACAF", 72),
    ("Queretaro", "México", "CONCACAF", 72),
    ("Inter Miami", "Estados Unidos", "CONCACAF", 75),
    ("Los Angeles FC", "Estados Unidos", "CONCACAF", 74),
    ("Columbus Crew", "Estados Unidos", "CONCACAF", 70),
    ("Seattle Sounders", "Estados Unidos", "CONCACAF", 70),
    ("FC Cincinnati", "Estados Unidos", "CONCACAF", 70),
    ("Nashvilel SC", "Estados Unidos", "CONCACAF", 70),
    ("Vancouver Whitecaps", "Estados Unidos", "CONCACAF", 70),
    ("Toronto FC", "Canadá", "CONCACAF", 68),
    ("New York City FC", "Estados Unidos", "CONCACAF", 68),
    ("D.C. United", "Estados Unidos", "CONCACAF", 68),
    ("Atlanta United FC", "Estados Unidos", "CONCACAF", 68),
    # OFC
    ("Auckland City", "Nueva Zelanda", "OFC", 50),
]

MEDIA_MUNDIAL = {n: m for n, _, _, m in MUNDIAL_CLUBES}
PAIS_MUNDIAL = {n: p for n, p, _, _ in MUNDIAL_CLUBES}
CONF_MUNDIAL = {n: c for n, _, c, _ in MUNDIAL_CLUBES}


def clubes_de(confederacion):
    """Nombres de los clubes de una confederación, de mayor a menor media."""
    return sorted((n for n, _, c, _ in MUNDIAL_CLUBES if c == confederacion),
                  key=lambda n: -MEDIA_MUNDIAL[n])


assert len(MEDIA_MUNDIAL) == len(MUNDIAL_CLUBES), "Hay clubes del Mundial con nombre repetido"

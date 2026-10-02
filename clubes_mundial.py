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
    ("Paris Saint-Germain", "Francia", "UEFA", 90, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/160.png&h=96&w=96"),
    ("Real Madrid", "España", "UEFA", 90, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/86.png&h=96&w=96"),
    ("Manchester City", "Inglaterra", "UEFA", 90, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/382.png&h=96&w=96"),
    ("Bayern Múnich", "Alemania", "UEFA", 90, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/132.png&h=96&w=96"),
    ("Arsenal (ING)", "Inglaterra", "UEFA", 90, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/359.png&h=96&w=96"),
    ("Liverpool (ING)", "Inglaterra", "UEFA", 90, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/364.png&h=96&w=96"),
    ("FC Barcelona", "España", "UEFA", 90, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/83.png&h=96&w=96"),
    ("Inter de Milán", "Italia", "UEFA", 88, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/110.png&h=96&w=96"),
    ("Chelsea", "Inglaterra", "UEFA", 90, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/363.png&h=96&w=96"),
    ("Atlético Madrid", "España", "UEFA", 88, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/1068.png&h=96&w=96"),
    ("Borussia Dortmund", "Alemania", "UEFA", 86, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/124.png&h=96&w=96"),
    ("Bayer Leverkusen", "Alemania", "UEFA", 85, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/131.png&h=96&w=96"),
    ("Juventus", "Italia", "UEFA", 83, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/111.png&h=96&w=96"),
    ("Napoli", "Italia", "UEFA", 83, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/114.png&h=96&w=96"),
    ("Tottenham", "Inglaterra", "UEFA", 79, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/367.png&h=96&w=96"),
    ("Milan", "Italia", "UEFA", 82, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/103.png&h=96&w=96"),
    ("Atalanta", "Italia", "UEFA", 81, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/105.png&h=96&w=96"),
    ("Benfica", "Portugal", "UEFA", 80, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/1929.png&h=96&w=96"),
    ("Sporting CP", "Portugal", "UEFA", 80, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/2250.png&h=96&w=96"),
    ("Newcastle United", "Inglaterra", "UEFA", 80, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/361.png&h=96&w=96"),
    ("Aston Villa", "Inglaterra", "UEFA", 83, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/362.png&h=96&w=96"),
    ("Manchester United", "Inglaterra", "UEFA", 84, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/360.png&h=96&w=96"),
    ("Porto", "Portugal", "UEFA", 80, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/437.png&h=96&w=96"),
    ("Roma", "Italia", "UEFA", 82, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/104.png&h=96&w=96"),
    ("Olympique de Marsella", "Francia", "UEFA", 79, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/176.png&h=96&w=96"),
    ("Sevilla", "España", "UEFA", 79, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/243.png&h=96&w=96"),
    ("RB Leipzig", "Alemania", "UEFA", 80, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/11420.png&h=96&w=96"),
    ("Monaco", "Francia", "UEFA", 79, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/174.png&h=96&w=96"),
    ("Lyon", "Francia", "UEFA", 79, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/167.png&h=96&w=96"),
    ("Ajax", "Países Bajos", "UEFA", 76, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/139.png&h=96&w=96"),
    ("Lille", "Francia", "UEFA", 78, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/166.png&h=96&w=96"),
    # AFC
    ("Al-Hilal", "Arabia Saudita", "AFC", 80, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/929.png&h=96&w=96"),
    ("Al-Ahli", "Arabia Saudita", "AFC", 78, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/8346.png&h=96&w=96"),
    ("Al-Nassr", "Arabia Saudita", "AFC", 77, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/817.png&h=96&w=96"),
    ("Al-Ittihad", "Arabia Saudita", "AFC", 76, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/2276.png&h=96&w=96"),
    ("Vissel Kobe", "Japón", "AFC", 72, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/7477.png&h=96&w=96"),
    ("Kashima Antlers", "Japón", "AFC", 71, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/7115.png&h=96&w=96"),
    ("Gamba Osaka", "Japón", "AFC", 69, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/7102.png&h=96&w=96"),
    ("Urawa Reds D.", "Japón", "AFC", 70, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/3385.png&h=96&w=96"),
    ("Kawasaki Frontale", "Japón", "AFC", 68, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/7112.png&h=96&w=96"),
    ("Ulsan HD", "Corea del Sur", "AFC", 68, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/7120.png&h=96&w=96"),
    ("Al-Sadd", "Qatar", "AFC", 66, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/7135.png&h=96&w=96"),
    ("Al-Duhail", "Qatar", "AFC", 66, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/12008.png&h=96&w=96"),
    ("Shabab Al-Ahli", "Emiratos Árabes Unidos", "AFC", 63, "https://img.a.transfermarkt.technology/wappen/head/60529.png?lm=1789463064"),
    ("Al-Ain", "Emiratos Árabes Unidos", "AFC", 66, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/7128.png&h=96&w=96"),
    ("Newcastle Jets", "Australia", "AFC", 57, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/5323.png&h=96&w=96"),
    ("Adelade United FC", "Australia", "AFC", 56, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/5321.png&h=96&w=96"),
    ("Shanghai Port", "China", "AFC", 60, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/15515.png&h=96&w=96"),
    # CAF
    ("Al Ahly", "Egipto", "CAF", 75, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/10207.png&h=96&w=96"),
    ("Pyramids", "Egipto", "CAF", 72, "https://img.a.transfermarkt.technology/wappen/head/44664.png?lm=1789461893"),
    ("Mamelodi Sundowns", "Sudáfrica", "CAF", 71, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/7084.png&h=96&w=96"),
    ("Wydad Casablanca", "Marruecos", "CAF", 70),
    ("Espérance de Tunis", "Túnez", "CAF", 70),
    ("Zamalek", "Egipto", "CAF", 68),
    ("RS Berkane", "Marruecos", "CAF", 66),
    ("Orlando Pirates", "Sudáfrica", "CAF", 66, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/7085.png&h=96&w=96"),
    ("Raja Casablanca", "Marruecos", "CAF", 64),
    ("TP Mazembe", "RD Congo", "CAF", 62),
    # CONCACAF
    ("Club América", "México", "CONCACAF", 77, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/227.png&h=96&w=96"),
    ("Monterrey", "México", "CONCACAF", 76, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/220.png&h=96&w=96"),
    ("Cruz Azul", "México", "CONCACAF", 76, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/218.png&h=96&w=96"),
    ("Toluca", "México", "CONCACAF", 74, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/223.png&h=96&w=96"),
    ("Tigres", "México", "CONCACAF", 74, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/232.png&h=96&w=96"),
    ("León", "México", "CONCACAF", 74, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/228.png&h=96&w=96"),
    ("Pachuca", "México", "CONCACAF", 72, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/234.png&h=96&w=96"),
    ("Guadalajara", "México", "CONCACAF", 72, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/219.png&h=96&w=96"),
    ("Queretaro", "México", "CONCACAF", 72, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/222.png&h=96&w=96"),
    ("Inter Miami", "Estados Unidos", "CONCACAF", 75, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/20232.png&h=96&w=96"),
    ("LA Galaxy", "Estados Unidos", "CONCACAF", 74, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/187.png&h=96&w=96"),
    ("Columbus Crew", "Estados Unidos", "CONCACAF", 69, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/183.png&h=96&w=96"),
    ("Seattle Sounders", "Estados Unidos", "CONCACAF", 70, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/9726.png&h=96&w=96"),
    ("FC Cincinnati", "Estados Unidos", "CONCACAF", 70, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/18267.png&h=96&w=96"),
    ("Nashvilel SC", "Estados Unidos", "CONCACAF", 70, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/18986.png&h=96&w=96"),
    ("Vancouver Whitecaps", "Estados Unidos", "CONCACAF", 70, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/9727.png&h=96&w=96"),
    ("Toronto FC", "Estados Unidos", "CONCACAF", 68, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/7318.png&h=96&w=96"),
    ("New York City FC", "Estados Unidos", "CONCACAF", 68, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/17606.png&h=96&w=96"),
    ("D.C. United", "Estados Unidos", "CONCACAF", 68, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/193.png&h=96&w=96"),
    ("Atlanta United FC", "Estados Unidos", "CONCACAF", 68, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/18418.png&h=96&w=96"),
    # OFC
    ("Auckland City", "Nueva Zelanda", "OFC", 50, "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/7279.png&h=96&w=96"),
]

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
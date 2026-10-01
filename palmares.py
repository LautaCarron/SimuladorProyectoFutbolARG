"""Palmarés histórico oficial de cada liga y copa, hasta 2025 inclusive (la temporada 1 del
simulador es 2026, así que lo que se gana desde ahí lo suman las temporadas simuladas).

Fuente: Wikipedia en español (tablas de palmarés de cada torneo, con datos de la AFA y la CONMEBOL),
contado temporada por temporada. Los nombres están adaptados a los del simulador (p. ej. Vélez,
Ferro, Talleres (RE)); los clubes históricos que ya no juegan (Alumni, Lomas Athletic, etc.)
figuran igual. Nombres anteriores sumados al club actual: Deportivo Italiano = Sportivo Italiano,
Atlético Campana = Villa Dálmine."""

import copy

PALMARES = {
    # Primera División · campeonatos oficiales (era amateur + profesional). Incluye el Clausura 2025 (Estudiantes), el Apertura 2025 (Platense) y el Campeón de Liga 2025 (Rosario Central).
    "hist_primera": {
        "River Plate": 38, "Boca Juniors": 35, "Racing": 18, "Independiente": 16, "San Lorenzo": 15,
        "Vélez": 11, "Alumni": 10, "Estudiantes (LP)": 7, "Lomas Athletic": 6, "Newell's": 6, "Huracán": 5,
        "Rosario Central": 5, "Argentinos Juniors": 3, "Belgrano Athletic": 3, "Estudiantil Porteño": 2,
        "Ferro": 2, "Lanús": 2, "Porteño": 2, "Quilmes": 2, "Arsenal": 1, "Banfield": 1, "Chacarita": 1,
        "Dock Sud": 1, "Gimnasia (LP)": 1, "Old Caledonians": 1, "Platense": 1, "Saint Andrew's": 1,
        "Sportivo Barracas": 1,
    },
    # Primera Nacional / B Nacional · desde 1986-87 (2014 y 2019-20 sin campeón).
    "hist_nacional": {
        "Banfield": 3, "Olimpo": 3, "Aldosivi": 2, "Argentinos Juniors": 2, "Atlético Tucumán": 2,
        "Atlético de Rafaela": 2, "Huracán": 2, "Instituto": 2, "Talleres": 2, "Arsenal": 1, "Belgrano": 1,
        "Chaco For Ever": 1, "Deportivo Armenio": 1, "Estudiantes (LP)": 1, "Gimnasia (Jujuy)": 1,
        "Gimnasia (Mendoza)": 1, "Godoy Cruz": 1, "Huracán (Corrientes)": 1, "Independiente Rivadavia": 1,
        "Lanús": 1, "Mandiyú (Corrientes)": 1, "Quilmes": 1, "River Plate": 1, "Rosario Central": 1,
        "San Martín (Tucumán)": 1, "Sarmiento (Junín)": 1, "Tigre": 1, "Tiro Federal (Rosario)": 1,
    },
    # Torneo Federal A · desde 2014 (en 2014, los 5 ganadores de zona; 2019-20 sin campeón).
    "hist_federal": {
        "Central Córdoba (SdE)": 2, "Agropecuario": 1, "Central Norte": 1, "Ciudad de Bolívar": 1,
        "Deportivo Madryn": 1, "Estudiantes (Río Cuarto)": 1, "Gimnasia y Tiro": 1, "Guillermo Brown": 1,
        "Güemes": 1, "Juventud Unida (Gualeguaychú)": 1, "Racing (Córdoba)": 1, "San Martín (Tucumán)": 1,
        "Sportivo Estudiantes (San Luis)": 1, "Talleres": 1, "Unión (Mar del Plata)": 1,
    },
    # Primera B Metropolitana · desde 1986-87, como tercera categoría (2014 y 2019-20 sin campeón).
    "hist_pb": {
        "Almirante Brown": 3, "All Boys": 2, "Atlanta": 2, "Deportivo Morón": 2, "Flandria": 2, "Platense": 2,
        "Sarmiento (Junín)": 2, "Sportivo Italiano": 2, "Talleres (RE)": 2, "Argentinos de Rosario": 1,
        "Barracas Central": 1, "Brown de Adrogué": 1, "Central Cordoba de Rosario": 1, "Chacarita": 1,
        "Colegiales": 1, "Defensa y Justicia": 1, "Defensores Unidos": 1, "Defensores de Belgrano": 1,
        "Deportivo Español": 1, "El Porvenir": 1, "Estudiantes (BA)": 1, "Ferro": 1, "Ituzaingó": 1,
        "Midland": 1, "Nueva Chicago": 1, "Quilmes": 1, "Tigre": 1, "Villa Dálmine": 1, "Villa San Carlos": 1,
    },
    # Primera C Metropolitana · desde 1986-87, como cuarta categoría (2014 y 2019-20 sin campeón).
    "hist_pc": {
        "Colegiales": 3, "Argentino (Q)": 2, "Berazategui": 2, "Cambaceres": 2, "Defensores Unidos": 2,
        "Deportivo Laferrere": 2, "Deportivo Merlo": 2, "Excursionistas": 2, "Villa Dálmine": 2,
        "Acassuso": 1, "Argentino de Merlo": 1, "Argentinos de Rosario": 1, "Barracas Central": 1,
        "Camioneros": 1, "Cañuelas": 1, "Central Cordoba de Rosario": 1, "Comunicaciones": 1,
        "Defensores de Belgrano": 1, "Dock Sud": 1, "Flandria": 1, "General Lamadrid": 1, "Ituzaingó": 1,
        "Real Pilar": 1, "Sacachispas": 1, "San Telmo": 1, "Sportivo Italiano": 1, "Temperley": 1,
        "UAI Urquiza": 1, "Villa San Carlos": 1,
    },
    # Copa Argentina · 1969 y desde 2011-12.
    "hist_copa": {
        "Boca Juniors": 4, "River Plate": 3, "Arsenal": 1, "Central Córdoba (SdE)": 1, "Estudiantes (LP)": 1,
        "Huracán": 1, "Independiente Rivadavia": 1, "Patronato": 1, "Rosario Central": 1,
    },
    # Supercopa Argentina · desde 2012 (campeón de Primera vs. ganador de la Copa Argentina). Ediciones
    # 2012-2019 y 2022-2024 (la de 2024 se jugó en septiembre de 2025); no se jugaron 2020 ni 2021.
    "hist_super": {
        "River Plate": 3, "Boca Juniors": 2, "Vélez": 2, "Arsenal": 1, "Huracán": 1, "Lanús": 1,
        "San Lorenzo": 1,
    },
    # Copa Libertadores · 1960-2025.
    "hist_lib": {
        "Independiente": 7, "Boca Juniors": 6, "Peñarol": 5, "Estudiantes (LP)": 4, "Flamengo": 4,
        "River Plate": 4, "Grêmio": 3, "Nacional": 3, "Olimpia": 3, "Palmeiras": 3, "Santos": 3,
        "São Paulo": 3, "Atlético Nacional": 2, "Cruzeiro": 2, "Internacional": 2, "Argentinos Juniors": 1,
        "Atlético-MG": 1, "Botafogo": 1, "Colo Colo": 1, "Corinthians": 1, "Fluminense": 1,
        "Liga de Quito": 1, "Once Caldas": 1, "Racing": 1, "San Lorenzo": 1, "Vasco da Gama": 1, "Vélez": 1,
    },
    # Copa Sudamericana · 2002-2025.
    "hist_sud": {
        "Athletico-PR": 2, "Boca Juniors": 2, "Independiente": 2, "Independiente del Valle": 2, "Lanús": 2,
        "Liga de Quito": 2, "Arsenal": 1, "Chapecoense": 1, "Cienciano del Cusco": 1, "Defensa y Justicia": 1,
        "Independiente Santa Fe": 1, "Internacional": 1, "Pachuca": 1, "Racing": 1, "River Plate": 1,
        "San Lorenzo": 1, "São Paulo": 1, "Universidad de Chile": 1,
    },
    # Recopa Sudamericana · 1989-2025 (la de 2026 se juega en el simulador).
    "hist_rec": {
        "Boca Juniors": 4, "River Plate": 3, "Grêmio": 2, "Internacional": 2, "Liga de Quito": 2,
        "Olimpia": 2, "São Paulo": 2, "Atlético Nacional": 1, "Atlético-MG": 1, "Cienciano del Cusco": 1,
        "Colo Colo": 1, "Corinthians": 1, "Cruzeiro": 1, "Defensa y Justicia": 1, "Flamengo": 1,
        "Fluminense": 1, "Independiente": 1, "Independiente del Valle": 1, "Nacional": 1, "Palmeiras": 1,
        "Racing": 1, "Santos": 1, "Vélez": 1,
    },
}


def palmares_inicial():
    """Copia del palmarés histórico para una partida nueva (cada partida suma sus títulos)."""
    return copy.deepcopy(PALMARES)
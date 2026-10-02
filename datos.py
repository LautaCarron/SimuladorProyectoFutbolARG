"""Datos: equipos, medias, escudos, origen y región de cada club.

Es el único archivo que hay que tocar para cambiar planteles, medias iniciales o
escudos. No tiene lógica de simulación.
"""

import streamlit as st

from clubes_int import CLUBES_INT, OSCUROS_INT
from regional import GRUPO_FEDERAL_REG, REGIONAL
from clubes_mundial import MUNDIAL_CLUBES

# ----------------------------------------------------------------------------
# DATOS: equipos reales de la temporada 2026 (medias orientativas, escala ~40-95).
# Primera: 30 equipos (ESPN, Liga Profesional 2026) · Primera Nacional: 36 (ESPN,
# Primera Nacional 2026) · debajo de la Primera Nacional el fútbol argentino se divide
# geográficamente: Federal A (clubes del interior, indirectamente afiliados) y Primera B
# (clubes metropolitanos, CABA/Gran Buenos Aires, directamente afiliados). Debajo de la
# Primera B está la Primera C. Todas las categorías se simulan (ver torneos.py).
# ----------------------------------------------------------------------------
EQUIPOS = {
    "River Plate": 80, "Boca Juniors": 80, "Estudiantes (LP)": 79,
    "Racing": 77, "Vélez": 79, "Rosario Central": 77,
    "Talleres": 76, "Lanús": 77, "Huracán": 74,
    "Independiente": 76, "Belgrano": 76, "San Lorenzo": 74,
    "Argentinos Juniors": 75, "Independiente Rivadavia": 74, "Defensa y Justicia": 73,
    "Gimnasia (LP)": 72, "Unión": 72, "Newell's": 71,
    "Platense": 70, "Instituto": 71, "Tigre": 70,
    "Banfield": 70, "Central Córdoba (SdE)": 70, "Barracas Central": 68,
    "Atlético Tucumán": 68, "Sarmiento (Junín)": 68, "Deportivo Riestra": 64,
    "Gimnasia (Mendoza)": 69, "Estudiantes (Río Cuarto)": 63, "Aldosivi": 67,
}
EQUIPOS_B = {
    "Godoy Cruz": 68, "Colón": 68, "Almagro": 62,
    "Quilmes": 64, "Patronato": 64, "San Martín (San Juan)": 64,
    "Ferro": 64, "Chacarita": 61, "Atlanta": 62,
    "Nueva Chicago": 59, "All Boys": 60, "San Martín (Tucumán)": 63,
    "Deportivo Madryn": 62, "Temperley": 63, "Deportivo Morón": 64,
    "Almirante Brown": 59, "Racing (Córdoba)": 60, "Gimnasia (Jujuy)": 64,
    "Deportivo Maipú": 60, "Güemes": 50, "Agropecuario": 60,
    "Chaco For Ever": 58, "Defensores de Belgrano": 58, "Mitre (SdE)": 58,
    "Central Norte": 58, "Atlético de Rafaela": 58, "Ciudad de Bolívar": 57,
    "Tristán Suárez": 57, "Los Andes": 57, "Estudiantes (BA)": 57,
    "San Miguel": 55, "Colegiales": 55,
    "Midland": 53, "San Telmo": 54,
    "Gimnasia y Tiro": 61, "Acassuso": 53,
}
# Federal A (interior): ascienden 4 a la Primera Nacional (1°, 2°, 3° y el campeón del
# reducido) y bajan a esta categoría los descendidos de la B que sean del interior.
EQUIPOS_FEDERAL = {
    "9 de Julio (Rafaela)": 51, "Atlético Escobar": 45, "Defensores de Belgrano (VR)": 49,
    "Douglas Haig": 53, "El Linqueño": 47, "Gimnasia (Chivilcoy)": 50,
    "Gimnasia (CdU)": 51, "Independiente (Chivilcoy)": 50, "Sportivo Las Parejas": 49,
    "Sportivo Belgrano": 51, "Bartolomé Mitre (Posadas)": 48, "Boca Unidos": 51,
    "Defensores de Vilelas": 44, "Juventud Antoniana": 50, "San Martín (Formosa)": 50,
    "Sarmiento (La Banda)": 50, "Sarmiento (Resistencia)": 47, "Sol de América (Formosa)": 48,
    "Tucumán Central": 44, "Argentino (Monte Maíz)": 51, "Atenas (Río Cuarto)": 50,
    "Cipolletti": 51, "Costa Brava": 49, "Deportivo Rincón": 44,
    "FADEP": 44, "Huracán Las Heras": 50, "Juventud Unida Universitario": 48,
    "San Martín (Mendoza)": 49, "Alvarado": 53, "Círculo Deportivo": 47,
    "Germinal": 48, "Guillermo Brown": 53, "Kimberley": 49,
    "Olimpo": 53, "Ramón Santamarina": 49, "Sol de Mayo": 47,
    "Villa Mitre": 50,
}
# Primera B (Metropolitana): clubes de CABA / Gran Buenos Aires. Es el equivalente del
# Federal A pero para el lado metropolitano: liga todos contra todos ida y vuelta, ascienden
# 2 a la Primera Nacional y bajan 2 a la Primera C.
EQUIPOS_PRIMERA_B = {
    "Excursionistas": 50, "Comunicaciones": 50,
    "UAI Urquiza": 40, "Cañuelas": 44, "Liniers": 44,
    "Argentino de Merlo": 40, "Talleres (RE)": 50, "Argentino (Q)": 40,
    "Dock Sud": 40, "Fénix": 40, "Deportivo Laferrere": 45,
    "Villa San Carlos": 47, "Villa Dálmine": 45, "Deportivo Merlo": 40,
    "Brown de Adrogué": 47, "Arsenal": 50, "Camioneros": 47,
    "Defensores Unidos": 42, "Sportivo Italiano": 44, "Flandria": 43,
}
# Primera C (Metropolitana)
EQUIPOS_PRIMERA_C = {
    "Deportivo Español": 40, "Berazategui": 33, "Yupanqui": 30,
    "Victoriano Arenas": 37, "Atlas": 36, "Cambaceres": 33,
    "Central Ballester": 32, "El Porvenir": 35, "Ituzaingó": 38,
    "Puerto Nuevo": 31, "Real Pilar": 41, "Sacachispas": 38,
    "Argentinos de Rosario": 25, "Central Cordoba de Rosario":30,
    "Paraguayo":25,
}
# Torneo Regional Amateur: 245 clubes en 12 regiones (datos completos en regional.py,
# generado del JSON oficial del torneo). Acá sólo nombre -> media inicial.
EQUIPOS_REGIONAL = {x["nombre"]: x["media"] for x in REGIONAL}


# Escudos oficiales: ESPN (Primera y Primera Nacional), Wikimedia Commons / Wikipedia y
# TheSportsDB (Federal A). Van ligados al nombre: si un club cambia de categoría,
# conserva su nombre y su escudo.
ESCUDOS = {
    "River Plate": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/16.png&h=96&w=96",
    "Boca Juniors": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/5.png&h=96&w=96",
    "Estudiantes (LP)": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/8.png&h=96&w=96",
    "Racing": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/15.png&h=96&w=96",
    "Vélez": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/21.png&h=96&w=96",
    "Rosario Central": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/17.png&h=96&w=96",
    "Talleres": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/19.png&h=96&w=96",
    "Lanús": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/12.png&h=96&w=96",
    "Huracán": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/10.png&h=96&w=96",
    "Independiente": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/11.png&h=96&w=96",
    "Belgrano": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/4.png&h=96&w=96",
    "San Lorenzo": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/18.png&h=96&w=96",
    "Argentinos Juniors": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/3.png&h=96&w=96",
    "Independiente Rivadavia": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/9744.png&h=96&w=96",
    "Defensa y Justicia": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/8950.png&h=96&w=96",
    "Gimnasia (LP)": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/9.png&h=96&w=96",
    "Unión": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/20.png&h=96&w=96",
    "Newell's": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/14.png&h=96&w=96",
    "Platense": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/7764.png&h=96&w=96",
    "Instituto": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/2975.png&h=96&w=96",
    "Tigre": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/7767.png&h=96&w=96",
    "Banfield": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/235.png&h=96&w=96",
    "Central Córdoba (SdE)": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/11989.png&h=96&w=96",
    "Barracas Central": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/10060.png&h=96&w=96",
    "Atlético Tucumán": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/9785.png&h=96&w=96",
    "Sarmiento (Junín)": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/10158.png&h=96&w=96",
    "Deportivo Riestra": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/17702.png&h=96&w=96",
    "Gimnasia (Mendoza)": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/11972.png&h=96&w=96",
    "Estudiantes (Río Cuarto)": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/19685.png&h=96&w=96",
    "Aldosivi": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/9739.png&h=96&w=96",
    "Godoy Cruz": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/6756.png&h=96&w=96",
    "Colón": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/7.png&h=96&w=96",
    "Almagro": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/2.png&h=96&w=96",
    "Quilmes": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/2741.png&h=96&w=96",
    "Patronato": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/10374.png&h=96&w=96",
    "San Martín (San Juan)": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/7845.png&h=96&w=96",
    "Ferro": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/9743.png&h=96&w=96",
    "Chacarita": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/6.png&h=96&w=96",
    "Atlanta": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/10146.png&h=96&w=96",
    "Nueva Chicago": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/236.png&h=96&w=96",
    "All Boys": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/9786.png&h=96&w=96",
    "San Martín (Tucumán)": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/17814.png&h=96&w=96",
    "Deportivo Madryn": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/18260.png&h=96&w=96",
    "Temperley": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/10162.png&h=96&w=96",
    "Deportivo Morón": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/10154.png&h=96&w=96",
    "Almirante Brown": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/9740.png&h=96&w=96",
    "Racing (Córdoba)": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/19145.png&h=96&w=96",
    "Gimnasia (Jujuy)": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/5263.png&h=96&w=96",
    "Deportivo Maipú": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/11978.png&h=96&w=96",
    "Güemes": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/18284.png&h=96&w=96",
    "Agropecuario": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/13913.png&h=96&w=96",
    "Chaco For Ever": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/11963.png&h=96&w=96",
    "Defensores de Belgrano": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/10151.png&h=96&w=96",
    "Mitre (SdE)": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/11990.png&h=96&w=96",
    "Central Norte": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/11993.png&h=96&w=96",
    "Atlético de Rafaela": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/9747.png&h=96&w=96",
    "Ciudad de Bolívar": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/21799.png&h=96&w=96",
    "Tristán Suárez": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/10163.png&h=96&w=96",
    "Los Andes": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/13.png&h=96&w=96",
    "Estudiantes (BA)": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/17352.png&h=96&w=96",
    "San Miguel": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/10058.png&h=96&w=96",
    "Colegiales": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/10149.png&h=96&w=96",
    "9 de Julio (Rafaela)": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/77/Logo9dejulio.png/120px-Logo9dejulio.png",
    "Atlético Escobar": "https://r2.thesportsdb.com/images/media/team/badge/pzrlm61772810503.png/small",
    "Defensores de Belgrano (VR)": "https://upload.wikimedia.org/wikipedia/en/thumb/e/e0/Def_Belgrano_VR_logo.svg/120px-Def_Belgrano_VR_logo.svg.png",
    "Douglas Haig": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/21/Douglas_Haig_de_Pergamino.png/120px-Douglas_Haig_de_Pergamino.png",
    "El Linqueño": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/31/Club_El_Linque%C3%B1o.png/120px-Club_El_Linque%C3%B1o.png",
    "Gimnasia (Chivilcoy)": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/53/Gimnasia_y_Esgrima_de_Chivilcoy.png/120px-Gimnasia_y_Esgrima_de_Chivilcoy.png",
    "Gimnasia (CdU)": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/eb/ESCUDOORIGINALGIMNASIA.gif/120px-ESCUDOORIGINALGIMNASIA.gif",
    "Independiente (Chivilcoy)": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/27/EscudoOficialIndependienteChivilcoy.png/120px-EscudoOficialIndependienteChivilcoy.png",
    "Sportivo Las Parejas": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/63/Sportivo_lasparejas_2021.png/120px-Sportivo_lasparejas_2021.png",
    "Sportivo Belgrano": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/94/Escudo_del_Club_Sportivo_Belgrano_de_San_Francisco.svg/120px-Escudo_del_Club_Sportivo_Belgrano_de_San_Francisco.svg.png",
    "Bartolomé Mitre (Posadas)": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/18/ESCUDO_MITRE.png/120px-ESCUDO_MITRE.png",
    "Boca Unidos": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/37/Escudo_del_Club_Atl%C3%A9tico_Boca_Unidos.svg/120px-Escudo_del_Club_Atl%C3%A9tico_Boca_Unidos.svg.png",
    "Defensores de Vilelas": "https://r2.thesportsdb.com/images/media/team/badge/6kqizu1772810693.png/small",
    "Juventud Antoniana": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/Escudo_Oficial_Centro_Juventud_Antoniana.svg/120px-Escudo_Oficial_Centro_Juventud_Antoniana.svg.png",
    "San Martín (Formosa)": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/02/Club_Sportivo_General_San_Mart%C3%ADn.svg/120px-Club_Sportivo_General_San_Mart%C3%ADn.svg.png",
    "Sarmiento (La Banda)": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d6/Escudo_Sarmiento_Estrellas_Doradas.png/120px-Escudo_Sarmiento_Estrellas_Doradas.png",
    "Sarmiento (Resistencia)": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e6/Sarmiento_%28Resistencia%29.png/120px-Sarmiento_%28Resistencia%29.png",
    "Sol de América (Formosa)": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bd/Sol_de_Am%C3%A9rica.png/120px-Sol_de_Am%C3%A9rica.png",
    "Tucumán Central": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Escudo_Club_Tucum%C3%A1n_Central.svg/120px-Escudo_Club_Tucum%C3%A1n_Central.svg.png",
    "Argentino (Monte Maíz)": "https://upload.wikimedia.org/wikipedia/commons/8/8b/Argentino.png",
    "Atenas (Río Cuarto)": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/62/Club_Sportivo_y_Biblioteca_Atenas_Rio_Cuarto_Escudo_Logo.png/120px-Club_Sportivo_y_Biblioteca_Atenas_Rio_Cuarto_Escudo_Logo.png",
    "Cipolletti": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8d/Escudo_de_Cipo.png/120px-Escudo_de_Cipo.png",
    "Costa Brava": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0e/Club_Atl%C3%A9tico_Costa_Brava.png/120px-Club_Atl%C3%A9tico_Costa_Brava.png",
    "Deportivo Rincón": "https://r2.thesportsdb.com/images/media/team/badge/djv8tn1775755034.png/small",
    "FADEP": "https://r2.thesportsdb.com/images/media/team/badge/979ips1772811586.png/small",
    "Huracán Las Heras": "https://r2.thesportsdb.com/images/media/team/badge/kgaxdg1678854332.png/small",
    "Juventud Unida Universitario": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b0/Escudo_del_Club_Juventud_de_Unida_San_Luis.svg/120px-Escudo_del_Club_Juventud_de_Unida_San_Luis.svg.png",
    "San Martín (Mendoza)": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/aa/Atl%C3%A9tico_Club_San_Mart%C3%ADn.png/120px-Atl%C3%A9tico_Club_San_Mart%C3%ADn.png",
    "Alvarado": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e7/Escudo_del_Club_Alvarado_%28Mar_del_Plata%29_-_BSAS.svg/120px-Escudo_del_Club_Alvarado_%28Mar_del_Plata%29_-_BSAS.svg.png",
    "Círculo Deportivo": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Circulo_deportivo.png/120px-Circulo_deportivo.png",
    "Germinal": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/Club_Atl%C3%A9tico_Germinal.svg/120px-Club_Atl%C3%A9tico_Germinal.svg.png",
    "Guillermo Brown": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bb/Escudo_de_Guillermo_Brown.svg/120px-Escudo_de_Guillermo_Brown.svg.png",
    "Kimberley": "https://r2.thesportsdb.com/images/media/team/badge/l53nr11734114727.png/small",
    "Olimpo": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ea/EscudoOlimpo.svg/120px-EscudoOlimpo.svg.png",
    "Ramón Santamarina": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/93/Escudo_del_Club_Santa_Marina_de_Tandil.svg/120px-Escudo_del_Club_Santa_Marina_de_Tandil.svg.png",
    "Sol de Mayo": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/Club_Sol_de_Mayo.png/120px-Club_Sol_de_Mayo.png",
    "Villa Mitre": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b1/Escudo_Club_Villa_Mitre.png/120px-Escudo_Club_Villa_Mitre.png",
    "Acassuso": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/10145.png&h=96&w=96",
    "Gimnasia y Tiro": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/10743.png&h=96&w=96",
    "Midland": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/10109.png&h=96&w=96",
    "San Telmo": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/10157.png&h=96&w=96",
    "Argentino de Merlo": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/17700.png&h=96&w=96",
    "Arsenal": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/2635.png&h=96&w=96",
    "Atlas": "https://thumb.wikimedia.org/wikipedia/commons/thumb/6/6c/Club_Atletico_Atlas.svg/960px-Club_Atletico_Atlas.svg.png?utm_source=es.wikipedia.org&utm_campaign=imageinfo&utm_content=thumbnail",
    "Berazategui": "https://r2.thesportsdb.com/images/media/team/badge/syrkoa1734118369.png/small",
    "Brown de Adrogué": "https://upload.wikimedia.org/wikipedia/commons/b/b8/Escudo_del_Club_Brown_de_Adrogue.svg?utm_source=commons.wikimedia.org&utm_campaign=index&utm_content=original",
    "Cambaceres": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/17694.png&h=96&w=96",
    "Cañuelas": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f4/Escudo_del_Ca%C3%B1uelas_F%C3%BAtbol_Club.svg/120px-Escudo_del_Ca%C3%B1uelas_F%C3%BAtbol_Club.svg.png",
    "Central Ballester": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/10100.png&h=96&w=96",
    "Comunicaciones": "https://upload.wikimedia.org/wikipedia/commons/e/e7/Club_comunicaciones_ba_logo.png?utm_source=es.wikipedia.org&utm_campaign=index&utm_content=original",
    "Deportivo Español": "https://r2.thesportsdb.com/images/media/team/badge/kn3b8o1734118782.png/small",
    "Excursionistas": "https://thumb.wikimedia.org/wikipedia/commons/thumb/1/10/Club_Atletico_Excursionistas.svg/500px-Club_Atletico_Excursionistas.svg.png?utm_source=es.wikipedia.org&utm_campaign=imageinfo&utm_content=thumbnail",
    "Deportivo Laferrere": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/17695.png&h=96&w=96",
    "Deportivo Merlo": "https://thumb.wikimedia.org/wikipedia/commons/thumb/8/80/Escudo_del_Club_Deportivo_Merlo.svg/960px-Escudo_del_Club_Deportivo_Merlo.svg.png?utm_source=es.wikipedia.org&utm_campaign=imageinfo&utm_content=thumbnail",
    "Dock Sud": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/10103.png&h=96&w=96",
    "El Porvenir": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/10061.png&h=96&w=96",
    "Fénix": "https://r2.thesportsdb.com/images/media/team/badge/qti6qf1677993533.png/small",
    "Ituzaingó": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/10105.png&h=96&w=96",
    "Villa Dálmine": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/10064.png&h=96&w=96",
    "Camioneros": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/18662.png&h=96&w=96",
    "Liniers": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/10107.png&h=96&w=96",
    "Defensores Unidos": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/17697.png&h=96&w=96",
    "Sacachispas": "https://upload.wikimedia.org/wikipedia/commons/1/14/Logo_del_Sacachispas_F%C3%BAtbol_Club.svg?utm_source=commons.wikimedia.org&utm_campaign=index&utm_content=original",
    "Real Pilar":"https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/18844.png&h=96&w=96",
    "Puerto Nuevo": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b1/Club_Atl%C3%A9tico_Puerto_Nuevo.svg/120px-Club_Atl%C3%A9tico_Puerto_Nuevo.svg.png",
    "Yupanqui": "https://r2.thesportsdb.com/images/media/team/badge/glp53l1734121542.png/small",
    "Villa San Carlos": "https://upload.wikimedia.org/wikipedia/commons/1/11/ESCUDO_OFICIAL_DEL_CLUB_VILLA_SAN_CARLOS.png?utm_source=es.wikipedia.org&utm_campaign=index&utm_content=original",
    "Talleres (RE)": "https://upload.wikimedia.org/wikipedia/commons/9/9d/Talleres_ba_logo.png?utm_source=es.wikipedia.org&utm_campaign=index&utm_content=original",
    "UAI Urquiza": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/17705.png&h=96&w=96",
    "Victoriano Arenas": "https://upload.wikimedia.org/wikipedia/commons/6/65/Victoriano_Arenas_escudo_2025.png?utm_source=es.wikipedia.org&utm_campaign=index&utm_content=original",
    "Sportivo Italiano": "https://upload.wikimedia.org/wikipedia/commons/3/3b/Club_Sportivo_Italiano_%28Argentina%29_logo.svg?utm_source=es.wikipedia.org&utm_campaign=index&utm_content=original",
    "Flandria": "https://upload.wikimedia.org/wikipedia/commons/3/30/Club_flandria_escudo.png?utm_source=es.wikipedia.org&utm_campaign=index&utm_content=original",
    "Argentino (Q)": "https://upload.wikimedia.org/wikipedia/commons/3/33/ArgentinodeQuilmes.png?utm_source=es.wikipedia.org&utm_campaign=index&utm_content=original",
    "Argentinos de Rosario": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/10048.png&h=96&w=96",
    "Central Cordoba de Rosario": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/Club_Atl%C3%A9tico_Central_C%C3%B3rdoba_Rosario%29.svg/120px-Club_Atl%C3%A9tico_Central_C%C3%B3rdoba_Rosario%29.svg.png",
    "Paraguayo": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/10110.png&h=96&w=96",

}
# Regional Amateur: escudos del JSON del torneo (interiorfutbolero.com.ar)
ESCUDOS.update({x["nombre"]: x["escudo"] for x in REGIONAL})
# Clubes de los otros países de la CONMEBOL (copas internacionales)
ESCUDOS.update({n: url for n, _, _, url in CLUBES_INT})
# Si la fila tiene 5 elementos, agarra el nombre (x[0]) y la URL del escudo (x[4])
ESCUDOS.update({x[0]: x[4] for x in MUNDIAL_CLUBES if len(x) >= 5})

# Escudos de borde oscuro (negro, bordó, azul marino): en modo oscuro se les dibuja un
# contorno claro para que no se pierdan contra el fondo (p. ej. Central Norte).
ESCUDOS_OSCUROS = {
    "Central Norte", "Santa Cruz Futbol Club (Río Turbio)", "La Cantera (Posadas)",
    "Unión (Oncativo)", "Parque Sur (Concepción del Uruguay)", "San Lorenzo (Villa Castells)",
    "San Martín (San Juan)", "Deportivo Español", "Montecaseros",
    "Colocasi (San Francisco del Monte de Oro)", "Villa Dálmine", "Patronato", "FADEP",
    "Jorge Newbery (Comodoro Rivadavia)", "Huracán (Corrientes)", "Social Pinto",
    "Ciudad de Bolívar", "Embajadores (Olavarría)", "Río Grande (Neuquén)",
    "El Fortín (Olavarría)", "Atlético Escobar", "San Luis de la Puntilla (Belen)",
    "Defensores de Belgrano", "Deportivo Norte (Mar del Plata)", "Atlético San Julián",
    "Deportivo Trancas", "Deportivo Municipal (La Leonesa)", "Atlético Regina (Villa Regina)",
    "Talleres (Nueva Esperanza)",
}
ESCUDOS_OSCUROS |= set(OSCUROS_INT)

# Origen geográfico real de cada club: "Interior" o "Metropolitana" (CABA / Gran
# Buenos Aires). Sirve para mandar a cada equipo a su categoría real (Federal A o
# Primera B) el día que descienda del todo. Los del Federal A ya son todos del
# interior y los de Primera B ya son todos metropolitanos, así que acá sólo hace
# falta etiquetar a mano los de Primera y Primera Nacional.
ORIGEN = {
    # Primera
    "River Plate": "Metropolitana", "Boca Juniors": "Metropolitana",
    "Estudiantes (LP)": "Metropolitana", "Racing": "Metropolitana",
    "Vélez": "Metropolitana", "Rosario Central": "Metropolitana",
    "Talleres": "Interior", "Lanús": "Metropolitana",
    "Huracán": "Metropolitana", "Independiente": "Metropolitana",
    "Belgrano": "Interior", "San Lorenzo": "Metropolitana",
    "Argentinos Juniors": "Metropolitana", "Independiente Rivadavia": "Interior",
    "Defensa y Justicia": "Metropolitana", "Gimnasia (LP)": "Metropolitana",
    "Unión": "Metropolitana", "Newell's": "Metropolitana",
    "Platense": "Metropolitana", "Instituto": "Interior",
    "Tigre": "Metropolitana", "Banfield": "Metropolitana",
    "Central Córdoba (SdE)": "Interior", "Barracas Central": "Metropolitana",
    "Atlético Tucumán": "Interior", "Sarmiento (Junín)": "Metropolitana",
    "Deportivo Riestra": "Metropolitana", "Gimnasia (Mendoza)": "Interior",
    "Estudiantes (Río Cuarto)": "Interior", "Aldosivi": "Interior",
    # Primera Nacional
    "Godoy Cruz": "Interior", "Colón": "Metropolitana", "Almagro": "Metropolitana",
    "Quilmes": "Metropolitana", "Patronato": "Interior",
    "San Martín (San Juan)": "Interior", "Ferro": "Metropolitana",
    "Chacarita": "Metropolitana", "Atlanta": "Metropolitana",
    "Nueva Chicago": "Metropolitana", "All Boys": "Metropolitana",
    "San Martín (Tucumán)": "Interior", "Deportivo Madryn": "Interior",
    "Temperley": "Metropolitana", "Deportivo Morón": "Metropolitana",
    "Almirante Brown": "Metropolitana", "Racing (Córdoba)": "Interior",
    "Gimnasia (Jujuy)": "Interior", "Deportivo Maipú": "Interior",
    "Güemes": "Interior", "Agropecuario": "Interior",
    "Chaco For Ever": "Interior", "Defensores de Belgrano": "Metropolitana",
    "Mitre (SdE)": "Interior", "Central Norte": "Interior",
    "Atlético de Rafaela": "Interior", "Ciudad de Bolívar": "Interior",
    "Tristán Suárez": "Metropolitana", "Los Andes": "Metropolitana",
    "Estudiantes (BA)": "Metropolitana", "San Miguel": "Metropolitana",
    "Colegiales": "Metropolitana",
    "Midland": "Metropolitana", "San Telmo": "Metropolitana",
    "Gimnasia y Tiro": "Interior", "Acassuso": "Metropolitana",
}


def origen(nombre):
    if nombre in EQUIPOS_FEDERAL or nombre in EQUIPOS_REGIONAL:
        return "Interior"
    if nombre in EQUIPOS_PRIMERA_B or nombre in EQUIPOS_PRIMERA_C:
        return "Metropolitana"
    return ORIGEN.get(nombre, "Interior")


# Región de cada club del Federal A (y de cualquier club "Interior" de Primera o la
# Primera Nacional que algún día pueda terminar ahí): sirve para armar los 5 grupos
# de la fase 1 "por cercanía". Los que no están acá caen en "Centro" por defecto.
F_GRUPOS_NOMBRES = ["Norte", "Centro", "Buenos Aires", "Patagonia", "Cuyo"]
REGION = {
    # Federal A
    "9 de Julio (Rafaela)": "Centro", "Atlético Escobar": "Centro",
    "Defensores de Belgrano (VR)": "Buenos Aires", "Douglas Haig": "Buenos Aires",
    "El Linqueño": "Buenos Aires", "Gimnasia (Chivilcoy)": "Buenos Aires",
    "Gimnasia (CdU)": "Centro", "Independiente (Chivilcoy)": "Buenos Aires",
    "Sportivo Las Parejas": "Centro", "Sportivo Belgrano": "Centro",
    "Bartolomé Mitre (Posadas)": "Norte", "Boca Unidos": "Norte",
    "Defensores de Vilelas": "Norte", "Juventud Antoniana": "Norte",
    "San Martín (Formosa)": "Norte", "Sarmiento (La Banda)": "Norte",
    "Sarmiento (Resistencia)": "Norte", "Sol de América (Formosa)": "Norte",
    "Tucumán Central": "Norte", "Argentino (Monte Maíz)": "Centro",
    "Atenas (Río Cuarto)": "Centro", "Cipolletti": "Cuyo",
    "Costa Brava": "Patagonia", "Deportivo Rincón": "Patagonia",
    "FADEP": "Cuyo", "Huracán Las Heras": "Cuyo",
    "Juventud Unida Universitario": "Cuyo",
    "San Martín (Mendoza)": "Cuyo", "Alvarado": "Buenos Aires",
    "Círculo Deportivo": "Buenos Aires", "Germinal": "Buenos Aires",
    "Guillermo Brown": "Patagonia", "Kimberley": "Buenos Aires",
    "Olimpo": "Buenos Aires", "Ramón Santamarina": "Buenos Aires",
    "Sol de Mayo": "Patagonia", "Villa Mitre": "Buenos Aires",
    # Interior de Primera y de la Primera Nacional (por si algún día caen tan bajo)
    "Talleres": "Centro", "Belgrano": "Centro", "Independiente Rivadavia": "Cuyo", 
    "Instituto": "Centro", "Central Córdoba (SdE)": "Norte", "Atlético Tucumán": "Norte",
    "Gimnasia (Mendoza)": "Cuyo", "Estudiantes (Río Cuarto)": "Centro", "Aldosivi": "Buenos Aires",
    "Godoy Cruz": "Cuyo", "Patronato": "Centro", "San Martín (San Juan)": "Cuyo", "San Martín (Tucumán)": "Norte",
    "Deportivo Madryn": "Patagonia", "Racing (Córdoba)": "Centro",
    "Gimnasia (Jujuy)": "Norte", "Deportivo Maipú": "Cuyo",
    "Güemes": "Norte", "Agropecuario": "Buenos Aires", "Chaco For Ever": "Norte",
    "Mitre (SdE)": "Norte", "Central Norte": "Norte", "Atlético de Rafaela": "Centro",
    "Ciudad de Bolívar": "Buenos Aires", "Gimnasia y Tiro": "Norte",
}


# Clubes del Regional Amateur: si ascienden, van al grupo del Federal A de su región
REGION.update({x["nombre"]: GRUPO_FEDERAL_REG[x["region"]] for x in REGIONAL})


def region_de(nombre):
    return REGION.get(nombre, "Centro")


# Región del Torneo Regional Amateur (una de las 12 del JSON) de cada club del interior que
# no está en el JSON: los del Federal A y los del interior de Primera y la Primera Nacional.
# Es la liga que juegan si algún día descienden al Regional (se respeta su provincia/ciudad).
REGION_REGIONAL = {
    # Federal A
    "9 de Julio (Rafaela)": "Litoral", "Atlético Escobar": "AMBA y La Plata",
    "Defensores de Belgrano (VR)": "Norte Bonaerense", "Douglas Haig": "Norte Bonaerense",
    "El Linqueño": "Norte Bonaerense", "Gimnasia (Chivilcoy)": "Norte Bonaerense",
    "Gimnasia (CdU)": "Litoral", "Independiente (Chivilcoy)": "Norte Bonaerense",
    "Sportivo Las Parejas": "Litoral", "Sportivo Belgrano": "Centro",
    "Bartolomé Mitre (Posadas)": "NEA Este", "Boca Unidos": "NEA Este",
    "Defensores de Vilelas": "NEA Oeste", "Juventud Antoniana": "NOA Norte",
    "San Martín (Formosa)": "NEA Oeste", "Sarmiento (La Banda)": "NOA Sur",
    "Sarmiento (Resistencia)": "NEA Oeste", "Sol de América (Formosa)": "NEA Oeste",
    "Tucumán Central": "NOA Sur", "Argentino (Monte Maíz)": "Centro",
    "Atenas (Río Cuarto)": "Centro", "Cipolletti": "Patagonia Norte",
    "Costa Brava": "Pampeana Sur", "Deportivo Rincón": "Patagonia Norte",
    "FADEP": "Cuyo", "Huracán Las Heras": "Cuyo", "Juventud Unida Universitario": "Cuyo",
    "San Martín (Mendoza)": "Cuyo", "Alvarado": "Pampeana Sur",
    "Círculo Deportivo": "Pampeana Sur", "Germinal": "Patagonia Sur",
    "Guillermo Brown": "Patagonia Sur", "Kimberley": "Pampeana Sur",
    "Olimpo": "Pampeana Sur", "Ramón Santamarina": "Pampeana Sur",
    "Sol de Mayo": "Patagonia Norte", "Villa Mitre": "Pampeana Sur",
    # Interior de Primera
    "Talleres": "Centro", "Belgrano": "Centro", "Instituto": "Centro",
    "Estudiantes (Río Cuarto)": "Centro", "Independiente Rivadavia": "Cuyo",
    "Gimnasia (Mendoza)": "Cuyo", "Central Córdoba (SdE)": "NOA Sur",
    "Atlético Tucumán": "NOA Sur", "Aldosivi": "Pampeana Sur",
    # Interior de la Primera Nacional
    "Godoy Cruz": "Cuyo", "Deportivo Maipú": "Cuyo", "San Martín (San Juan)": "Cuyo",
    "Patronato": "Litoral", "Atlético de Rafaela": "Litoral",
    "San Martín (Tucumán)": "NOA Sur", "Güemes": "NOA Sur", "Mitre (SdE)": "NOA Sur",
    "Gimnasia (Jujuy)": "NOA Norte", "Gimnasia y Tiro": "NOA Norte", "Central Norte": "NOA Norte",
    "Racing (Córdoba)": "Centro", "Chaco For Ever": "NEA Oeste",
    "Deportivo Madryn": "Patagonia Sur", "Agropecuario": "Norte Bonaerense",
    "Ciudad de Bolívar": "Pampeana Sur",
}
REGION_REGIONAL.update({x["nombre"]: x["region"] for x in REGIONAL})
# Si aparece un club del interior sin región del Regional asignada, va a la región del
# Regional que corresponde a su grupo del Federal A
_GRUPO_A_REGION = {"Norte": "NOA Sur", "Centro": "Centro", "Buenos Aires": "Norte Bonaerense",
                   "Patagonia": "Patagonia Norte", "Cuyo": "Cuyo"}


def region_regional(nombre):
    return REGION_REGIONAL.get(nombre) or _GRUPO_A_REGION.get(region_de(nombre), "Centro")


N = len(EQUIPOS)            # Primera
NB = len(EQUIPOS_B)         # Primera Nacional
NF = len(EQUIPOS_FEDERAL)   # Federal A
NPB = len(EQUIPOS_PRIMERA_B)  # Primera B
NPC = len(EQUIPOS_PRIMERA_C)  # Primera C

_todos = (list(EQUIPOS) + list(EQUIPOS_B) + list(EQUIPOS_FEDERAL) + list(EQUIPOS_PRIMERA_B)
          + list(EQUIPOS_PRIMERA_C) + [x["nombre"] for x in REGIONAL])
if N != 30 or NB != 36 or NF < 6 or NPB < 6 or NPC < 6 or len(set(_todos)) != len(_todos):
    st.error("Hay un error en la cantidad de equipos o nombres repetidos.")
    st.stop()
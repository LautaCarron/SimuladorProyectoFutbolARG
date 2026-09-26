"""
Simulador del fútbol argentino: Primera División + Primera Nacional (B Nacional)
-------------------------------------------------------------------------------
Ejecutar con:
    python -m pip install streamlit numpy pandas
    python -m streamlit run simuladorafa.py

PRIMERA DIVISIÓN (30 equipos)
  * Fase 1: todos contra todos, 29 fechas (una vuelta).
  * Fase 2: tres zonas de 10 según la tabla (Campeonato 1-10, Intermedia 11-20,
    Descenso 21-30), 9 fechas dentro de la zona con localía invertida.
  * Destinos: 1-5 Libertadores · 6-8 Sudamericana · 11 Fase previa Libertadores
    · 12-13 Sudamericana · 28-30 descienden · 27° juega la PROMOCIÓN.

PRIMERA NACIONAL (36 equipos)
  * Fase 1: 2 zonas de 18 (A y B), una sola rueda (17 fechas) + 8 fechas
    interzonales cruzadas entre ambas zonas antes de pasar a la fase 2 (localía
    fija: cada equipo es local en 4 de esas 8 fechas).
  * Se reparten en 3 zonas de 12 y TODOS los puntos vuelven a 0:
      Campeonato: 1°-6° de cada zona · Intermedia: 7°-12° de cada zona
      Descenso: 13°-18° de cada zona.  Una sola rueda en cada una.
  * Campeonato: 1° campeón + ascenso · 2° ascenso · 3°-4° a cuartos del reducido
    · 5°-12° a octavos.   Intermedia: 1°-4° a octavos.
    Descenso: los 6 últimos descienden.
  * Reducido (14 equipos): octavos (12) -> cuartos (8: los 6 ganadores + 3°-4° de
    Campeonato) -> semifinal -> final. Todo a partido único, sin alargue: si
    empatan, penales. Localía: Campeonato siempre local frente a Intermedia; entre
    equipos de la misma zona, el que tenga más puntos.
  * Campeón del reducido asciende. El perdedor de la final juega la PROMOCIÓN
    (un partido) contra el 27° de Primera, el mejor descendido.

Cada equipo tiene una "media interna" (fuerza) que cambia cada temporada.
Los partidos se simulan con goles Poisson y cada equipo tiene una "forma del
día" aleatoria: cuanto mayor es el nivel de sorpresas, más seguido gana el
que tiene menos media.
"""

import hashlib
import html
import re
import time
import unicodedata

import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Simulador Fútbol Argentino", page_icon="⚽", layout="wide")

# ----------------------------------------------------------------------------
# DATOS: equipos reales de la temporada 2026 (medias orientativas, escala ~40-95).
# Primera: 30 equipos (ESPN, Liga Profesional 2026) · Primera Nacional: 32 (ESPN,
# Primera Nacional 2026) · debajo de la Primera Nacional el fútbol argentino se divide
# geográficamente: Federal A (clubes del interior) y Primera B (clubes metropolitanos,
# CABA/Gran Buenos Aires). Ninguna de las dos se simula todavía (no tienen fixture ni
# tabla propia): son solo el lugar de donde salen y a donde van los movimientos de la
# Primera Nacional, cada uno según si el club es del interior o metropolitano.
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
    "Ferro": 64, "Chacarita": 62, "Atlanta": 63,
    "Nueva Chicago": 60, "All Boys": 60, "San Martín (Tucumán)": 62,
    "Deportivo Madryn": 61, "Temperley": 62, "Deportivo Morón": 64,
    "Almirante Brown": 60, "Racing (Córdoba)": 60, "Gimnasia (Jujuy)": 64,
    "Deportivo Maipú": 60, "Güemes": 60, "Agropecuario": 60,
    "Chaco For Ever": 59, "Defensores de Belgrano": 59, "Mitre (SdE)": 58,
    "Central Norte": 58, "Atlético de Rafaela": 58, "Ciudad de Bolívar": 57,
    "Tristán Suárez": 57, "Los Andes": 57, "Estudiantes (BA)": 57,
    "San Miguel": 56, "Colegiales": 55,
    "Midland": 56, "San Telmo": 58,
    "Gimnasia y Tiro": 61, "Acassuso": 57,
}
# Categoría inferior: de acá salen los 6 equipos que reemplazan a los descendidos de la B
# y hacia acá bajan los 6 que descienden de la B (no se simula esa liga).
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
    "Olimpo": 52, "Ramón Santamarina": 49, "Sol de Mayo": 47,
    "Villa Mitre": 50,
}
# Primera B (Metropolitana): clubes de CABA / Gran Buenos Aires. Cumple el mismo rol
# que el Federal A pero para el lado metropolitano (tampoco se simula esta liga).
EQUIPOS_PRIMERA_B = {
    "Deportivo Español": 44, "Excursionistas": 50, "Comunicaciones": 50,
    "Sacachispas": 39, "UAI Urquiza": 40, "Cañuelas": 44,
    "Berazategui": 43, "Liniers": 44, "Argentino de Merlo": 44,
    "Yupanqui": 46, "Victoriano Arenas": 47, "Talleres (RE)": 49,
    "Argentino (Q)": 40, "Atlas": 39, "Cambaceres": 46,
    "Dock Sud": 40, "Fénix": 40, "Central Ballester": 40,
    "Deportivo Laferrere": 45, "El Porvenir": 44, "Ituzaingó": 44,
    "Puerto Nuevo": 38, "Villa San Carlos": 47,"Villa Dálmine": 45,
    "Deportivo Merlo": 40, "Brown de Adrogué": 44, "Arsenal" :50,
    "Camioneros": 43, "Defensores Unidos": 42, "Real Pilar": 41,
    "Sportivo Italiano": 44, "Flandria": 43,
}

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
    "Defensores de Vilelas": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d2/Club_Atl%C3%A9tico_Defensores_de_Vilelas.png/120px-Club_Atl%C3%A9tico_Defensores_de_Vilelas.png",
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
    "Kimberley": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/02/Escudo_Kimberley.png/120px-Escudo_Kimberley.png",
    "Olimpo": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ea/EscudoOlimpo.svg/120px-EscudoOlimpo.svg.png",
    "Ramón Santamarina": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/93/Escudo_del_Club_Santa_Marina_de_Tandil.svg/120px-Escudo_del_Club_Santa_Marina_de_Tandil.svg.png",
    "Sol de Mayo": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/Club_Sol_de_Mayo.png/120px-Club_Sol_de_Mayo.png",
    "Villa Mitre": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b1/Escudo_Club_Villa_Mitre.png/120px-Escudo_Club_Villa_Mitre.png",
    "Acassuso": "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEj5jU0bnkbnc6e6EqZE87i09WXizE0DrsLWNtjw6S47G9NP6l6WEZQs0xPYW8E1kOp5_bhXYmKzMAt79cc1lzRfjmMsVbkQTHdhnjUlHcWYrjfYRdoIHxUMnHTzg3yD_KI4Yc1MG5GTmR5Ai7GonAp_vGT41WuCCbYbKYinvRHxE_W06KhmFFu0RRXd/s512/Acassuso.png",
    "Gimnasia y Tiro": "https://2.bp.blogspot.com/-c1rp4nLOdHs/W-zUDjpZZKI/AAAAAAABSzQ/X2nSsoNmU0oFB_3fVLLngcBBLUvSsaYQQCLcBGAs/s1600/Club%2Bde%2BGimnasia%2By%2BTiro.png",
    "Midland": "https://www.estadiosdeargentina.com.ar/wp-content/uploads/2015/01/Midland_escudo.png",
    "San Telmo": "https://clubsantelmo.com.ar/wp-content/uploads/2021/03/ESCUDO-ACTUAL.png",
    "Argentino de Merlo": "https://images.seeklogo.com/logo-png/64/2/club-atletico-argentino-de-merlo-buenos-aires-logo-png_seeklogo-644084.png",
    "Arsenal": "https://logos-world.net/wp-content/uploads/2020/04/Arsenal-Logo.png",
    "Atlas": "https://thumb.wikimedia.org/wikipedia/commons/thumb/6/6c/Club_Atletico_Atlas.svg/960px-Club_Atletico_Atlas.svg.png?utm_source=es.wikipedia.org&utm_campaign=imageinfo&utm_content=thumbnail",
    "Berazategui": "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEgXKTZBEDfx3Qt7Q2tCgFyylQunR6hDIWMk2qK4ISq3eQrsmmJXrBFub-KnXzDuI4_RvNMak7AGyA0OOtuGPWgkBUco0HSil0QqXC1zdac3EqyP5gNMyIAX_OWLsZReErCQJP3ZdDfR5iA/s1600/Berazategui_Logo.png",
    "Brown de Adrogué": "https://upload.wikimedia.org/wikipedia/commons/b/b8/Escudo_del_Club_Brown_de_Adrogue.svg?utm_source=commons.wikimedia.org&utm_campaign=index&utm_content=original",
    "Cambaceres": "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEhkZ6i4LCSNIle6kxeSmqB7evS_e2qsAiSNIEyx2QcnZACvnA6POh3xQxAatsp7VDKzW02YKGvi8JQjfQ5AQj8O13JRpqE5jK8GmAngl37o0igHqblLkwyy1eMQv_hdlMDbcQ7ligMUr79BSMOt9Y2tXhErj98Gxv3hL02c9e0BYJeTzanA2XNY3gBYH5A/s512/Cambaceres.png",
    "Cañuelas": "https://i.pinimg.com/474x/71/e7/9b/71e79b2fc6d5704d8a50dddff7cd3b21.jpg",
    "Central Ballester": "https://images.seeklogo.com/logo-png/3/1/club-social-y-deportivo-central-ballester-logo-png_seeklogo-32214.png",
    "Comunicaciones": "https://upload.wikimedia.org/wikipedia/commons/e/e7/Club_comunicaciones_ba_logo.png?utm_source=es.wikipedia.org&utm_campaign=index&utm_content=original",
    "Deportivo Español": "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEiPjpvGYKa8Utk8PjoAuNx-Tra-81sVvAgZOW34wAh9nBZl32VKA7qASOIO-NJtQhi8RSCiMQJC5BfaS8bAwYdiG91u6eYTjaiP5Llr0tvMS00bRwkbg8qS2od1Li4_QhVwxWBVVTyomKAV-e8Gl1VQSi2FZYDiR-uipqHgfWshk2ubt3DwUUTUf3QW/s512/Club%20Deportivo%20Espanol.png",
    "Excursionistas": "https://thumb.wikimedia.org/wikipedia/commons/thumb/1/10/Club_Atletico_Excursionistas.svg/500px-Club_Atletico_Excursionistas.svg.png?utm_source=es.wikipedia.org&utm_campaign=imageinfo&utm_content=thumbnail",
    "Deportivo Laferrere": "https://blogger.googleusercontent.com/img/a/AVvXsEiDZvm80tML0UvLLlPj4BDDFvpwj3yIpYJZadFVJzbQzMrd9oddmzQ8xqKui_WgwvnQC8GcjyildnsZhIO9eXHUjJtCc9rfN3sJc9OuC9Ay0MdhWk2FLaJfOlNYjQQb7Q9vLBsnGeqyuVl-zWFLJ5EH0qfsdTXf6u7YYJ0aZqvygq81nTok8oy3hjWz=s512",
    "Deportivo Merlo": "https://thumb.wikimedia.org/wikipedia/commons/thumb/8/80/Escudo_del_Club_Deportivo_Merlo.svg/960px-Escudo_del_Club_Deportivo_Merlo.svg.png?utm_source=es.wikipedia.org&utm_campaign=imageinfo&utm_content=thumbnail",
    "Dock Sud": "https://tse3.mm.bing.net/th/id/OIP.7Drgs39OnX522kyu7UjKzwHaHa?r=0&rs=1&pid=ImgDetMain&o=7&rm=3",
    "El Porvenir": "https://tse4.mm.bing.net/th/id/OIP.4plidCe8UCcoqaD8Og38PwHaHa?r=0&rs=1&pid=ImgDetMain&o=7&rm=3",
    "Fénix": "https://alchetron.com/cdn/club-atltico-fnix-6965bd97-e2db-4ea5-99b2-f98f3350400-resize-750.jpeg",
    "Ituzaingó": "https://images.seeklogo.com/logo-png/36/1/club-atletico-ituzaingo-de-ituzaingo-buenos-aires-logo-png_seeklogo-362689.png",
    "Villa Dálmine": "https://i.pinimg.com/474x/9b/b9/c6/9bb9c6f84196a267a867d9684055f8cf.jpg",
    "Camioneros": "https://i.pinimg.com/474x/0e/7c/9d/0e7c9da9683fac2e1ffce4c7b605256d.jpg",
    "Liniers": "https://images.seeklogo.com/logo-png/64/1/club-social-y-deportivo-liniers-de-san-justo-la-ma-logo-png_seeklogo-644266.png",
    "Defensores Unidos": "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEi2zuH40qD3t3tEM-qTynzIo8JGNUADJXLJM6xf1qRd-cOPIFOAw312ewNAmA9l38wjhODXnGzqMLNWRaLufJFSf4Jg_o26AgeEAqlKLEgYX6gyJkKo9s3wr5_AYW-3o1L8VJ-Y-gxAvhs/s1600/Defensores+Unidos.png",
    "Sacachispas": "https://upload.wikimedia.org/wikipedia/commons/1/14/Logo_del_Sacachispas_F%C3%BAtbol_Club.svg?utm_source=commons.wikimedia.org&utm_campaign=index&utm_content=original",
    "Real Pilar":"https://images.seeklogo.com/logo-png/64/1/real-pilar-futbol-club-de-pilar-buenos-aires-logo-png_seeklogo-644075.png",
    "Puerto Nuevo": "https://vectorseek.com/wp-content/uploads/2024/01/CA-Puerto-Novo-Logo-Vector.svg-.png",
    "Yupanqui": "https://tse2.mm.bing.net/th/id/OIP.kCr3VNcdI2NJrKiQ5Hz4qQHaHa?r=0&rs=1&pid=ImgDetMain&o=7&rm=3",
    "Villa San Carlos": "https://upload.wikimedia.org/wikipedia/commons/1/11/ESCUDO_OFICIAL_DEL_CLUB_VILLA_SAN_CARLOS.png?utm_source=es.wikipedia.org&utm_campaign=index&utm_content=original",
    "Talleres (RE)": "https://upload.wikimedia.org/wikipedia/commons/9/9d/Talleres_ba_logo.png?utm_source=es.wikipedia.org&utm_campaign=index&utm_content=original",
    "UAI Urquiza": "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEjF5SloVGhge9NZ4fgQEkQnPfJ3pEApV8vgMRDXePWiia58JTAtOxPfpRvofA5sdaIE_Gu2FNZwhDVjq95VWEABBVDBd-7WH-Ba5Nh9Wbn3qf1VFS95hku7Q2qHJ5-sxv4KwRRuWlUvEL9OBzgajV_j9VTHt0MMNRogGLR2ickPtSsGuxdndOVHlSh_vYY/s512/Club%20Deportivo%20UAI%20Urquiza.png",
    "Victoriano Arenas": "https://upload.wikimedia.org/wikipedia/commons/6/65/Victoriano_Arenas_escudo_2025.png?utm_source=es.wikipedia.org&utm_campaign=index&utm_content=original",
    "Sportivo Italiano": "https://upload.wikimedia.org/wikipedia/commons/3/3b/Club_Sportivo_Italiano_%28Argentina%29_logo.svg?utm_source=es.wikipedia.org&utm_campaign=index&utm_content=original",
    "Flandria": "https://upload.wikimedia.org/wikipedia/commons/3/30/Club_flandria_escudo.png?utm_source=es.wikipedia.org&utm_campaign=index&utm_content=original",
    "Argentino (Q)": "https://upload.wikimedia.org/wikipedia/commons/3/33/ArgentinodeQuilmes.png?utm_source=es.wikipedia.org&utm_campaign=index&utm_content=original",


}

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
    """"Interior" o "Metropolitana": a qué categoría baja este club si algún día
    desciende del todo (Federal A o Primera B, respectivamente)."""
    if nombre in EQUIPOS_FEDERAL:
        return "Interior"
    if nombre in EQUIPOS_PRIMERA_B:
        return "Metropolitana"
    return ORIGEN.get(nombre, "Interior")


# Región de cada club del Federal A (y de cualquier club "Interior" de Primera o la
# Primera Nacional que algún día pueda terminar ahí): sirve para armar los 4 grupos
# de la fase 1 "por cercanía". Los que no están acá caen en "Centro" por defecto.
F_GRUPOS_NOMBRES = ["Norte", "Centro", "Buenos Aires", "Cuyo y Patagonia"]
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


def region_de(nombre):
    return REGION.get(nombre, "Centro")


N = len(EQUIPOS)            # Primera
NB = len(EQUIPOS_B)         # Primera Nacional
NF = len(EQUIPOS_FEDERAL)   # Federal A
NPB = len(EQUIPOS_PRIMERA_B)  # Primera B

_todos = list(EQUIPOS) + list(EQUIPOS_B) + list(EQUIPOS_FEDERAL) + list(EQUIPOS_PRIMERA_B)
if N != 30 or NB != 36 or NF < 6 or NPB < 6 or len(set(_todos)) != len(_todos):
    st.error("Primera debe tener 30 equipos, la Primera Nacional 36, el Federal A y la "
             "Primera B al menos 6 cada uno, y no puede haber nombres repetidos. Ahora hay "
             f"{N}, {NB}, {NF} y {NPB}.")
    st.stop()

ESCALA = 20.0        # cuánto pesa la diferencia de medias en los goles esperados
LOCALIA = 4.5        # ventaja fija de local (en puntos de media)
GOLES_BASE = 1.16    # goles esperados por equipo en un partido parejo (~2.2 por partido)
DISPERSION = 16.0    # menor valor = más partidos "raros" (0-0 seguidos de goleadas)
RHO_DC = -0.05       # corrección Dixon-Coles: un poco más de 0-0 y 1-1 (fútbol argentino)
TOPE_GOLES = 10      # marcadores posibles por equipo: 0..9
_TOT = np.add.outer(np.arange(TOPE_GOLES), np.arange(TOPE_GOLES))
# Los marcadores muy abultados quedan como rareza (6+ goles ≈ 0,8% de los partidos)
AMORTIGUAR = np.where(_TOT >= 8, 0.06, np.where(_TOT >= 6, 0.16, np.where(_TOT == 5, 0.75, 1.0)))
_LOG_FACT = np.concatenate([[0.0], np.cumsum(np.log(np.arange(1, TOPE_GOLES)))])
P_GOL_PENAL = 0.76   # probabilidad de convertir cada penal de la tanda
REVERSION = 0.15     # cuánto vuelven las medias hacia el promedio de su liga cada temporada
MIN_R, MAX_R = 40.0, 95.0

# Primera
ZONA_TAM = N // 3                 # 10 equipos por zona
FECHAS_F1 = N - 1                 # 29 fechas todos contra todos
FECHAS_F2 = ZONA_TAM - 1          # 9 fechas por zona
TOTAL_FECHAS = FECHAS_F1 + FECHAS_F2
ZONAS = ["Campeonato", "Intermedia", "Descenso"]
STATS = ("pj", "g", "e", "p", "gf", "gc")

# Primera Nacional
B_ZONA_TAM = NB // 2              # 18 equipos por zona en la fase 1
B_TAM2 = [12, 12, 12]             # Campeonato, Intermedia, Descenso
B_F1_ZONAL = B_ZONA_TAM - 1        # 17 fechas de zona (una rueda de 18)
B_F1_INTER = 8                     # 8 fechas interzonales antes de pasar a la fase 2
B_F1 = B_F1_ZONAL + B_F1_INTER     # 25 fechas en total en la fase 1 de la B
B_F2 = B_TAM2[2] - 1              # 11 fechas (las tres zonas son de 12)
B_RED = 4                         # octavos, cuartos, semifinales, final
B_TOTAL = B_F1 + B_F2 + B_RED + 1 # + promoción = 31
B_ETAPAS = ["Octavos del reducido", "Cuartos del reducido", "Semifinales del reducido",
            "Final del reducido"]
B_ZONAS2 = ["Campeonato", "Intermedia", "Descenso"]

# Federal A: la fase 1 tiene 4 grupos "por cercanía" cuyo tamaño no es fijo (el plantel
# cambia con los ascensos/descensos), así que su cantidad de fechas se calcula por
# temporada (ver nueva_estructura_f), no acá.
F_ZONA_TAM = 10                   # Campeonato y Descenso en la fase 2 (10 y 10)
F_F2_RONDAS = F_ZONA_TAM - 1       # 9 fechas, una rueda
F_RED = 3                          # cuartos, semifinales, final
F_ETAPAS = ["Cuartos del reducido", "Semifinales del reducido", "Final del reducido"]

COLOR_ORO = "rgba(255, 215, 0, 0.40)"
COLORES_DESTINO = {
    "Libertadores": "rgba(52, 152, 219, 0.28)",
    "Fase previa Libertadores": "rgba(133, 193, 233, 0.30)",
    "Sudamericana": "rgba(243, 156, 18, 0.28)",
    "Promoción": "rgba(155, 89, 182, 0.30)",
    "Desciende": "rgba(231, 76, 60, 0.25)",
}
COLORES_ZONA = ["rgba(46, 204, 113, 0.22)", "rgba(241, 196, 15, 0.22)", "rgba(231, 76, 60, 0.20)"]
COLORES_B = {
    "Campeón · Ascenso": COLOR_ORO,
    "Ascenso directo": "rgba(46, 204, 113, 0.30)",
    "Cuartos del reducido": "rgba(52, 152, 219, 0.28)",
    "Octavos del reducido": "rgba(133, 193, 233, 0.30)",
    "Desciende": "rgba(231, 76, 60, 0.25)",
    "→ Zona Campeonato": COLORES_ZONA[0],
    "→ Zona Intermedia": COLORES_ZONA[1],
    "→ Zona Descenso": COLORES_ZONA[2],
}
COLORES_F = {
    "Campeón · Ascenso": COLOR_ORO,
    "Ascenso directo": "rgba(46, 204, 113, 0.30)",
    "Reducido": "rgba(52, 152, 219, 0.28)",
    "→ Fase 2": "rgba(46, 204, 113, 0.22)",
}


def destino(pos):
    """Destino en Primera según la posición final (1-30)."""
    if 1 <= pos <= 5:
        return "Libertadores"
    if 6 <= pos <= 8:
        return "Sudamericana"
    if pos == 11:
        return "Fase previa Libertadores"
    if pos in (12, 13):
        return "Sudamericana"
    if pos == N - 3:
        return "Promoción"
    if pos >= N - 2:
        return "Desciende"
    return ""


def destino_b1(pos):
    """Fase 1 de la B: a qué zona de la fase 2 pasa según la posición en la zona A/B."""
    if pos <= 6:
        return "→ Zona Campeonato"
    if pos <= 12:
        return "→ Zona Intermedia"
    return "→ Zona Descenso"


def destino_b2(z, pos):
    """Fase 2 de la B: destino según la zona (0 Campeonato, 1 Intermedia, 2 Descenso)."""
    if z == 0:
        if pos == 1:
            return "Campeón · Ascenso"
        if pos == 2:
            return "Ascenso directo"
        return "Cuartos del reducido" if pos <= 4 else "Octavos del reducido"
    if z == 1:
        return "Octavos del reducido" if pos <= 4 else "Eliminado"
    return "Permanece" if pos <= 6 else "Desciende"


def destino_f1(pos):
    """Fase 1 del Federal A: quiénes pasan a la fase 2 dentro de su grupo."""
    return "→ Fase 2" if pos <= 5 else ""


def destino_f2(z, pos):
    """Fase 2 del Federal A: destino según la zona (0 Campeonato, 1 Descenso)."""
    if z == 0:
        if pos == 1:
            return "Campeón · Ascenso"
        if pos == 2:
            return "Ascenso directo"
        return "Reducido" if pos <= 10 else ""
    return ""


# ----------------------------------------------------------------------------
# MOTOR COMÚN
# ----------------------------------------------------------------------------
def generar_fixture(n):
    """Todos contra todos, una vuelta (método de Berger). Lista de fechas.

    Las localías quedan balanceadas: cada equipo es local en la mitad de sus
    partidos (±1) y nunca juega más de 2 fechas seguidas de local o de visitante.
    """
    impar = n % 2 == 1
    m = n + 1 if impar else n
    fechas = []
    for r in range(m - 1):
        pares = [(r, m - 1) if r % 2 == 0 else (m - 1, r)]
        for k in range(1, m // 2):
            x, y = (r + k) % (m - 1), (r - k) % (m - 1)
            pares.append((x, y) if k % 2 == 1 else (y, x))
        if impar:
            pares = [p for p in pares if m - 1 not in p]
        fechas.append(pares)
    return fechas


def generar_fixture_interzonal(rng, za, zb, rondas):
    """`rondas` fechas cruzando las zonas A y B: cada equipo enfrenta a `rondas`
    rivales distintos de la otra zona (rotación tipo Latin square, sin repetir
    cruces) y es local en exactamente la mitad de esas fechas: la zona local
    alterna fecha a fecha, así que con `rondas` par cada equipo termina 50/50."""
    n = len(za)
    orden_b = rng.permutation(n)
    fechas = []
    for r in range(rondas):
        a_local = r % 2 == 0
        pares = []
        for i in range(n):
            x, y = int(za[i]), int(zb[int(orden_b[(i + r) % n])])
            pares.append((x, y) if a_local else (y, x))
        fechas.append(pares)
    return fechas


def ultimas_localias(fechas, cuantas=2):
    """Condición (1 local, 0 visitante) de las últimas fechas de cada equipo."""
    prev = {}
    for pares in fechas[-cuantas:]:
        for a, b in pares:
            prev.setdefault(a, []).append(1)
            prev.setdefault(b, []).append(0)
    return prev


def puntaje_localias(fechas, previas, balance=None):
    """Penaliza rachas de 3+ fechas con la misma condición y desbalances local/visitante."""
    seq = {t: list(v) for t, v in previas.items()}
    ini = {t: len(v) for t, v in previas.items()}
    for pares in fechas:
        for a, b in pares:
            seq.setdefault(a, []).append(1)
            seq.setdefault(b, []).append(0)
    s = 0
    for t, q in seq.items():
        run = 1
        for i in range(1, len(q)):
            run = run + 1 if q[i] == q[i - 1] else 1
            if run > 2:
                s += 10 * (run - 2)
        nuevo = q[ini.get(t, 0):]
        total = (balance or {}).get(t, 0) + 2 * sum(nuevo) - len(nuevo)
        s += 3 * max(0, abs(total) - 1)
    return s


def balance_localias(fechas):
    """Partidos de local menos partidos de visitante de cada equipo."""
    bal = {}
    for pares in fechas:
        for a, b in pares:
            bal[a] = bal.get(a, 0) + 1
            bal[b] = bal.get(b, 0) - 1
    return bal


def fixture_revancha(rng, ids, H, previas, balance=None, intentos=300):
    """Una rueda entre `ids` respetando la revancha: si x fue local contra y antes,
    ahora es local y. Los cruces nuevos le dan la localía al que viene jugando menos
    de local. Entre los órdenes posibles elige el de localías más parejas."""
    base = generar_fixture(len(ids))
    mejor = None
    for t in range(intentos):
        perm = np.asarray(ids) if t == 0 else rng.permutation(ids)
        bal = dict(balance or {})
        fechas = []
        for pares in base:
            fecha = []
            for a, b in pares:
                x, y = int(perm[a]), int(perm[b])
                if H[x, y]:
                    x, y = y, x                                  # localía invertida
                elif not H[y, x] and bal.get(y, 0) < bal.get(x, 0):
                    x, y = y, x                                  # cruce nuevo: equilibra
                bal[x] = bal.get(x, 0) + 1
                bal[y] = bal.get(y, 0) - 1
                fecha.append((x, y))
            fechas.append(fecha)
        s = puntaje_localias(fechas, previas, balance)
        if mejor is None or s < mejor[0]:
            mejor = (s, fechas)
            if s == 0:
                break
    return mejor[1]


def jugar(rng, r_local, r_visita, sorpresa, escala=ESCALA, localia=LOCALIA):
    """Simula partidos (vectorizado). Devuelve goles local y visitante.

    sorpresa = desvío (en puntos de media) de la "forma del día": en cada
    partido cada equipo rinde un poco por encima o por debajo de su media.
    """
    r_local = np.asarray(r_local, float)
    r_visita = np.asarray(r_visita, float)
    forma = rng.normal(0.0, sorpresa, r_local.shape) - rng.normal(0.0, sorpresa, r_local.shape)
    d_ef = (r_local - r_visita) + forma + localia
    d_ef = 28.0 * np.tanh(d_ef / 28.0)          # las diferencias enormes no se disparan
    # "Ritmo" del partido (media 1): hay partidos cerrados (0-0, 1-0) y otros
    # abiertos (3-2). Los resultados muy abultados quedan como rareza.
    ritmo = rng.gamma(DISPERSION, 1.0 / DISPERSION, size=d_ef.shape)
    lam_l = GOLES_BASE * ritmo * np.exp(d_ef / (2 * escala))
    lam_v = GOLES_BASE * ritmo * np.exp(-d_ef / (2 * escala))
    # Matriz de probabilidades de cada marcador: Poisson + Dixon-Coles + amortiguación
    k = np.arange(TOPE_GOLES)
    pl = np.exp(k * np.log(lam_l[..., None]) - lam_l[..., None] - _LOG_FACT)
    pv = np.exp(k * np.log(lam_v[..., None]) - lam_v[..., None] - _LOG_FACT)
    M = pl[..., :, None] * pv[..., None, :]
    M[..., 0, 0] *= 1 - lam_l * lam_v * RHO_DC
    M[..., 0, 1] *= 1 + lam_l * RHO_DC
    M[..., 1, 0] *= 1 + lam_v * RHO_DC
    M[..., 1, 1] *= 1 - RHO_DC
    M = np.clip(M, 0.0, None) * AMORTIGUAR
    acum = np.cumsum(M.reshape(*d_ef.shape, TOPE_GOLES ** 2), axis=-1)
    u = rng.random(d_ef.shape)[..., None] * acum[..., -1:]
    idx = (acum < u).sum(axis=-1)
    return idx // TOPE_GOLES, idx % TOPE_GOLES


def tanda_penales(rng, gana_local):
    """Tanda de penales (patea primero el local) coherente con el ganador ya definido.

    Devuelve dos listas de bool (convertido / errado) para local y visitante.
    """
    while True:
        tl, tv = [], []
        for i in range(5):
            tl.append(bool(rng.random() < P_GOL_PENAL))
            if sum(tl) > sum(tv) + (5 - len(tv)) or sum(tv) > sum(tl) + (5 - len(tl)):
                break
            tv.append(bool(rng.random() < P_GOL_PENAL))
            if sum(tl) > sum(tv) + (5 - len(tv)) or sum(tv) > sum(tl) + (5 - len(tl)):
                break
        while sum(tl) == sum(tv):                   # muerte súbita
            tl.append(bool(rng.random() < P_GOL_PENAL))
            tv.append(bool(rng.random() < P_GOL_PENAL))
        if (sum(tl) > sum(tv)) == bool(gana_local):
            return tl, tv


def nuevo_partido(liga, fecha, rotulo, comp, local, visita, gl, gv,
                  tanda=None, gana=None, neutral=False):
    """Registro de un partido jugado (para resultados, fichas, buscador y cuadros)."""
    gl, gv = int(gl), int(gv)
    if gana is None:
        gana = local if gl > gv else visita if gv > gl else None
    return {
        "liga": liga, "fecha": int(fecha), "rotulo": rotulo, "comp": comp,
        "local": local, "visita": visita, "gl": gl, "gv": gv, "gana": gana,
        "tanda": tanda, "pen": (sum(tanda[0]), sum(tanda[1])) if tanda else None,
        "neutral": neutral,
    }


def rotulo_p(n):
    return f"Fecha {n}" + (" · Fase 2" if n > FECHAS_F1 else "")


def rotulo_b(n):
    if n <= B_F1:
        return f"Fecha {n} · Fase 1"
    if n <= B_F1 + B_F2:
        return f"Fecha {n} · Fase 2 (fecha {n - B_F1})"
    if n <= B_F1 + B_F2 + B_RED:
        return f"Fecha {n} · {B_ETAPAS[n - B_F1 - B_F2 - 1]}"
    return f"Fecha {n} · Promoción"


def rotulo_f(SF, n):
    f1 = SF["f1_rondas"]
    if n <= f1:
        return f"Fecha {n} · Fase 1"
    if n <= f1 + F_F2_RONDAS:
        return f"Fecha {n} · Fase 2 (fecha {n - f1})"
    return f"Fecha {n} · {F_ETAPAS[n - f1 - F_F2_RONDAS - 1]}"


def jugar_ko(rng, r_loc, r_vis, sorpresa, localia=LOCALIA):
    """Partido único eliminatorio SIN alargue: si empatan, penales directos.

    Devuelve goles local, goles visitante, si ganó el local y si hubo penales.
    """
    gl, gv = jugar(rng, r_loc, r_vis, sorpresa, localia=localia)
    p_loc = np.clip(0.5 + (np.asarray(r_loc, float) - np.asarray(r_vis, float)) / 400, 0.35, 0.65)
    pen_local = rng.random(np.shape(gl)) < p_loc
    gana_local = np.where(gl != gv, gl > gv, pen_local)
    return gl, gv, gana_local, gl == gv


def jugar_ko_posicion(rng, r_loc, r_vis, sorpresa, localia=LOCALIA):
    """Partido único del reducido del Federal A (menos la final): el local ya es el
    mejor ubicado en la tabla, y si empatan gana directamente el local (sin penales;
    es decir, gana el que quedó mejor en la tabla)."""
    gl, gv = jugar(rng, r_loc, r_vis, sorpresa, localia=localia)
    gana_local = gl >= gv
    return gl, gv, gana_local, gl == gv


def jugar_reducido_federal(rng, r, A, B, sorpresa, final):
    """Cruce del reducido del Federal A: A siempre es el mejor ubicado (cruces_mejor_peor
    ya lo deja así). En cuartos y semis juega de local y el empate lo gana él; la final
    es en cancha neutral y el empate se define por penales."""
    if final:
        gl, gv, gana_local, pen = jugar_ko(rng, r[A["id"]], r[B["id"]], sorpresa, localia=0.0)
    else:
        gl, gv, gana_local, pen = jugar_ko_posicion(rng, r[A["id"]], r[B["id"]], sorpresa)
    gan = {k: np.where(gana_local, A[k], B[k]) for k in A}
    per = {k: np.where(gana_local, B[k], A[k]) for k in A}
    return A, B, gl, gv, gan, per, pen


def sumar_partidos(E, h, a, gh, ga):
    """Actualiza las estadísticas de la liga E (dict con arrays de STATS)."""
    E["pj"][h] += 1
    E["pj"][a] += 1
    E["gf"][h] += gh
    E["gc"][h] += ga
    E["gf"][a] += ga
    E["gc"][a] += gh
    E["g"][h] += (gh > ga)
    E["g"][a] += (ga > gh)
    E["p"][h] += (gh < ga)
    E["p"][a] += (ga < gh)
    E["e"][h] += (gh == ga)
    E["e"][a] += (gh == ga)


def df_stats(nombres, r, v, ids):
    """Tabla ordenada de los equipos `ids` (con columna interna 'id')."""
    ids = np.asarray(ids)
    df = pd.DataFrame({
        "id": ids,
        "Equipo": [nombres[i] for i in ids],
        "PJ": v["pj"][ids], "G": v["g"][ids], "E": v["e"][ids], "P": v["p"][ids],
        "GF": v["gf"][ids], "GC": v["gc"][ids],
    })
    df["DG"] = df["GF"] - df["GC"]
    df["Pts"] = 3 * df["G"] + df["E"]
    df["Media"] = np.asarray(r)[ids].round(1)
    return df.sort_values(["Pts", "DG", "GF"], ascending=False).reset_index(drop=True)


# ----------------------------------------------------------------------------
# MOTOR PRIMERA
# ----------------------------------------------------------------------------
def nueva_estructura(S):
    """Reinicia stats y fixture de la Primera para la temporada actual."""
    perm = S["rng"].permutation(N)
    fechas = generar_fixture(N)
    S["fechas"] = [[(int(perm[a]), int(perm[b])) for a, b in p] for p in fechas]
    S["fecha"] = 0
    S["fase"] = 1
    S["zonas"] = None
    S["zona_de"] = None
    S["snap"] = None
    S["tabla_f1"] = None
    S["acumular"] = True
    for k in STATS:
        S[k] = np.zeros(N, dtype=int)
    S["historial"] = []
    S["log"] = []           # partidos jugados (dicts de nuevo_partido)
    S["pos_hist"] = []      # (fase, posiciones por id) después de cada fecha
    S["sorpresas"] = 0
    S["cerrada"] = False


def vista(S):
    """Estadísticas a mostrar (en la fase 2 pueden excluir la fase 1)."""
    if S["fase"] == 2 and not S["acumular"]:
        return {k: S[k] - S["snap"][k] for k in STATS}
    return {k: S[k] for k in STATS}


def df_base(S, ids):
    return df_stats(S["nombres"], S["r"], vista(S), ids)


def tabla_general(S):
    df = df_base(S, np.arange(N))
    df.insert(0, "Pos", df.index + 1)
    return df


def tabla_zona(S, z):
    df = df_base(S, S["zonas"][z])
    df.insert(0, "Pos", z * ZONA_TAM + df.index + 1)
    df["Destino"] = [destino(p) for p in df["Pos"]]
    return df


def tabla_final(S):
    return pd.concat([tabla_zona(S, z) for z in range(3)])


def iniciar_fase2(S, acumular):
    """Arma las zonas según la tabla de la fase 1 y agrega las 9 fechas."""
    S["tabla_f1"] = tabla_general(S)          # queda guardada para consultarla después
    orden = S["tabla_f1"]["id"].to_numpy()
    S["zonas"] = [orden[z * ZONA_TAM:(z + 1) * ZONA_TAM] for z in range(3)]
    S["zona_de"] = np.zeros(N, dtype=int)
    for z, ids in enumerate(S["zonas"]):
        S["zona_de"][ids] = z
    S["snap"] = {k: S[k].copy() for k in STATS}
    S["acumular"] = acumular

    # H[x, y] = True si x fue local contra y en la fase 1
    H = np.zeros((N, N), dtype=bool)
    for pares in S["fechas"][:FECHAS_F1]:
        for a, b in pares:
            H[a, b] = True

    previas = ultimas_localias(S["fechas"][:FECHAS_F1])
    por_zona = [fixture_revancha(S["rng"], S["zonas"][z], H, previas) for z in range(3)]
    for k in range(FECHAS_F2):
        S["fechas"].append([p for z in range(3) for p in por_zona[z][k]])
    S["fase"] = 2


def simular_fecha(S, P, acumular=True):
    if S["fecha"] >= len(S["fechas"]):
        return
    pares = S["fechas"][S["fecha"]]
    h = np.array([x[0] for x in pares])
    a = np.array([x[1] for x in pares])
    gh, ga = jugar(S["rng"], S["r"][h], S["r"][a], **P)
    sumar_partidos(S, h, a, gh, ga)

    # Sorpresa = ganó el equipo con menor media (diferencia mínima de 3 puntos)
    d = S["r"][h] - S["r"][a]
    sorp = ((d >= 3) & (ga > gh)) | ((d <= -3) & (gh > ga))
    S["sorpresas"] += int(sorp.sum())

    nom = S["nombres"]
    datos = {
        "Local": [nom[i] for i in h],
        "GL": gh, "GV": ga,
        "Visitante": [nom[i] for i in a],
    }
    if S["fase"] == 2:
        datos = {"Zona": [ZONAS[S["zona_de"][i]] for i in h], **datos}
    S["historial"].append(pd.DataFrame(datos))
    n_f = S["fecha"] + 1
    for x, y, g1, g2 in zip(h, a, gh, ga):
        comp = "Fase 1" if S["fase"] == 1 else f"Zona {ZONAS[S['zona_de'][x]]}"
        S["log"].append(nuevo_partido("Primera División", n_f, rotulo_p(n_f), comp,
                                      nom[x], nom[y], g1, g2))
    tabla = tabla_general(S) if S["fase"] == 1 else tabla_final(S)
    pos = np.zeros(N, dtype=int)
    pos[tabla["id"].to_numpy()] = tabla["Pos"].to_numpy()
    S["pos_hist"].append((S["fase"], pos))
    S["fecha"] += 1

    if S["fase"] == 1 and S["fecha"] == FECHAS_F1:
        iniciar_fase2(S, acumular)


# ----------------------------------------------------------------------------
# MOTOR PRIMERA NACIONAL
# ----------------------------------------------------------------------------
# Un "bloque" es un dict de arrays (n, k) con las claves:
#   id (equipo), zona (0 Campeonato / 1 Intermedia), pts (puntos en su zona de la
#   fase 2) y seed (orden de mérito 1-12). Sirve tanto para un cuadro real (n=1)
#   como para miles de simulaciones a la vez.
def unir(T1, T2):
    return {k: np.concatenate([T1[k], T2[k]], axis=1) for k in T1}


def cruces_mejor_peor(T):
    """Ordena por mérito y cruza el mejor con el peor (1 vs último, 2 vs anteúltimo...)."""
    idx = np.argsort(T["seed"], axis=1)
    T = {k: np.take_along_axis(v, idx, axis=1) for k, v in T.items()}
    m = T["id"].shape[1] // 2
    A = {k: v[:, :m] for k, v in T.items()}
    B = {k: v[:, ::-1][:, :m] for k, v in T.items()}
    return A, B


def a_es_local(A, B):
    """Localía del reducido.

    1) Campeonato vs Intermedia: siempre local el de Campeonato.
    2) Misma zona: local el que sumó más puntos en esa zona (empate: mejor posición).
    """
    a_camp = A["zona"] == 0
    a_mas_pts = (A["pts"] > B["pts"]) | ((A["pts"] == B["pts"]) & (A["seed"] < B["seed"]))
    return np.where(A["zona"] != B["zona"], a_camp, a_mas_pts)


def ko_jugar(rng, r, A, B, sorpresa):
    """Juega los cruces A vs B (partido único, penales directos si empatan)."""
    a_loc = a_es_local(A, B)
    loc = {k: np.where(a_loc, A[k], B[k]) for k in A}
    vis = {k: np.where(a_loc, B[k], A[k]) for k in A}
    gl, gv, gana_local, pen = jugar_ko(rng, r[loc["id"]], r[vis["id"]], sorpresa)
    gan = {k: np.where(gana_local, loc[k], vis[k]) for k in A}
    per = {k: np.where(gana_local, vis[k], loc[k]) for k in A}
    return loc, vis, gl, gv, gan, per, pen


def nueva_estructura_b(SB, rng):
    """Sortea las zonas A y B (16 c/u) y arma el fixture de la fase 1."""
    n = len(SB["nombres"])
    perm = rng.permutation(n)
    SB["zonas"] = [perm[:B_ZONA_TAM], perm[B_ZONA_TAM:]]
    SB["zona_de"] = np.zeros(n, dtype=int)
    SB["zona_de"][SB["zonas"][1]] = 1
    base = generar_fixture(B_ZONA_TAM)
    fechas_zonal = [
        [(int(ids[a]), int(ids[b])) for ids in SB["zonas"] for a, b in base[k]]
        for k in range(B_F1_ZONAL)
    ]
    fechas_inter = generar_fixture_interzonal(rng, SB["zonas"][0], SB["zonas"][1], B_F1_INTER)
    SB["fechas"] = fechas_zonal + fechas_inter
    SB["fecha"] = 0
    for k in STATS:
        SB[k] = np.zeros(n, dtype=int)
    SB["historial"] = []
    SB["log"] = []
    SB["pos_hist"] = []
    SB["bracket"] = []          # partidos del reducido por ronda
    SB["promo_partido"] = None
    SB["tablas_f1"] = None
    SB["zonas2"] = None
    SB["zona2_de"] = None
    SB["fechas2"] = None
    SB["ord2"] = None
    SB["campeon"] = None
    SB["asc_directo"] = []
    SB["desc_b"] = []
    SB["red"] = None
    SB["entrantes"] = None
    SB["asc_reducido"] = None
    SB["perdedor_final"] = None
    SB["promo"] = None


def tabla_b_f1(SB, z):
    """Tabla de la zona A (0) o B (1) de la fase 1."""
    df = df_stats(SB["nombres"], SB["r"], SB, SB["zonas"][z])
    df.insert(0, "Pos", df.index + 1)
    df["Destino"] = [destino_b1(p) for p in df["Pos"]]
    return df


def tabla_b_f2(SB, z):
    """Tabla de la zona de la fase 2 (0 Campeonato, 1 Intermedia, 2 Descenso)."""
    df = df_stats(SB["nombres"], SB["r"], SB, SB["zonas2"][z])
    df.insert(0, "Pos", df.index + 1)
    df["Destino"] = [destino_b2(z, p) for p in df["Pos"]]
    return df


def iniciar_fase2_b(SB, rng):
    """Fin de la fase 1: reparte en 3 zonas y REINICIA TODOS LOS PUNTOS A 0."""
    SB["tablas_f1"] = [tabla_b_f1(SB, z) for z in range(2)]
    ordA = SB["tablas_f1"][0]["id"].to_numpy()
    ordB = SB["tablas_f1"][1]["id"].to_numpy()
    cortes = ((0, 6), (6, 12), (12, 18))       # 6+6 / 6+6 / 6+6 = 12 / 12 / 12
    zonas2 = []
    for a, b in cortes:
        ids = np.concatenate([ordA[a:b], ordB[a:b]])
        zonas2.append(rng.permutation(ids))
    SB["zonas2"] = zonas2
    SB["zona2_de"] = np.zeros(len(SB["nombres"]), dtype=int)
    for z, ids in enumerate(zonas2):
        SB["zona2_de"][ids] = z

    for k in STATS:                             # reset total de puntos y estadísticas
        SB[k] = np.zeros(len(SB["nombres"]), dtype=int)

    # Los que ya se cruzaron en la fase 1 (misma zona A/B) juegan la revancha con la
    # localía invertida; el resto se ordena para que las localías queden parejas.
    n = len(SB["nombres"])
    H = np.zeros((n, n), dtype=bool)
    for pares in SB["fechas"]:
        for a, b in pares:
            H[a, b] = True
    previas = ultimas_localias(SB["fechas"])
    balance = balance_localias(SB["fechas"])
    por_zona = [fixture_revancha(rng, ids, H, previas, balance) for ids in zonas2]
    SB["fechas2"] = []
    for k in range(B_F2):
        SB["fechas2"].append([p for fz in por_zona if k < len(fz) for p in fz[k]])


def iniciar_reducido(SB):
    """Fin de la fase 2: define ascensos directos, descensos y arma el reducido."""
    ids = [tabla_b_f2(SB, z)["id"].to_numpy() for z in range(3)]
    SB["ord2"] = ids
    SB["campeon"] = int(ids[0][0])
    SB["asc_directo"] = [int(ids[0][0]), int(ids[0][1])]
    SB["desc_b"] = [int(i) for i in ids[2][6:]]

    pts = 3 * SB["g"] + SB["e"]

    def bloque(idx, seed0, zona):
        idx = np.asarray(idx)[None, :]
        return {"id": idx, "zona": np.full(idx.shape, zona), "pts": pts[idx],
                "seed": np.arange(seed0, seed0 + idx.shape[1])[None, :]}

    directos = bloque(ids[0][2:4], 1, 0)                                     # 3°-4° Campeonato
    octavos = unir(bloque(ids[0][4:12], 3, 0), bloque(ids[1][:4], 11, 1))    # 5°-12° C + 1°-4° I
    SB["red"] = {"directos": directos, "octavos": octavos, "ganadores": None}

    filas = []
    for i in range(2):
        filas.append((i + 1, SB["nombres"][ids[0][2 + i]], f"{3 + i}° Campeonato", "Cuartos"))
    for i in range(8):
        filas.append((3 + i, SB["nombres"][ids[0][4 + i]], f"{5 + i}° Campeonato", "Octavos"))
    for i in range(4):
        filas.append((11 + i, SB["nombres"][ids[1][i]], f"{1 + i}° Intermedia", "Octavos"))
    SB["entrantes"] = pd.DataFrame(filas, columns=["Mérito", "Equipo", "Origen", "Entra en"])


def _fila_historial(SB, instancia, loc, vis, gl, gv, definicion):
    nom = SB["nombres"]
    return pd.DataFrame({
        "Instancia": instancia,
        "Local": [nom[i] for i in loc], "GL": gl, "GV": gv,
        "Visitante": [nom[i] for i in vis], "Definición": definicion,
    })


def simular_fecha_b(S, P):
    """Simula la próxima fecha de la B. La promoción espera a que termine la Primera."""
    SB, rng = S["b"], S["rng"]
    f = SB["fecha"]
    if f >= B_TOTAL or (f == B_TOTAL - 1 and S["fecha"] < TOTAL_FECHAS):
        return
    r, nom = SB["r"], SB["nombres"]

    if f < B_F1 + B_F2:                                   # ---- zonas (fase 1 y fase 2)
        if f < B_F1:
            pares = SB["fechas"][f]
            if f < B_F1_ZONAL:
                etiqueta = lambda i: f"Zona {'AB'[SB['zona_de'][i]]}"
            else:
                etiqueta = lambda i: "Interzonal"
        else:
            pares = SB["fechas2"][f - B_F1]
            etiqueta = lambda i: f"Zona {B_ZONAS2[SB['zona2_de'][i]]}"
        h = np.array([x[0] for x in pares])
        a = np.array([x[1] for x in pares])
        gh, ga = jugar(rng, r[h], r[a], **P)
        sumar_partidos(SB, h, a, gh, ga)
        SB["historial"].append(_fila_historial(
            SB, [etiqueta(i) for i in h], h, a, gh, ga, ""))
        for x, y, g1, g2 in zip(h, a, gh, ga):
            SB["log"].append(nuevo_partido("Primera Nacional", f + 1, rotulo_b(f + 1),
                                           etiqueta(x), nom[x], nom[y], g1, g2))
        if f < B_F1:
            dfs, tag = [tabla_b_f1(SB, z) for z in range(2)], 1
        else:
            dfs, tag = [tabla_b_f2(SB, z) for z in range(3)], 2
        pos = np.zeros(len(nom), dtype=int)
        for dfz in dfs:
            pos[dfz["id"].to_numpy()] = dfz["Pos"].to_numpy()
        SB["pos_hist"].append((tag, pos))
        SB["fecha"] += 1
        if SB["fecha"] == B_F1:
            iniciar_fase2_b(SB, rng)
        elif SB["fecha"] == B_F1 + B_F2:
            iniciar_reducido(SB)

    elif f < B_F1 + B_F2 + B_RED:                         # ---- reducido
        etapa = f - B_F1 - B_F2
        red = SB["red"]
        if etapa == 0:
            T = red["octavos"]
        elif etapa == 1:
            T = unir(red["directos"], red["ganadores"])   # 3°-4° de Campeonato + 6 ganadores
        else:
            T = red["ganadores"]
        A, B = cruces_mejor_peor(T)
        loc, vis, gl, gv, gan, per, pen = ko_jugar(rng, r, A, B, P["sorpresa"])
        red["ganadores"] = gan
        ronda = []
        for li, vi, g1, g2, wi, p in zip(loc["id"][0], vis["id"][0], gl[0], gv[0],
                                          gan["id"][0], pen[0]):
            tanda = tanda_penales(rng, wi == li) if p else None
            partido = nuevo_partido("Primera Nacional", f + 1, rotulo_b(f + 1), B_ETAPAS[etapa],
                                    nom[li], nom[vi], g1, g2, tanda=tanda, gana=nom[wi])
            ronda.append(partido)
            SB["log"].append(partido)
        SB["bracket"].append(ronda)
        definicion = [f"Penales {m['pen'][0]}-{m['pen'][1]}: {m['gana']}" if m["pen"] else ""
                      for m in ronda]
        SB["historial"].append(_fila_historial(
            SB, B_ETAPAS[etapa], loc["id"][0], vis["id"][0], gl[0], gv[0], definicion))
        if etapa == B_RED - 1:
            SB["asc_reducido"] = int(gan["id"][0, 0])
            SB["perdedor_final"] = int(per["id"][0, 0])
        SB["fecha"] += 1

    else:                                                 # ---- promoción
        final_p = tabla_final(S)
        fila = final_p[final_p["Pos"] == N - 3].iloc[0]   # mejor descendido: 27°
        p_id, p_nom = int(fila["id"]), fila["Equipo"]
        b_id = SB["perdedor_final"]
        gl, gv, gana_b, pen = jugar_ko(rng, np.array([r[b_id]]), np.array([S["r"][p_id]]),
                                       P["sorpresa"], localia=0.0)    # cancha neutral
        tanda = tanda_penales(rng, gana_b[0]) if pen[0] else None
        partido = nuevo_partido("Promoción", f + 1, "Promoción", "Promoción", nom[b_id], p_nom,
                                gl[0], gv[0], tanda=tanda,
                                gana=nom[b_id] if gana_b[0] else p_nom, neutral=True)
        SB["log"].append(partido)
        SB["promo_partido"] = partido
        partes = ["Cancha neutral"]
        if pen[0]:
            partes.append(f"Penales {partido['pen'][0]}-{partido['pen'][1]}: {partido['gana']}")
        SB["historial"].append(pd.DataFrame({
            "Instancia": "Promoción", "Local": [nom[b_id]], "GL": gl, "GV": gv,
            "Visitante": [p_nom], "Definición": " · ".join(partes),
        }))
        SB["promo"] = {"b_id": b_id, "p_id": p_id, "p_nombre": p_nom, "gana_b": bool(gana_b[0])}
        SB["fecha"] += 1


# ----------------------------------------------------------------------------
# MOTOR FEDERAL A
# ----------------------------------------------------------------------------
def nueva_estructura_f(SF, rng):
    """Arma los 4 grupos por cercanía y el fixture ida y vuelta de la fase 1.

    El tamaño de cada grupo no es fijo (el plantel del Federal A cambia con los
    ascensos y descensos de la Primera Nacional), así que la cantidad de fechas se
    recalcula cada temporada según el grupo más largo."""
    n = len(SF["nombres"])
    grupos = {g: [] for g in F_GRUPOS_NOMBRES}
    for i, nom in enumerate(SF["nombres"]):
        grupos[region_de(nom)].append(i)
    SF["grupos"] = [np.array(grupos[g], dtype=int) for g in F_GRUPOS_NOMBRES]
    SF["grupo_de"] = np.zeros(n, dtype=int)
    for g, ids in enumerate(SF["grupos"]):
        SF["grupo_de"][ids] = g

    idas = [generar_fixture(len(ids)) for ids in SF["grupos"]]
    rondas_ida = max((len(f) for f in idas), default=0)
    fechas = []
    for k in range(rondas_ida):
        fecha = []
        for ids, f in zip(SF["grupos"], idas):
            if k < len(f):
                fecha += [(int(ids[a]), int(ids[b])) for a, b in f[k]]
        fechas.append(fecha)
    fechas += [[(v, l) for l, v in fecha] for fecha in fechas]     # vuelta: local/visitante al revés
    SF["fechas"] = fechas
    SF["f1_rondas"] = rondas_ida * 2
    SF["total"] = SF["f1_rondas"] + F_F2_RONDAS + F_RED

    SF["fecha"] = 0
    for k in STATS:
        SF[k] = np.zeros(n, dtype=int)
    SF["historial"] = []
    SF["log"] = []
    SF["pos_hist"] = []
    SF["bracket"] = []
    SF["tablas_f1"] = None
    SF["zonas2"] = None
    SF["zona2_de"] = None
    SF["fechas2"] = None
    SF["ord2"] = None
    SF["campeon"] = None
    SF["asc_directo"] = []
    SF["red"] = None
    SF["entrantes"] = None
    SF["asc_reducido"] = None
    SF["ascendidos"] = []


def tabla_f_grupo(SF, g):
    """Tabla del grupo `g` (0-3, por cercanía) de la fase 1."""
    df = df_stats(SF["nombres"], SF["r"], SF, SF["grupos"][g])
    df.insert(0, "Pos", df.index + 1)
    df["Destino"] = [destino_f1(p) for p in df["Pos"]]
    return df


def tabla_f_f2(SF, z):
    """Tabla de la zona de la fase 2 (0 Campeonato, 1 Descenso)."""
    df = df_stats(SF["nombres"], SF["r"], SF, SF["zonas2"][z])
    df.insert(0, "Pos", df.index + 1)
    df["Destino"] = [destino_f2(z, p) for p in df["Pos"]]
    return df


def iniciar_fase2_f(SF, rng):
    """Fin de la fase 1: clasifican los 5 primeros de cada grupo (20 en total), se
    reparten en Zona Campeonato y Zona Descenso (10 y 10) y TODOS los puntos vuelven
    a 0."""
    SF["tablas_f1"] = [tabla_f_grupo(SF, g) for g in range(len(SF["grupos"]))]
    clasif = pd.concat([df.head(5) for df in SF["tablas_f1"]])
    clasif = clasif.sort_values(["Pts", "DG", "GF"], ascending=False).reset_index(drop=True)
    orden = clasif["id"].to_numpy()
    SF["zonas2"] = [orden[:F_ZONA_TAM], orden[F_ZONA_TAM:2 * F_ZONA_TAM]]
    SF["zona2_de"] = np.full(len(SF["nombres"]), -1, dtype=int)   # -1: no clasificó a fase 2
    for z, ids in enumerate(SF["zonas2"]):
        SF["zona2_de"][ids] = z

    for k in STATS:
        SF[k] = np.zeros(len(SF["nombres"]), dtype=int)

    base = [generar_fixture(F_ZONA_TAM), generar_fixture(F_ZONA_TAM)]
    SF["fechas2"] = [
        [(int(ids[a]), int(ids[b])) for ids, fx in zip(SF["zonas2"], base) for a, b in fx[k]]
        for k in range(F_F2_RONDAS)
    ]


def iniciar_reducido_f(SF):
    """Fin de la fase 2: 1° y 2° de Campeonato ascienden directo; del 3° al 10°
    arman el reducido."""
    ids = tabla_f_f2(SF, 0)["id"].to_numpy()
    SF["ord2"] = ids
    SF["campeon"] = int(ids[0])
    SF["asc_directo"] = [int(ids[0]), int(ids[1])]

    pts = 3 * SF["g"] + SF["e"]
    idx = ids[2:10][None, :]
    SF["red"] = {"id": idx, "pts": pts[idx], "seed": np.arange(1, 9)[None, :]}
    SF["entrantes"] = pd.DataFrame(
        [(i + 1, SF["nombres"][ids[2 + i]], f"{3 + i}° Campeonato") for i in range(8)],
        columns=["Mérito", "Equipo", "Origen"],
    )


def simular_fecha_f(SF, P, rng):
    f = SF["fecha"]
    if f >= SF["total"]:
        return
    r, nom = SF["r"], SF["nombres"]

    if f < SF["f1_rondas"] + F_F2_RONDAS:                 # ---- zonas (fase 1 y fase 2)
        if f < SF["f1_rondas"]:
            pares = SF["fechas"][f]
            etiqueta = lambda i: f"Zona {F_GRUPOS_NOMBRES[SF['grupo_de'][i]]}"
        else:
            pares = SF["fechas2"][f - SF["f1_rondas"]]
            etiqueta = lambda i: "Campeonato" if SF["zona2_de"][i] == 0 else "Descenso"
        if pares:
            h = np.array([x[0] for x in pares])
            a = np.array([x[1] for x in pares])
            gh, ga = jugar(rng, r[h], r[a], **P)
            sumar_partidos(SF, h, a, gh, ga)
            SF["historial"].append(_fila_historial(SF, [etiqueta(i) for i in h], h, a, gh, ga, ""))
            for x, y, g1, g2 in zip(h, a, gh, ga):
                SF["log"].append(nuevo_partido("Federal A", f + 1, rotulo_f(SF, f + 1),
                                               etiqueta(x), nom[x], nom[y], g1, g2))
            if f < SF["f1_rondas"]:
                dfs = [tabla_f_grupo(SF, g) for g in range(len(SF["grupos"]))]
            else:
                dfs = [tabla_f_f2(SF, z) for z in range(2)]
            pos = np.zeros(len(nom), dtype=int)
            for dfz in dfs:
                pos[dfz["id"].to_numpy()] = dfz["Pos"].to_numpy()
            SF["pos_hist"].append((0 if f < SF["f1_rondas"] else 1, pos))
        SF["fecha"] += 1
        if SF["fecha"] == SF["f1_rondas"]:
            iniciar_fase2_f(SF, rng)
        elif SF["fecha"] == SF["f1_rondas"] + F_F2_RONDAS:
            iniciar_reducido_f(SF)

    else:                                                  # ---- reducido
        etapa = f - SF["f1_rondas"] - F_F2_RONDAS
        T = SF["red"] if etapa == 0 else SF["ganadores"]
        A, B = cruces_mejor_peor(T)
        final = etapa == F_RED - 1
        loc, vis, gl, gv, gan, per, pen = jugar_reducido_federal(rng, r, A, B, P["sorpresa"], final)
        SF["ganadores"] = gan
        ronda = []
        for li, vi, g1, g2, wi, p in zip(loc["id"][0], vis["id"][0], gl[0], gv[0],
                                          gan["id"][0], pen[0]):
            tanda = tanda_penales(rng, wi == li) if (p and final) else None
            partido = nuevo_partido("Federal A", f + 1, rotulo_f(SF, f + 1), F_ETAPAS[etapa],
                                    nom[li], nom[vi], g1, g2, tanda=tanda, gana=nom[wi],
                                    neutral=final)
            ronda.append(partido)
            SF["log"].append(partido)
        SF["bracket"].append(ronda)
        definicion = []
        for m in ronda:
            if m["pen"]:
                definicion.append(f"Penales {m['pen'][0]}-{m['pen'][1]}: {m['gana']}")
            elif m["gl"] == m["gv"]:
                definicion.append(f"Ganó {m['gana']} por mejor posición en la tabla")
            else:
                definicion.append("")
        SF["historial"].append(_fila_historial(SF, F_ETAPAS[etapa], loc["id"][0], vis["id"][0],
                                               gl[0], gv[0], definicion))
        if final:
            SF["asc_reducido"] = int(gan["id"][0, 0])
            SF["ascendidos"] = SF["asc_directo"] + [SF["asc_reducido"]]
        SF["fecha"] += 1


VERSION_ESTADO = 6       # cambia si se modifica la estructura del estado guardado


def crear_estado():
    # Semilla tomada del reloj: cada ejecución/reinicio da resultados distintos
    rng = np.random.default_rng(time.time_ns() % (2**32))
    S = {
        "rng": rng, "temp": 1, "campeones": [], "movimientos": None,
        "rating": {**{k: float(v) for k, v in EQUIPOS.items()},
                   **{k: float(v) for k, v in EQUIPOS_B.items()},
                   **{k: float(v) for k, v in EQUIPOS_FEDERAL.items()},
                   **{k: float(v) for k, v in EQUIPOS_PRIMERA_B.items()}},
        "nombres": list(EQUIPOS),
        "r": np.array(list(EQUIPOS.values()), dtype=float),
        "federal": list(EQUIPOS_FEDERAL),
        "primera_b": list(EQUIPOS_PRIMERA_B),
        "cerrada_ambas": False, "version": VERSION_ESTADO,
    }
    nueva_estructura(S)
    SB = {"nombres": list(EQUIPOS_B), "r": np.array(list(EQUIPOS_B.values()), dtype=float)}
    nueva_estructura_b(SB, rng)
    S["b"] = SB
    SF = {"nombres": list(EQUIPOS_FEDERAL), "r": np.array(list(EQUIPOS_FEDERAL.values()), dtype=float)}
    nueva_estructura_f(SF, rng)
    S["f"] = SF
    return S


def nueva_temporada(S, volatilidad):
    """Ascensos, descensos y promoción + evolución de las medias + nuevos fixtures."""
    SB, SF, rng = S["b"], S["f"], S["rng"]
    # 1) guardar las medias actuales (incluye ediciones manuales)
    for nom, x in zip(S["nombres"], S["r"]):
        S["rating"][nom] = float(x)
    for nom, x in zip(SB["nombres"], SB["r"]):
        S["rating"][nom] = float(x)
    for nom, x in zip(SF["nombres"], SF["r"]):
        S["rating"][nom] = float(x)

    # 2) ascensos y descensos
    final = tabla_final(S)
    promo = SB["promo"]
    p27 = promo["p_nombre"]
    directos = [SB["nombres"][i] for i in SB["asc_directo"]]
    reducido = SB["nombres"][SB["asc_reducido"]]
    suben = directos + [reducido]
    bajan_p = list(final[final["Pos"] >= N - 2]["Equipo"])          # 28° al 30°
    if promo["gana_b"]:                                              # gana la promoción el de la B
        suben.append(SB["nombres"][promo["b_id"]])
        bajan_p.append(p27)
    bajan_b = [SB["nombres"][i] for i in SB["desc_b"]]              # 7° al 12° de Zona Descenso
    bajan_b_fed = [n for n in bajan_b if origen(n) == "Interior"]
    bajan_b_pb = [n for n in bajan_b if origen(n) == "Metropolitana"]

    S["nombres"] = [n for n in S["nombres"] if n not in bajan_p] + suben
    base_b = [n for n in SB["nombres"] if n not in suben and n not in bajan_b] + bajan_p
    # Del Federal A ascienden SIEMPRE los 3 (1°, 2° y el campeón del reducido), sin
    # importar cuántos hayan bajado ese año a esa categoría. El resto de los lugares
    # que falten para completar los 36 se sortea entre el Federal A y la Primera B,
    # con más chances los de mejor media.
    ascendidos_f = [SF["nombres"][i] for i in SF["ascendidos"]]
    garantizados = list(ascendidos_f)
    # Salvaguarda: si la B liberó menos de 3 lugares, se relegan un par de equipos
    # más (los de peor media) para no romper el tamaño fijo de 36.
    sobran = len(base_b) + len(garantizados) - NB
    if sobran > 0:
        peores = sorted(base_b, key=lambda n: S["rating"][n])[:sobran]
        for n in peores:
            base_b.remove(n)
            bajan_b.append(n)
            (bajan_b_fed if origen(n) == "Interior" else bajan_b_pb).append(n)

    faltan = max(0, NB - len(base_b) - len(garantizados))
    pool = [n for n in (S["federal"] + S["primera_b"]) if n not in garantizados]
    if faltan > 0:
        w = np.exp((np.array([S["rating"][n] for n in pool]) - 50.0) / 6.0)
        elegidos = set(rng.choice(len(pool), size=faltan, replace=False, p=w / w.sum()).tolist())
    else:
        elegidos = set()
    entran = garantizados + [pool[i] for i in elegidos]
    resto = [n for i, n in enumerate(pool) if i not in elegidos]
    S["federal"] = [n for n in resto if origen(n) == "Interior"] + bajan_b_fed
    S["primera_b"] = [n for n in resto if origen(n) == "Metropolitana"] + bajan_b_pb
    SB["nombres"] = base_b + entran

    entran_fed = [n for n in entran if origen(n) == "Interior"]
    entran_pb = [n for n in entran if origen(n) == "Metropolitana"]
    S["movimientos"] = {
        "directos": directos, "reducido": reducido,
        "bajan_p": bajan_p, "bajan_b_fed": bajan_b_fed, "bajan_b_pb": bajan_b_pb,
        "entran_fed": entran_fed, "entran_pb": entran_pb,
        "campeon_federal": SF["nombres"][SF["campeon"]] if SF["campeon"] is not None else None,
        "ascendidos_federal": ascendidos_f,
        "promo_texto": (
            f"La promoción la ganó {'el equipo de la B' if promo['gana_b'] else p27}"
            + (f": asciende {suben[-1]} y baja {p27}." if promo["gana_b"]
               else f", que se mantiene en Primera.")),
    }

    # 3) las medias vuelven un poco hacia el promedio de la liga en la que juegan
    #    (los ascendidos suben un poco, los descendidos bajan) más un ruido aleatorio
    for nombres in (S["nombres"], SB["nombres"], S["federal"], S["primera_b"]):
        arr = np.array([S["rating"][n] for n in nombres])
        arr = arr + REVERSION * (arr.mean() - arr) + rng.normal(0, volatilidad, len(arr))
        arr = np.clip(arr, MIN_R, MAX_R)
        for n, x in zip(nombres, arr):
            S["rating"][n] = float(x)
    S["r"] = np.array([S["rating"][n] for n in S["nombres"]])
    SB["r"] = np.array([S["rating"][n] for n in SB["nombres"]])
    SF["nombres"] = list(S["federal"])
    SF["r"] = np.array([S["rating"][n] for n in SF["nombres"]])

    S["temp"] += 1
    S["cerrada_ambas"] = False
    nueva_estructura(S)
    nueva_estructura_b(SB, rng)
    nueva_estructura_f(SF, rng)


# ----------------------------------------------------------------------------
# PRESENTACIÓN (estilos, escudos, tarjetas)
# ----------------------------------------------------------------------------
CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Barlow+Condensed:wght@600;700;800&display=swap');
:root{--cel:#74ACDF;--cel2:#4a90d0;--navy:#0b1d3a;--gold:#d4a017;--line:rgba(128,128,128,.2);--soft:rgba(128,128,128,.055);--soft2:rgba(128,128,128,.1);--acc:#2f7fd0;--pen:#7c3aed;--win:#16a34a;--lose:#dc2626;}
html,body,.stApp,.stMarkdown,button,input,textarea,[data-testid="stMetricValue"]{font-family:'Inter',system-ui,-apple-system,sans-serif !important;}
.block-container{padding-top:1.2rem;padding-bottom:3rem;max-width:1440px;}
[data-testid="stSidebar"] h2{font-size:1.05rem;}
/* ---------- cabecera ---------- */
.hero{position:relative;overflow:hidden;background:radial-gradient(circle at 88% 20%,rgba(116,172,223,.35),transparent 42%),linear-gradient(120deg,#07142b 0%,#0b1d3a 45%,#123a6b 100%);color:#fff;border-radius:18px;padding:24px 28px 20px;margin-bottom:12px;box-shadow:0 14px 34px rgba(7,20,43,.28);}
.hero::before{content:"";position:absolute;left:0;right:0;top:0;height:6px;background:linear-gradient(90deg,var(--cel) 0 33.3%,#fff 33.3% 66.6%,var(--cel) 66.6%);}
.hero .sol{position:absolute;right:26px;top:14px;font-size:64px;opacity:.14;}
.hero-top{display:flex;justify-content:space-between;align-items:flex-end;gap:18px;flex-wrap:wrap;}
.hero-k{text-transform:uppercase;letter-spacing:.18em;font-size:.68rem;font-weight:700;color:var(--cel);}
.hero h1{color:#fff !important;font-family:'Barlow Condensed',sans-serif !important;font-size:2.35rem;font-weight:800;margin:2px 0 0;padding:0;letter-spacing:.01em;line-height:1.05;text-transform:uppercase;}
.hero p{margin:4px 0 0;opacity:.72;font-size:.9rem;}
.hero-stats{display:flex;gap:10px;flex-wrap:wrap;}
.hs{background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.14);border-radius:12px;padding:8px 14px;min-width:128px;}
.hs span{display:block;font-size:.64rem;opacity:.7;text-transform:uppercase;letter-spacing:.09em;font-weight:600;}
.hs b{font-family:'Barlow Condensed',sans-serif;font-size:1.35rem;font-weight:700;letter-spacing:.02em;}
.hs .bar{height:4px;border-radius:3px;background:rgba(255,255,255,.15);margin-top:4px;overflow:hidden;}
.hs .bar i{display:block;height:100%;background:var(--cel);}
/* ---------- navegación ---------- */
.stTabs [data-baseweb="tab-list"]{gap:6px;border-bottom:1px solid var(--line);}
.stTabs [data-baseweb="tab"]{font-weight:700;padding:10px 16px;border-radius:10px 10px 0 0;}
.stTabs [data-baseweb="tab"] p{font-size:.95rem;}
.stTabs [data-baseweb="tab-highlight"]{background:var(--cel2);height:3px;}
.stTabs .stTabs [data-baseweb="tab"] p{font-size:.86rem;}
.stTabs .stTabs [data-baseweb="tab"]{padding:8px 12px;}
/* ---------- botones / widgets ---------- */
.stButton>button,[data-testid="stBaseButton-primary"],[data-testid="stBaseButton-secondary"]{border-radius:10px;font-weight:600;}
[data-testid="stExpander"] details{border-radius:12px;border:1px solid var(--line);background:var(--soft);}
[data-testid="stExpander"] summary{font-weight:700;}
[data-testid="stDataFrame"]{border-radius:12px;overflow:hidden;border:1px solid var(--line);}
/* ---------- barra de estado de cada liga ---------- */
.status{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:6px 0 10px;}
.stc{border:1px solid var(--line);background:var(--soft);border-radius:12px;padding:10px 14px;}
.stc span{display:block;font-size:.66rem;text-transform:uppercase;letter-spacing:.08em;font-weight:700;opacity:.65;}
.stc b{font-family:'Barlow Condensed',sans-serif;font-size:1.3rem;font-weight:700;}
.stc .bar{height:5px;border-radius:3px;background:var(--soft2);margin-top:6px;overflow:hidden;}
.stc .bar i{display:block;height:100%;background:linear-gradient(90deg,var(--cel2),var(--cel));}
.aviso{border-left:4px solid var(--cel2);background:color-mix(in srgb,var(--cel) 10%,transparent);border-radius:8px;padding:9px 14px;font-size:.88rem;margin:4px 0 10px;}
/* ---------- títulos de sección ---------- */
.sec{display:flex;align-items:baseline;gap:10px;margin:8px 0 10px;flex-wrap:wrap;}
.sec .tt{font-family:'Barlow Condensed',sans-serif;font-size:1.45rem;font-weight:700;letter-spacing:.01em;text-transform:uppercase;border-left:5px solid var(--c,#2f7fd0);padding-left:10px;line-height:1.1;}
.sec .sub{font-size:.82rem;opacity:.62;}
.chip{display:inline-flex;align-items:center;gap:4px;padding:2px 10px;border-radius:999px;font-size:.7rem;font-weight:700;letter-spacing:.03em;background:color-mix(in srgb,var(--c) 14%,transparent);color:var(--c);border:1px solid color-mix(in srgb,var(--c) 38%,transparent);white-space:nowrap;}
.legend{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:.76rem;opacity:.85;margin:8px 2px 4px;}
.legend span{display:inline-flex;align-items:center;gap:6px;}
.legend i{width:12px;height:12px;border-radius:3px;display:inline-block;}
/* ---------- escudos ---------- */
.crest-img{object-fit:contain;flex:none;vertical-align:middle;filter:drop-shadow(0 1px 1px rgba(0,0,0,.18));}
.crest{display:inline-flex;align-items:center;justify-content:center;color:#fff;font-weight:800;border-radius:7px 7px 50% 50%/7px 7px 62% 62%;flex:none;letter-spacing:-.03em;line-height:1;}
/* ---------- partidos ---------- */
.score{display:flex;justify-content:center;align-items:center;gap:6px;font-family:'Barlow Condensed',sans-serif;font-weight:700;font-size:1.25rem;font-variant-numeric:tabular-nums;white-space:nowrap;}
.score .n{background:var(--soft2);border-radius:7px;min-width:28px;text-align:center;padding:0 7px;line-height:1.5;}
.score .n.w{background:color-mix(in srgb,var(--win) 20%,transparent);color:color-mix(in srgb,var(--win) 80%,currentColor);}
.score small{font-weight:700;font-size:.92rem;color:var(--pen);}
.score .sep{opacity:.4;}
.score .vs{font-family:'Inter',sans-serif;font-size:.72rem;font-weight:700;letter-spacing:.08em;opacity:.55;border:1px dashed var(--line);border-radius:6px;padding:2px 8px;}
details.tanda{margin:0 0 8px;border:1px dashed color-mix(in srgb,var(--pen) 45%,transparent);border-radius:10px;padding:5px 10px;background:color-mix(in srgb,var(--pen) 6%,transparent);font-size:.8rem;}
details.tanda summary{cursor:pointer;font-weight:700;color:var(--pen);}
.trow{display:flex;align-items:center;gap:8px;margin-top:6px;flex-wrap:wrap;}
.trow .tn{min-width:120px;font-weight:600;}
.trow .tt{font-weight:800;min-width:16px;}
.pk{display:inline-flex;width:19px;height:19px;border-radius:50%;align-items:center;justify-content:center;font-size:.66rem;font-weight:800;color:#fff;margin-right:3px;}
.pk.ok{background:var(--win);}.pk.no{background:var(--lose);}
[class*="st-key-fx"] [data-testid="stHorizontalBlock"]{flex-wrap:nowrap !important;align-items:center;background:var(--soft);border:1px solid var(--line);border-radius:12px;padding:6px 8px;margin-bottom:2px;transition:border-color .15s;}
[class*="st-key-fx"] [data-testid="stHorizontalBlock"]:hover{border-color:color-mix(in srgb,var(--cel2) 60%,transparent);}
[class*="st-key-fx"] [data-testid="stColumn"]{min-width:0 !important;width:auto !important;flex:5 1 0 !important;}
[class*="st-key-fx"] [data-testid="stColumn"]:nth-child(2){flex:3.6 1 0 !important;}
[class*="st-key-fx"] [data-testid="stVerticalBlock"]{gap:.45rem;}
[class*="st-key-fx"] button{border:none !important;background:transparent !important;box-shadow:none !important;padding:2px 4px !important;min-height:0 !important;}
[class*="st-key-fx"] button p{font-weight:600;font-size:.88rem;line-height:1.2;}
[class*="st-key-fx"] button:hover p{color:var(--cel2);text-decoration:underline;}
[class*="st-key-fx"] [data-testid="stColumn"]:nth-child(1) button{justify-content:flex-end;text-align:right;width:100%;}
[class*="st-key-fx"] [data-testid="stColumn"]:nth-child(3) button{justify-content:flex-start;text-align:left;width:100%;}
.fx-head{display:flex;align-items:center;gap:8px;margin:2px 0 8px;flex-wrap:wrap;}
.mrow{border:1px solid var(--line);border-radius:12px;padding:8px 12px;margin-bottom:8px;background:var(--soft);}
.mrow .meta{display:flex;gap:6px;align-items:center;flex-wrap:wrap;font-size:.74rem;margin-bottom:5px;}
.mline{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:10px;}
.side{display:flex;align-items:center;gap:8px;font-weight:600;font-size:.9rem;}
.side.l{justify-content:flex-end;text-align:right;}
.side.w{font-weight:800;}
/* ---------- tarjetas ---------- */
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;margin:4px 0 14px;}
.card{border:1px solid var(--line);background:var(--soft);border-radius:14px;padding:13px 16px;border-top:3px solid var(--c,#2f7fd0);}
.card .k{font-size:.68rem;text-transform:uppercase;letter-spacing:.08em;font-weight:700;opacity:.68;}
.card .v{display:flex;align-items:center;gap:8px;font-weight:700;font-size:.98rem;margin-top:8px;flex-wrap:wrap;}
.card .v.big{font-family:'Barlow Condensed',sans-serif;font-size:1.7rem;}
.card .s{font-size:.78rem;opacity:.7;margin-top:5px;}
.movlist{display:flex;flex-wrap:wrap;gap:7px;margin:4px 0 12px;}
.mv{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--line);border-radius:999px;padding:3px 11px 3px 5px;font-size:.8rem;font-weight:600;background:var(--soft);}
.mv .d{font-weight:800;}
.up{color:var(--win);}.down{color:var(--lose);}
.mlab{font-size:.7rem;text-transform:uppercase;letter-spacing:.08em;font-weight:700;opacity:.72;margin:6px 0 4px;}
.tlist{display:flex;flex-wrap:wrap;gap:8px;margin:4px 0 8px;}
.tl{display:inline-flex;align-items:center;gap:7px;border:1px solid var(--line);border-radius:10px;padding:5px 10px 5px 6px;font-weight:600;font-size:.86rem;background:var(--soft);}
.tl small{opacity:.6;font-weight:700;}
.champ{border-radius:14px;padding:18px;text-align:center;background:linear-gradient(135deg,rgba(212,160,23,.25),rgba(212,160,23,.05));border:1px solid rgba(212,160,23,.55);}
.champ .t{font-size:.68rem;text-transform:uppercase;letter-spacing:.14em;font-weight:800;color:#b7860b;}
.champ .nm{font-family:'Barlow Condensed',sans-serif;font-weight:800;font-size:1.5rem;margin-top:8px;text-transform:uppercase;}
.champ .s{font-size:.76rem;opacity:.75;margin-top:2px;}
/* ---------- cuadro del reducido ---------- */
.bracket{display:grid;grid-template-columns:repeat(5,minmax(205px,1fr));gap:28px;overflow-x:auto;padding:4px 2px 14px;}
.round{display:flex;flex-direction:column;}
.round-h{text-align:center;margin-bottom:10px;}
.round-b{display:flex;flex-direction:column;justify-content:space-around;gap:14px;flex:1;}
.bm{position:relative;border:1px solid var(--line);border-radius:12px;background:var(--soft);}
.round:not(.last) .bm::after{content:"";position:absolute;right:-29px;top:50%;width:28px;border-top:2px solid var(--line);}
.bt{display:flex;align-items:center;gap:7px;padding:7px 10px;font-size:.84rem;}
.bt+.bt{border-top:1px solid var(--line);}
.bt .nm{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-weight:600;}
.bt .g{font-family:'Barlow Condensed',sans-serif;font-size:1.05rem;font-weight:700;min-width:14px;text-align:right;}
.bt .p{font-size:.74rem;font-weight:800;color:var(--pen);}
.bt .lv{font-size:.58rem;font-weight:800;border:1px solid var(--line);border-radius:4px;padding:0 4px;opacity:.7;}
.bt.win{background:color-mix(in srgb,var(--win) 12%,transparent);box-shadow:inset 3px 0 0 var(--win);}
.bt.win .nm{font-weight:800;}
.bt.lose{opacity:.5;}
.bt.tbd .nm{opacity:.5;font-style:italic;font-weight:500;}
.bfoot{font-size:.7rem;padding:4px 10px 6px;border-top:1px dashed var(--line);}
.bfoot b{color:var(--win);}
.bm details.tanda{margin:0 8px 8px;font-size:.72rem;}
.bm .trow .tn{min-width:0;}
.promo{margin-top:14px;}
/* ---------- ficha de club ---------- */
.team-head{display:flex;align-items:center;gap:16px;margin-bottom:8px;flex-wrap:wrap;}
.team-head .tn{font-family:'Barlow Condensed',sans-serif;font-size:1.9rem;font-weight:800;text-transform:uppercase;line-height:1;}
.rec{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0 12px;}
.rec div{border:1px solid var(--line);background:var(--soft);border-radius:10px;padding:5px 12px;text-align:center;min-width:54px;}
.rec b{display:block;font-family:'Barlow Condensed',sans-serif;font-size:1.25rem;}
.rec span{font-size:.64rem;text-transform:uppercase;letter-spacing:.07em;opacity:.7;font-weight:600;}
.form{display:inline-flex;gap:4px;vertical-align:middle;margin-top:3px;}
.fm{width:22px;height:22px;border-radius:6px;display:inline-flex;align-items:center;justify-content:center;color:#fff;font-size:.68rem;font-weight:800;}
.fm.G{background:var(--win);}.fm.E{background:#64748b;}.fm.P{background:var(--lose);}
.next{border:1px solid var(--line);border-left:4px solid var(--cel2);border-radius:10px;padding:8px 12px;background:var(--soft);font-size:.86rem;margin-bottom:10px;display:flex;align-items:center;gap:8px;flex-wrap:wrap;}
.cgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;margin-top:8px;}
.ct{display:flex;flex-direction:column;align-items:center;gap:8px;text-align:center;border:1px solid var(--line);background:var(--soft);border-radius:14px;padding:14px 8px;font-weight:600;font-size:.84rem;}
.catgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;margin-top:8px;}
</style>"""

COLOR_COMP = [
    ("Campeonato", "#16a34a"), ("Intermedia", "#d97706"), ("Descenso", "#dc2626"),
    ("Zona A", "#4f46e5"), ("Zona B", "#0891b2"), ("Octavos", "#2563eb"),
    ("Cuartos", "#1d4ed8"), ("Semifinal", "#7c3aed"), ("Final", "#b7860b"),
    ("Promoción", "#9333ea"), ("Fase 1", "#475569"), ("Federal A", "#b45309"),
    ("Primera B", "#0369a1"),
    ("Primera División", "#1e5aa8"), ("Primera Nacional", "#0f766e"),
]
esc = html.escape


def color_de(txt):
    for k, c in COLOR_COMP:
        if k in txt:
            return c
    return "#64748b"


def chip(txt, color=None):
    return f'<span class="chip" style="--c:{color or color_de(txt)}">{esc(txt)}</span>'


def seccion(titulo, sub="", color="#2f7fd0"):
    sub = f'<span class="sub">{esc(sub)}</span>' if sub else ""
    st.markdown(f'<div class="sec" style="--c:{color}"><span class="tt">{titulo}</span>{sub}</div>',
                unsafe_allow_html=True)


def aviso(txt):
    st.markdown(f'<div class="aviso">{txt}</div>', unsafe_allow_html=True)


def leyenda(items):
    st.markdown('<div class="legend">' + "".join(
        f'<span><i style="background:{c}"></i>{esc(t)}</span>' for t, c in items) + "</div>",
        unsafe_allow_html=True)


def iniciales(nombre):
    base = nombre.split("(")[0].replace("'", "").strip()
    w = base.split()
    return (w[0][0] + w[1][0]).upper() if len(w) >= 2 else base[:3].upper()


def crest(nombre, size=26):
    """Escudo real del club (o un distintivo con sus iniciales si no hay imagen)."""
    url = ESCUDOS.get(nombre)
    if url:
        return (f'<img class="crest-img" src="{esc(url)}" width="{size}" height="{size}" '
                f'alt="" loading="lazy" title="{esc(nombre)}">')
    h = int(hashlib.md5(nombre.encode("utf-8")).hexdigest()[:6], 16)
    return (f'<span class="crest" style="width:{size}px;height:{size + 2}px;'
            f'font-size:{max(8, round(size * 0.36))}px;background:linear-gradient(160deg,'
            f'hsl({h % 360},62%,44%),hsl({(h // 360 + 25) % 360},58%,28%))">'
            f'{esc(iniciales(nombre))}</span>')


def norm(s):
    s = unicodedata.normalize("NFKD", str(s).lower())
    return "".join(c for c in s if not unicodedata.combining(c))


_STOP = {"fecha", "vs", "contra", "de", "del", "la", "el", "y", "-", "fch", "f"}


def coincide(consulta, texto, fecha, marcadores):
    """Cada palabra de la búsqueda tiene que aparecer. Un número = número de fecha;
    algo como 2-1 = resultado (en cualquier orden)."""
    for t in norm(consulta).replace("–", "-").split():
        if t in _STOP:
            continue
        if t.isdigit():
            if int(t) != fecha:
                return False
        elif re.fullmatch(r"\d+-\d+", t):
            if t not in marcadores:
                return False
        elif t not in texto:
            return False
    return True


def todos_los_partidos():
    return S["log"] + S["b"]["log"] + S["f"]["log"]


def categoria_de(nombre):
    if nombre in S["nombres"]:
        return "Primera División"
    if nombre in S["b"]["nombres"]:
        return "Primera Nacional"
    if nombre in S["federal"]:
        return "Federal A"
    if nombre in S["primera_b"]:
        return "Primera B"
    return ""


def marcador_html(p, crests=False):
    cl = crest(p["local"], 22) if crests else ""
    cv = crest(p["visita"], 22) if crests else ""
    if p["gl"] is None:
        return f'<div class="score">{cl}<span class="vs">VS</span>{cv}</div>'
    wl = ' w' if p["gana"] == p["local"] else ''
    wv = ' w' if p["gana"] == p["visita"] else ''
    pl = pv = ""
    if p["pen"]:
        pl, pv = f"<small>({p['pen'][0]})</small>", f"<small>({p['pen'][1]})</small>"
    return (f'<div class="score">{cl}<span class="n{wl}">{p["gl"]}</span>{pl}<span class="sep">–</span>'
            f'{pv}<span class="n{wv}">{p["gv"]}</span>{cv}</div>')


def tanda_html(p, abierto=False):
    if not p.get("tanda"):
        return ""
    filas = ""
    for nombre, serie, total in ((p["local"], p["tanda"][0], p["pen"][0]),
                                 (p["visita"], p["tanda"][1], p["pen"][1])):
        dots = "".join('<span class="pk ok">✓</span>' if x else '<span class="pk no">✗</span>'
                       for x in serie)
        filas += (f'<div class="trow">{crest(nombre, 18)}<span class="tn">{esc(nombre)}:</span>'
                  f'<span class="tt">{total}</span><span>{dots}</span></div>')
    return (f'<details class="tanda"{" open" if abierto else ""}><summary>🥅 Penales · '
            f'{esc(p["local"])} {p["pen"][0]} – {p["pen"][1]} {esc(p["visita"])}</summary>'
            f'{filas}</details>')


def fila_partido_html(p, abierto=False):
    """Partido en formato tarjeta."""
    wl = " w" if p["gana"] == p["local"] else ""
    wv = " w" if p["gana"] == p["visita"] else ""
    meta = (chip(p["liga"]) + (chip(p["comp"]) if p["comp"] != p["liga"] else "")
            + f'<span style="opacity:.7;font-weight:600">{esc(p["rotulo"])}</span>'
            + ('<span style="opacity:.6">· cancha neutral</span>' if p["neutral"] else ""))
    return (f'<div class="mrow"><div class="meta">{meta}</div><div class="mline">'
            f'<div class="side l{wl}">{esc(p["local"])} {crest(p["local"], 26)}</div>'
            f'{marcador_html(p)}'
            f'<div class="side{wv}">{crest(p["visita"], 26)} {esc(p["visita"])}</div></div>'
            f'{tanda_html(p, abierto)}</div>')


def lista_equipos_html(items):
    """items: lista de (nombre, detalle)."""
    if not items:
        return '<div style="opacity:.6">Por definir</div>'
    return '<div class="tlist">' + "".join(
        f'<span class="tl">{crest(n, 26)}{esc(n)}{f" <small>{esc(d)}</small>" if d else ""}</span>'
        for n, d in items) + "</div>"


def resultado_para(p, nombre):
    local = p["local"] == nombre
    gf, gc = (p["gl"], p["gv"]) if local else (p["gv"], p["gl"])
    letra = "G" if gf > gc else "P" if gf < gc else "E"
    return local, gf, gc, letra


# ---- Calendario: partidos jugados y por jugar -------------------------------
def pendiente(liga, n, rotulo, comp, local, visita):
    return {"liga": liga, "fecha": n, "rotulo": rotulo, "comp": comp, "local": local,
            "visita": visita, "gl": None, "gv": None, "gana": None, "tanda": None,
            "pen": None, "neutral": False}


def fechas_conocidas_p():
    return len(S["fechas"])


def partidos_fecha_p(n):
    if n <= S["fecha"]:
        return [p for p in S["log"] if p["fecha"] == n]
    nom = S["nombres"]
    return [pendiente("Primera División", n, rotulo_p(n),
                      "Fase 1" if n <= FECHAS_F1 else f"Zona {ZONAS[S['zona_de'][x]]}",
                      nom[x], nom[y]) for x, y in S["fechas"][n - 1]]


def fechas_conocidas_b():
    return max(SB["fecha"], B_F1 if SB["fechas2"] is None else B_F1 + B_F2)


def partidos_fecha_b(n):
    if n <= SB["fecha"]:
        return [p for p in SB["log"] if p["fecha"] == n]
    nom = SB["nombres"]
    if n <= B_F1:
        return [pendiente("Primera Nacional", n, rotulo_b(n), f"Zona {'AB'[SB['zona_de'][x]]}",
                          nom[x], nom[y]) for x, y in SB["fechas"][n - 1]]
    return [pendiente("Primera Nacional", n, rotulo_b(n),
                      f"Zona {B_ZONAS2[SB['zona2_de'][x]]}", nom[x], nom[y])
            for x, y in SB["fechas2"][n - 1 - B_F1]]


def fechas_conocidas_f():
    return max(SF["fecha"], SF["f1_rondas"] if SF["fechas2"] is None else SF["f1_rondas"] + F_F2_RONDAS)


def partidos_fecha_f(n):
    if n <= SF["fecha"]:
        return [p for p in SF["log"] if p["fecha"] == n]
    nom = SF["nombres"]
    if n <= SF["f1_rondas"]:
        return [pendiente("Federal A", n, rotulo_f(SF, n), f"Zona {F_GRUPOS_NOMBRES[SF['grupo_de'][x]]}",
                          nom[x], nom[y]) for x, y in SF["fechas"][n - 1]]
    return [pendiente("Federal A", n, rotulo_f(SF, n),
                      "Campeonato" if SF["zona2_de"][x] == 0 else "Descenso", nom[x], nom[y])
            for x, y in SF["fechas2"][n - 1 - SF["f1_rondas"]]]


def proximo_partido(nombre):
    if nombre in S["nombres"]:
        for n in range(S["fecha"] + 1, fechas_conocidas_p() + 1):
            for p in partidos_fecha_p(n):
                if nombre in (p["local"], p["visita"]):
                    return p
    elif nombre in SB["nombres"]:
        for n in range(SB["fecha"] + 1, fechas_conocidas_b() + 1):
            for p in partidos_fecha_b(n):
                if nombre in (p["local"], p["visita"]):
                    return p
    elif nombre in SF["nombres"]:
        for n in range(SF["fecha"] + 1, fechas_conocidas_f() + 1):
            for p in partidos_fecha_f(n):
                if nombre in (p["local"], p["visita"]):
                    return p
    return None


# ---- Ficha de un club (con buscador de sus partidos) ------------------------
def render_ficha(nombre, clave):
    partidos = [p for p in todos_los_partidos() if nombre in (p["local"], p["visita"])]
    cat = categoria_de(nombre)
    filas, letras = [], []
    gf_t = gc_t = 0
    for p in partidos:
        local, gf, gc, letra = resultado_para(p, nombre)
        letras.append(letra)
        gf_t, gc_t = gf_t + gf, gc_t + gc
        rival = p["visita"] if local else p["local"]
        res = f"{gf}-{gc}"
        if p["pen"]:
            pf, pc = p["pen"] if local else p["pen"][::-1]
            res += f" ({pf}-{pc} pen.)"
        if letra == "G":
            desenlace = "✅ Ganó"
        elif letra == "P":
            desenlace = "❌ Perdió"
        elif p["pen"]:
            desenlace = ("✅ Empató · ganó por penales" if p["gana"] == nombre
                         else "❌ Empató · perdió por penales")
        else:
            desenlace = "➖ Empató"
        cond = "Neutral" if p["neutral"] else ("Local" if local else "Visitante")
        comp = p["comp"] if p["comp"] == p["liga"] else f"{p['liga']} · {p['comp']}"
        filas.append({
            "Fecha": p["fecha"], "Competición": comp, "Condición": cond,
            " ": ESCUDOS.get(rival), "Rival": rival, "Resultado": res, "Desenlace": desenlace,
            "_t": norm(f"{rival} {nombre} {comp} {cond} {desenlace} {p['rotulo']}"),
            "_m": f" {gf}-{gc} {gc}-{gf} ",
        })

    g, e, pp = letras.count("G"), letras.count("E"), letras.count("P")
    forma = "".join(f'<span class="fm {x}">{x}</span>' for x in letras[-5:])
    st.markdown(
        f'<div class="team-head">{crest(nombre, 64)}<div><div class="tn">{esc(nombre)}</div>'
        f'<div style="margin-top:6px">{chip(cat) if cat else ""} '
        f'<span style="font-size:.8rem;opacity:.65">Temporada {S["temp"]}</span></div></div></div>',
        unsafe_allow_html=True)
    if cat == "Primera B":
        aviso("La Primera B no se simula partido a partido. Si este club asciende a la "
              "Primera Nacional, acá vas a ver todos sus partidos.")
        return
    st.markdown(
        f'<div class="rec"><div><b>{len(partidos)}</b><span>PJ</span></div>'
        f'<div><b>{g}</b><span>G</span></div><div><b>{e}</b><span>E</span></div>'
        f'<div><b>{pp}</b><span>P</span></div><div><b>{gf_t}</b><span>GF</span></div>'
        f'<div><b>{gc_t}</b><span>GC</span></div><div><b>{gf_t - gc_t:+d}</b><span>DG</span></div>'
        f'<div><span>Últimos 5</span><div class="form">{forma or "—"}</div></div></div>',
        unsafe_allow_html=True)
    prox = proximo_partido(nombre)
    if prox:
        rival = prox["visita"] if prox["local"] == nombre else prox["local"]
        cond = "Local" if prox["local"] == nombre else "Visitante"
        st.markdown(f'<div class="next"><b>Próximo partido</b> · {esc(prox["rotulo"])} · '
                    f'{chip(prox["comp"])} {cond} vs {crest(rival, 20)} <b>{esc(rival)}</b></div>',
                    unsafe_allow_html=True)
    if not filas:
        st.info("Este club todavía no jugó partidos esta temporada.")
        return

    q = st.text_input("🔍 Buscar partido", key=f"q_{clave}_{nombre}",
                      placeholder="Rival, número de fecha, resultado (2-1), local, visitante, "
                                  "zona, octavos…")
    vis = [f for f in filas if coincide(q, f["_t"], f["Fecha"], f["_m"])] if q else filas
    if not vis:
        st.warning("No hay partidos que coincidan con la búsqueda.")
        return
    if q:
        st.caption(f"{len(vis)} de {len(filas)} partidos")
    df = pd.DataFrame(vis).drop(columns=["_t", "_m"])

    def color_res(fila):
        d = fila["Desenlace"]
        c = ("rgba(22,163,74,.16)" if d.startswith("✅") else
             "rgba(220,38,38,.14)" if d.startswith("❌") else "rgba(100,116,139,.12)")
        return [f"background-color: {c}" if col in ("Resultado", "Desenlace") else ""
                for col in fila.index]

    st.dataframe(df.style.apply(color_res, axis=1), hide_index=True, width="stretch",
                 height=min(35 * (len(df) + 1) + 3, 460),
                 column_config={"Fecha": st.column_config.NumberColumn("Fecha", width="small"),
                                " ": st.column_config.ImageColumn(" ", width="small")})
    penales = [p for p in partidos if p["pen"]]
    if penales:
        st.markdown('<div class="mlab">Definiciones por penales</div>'
                    + "".join(fila_partido_html(p) for p in penales), unsafe_allow_html=True)


@st.dialog("Ficha del club", width="large")
def ver_equipo(nombre):
    render_ficha(nombre, "dlg")


# ---- Fixture y resultados ---------------------------------------------------
def render_fecha(partidos, clave):
    """Partidos de una fecha en dos columnas; cada club se puede tocar para ver su ficha."""
    grupos = []
    for p in partidos:
        if not grupos or grupos[-1][0] != p["comp"]:
            grupos.append((p["comp"], []))
        grupos[-1][1].append(p)
    for g, (comp, lista) in enumerate(grupos):
        if len(grupos) > 1 or comp not in ("Fase 1",):
            st.markdown(chip(comp) + (' <span style="opacity:.6;font-size:.75rem">cancha neutral'
                                      '</span>' if lista[0]["neutral"] else ""),
                        unsafe_allow_html=True)
        mitad = (len(lista) + 1) // 2
        cols = st.columns(2, gap="medium") if len(lista) > 1 else [st.container()]
        for lado, (c, sub) in enumerate(zip(cols, (lista[:mitad], lista[mitad:]))):
            with c, st.container(key=f"fx_{clave}_{g}_{lado}"):
                for i, p in enumerate(sub):
                    k = f"{clave}_{g}_{p['local']}_{p['visita']}"
                    c1, c2, c3 = st.columns([5, 3.6, 5], vertical_alignment="center", gap="small")
                    if c1.button(p["local"], key=f"{k}_l", help="Ver la ficha del club",
                                 width="stretch"):
                        ver_equipo(p["local"])
                    c2.markdown(marcador_html(p, crests=True), unsafe_allow_html=True)
                    if c3.button(p["visita"], key=f"{k}_v", help="Ver la ficha del club",
                                 width="stretch"):
                        ver_equipo(p["visita"])
                    if p["tanda"]:
                        st.markdown(tanda_html(p), unsafe_allow_html=True)


def _mover_fecha(key, delta, maximo):
    st.session_state[key] = min(max(1, st.session_state.get(key, 1) + delta), maximo)


def vista_fixture(liga):
    if liga == "p":
        total, jugadas, obtener, rotulo = fechas_conocidas_p(), S["fecha"], partidos_fecha_p, rotulo_p
        extra = "" if S["fase"] == 2 else " · las 9 fechas de la fase 2 se arman al terminar la fase 1"
    elif liga == "b":
        total, jugadas, obtener, rotulo = fechas_conocidas_b(), SB["fecha"], partidos_fecha_b, rotulo_b
        extra = ("" if SB["fechas2"] is not None else
                 " · la fase 2 se arma al terminar la fase 1")
    else:
        total, jugadas = fechas_conocidas_f(), SF["fecha"]
        obtener, rotulo = partidos_fecha_f, lambda n: rotulo_f(SF, n)
        extra = ("" if SF["zonas2"] is not None else
                 " · la fase 2 se arma al terminar la fase 1")
    seccion("Fixture y resultados", "Tocá un club para ver su ficha" + extra, "#1e5aa8")
    if total == 0:
        st.info("Todavía no hay fechas programadas.")
        return
    key = f"fx_sel_{liga}_{S['temp']}_{jugadas}"
    if key not in st.session_state:
        st.session_state[key] = max(1, min(jugadas, total))
    c1, c2, c3 = st.columns([1, 6, 1], vertical_alignment="bottom")
    c1.button("◀", key=f"{key}_prev", width="stretch", on_click=_mover_fecha,
              args=(key, -1, total), disabled=st.session_state[key] <= 1)
    elegida = c2.selectbox("Fecha", list(range(1, total + 1)), key=key, format_func=lambda n:
                           rotulo(n) + (" · ✔ jugada" if n <= jugadas else " · por jugar"),
                           label_visibility="collapsed")
    c3.button("▶", key=f"{key}_next", width="stretch", on_click=_mover_fecha,
              args=(key, 1, total), disabled=elegida >= total)
    estado = chip("Jugada", "#16a34a") if elegida <= jugadas else (
        chip("Próxima fecha", "#2f7fd0") if elegida == jugadas + 1 else chip("Por jugar", "#64748b"))
    st.markdown(f'<div class="fx-head"><b style="font-size:1.05rem">{esc(rotulo(elegida))}</b>'
                f'{estado}</div>', unsafe_allow_html=True)
    render_fecha(obtener(elegida), f"{liga}{S['temp']}_{elegida}")


# ---- Tablas -----------------------------------------------------------------
def ultimos_movs(hist):
    if len(hist) < 2 or hist[-1][0] != hist[-2][0]:
        return None
    return hist[-2][1] - hist[-1][1], hist[-1][1]


def color_mov(v):
    if str(v).startswith("▲"):
        return "color: #16a34a; font-weight: 700"
    if str(v).startswith("▼"):
        return "color: #dc2626; font-weight: 700"
    return "color: #94a3b8"


def mostrar_tabla(df, fn_color, hist=None):
    df = df.copy()
    mov = ultimos_movs(hist) if hist is not None else None
    if hist is not None:
        if mov:
            d = [int(x) for x in mov[0][df["id"].to_numpy()]]
            df.insert(1, "±", [f"▲{x}" if x > 0 else f"▼{-x}" if x < 0 else "=" for x in d])
        else:
            df.insert(1, "±", ["–"] * len(df))
    df.insert(2 if "±" in df.columns else 1, "Escudo", [ESCUDOS.get(n) for n in df["Equipo"]])
    df = df.drop(columns="id")
    orden = [c for c in ["Pos", "±", "Escudo", "Equipo", "Pts", "PJ", "G", "E", "P", "GF", "GC",
                         "DG", "Destino", "Media"] if c in df.columns]
    df = df[orden]
    sty = df.style.apply(fn_color, axis=1)
    if "±" in df.columns:
        sty = sty.map(color_mov, subset=["±"])
    sty = sty.set_properties(subset=["Pts"], **{"font-weight": "700"})
    st.dataframe(sty, hide_index=True, width="stretch", height=35 * (len(df) + 1) + 3,
                 column_config={
                     "Pos": st.column_config.NumberColumn("#", width=38),
                     "±": st.column_config.TextColumn("±", width=46,
                                                      help="Puestos ganados o perdidos en la última fecha"),
                     "Escudo": st.column_config.ImageColumn("", width=40),
                     "Equipo": st.column_config.TextColumn("Club", width="medium"),
                     "Pts": st.column_config.NumberColumn("Pts", width=52),
                     "Media": st.column_config.NumberColumn("Media", format="%.1f", width=62,
                                                            help="Fuerza interna del equipo"),
                 })


def colorear_fase1(fila):
    """Pinta según la zona a la que pasa (o pasaría) cada equipo de Primera."""
    c = COLORES_ZONA[(fila["Pos"] - 1) // ZONA_TAM]
    return [f"background-color: {c}"] * len(fila)


def colorear_destino(fila):
    """Pinta según el destino (copas / promoción / descenso); dorado para el líder."""
    pos = fila["Pos"]
    c = COLOR_ORO if pos == 1 else COLORES_DESTINO.get(destino(pos), "")
    return [f"background-color: {c}" if c else ""] * len(fila)


def colorear_b(fila):
    c = COLORES_B.get(fila["Destino"], "")
    return [f"background-color: {c}" if c else ""] * len(fila)


def colorear_f(fila):
    c = COLORES_F.get(fila["Destino"], "")
    return [f"background-color: {c}" if c else ""] * len(fila)


LEY_ZONAS = [("Pasa a Zona Campeonato", COLORES_ZONA[0]), ("Zona Intermedia", COLORES_ZONA[1]),
             ("Zona Descenso", COLORES_ZONA[2])]
LEY_DESTINOS = [("Líder", COLOR_ORO), ("Libertadores", COLORES_DESTINO["Libertadores"]),
                ("Fase previa Libertadores", COLORES_DESTINO["Fase previa Libertadores"]),
                ("Sudamericana", COLORES_DESTINO["Sudamericana"]),
                ("Promoción", COLORES_DESTINO["Promoción"]), ("Descenso", COLORES_DESTINO["Desciende"])]
LEY_B = [("Campeón", COLOR_ORO), ("Ascenso directo", COLORES_B["Ascenso directo"]),
         ("Cuartos del reducido", COLORES_B["Cuartos del reducido"]),
         ("Octavos del reducido", COLORES_B["Octavos del reducido"]),
         ("Desciende", COLORES_B["Desciende"])]
LEY_F = [("Campeón", COLOR_ORO), ("Ascenso directo", COLORES_F["Ascenso directo"]),
         ("Juega el reducido", COLORES_F["Reducido"])]


# ---- Movimientos de la temporada -------------------------------------------
def rachas(log, nombres):
    seq = {n: [] for n in nombres}
    for p in log:
        for eq in (p["local"], p["visita"]):
            if eq in seq:
                seq[eq].append(resultado_para(p, eq)[3])

    def cola(lst, ok):
        n = 0
        for x in reversed(lst):
            if x not in ok:
                break
            n += 1
        return n

    invicto = max(nombres, key=lambda n: cola(seq[n], "GE"))
    sin_ganar = max(nombres, key=lambda n: cola(seq[n], "EP"))
    ganando = max(nombres, key=lambda n: cola(seq[n], "G"))
    return ((invicto, cola(seq[invicto], "GE")), (sin_ganar, cola(seq[sin_ganar], "EP")),
            (ganando, cola(seq[ganando], "G")))


def card(k, v, s="", color="#2f7fd0", big=False):
    return (f'<div class="card" style="--c:{color}"><div class="k">{k}</div>'
            f'<div class="v{" big" if big else ""}">{v}</div><div class="s">{s}</div></div>')


def eq_html(n, size=26):
    return f'{crest(n, size)}<span>{esc(n)}</span>'


def partido_corto(p):
    pen = f" ({p['pen'][0]}-{p['pen'][1]} pen.)" if p["pen"] else ""
    return (f'{crest(p["local"], 22)}<span>{esc(p["local"])} <b>{p["gl"]}-{p["gv"]}</b>'
            f'{pen} {esc(p["visita"])}</span>{crest(p["visita"], 22)}')


def render_movimientos(log, hist, nombres, color):
    seccion("Movimientos de la temporada", "Cambios en la tabla, rachas y partidos destacados",
            color)
    log = [p for p in log if p["local"] in nombres or p["visita"] in nombres]
    if not log:
        st.info("Simulá una fecha para ver los movimientos de la temporada.")
        return
    cards = ""
    mov = ultimos_movs(hist)
    if mov:
        d, cur = mov
        iu, idn = int(np.argmax(d)), int(np.argmin(d))
        if d[iu] > 0:
            cards += card("▲ Mayor subida · última fecha", eq_html(nombres[iu]),
                          f"Ganó {d[iu]} puesto{'s' if d[iu] > 1 else ''}: del "
                          f"{cur[iu] + d[iu]}° al {cur[iu]}°", "#16a34a")
        if d[idn] < 0:
            cards += card("▼ Mayor caída · última fecha", eq_html(nombres[idn]),
                          f"Perdió {-d[idn]} puesto{'s' if d[idn] < -1 else ''}: del "
                          f"{cur[idn] + d[idn]}° al {cur[idn]}°", "#dc2626")
    gole = max(log, key=lambda p: (abs(p["gl"] - p["gv"]), p["gl"] + p["gv"]))
    if gole["gl"] != gole["gv"]:
        cards += card("💥 Mayor goleada", partido_corto(gole),
                      f"{gole['rotulo']} · {gole['comp']}", "#ea580c")
    mas = max(log, key=lambda p: (p["gl"] + p["gv"], -abs(p["gl"] - p["gv"])))
    cards += card("⚽ Partido con más goles", partido_corto(mas),
                  f"{mas['gl'] + mas['gv']} goles · {mas['rotulo']}", "#0891b2")
    (inv, n_inv), (sg, n_sg), (gan, n_gan) = rachas(log, nombres)
    if n_gan >= 2:
        cards += card("🔥 Racha ganadora", eq_html(gan), f"{n_gan} victorias seguidas", "#16a34a")
    cards += card("🛡️ Racha invicta", eq_html(inv), f"{n_inv} partidos sin perder", "#2f7fd0")
    cards += card("🧊 Racha sin ganar", eq_html(sg), f"{n_sg} partidos sin ganar", "#64748b")
    goles = sum(p["gl"] + p["gv"] for p in log)
    emp = sum(p["gl"] == p["gv"] for p in log)
    cards += card("📈 Goles por partido", f"{goles / len(log):.2f}",
                  f"{goles} goles en {len(log)} partidos · {100 * emp / len(log):.0f}% empates",
                  "#7c3aed", big=True)
    st.markdown(f'<div class="cards">{cards}</div>', unsafe_allow_html=True)

    if mov:
        d, cur = mov
        orden = np.argsort(-d)
        suben = [i for i in orden if d[i] > 0][:8]
        bajan = [i for i in orden[::-1] if d[i] < 0][:8]

        def lista(ids, cls, signo):
            return "".join(f'<span class="mv">{crest(nombres[i], 20)}{esc(nombres[i])}'
                           f'<span class="d {cls}">{signo}{abs(d[i])}</span>'
                           f'<span style="opacity:.6">{cur[i]}°</span></span>' for i in ids) or "—"

        c1, c2 = st.columns(2)
        c1.markdown('<div class="mlab up">▲ Subieron en la última fecha</div><div class="movlist">'
                    + lista(suben, "up", "+") + "</div>", unsafe_allow_html=True)
        c2.markdown('<div class="mlab down">▼ Bajaron en la última fecha</div><div class="movlist">'
                    + lista(bajan, "down", "−") + "</div>", unsafe_allow_html=True)


# ---- Cuadro del reducido ----------------------------------------------------
def bracket_card(m, final=False):
    if m is None:
        fila = '<div class="bt tbd"><span class="nm">Por definir</span></div>'
        return f'<div class="bm">{fila}{fila}</div>'
    filas = ""
    for i, (nombre, g) in enumerate(((m["local"], m["gl"]), (m["visita"], m["gv"]))):
        cls = "win" if m["gana"] == nombre else "lose"
        pk = f'<span class="p">({m["pen"][i]})</span>' if m["pen"] else ""
        lv = "N" if m["neutral"] else ("L" if i == 0 else "V")
        tit = "Neutral" if lv == "N" else "Local" if lv == "L" else "Visitante"
        filas += (f'<div class="bt {cls}">{crest(nombre, 24)}<span class="nm" title="{esc(nombre)}">'
                  f'{esc(nombre)}</span><span class="lv" title="{tit}">{lv}</span>{pk}'
                  f'<span class="g">{g}</span></div>')
    pen = f"Penales {m['pen'][0]}-{m['pen'][1]} · " if m["pen"] else ""
    que = "🏆 Campeón" if final else "Avanza"
    return (f'<div class="bm">{filas}<div class="bfoot">{pen}{que}: <b>{esc(m["gana"])}</b></div>'
            f'{tanda_html(m)}</div>')


def bracket_html(SB):
    rondas = [list(r) for r in SB["bracket"]]
    # Ordena cada ronda según la siguiente para que el cuadro se lea de izquierda a derecha
    for k in range(len(rondas) - 1, 0, -1):
        nuevo = []
        for m in rondas[k]:
            for t in (m["local"], m["visita"]):
                for pm in rondas[k - 1]:
                    if pm["gana"] == t and all(pm is not x for x in nuevo):
                        nuevo.append(pm)
        nuevo += [pm for pm in rondas[k - 1] if all(pm is not x for x in nuevo)]
        rondas[k - 1] = nuevo
    titulos = ["Octavos", "Cuartos", "Semifinal", "Final"]
    tam = [4, 4, 2, 1]
    cols = ""
    for r in range(4):
        ms = rondas[r] if r < len(rondas) else [None] * tam[r]
        cards = "".join(bracket_card(m, final=(r == 3)) for m in ms)
        cols += (f'<div class="round"><div class="round-h">{chip(titulos[r])}</div>'
                 f'<div class="round-b">{cards}</div></div>')
    if len(rondas) == 4:
        c = rondas[3][0]["gana"]
        champ = (f'<div class="champ"><div class="t">Campeón del reducido</div>'
                 f'<div style="margin-top:10px">{crest(c, 56)}</div><div class="nm">{esc(c)}</div>'
                 f'<div class="s">Asciende a Primera División</div></div>')
    else:
        champ = ('<div class="champ" style="opacity:.55"><div class="t">Campeón del reducido</div>'
                 '<div class="nm">Por definir</div><div class="s">Asciende a Primera</div></div>')
    promo = ""
    if SB["promo_partido"]:
        promo = (f'<div class="promo"><div class="round-h">{chip("Promoción")}</div>'
                 f'{bracket_card(SB["promo_partido"])}</div>')
    elif len(rondas) == 4:
        perd = SB["nombres"][SB["perdedor_final"]]
        promo = (f'<div class="promo"><div class="round-h">{chip("Promoción")}</div>'
                 f'<div class="bm"><div class="bt">{crest(perd, 24)}<span class="nm">{esc(perd)}'
                 f'</span></div><div class="bt tbd"><span class="nm">27° de Primera</span></div>'
                 f'</div></div>')
    cols += (f'<div class="round last"><div class="round-h">{chip("Campeón", "#b7860b")}</div>'
             f'<div class="round-b" style="justify-content:center">{champ}{promo}</div></div>')
    return f'<div class="bracket">{cols}</div>'


def bracket_html_f(SF):
    rondas = [list(r) for r in SF["bracket"]]
    for k in range(len(rondas) - 1, 0, -1):
        nuevo = []
        for m in rondas[k]:
            for t in (m["local"], m["visita"]):
                for pm in rondas[k - 1]:
                    if pm["gana"] == t and all(pm is not x for x in nuevo):
                        nuevo.append(pm)
        nuevo += [pm for pm in rondas[k - 1] if all(pm is not x for x in nuevo)]
        rondas[k - 1] = nuevo
    titulos = ["Cuartos", "Semifinal", "Final"]
    tam = [4, 2, 1]
    cols = ""
    for r in range(3):
        ms = rondas[r] if r < len(rondas) else [None] * tam[r]
        cards = "".join(bracket_card(m, final=(r == 2)) for m in ms)
        cols += (f'<div class="round"><div class="round-h">{chip(titulos[r])}</div>'
                 f'<div class="round-b">{cards}</div></div>')
    if len(rondas) == 3:
        c = rondas[2][0]["gana"]
        champ = (f'<div class="champ"><div class="t">Campeón del reducido</div>'
                 f'<div style="margin-top:10px">{crest(c, 56)}</div><div class="nm">{esc(c)}</div>'
                 f'<div class="s">Asciende a la Primera Nacional</div></div>')
    else:
        champ = ('<div class="champ" style="opacity:.55"><div class="t">Campeón del reducido</div>'
                 '<div class="nm">Por definir</div><div class="s">Asciende a la Primera Nacional'
                 '</div></div>')
    cols += (f'<div class="round last"><div class="round-h">{chip("Campeón", "#b7860b")}</div>'
             f'<div class="round-b" style="justify-content:center">{champ}</div></div>')
    return f'<div class="bracket">{cols}</div>'


def barra_estado(items, progreso):
    celdas = "".join(f'<div class="stc"><span>{esc(k)}</span><b>{esc(str(v))}</b></div>'
                     for k, v in items)
    celdas += (f'<div class="stc"><span>Progreso</span><b>{progreso:.0f}%</b>'
               f'<div class="bar"><i style="width:{progreso:.1f}%"></i></div></div>')
    st.markdown(f'<div class="status">{celdas}</div>', unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# INTERFAZ
# ----------------------------------------------------------------------------
st.markdown(CSS, unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Parámetros")
    sorpresa = st.slider("Nivel de sorpresas", 0.0, 15.0, 6.0, 0.5,
                         help="Qué tanto varía la 'forma del día' de cada equipo. "
                              "Más alto = más partidos donde gana el que tiene menos media.")
    volatilidad = st.slider("Volatilidad entre temporadas", 0.0, 10.0, 4.0, 0.5,
                            help="Qué tanto cambia la media de cada equipo al pasar de temporada.")
    acumular = st.checkbox("Arrastrar puntos de la fase 1 a las zonas (Primera)", value=True,
                           help="Solo Primera. Si está activado, las zonas parten con lo sumado en "
                                "las 29 fechas. Si no, cada zona arranca de cero. Se fija al "
                                "terminar la fase 1. En la B Nacional los puntos SIEMPRE se reinician.")
    st.caption("En cada partido, cada equipo rinde un poco mejor o peor que su "
               "media habitual. Los partidos del reducido y la promoción son a un solo "
               "partido y, si empatan, se definen por penales.")

P = dict(sorpresa=sorpresa)

if "S" not in st.session_state or st.session_state.S.get("version") != VERSION_ESTADO:
    st.session_state.S = crear_estado()
S = st.session_state.S
SB = S["b"]
SF = S["f"]

terminada = S["fecha"] >= TOTAL_FECHAS
terminada_b = SB["fecha"] >= B_TOTAL
terminada_f = SF["fecha"] >= SF["total"]
ambas = terminada and terminada_b and terminada_f
b_espera_primera = SB["fecha"] == B_TOTAL - 1 and not terminada     # promoción pendiente

# ---- Historial de campeones (se registra cuando terminan las dos ligas)
if ambas and not S["cerrada_ambas"]:
    S["campeones"].append((S["temp"], tabla_final(S).iloc[0]["Equipo"],
                           SB["nombres"][SB["campeon"]]))
    S["cerrada_ambas"] = True

# ---- Cabecera (sin resultados finales: no spoilea la temporada)
pct_p = 100 * S["fecha"] / TOTAL_FECHAS
pct_b = 100 * SB["fecha"] / B_TOTAL
pct_f = 100 * SF["fecha"] / SF["total"]
st.markdown(
    f'<div class="hero"><span class="sol">☀</span><div class="hero-top"><div>'
    f'<div class="hero-k">Temporada {S["temp"]} · Fútbol argentino</div>'
    f'<h1>Simulador de la Liga Argentina</h1>'
    f'<p>Primera División · Primera Nacional · Federal A · Reducido · Promoción</p></div>'
    f'<div class="hero-stats">'
    f'<div class="hs"><span>Primera División</span><b>Fecha {S["fecha"]}/{TOTAL_FECHAS}</b>'
    f'<div class="bar"><i style="width:{pct_p:.1f}%"></i></div></div>'
    f'<div class="hs"><span>Primera Nacional</span><b>Fecha {SB["fecha"]}/{B_TOTAL}</b>'
    f'<div class="bar"><i style="width:{pct_b:.1f}%"></i></div></div>'
    f'<div class="hs"><span>Federal A</span><b>Fecha {SF["fecha"]}/{SF["total"]}</b>'
    f'<div class="bar"><i style="width:{pct_f:.1f}%"></i></div></div>'
    f'<div class="hs"><span>Partidos jugados</span>'
    f'<b>{len(S["log"]) + len(SB["log"]) + len(SF["log"])}</b></div>'
    f'</div></div></div>', unsafe_allow_html=True)

g0, g1, g2, g3 = st.columns([3, 1.4, 1.4, 1.2], vertical_alignment="center")
g0.caption("Simulá fecha por fecha desde cada categoría, o todo junto con los botones de la derecha.")
if g1.button("⏩ Simular todo", disabled=ambas, width="stretch", type="primary",
             help="Simula lo que falta de las tres categorías."):
    while S["fecha"] < TOTAL_FECHAS:
        simular_fecha(S, P, acumular)
    while SB["fecha"] < B_TOTAL:
        simular_fecha_b(S, P)
    while SF["fecha"] < SF["total"]:
        simular_fecha_f(SF, P, S["rng"])
    st.rerun()
if g2.button("📅 Nueva temporada", disabled=not ambas, width="stretch",
             help="Se habilita cuando terminan la Primera, la Primera Nacional (incluida la "
                  "promoción) y el Federal A. Se aplican ascensos y descensos y cambian las medias."):
    nueva_temporada(S, volatilidad)
    st.rerun()
if g3.button("🔄 Reiniciar", width="stretch", help="Vuelve a la temporada 1."):
    st.session_state.S = crear_estado()
    st.rerun()

tab_p, tab_b, tab_f, tab_c, tab_h = st.tabs(["🏆 Primera División", "🥈 Primera Nacional",
                                             "🌎 Federal A", "🛡️ Clubes", "📜 Historial"])

# ============================================================================
# PRIMERA DIVISIÓN
# ============================================================================
with tab_p:
    c1, c2, c3 = st.columns([3, 1.4, 1.4], vertical_alignment="center")
    c1.markdown(chip("Liga Profesional · 30 equipos", "#1e5aa8") + " " +
                chip("Fase 1 · todos contra todos" if S["fase"] == 1 else "Fase 2 · zonas"),
                unsafe_allow_html=True)
    if c2.button("▶️ Próxima fecha", key="p_next", disabled=terminada, width="stretch",
                 type="primary"):
        simular_fecha(S, P, acumular)
        st.rerun()
    if c3.button("⏩ Hasta el final", key="p_all", disabled=terminada, width="stretch"):
        while S["fecha"] < TOTAL_FECHAS:
            simular_fecha(S, P, acumular)
        st.rerun()

    jugados = int(S["pj"].sum() // 2)
    pct = 100 * S["sorpresas"] / jugados if jugados else 0
    barra_estado([("Fase", "1 · Todos contra todos" if S["fase"] == 1 else "2 · Zonas"),
                  ("Fecha", f"{S['fecha']} / {TOTAL_FECHAS}"),
                  ("Sorpresas", f"{S['sorpresas']} ({pct:.0f}%)")], pct_p)
    if S["fase"] == 2 and S["fecha"] == FECHAS_F1:
        aviso("Terminó la fase 1: se armaron las zonas Campeonato, Intermedia y Descenso. "
              "Las 9 fechas siguientes se juegan dentro de cada zona, con la localía invertida.")

    sp = st.tabs(["📊 Posiciones", "📅 Fixture y resultados", "🔄 Movimientos", "🏁 Definiciones"])
    with sp[0]:
        if S["fase"] == 1:
            seccion("Tabla de posiciones", "Fase 1 · 29 fechas, todos contra todos", "#475569")
            mostrar_tabla(tabla_general(S), colorear_fase1, S["pos_hist"])
            leyenda(LEY_ZONAS)
        else:
            seccion("Fase 2 · Zonas", "9 fechas dentro de cada zona, localía invertida", "#16a34a")
            tabs = st.tabs([f"Zona {n}" for n in ZONAS] + ["Tabla fase 1"])
            for z, tab in enumerate(tabs[:3]):
                with tab:
                    mostrar_tabla(tabla_zona(S, z), colorear_destino, S["pos_hist"])
            with tabs[3]:
                mostrar_tabla(S["tabla_f1"], colorear_fase1)
                st.caption("Tabla final de las 29 fechas de la fase 1.")
            leyenda(LEY_DESTINOS)
        if S["fecha"] == 0:
            with st.expander("✏️ Editar medias internas de esta temporada"):
                ed = st.data_editor(
                    pd.DataFrame({"Equipo": S["nombres"], "Media": S["r"]}),
                    disabled=["Equipo"], hide_index=True, width="stretch",
                    key=f"editor_p_{S['temp']}",
                )
                S["r"] = np.clip(ed["Media"].to_numpy(float), MIN_R, MAX_R)
    with sp[1]:
        vista_fixture("p")
    with sp[2]:
        render_movimientos(S["log"], S["pos_hist"], S["nombres"], "#1e5aa8")
    with sp[3]:
        seccion("Definiciones de la temporada", "Campeón, copas, promoción y descensos", "#b7860b")
        if not terminada:
            aviso("Las definiciones aparecen acá cuando termina la temporada de Primera. "
                  "Destinos: 1°-5° Libertadores · 6°-8° y 12°-13° Sudamericana · 11° fase previa "
                  "de Libertadores · 27° Promoción · 28°-30° descienden.")
        else:
            final = tabla_final(S)

            def equipos(posiciones):
                sel = final[final["Pos"].isin(list(posiciones))]
                return lista_equipos_html([(r.Equipo, f"{r.Pos}°") for r in sel.itertuples()])

            st.caption("Están cerradas para no spoilear: tocá cada una para verla.")
            e1, e2 = st.columns(2)
            with e1:
                with st.expander("🏆 Campeón de Primera División", expanded=False):
                    campeon = final.iloc[0]["Equipo"]
                    st.markdown(f'<div class="champ"><div class="t">Campeón · Temporada {S["temp"]}'
                                f'</div><div style="margin-top:10px">{crest(campeon, 64)}</div>'
                                f'<div class="nm">{esc(campeon)}</div></div>', unsafe_allow_html=True)
                with st.expander("🌎 Clasificados · Copa Libertadores", expanded=False):
                    st.markdown('<div class="mlab">Fase de grupos (1° al 5°)</div>'
                                + equipos(range(1, 6)) + '<div class="mlab">Fase previa (11°)</div>'
                                + equipos([11]), unsafe_allow_html=True)
                with st.expander("🌎 Copa Sudamericana", expanded=False):
                    st.markdown('<div class="mlab">6° al 8° y 12°-13°</div>'
                                + equipos(list(range(6, 9)) + [12, 13]), unsafe_allow_html=True)
            with e2:
                with st.expander("🔁 Promoción", expanded=False):
                    txt = ('<div class="mlab">Juega la Promoción contra el perdedor de la final '
                           'del reducido (27°)</div>' + equipos([N - 3]))
                    if SB["promo_partido"]:
                        txt += fila_partido_html(SB["promo_partido"])
                    st.markdown(txt, unsafe_allow_html=True)
                with st.expander("⬇️ Descensos", expanded=False):
                    st.markdown('<div class="mlab">Descienden a la Primera Nacional (28° al 30°)</div>'
                                + equipos(range(N - 2, N + 1)), unsafe_allow_html=True)

# ============================================================================
# PRIMERA NACIONAL
# ============================================================================
with tab_b:
    fb = SB["fecha"]
    nom_b = SB["nombres"]
    if fb < B_F1:
        fase_txt = "1 · Zonas A y B"
    elif fb < B_F1 + B_F2:
        fase_txt = "2 · Tres zonas"
    elif fb < B_F1 + B_F2 + B_RED:
        fase_txt = "Reducido"
    elif fb < B_TOTAL:
        fase_txt = "Promoción"
    else:
        fase_txt = "Terminada"

    c1, c2, c3 = st.columns([3, 1.4, 1.4], vertical_alignment="center")
    c1.markdown(chip("Primera Nacional · 36 equipos") + " " + chip(f"Fase {fase_txt}", "#475569"),
                unsafe_allow_html=True)
    if c2.button("▶️ Próxima fecha", key="b_next", width="stretch", type="primary",
                 disabled=terminada_b or b_espera_primera):
        simular_fecha_b(S, P)
        st.rerun()
    if c3.button("⏩ Hasta el final", key="b_all", width="stretch",
                 disabled=terminada_b or b_espera_primera):
        while SB["fecha"] < B_TOTAL and not (SB["fecha"] == B_TOTAL - 1 and S["fecha"] < TOTAL_FECHAS):
            simular_fecha_b(S, P)
        st.rerun()

    barra_estado([("Fase", fase_txt), ("Fecha", f"{fb} / {B_TOTAL}"),
                  ("Partidos jugados", len(SB["log"]))], pct_b)
    if b_espera_primera:
        aviso("⏳ La Promoción se juega contra el 27° de Primera: terminá primero la temporada "
              "de Primera División.")
    if fb == B_F1:
        aviso("Terminó la fase 1: se repartieron los equipos en las zonas Campeonato, "
              "Intermedia y Descenso y <b>todos los puntos se reiniciaron a 0</b>.")
    if fb == B_F1 + B_F2:
        aviso("Terminó la fase 2: quedaron definidos los 12 clasificados al reducido. "
              "Mirá el cuadro en la pestaña <b>Reducido</b>.")

    sb = st.tabs(["📊 Posiciones", "📅 Fixture y resultados", "🏟️ Reducido", "🔄 Movimientos",
                  "🏁 Definiciones"])
    with sb[0]:
        if fb < B_F1:
            seccion("Fase 1 · Zonas A y B", "Una rueda + 8 fechas interzonales · 18 equipos por zona", "#4f46e5")
            tabs_b = st.tabs(["Zona A", "Zona B"])
            for z, tab in enumerate(tabs_b):
                with tab:
                    mostrar_tabla(tabla_b_f1(SB, z), colorear_b, SB["pos_hist"])
            leyenda([("1°-5° → Zona Campeonato", COLORES_ZONA[0]),
                     ("6°-10° → Zona Intermedia", COLORES_ZONA[1]),
                     ("11°-16° → Zona Descenso", COLORES_ZONA[2])])
        else:
            seccion("Fase 2 · Zonas", "Puntos reiniciados a 0 · una rueda por zona", "#16a34a")
            tabs_b = st.tabs([f"Zona {n}" for n in B_ZONAS2] + ["Fase 1"])
            for z in range(3):
                with tabs_b[z]:
                    mostrar_tabla(tabla_b_f2(SB, z), colorear_b, SB["pos_hist"])
            with tabs_b[3]:
                for z, nz in enumerate(["Zona A", "Zona B"]):
                    st.markdown(chip(nz), unsafe_allow_html=True)
                    mostrar_tabla(SB["tablas_f1"][z], colorear_b)
                st.caption("Posiciones finales de la fase 1 (sus puntos ya no cuentan).")
            leyenda(LEY_B)
        with st.expander("ℹ️ Formato de la Primera Nacional"):
            st.markdown(
                "Fase 1: dos zonas de 16, una rueda, más 8 fechas interzonales (localía fija "
                "4 y 4) cruzando ambas zonas. "
                "Después los puntos vuelven a 0 y se arman "
                "Campeonato, Intermedia y Descenso (12 cada una), una rueda cada una "
                "(si dos equipos ya se cruzaron en la fase 1, la revancha es con la localía "
                "invertida). Campeonato: 1° campeón y ascenso, 2° ascenso, 3°-4° a cuartos, "
                "5°-12° a octavos. Intermedia: 1°-4° a octavos. Descenso: bajan los 6 últimos. "
                "Reducido a partido único con penales directos; el campeón asciende y el perdedor "
                "de la final juega la promoción contra el 27° de Primera.")
        if fb == 0:
            with st.expander("✏️ Editar medias internas de esta temporada (Primera Nacional)"):
                edb = st.data_editor(
                    pd.DataFrame({"Equipo": SB["nombres"], "Media": SB["r"]}),
                    disabled=["Equipo"], hide_index=True, width="stretch",
                    key=f"editor_b_{S['temp']}",
                )
                SB["r"] = np.clip(edb["Media"].to_numpy(float), MIN_R, MAX_R)
    with sb[1]:
        vista_fixture("b")
    with sb[2]:
        seccion("Reducido por el tercer ascenso",
                "Octavos → Cuartos → Semifinal → Final · partido único, penales si empatan · "
                "L = local, V = visitante, N = neutral", "#2563eb")
        if fb < B_F1 + B_F2:
            aviso("El cuadro se completa al terminar la fase 2. Entran 3°-4° de Zona Campeonato "
                  "(directo a cuartos), 5°-12° de Campeonato y 1°-4° de Intermedia (octavos).")
        st.markdown(bracket_html(SB), unsafe_allow_html=True)
        if SB["entrantes"] is not None:
            with st.expander("Clasificados al reducido (orden de mérito)"):
                ent = SB["entrantes"].copy()
                ent.insert(1, " ", [ESCUDOS.get(n) for n in ent["Equipo"]])
                st.dataframe(ent, hide_index=True, width="stretch",
                             column_config={" ": st.column_config.ImageColumn(" ", width=40)})
    with sb[3]:
        render_movimientos(SB["log"], SB["pos_hist"], nom_b, "#0f766e")
    with sb[4]:
        seccion("Definiciones de la temporada", "Campeón, ascensos, promoción y descensos",
                "#b7860b")
        if SB["campeon"] is None:
            aviso("Las definiciones aparecen acá cuando termina la fase 2 de la Primera Nacional.")
        else:
            st.caption("Están cerradas para no spoilear: tocá cada una para verla.")
            e1, e2 = st.columns(2)
            with e1:
                with st.expander("🏆 Campeón de la Primera Nacional", expanded=False):
                    cb = nom_b[SB["campeon"]]
                    st.markdown(f'<div class="champ"><div class="t">Campeón · Temporada {S["temp"]}'
                                f'</div><div style="margin-top:10px">{crest(cb, 64)}</div>'
                                f'<div class="nm">{esc(cb)}</div><div class="s">Asciende a Primera'
                                f'</div></div>', unsafe_allow_html=True)
                with st.expander("⬆️ Clasificados · Ascensos", expanded=False):
                    asc = [(nom_b[SB["asc_directo"][0]], "campeón"), (nom_b[SB["asc_directo"][1]], "2°")]
                    if SB["asc_reducido"] is not None:
                        asc.append((nom_b[SB["asc_reducido"]], "reducido"))
                    if SB["promo"] and SB["promo"]["gana_b"]:
                        asc.append((nom_b[SB["promo"]["b_id"]], "promoción"))
                    st.markdown(lista_equipos_html(asc) + (
                        '' if SB["asc_reducido"] is not None else
                        '<div style="font-size:.8rem;opacity:.65">El tercer ascenso sale del '
                        'reducido.</div>'), unsafe_allow_html=True)
            with e2:
                with st.expander("🔁 Promoción", expanded=False):
                    if SB["promo_partido"]:
                        st.markdown(fila_partido_html(SB["promo_partido"], abierto=True),
                                    unsafe_allow_html=True)
                    elif SB["perdedor_final"] is not None:
                        st.markdown('<div class="mlab">Juega la promoción (perdedor de la final)</div>'
                                    + lista_equipos_html([(nom_b[SB["perdedor_final"]], "")]),
                                    unsafe_allow_html=True)
                    else:
                        st.caption("La juega el perdedor de la final del reducido contra el 27° "
                                   "de Primera.")
                with st.expander("⬇️ Descensos", expanded=False):
                    st.markdown(
                        '<div class="mlab">Descienden (7° al 12° de Zona Descenso): al Federal '
                        'A los del interior, a la Primera B los metropolitanos</div>'
                        + lista_equipos_html([
                            (nom_b[i], "Federal A" if origen(nom_b[i]) == "Interior" else "Primera B")
                            for i in SB["desc_b"]
                        ]), unsafe_allow_html=True)

# ============================================================================
# FEDERAL A
# ============================================================================
with tab_f:
    ff = SF["fecha"]
    nom_f = SF["nombres"]
    if ff < SF["f1_rondas"]:
        fase_txt_f = "1 · Grupos por cercanía"
    elif ff < SF["f1_rondas"] + F_F2_RONDAS:
        fase_txt_f = "2 · Campeonato y Descenso"
    elif ff < SF["total"]:
        fase_txt_f = "Reducido"
    else:
        fase_txt_f = "Terminada"

    c1, c2, c3 = st.columns([3, 1.4, 1.4], vertical_alignment="center")
    c1.markdown(chip(f"Federal A · {len(nom_f)} equipos") + " " +
                chip(f"Fase {fase_txt_f}", "#475569"), unsafe_allow_html=True)
    if c2.button("▶️ Próxima fecha", key="f_next", width="stretch", type="primary",
                 disabled=terminada_f):
        simular_fecha_f(SF, P, S["rng"])
        st.rerun()
    if c3.button("⏩ Hasta el final", key="f_all", width="stretch", disabled=terminada_f):
        while SF["fecha"] < SF["total"]:
            simular_fecha_f(SF, P, S["rng"])
        st.rerun()

    barra_estado([("Fase", fase_txt_f), ("Fecha", f"{ff} / {SF['total']}"),
                  ("Partidos jugados", len(SF["log"]))], pct_f)
    if ff == SF["f1_rondas"]:
        aviso("Terminó la fase 1: clasificaron los 5 primeros de cada grupo (20 equipos), "
              "repartidos en Zona Campeonato y Zona Descenso, y <b>todos los puntos se "
              "reiniciaron a 0</b>.")
    if ff == SF["f1_rondas"] + F_F2_RONDAS:
        aviso("Terminó la fase 2: 1° y 2° de Zona Campeonato ascendieron directo y quedó "
              "armado el reducido con el 3° al 10°. Mirá el cuadro en la pestaña "
              "<b>Reducido</b>.")

    sf_tabs = st.tabs(["📊 Posiciones", "📅 Fixture y resultados", "🏟️ Reducido", "🔄 Movimientos",
                       "🏁 Definiciones"])
    with sf_tabs[0]:
        if ff < SF["f1_rondas"]:
            seccion("Fase 1 · Grupos por cercanía", "Ida y vuelta · pasan los 5 primeros de "
                    "cada grupo", "#4f46e5")
            tabs_f = st.tabs(F_GRUPOS_NOMBRES)
            for g, tab in enumerate(tabs_f):
                with tab:
                    mostrar_tabla(tabla_f_grupo(SF, g), colorear_f, SF["pos_hist"])
            leyenda([("1°-5° → Fase 2", COLORES_F["→ Fase 2"])])
        else:
            seccion("Fase 2 · Zonas", "Puntos reiniciados a 0 · una rueda por zona", "#16a34a")
            tabs_f = st.tabs(["Campeonato", "Descenso", "Fase 1"])
            with tabs_f[0]:
                mostrar_tabla(tabla_f_f2(SF, 0), colorear_f, SF["pos_hist"])
            with tabs_f[1]:
                mostrar_tabla(tabla_f_f2(SF, 1), colorear_f, SF["pos_hist"])
            with tabs_f[2]:
                for g, dfg in zip(F_GRUPOS_NOMBRES, SF["tablas_f1"]):
                    st.markdown(chip(g), unsafe_allow_html=True)
                    mostrar_tabla(dfg, colorear_f)
                st.caption("Posiciones finales de la fase 1 (sus puntos ya no cuentan).")
            leyenda(LEY_F)
        with st.expander("ℹ️ Formato del Federal A"):
            st.markdown(
                "Fase 1: 4 grupos armados por cercanía geográfica, todos contra todos ida y "
                "vuelta. Pasan a la fase 2 los 5 primeros de cada grupo (20 equipos en total), "
                "que se reparten en Zona Campeonato y Zona Descenso (10 y 10) y arrancan con "
                "todos los puntos en 0; ahí juegan una rueda cada una. En Campeonato, 1° y 2° "
                "ascienden directo a la Primera Nacional; del 3° al 10° se juega un reducido a "
                "partido único en la cancha del mejor ubicado, que también es quien gana si el "
                "partido termina empatado. La final es en cancha neutral y ahí sí, si hay "
                "empate, se define por penales. El campeón del reducido también asciende.")
        if ff == 0:
            with st.expander("✏️ Editar medias internas de esta temporada (Federal A)"):
                edf = st.data_editor(
                    pd.DataFrame({"Equipo": nom_f, "Media": SF["r"]}),
                    disabled=["Equipo"], hide_index=True, width="stretch",
                    key=f"editor_f_{S['temp']}",
                )
                SF["r"] = np.clip(edf["Media"].to_numpy(float), MIN_R, MAX_R)
    with sf_tabs[1]:
        vista_fixture("f")
    with sf_tabs[2]:
        seccion("Reducido por el tercer ascenso",
                "Cuartos → Semifinal → Final · partido único · gana el mejor ubicado si "
                "empatan, menos en la final (cancha neutral, penales) · L = local, V = "
                "visitante, N = neutral", "#2563eb")
        if ff < SF["f1_rondas"] + F_F2_RONDAS:
            aviso("El cuadro se completa al terminar la fase 2. Entran el 3° al 10° de Zona "
                  "Campeonato.")
        st.markdown(bracket_html_f(SF), unsafe_allow_html=True)
        if SF["entrantes"] is not None:
            with st.expander("Clasificados al reducido (orden de mérito)"):
                ent = SF["entrantes"].copy()
                ent.insert(1, " ", [ESCUDOS.get(n) for n in ent["Equipo"]])
                st.dataframe(ent, hide_index=True, width="stretch",
                             column_config={" ": st.column_config.ImageColumn(" ", width=40)})
    with sf_tabs[3]:
        render_movimientos(SF["log"], SF["pos_hist"], nom_f, "#0f766e")
    with sf_tabs[4]:
        seccion("Definiciones de la temporada", "Campeón y ascensos a la Primera Nacional",
                "#b7860b")
        if SF["campeon"] is None:
            aviso("Las definiciones aparecen acá cuando termina la fase 2 del Federal A.")
        else:
            st.caption("Están cerradas para no spoilear: tocá cada una para verla.")
            with st.expander("🏆 Campeón del Federal A", expanded=False):
                cf = nom_f[SF["campeon"]]
                st.markdown(f'<div class="champ"><div class="t">Campeón · Temporada {S["temp"]}'
                            f'</div><div style="margin-top:10px">{crest(cf, 64)}</div>'
                            f'<div class="nm">{esc(cf)}</div><div class="s">Asciende a la Primera'
                            f' Nacional</div></div>', unsafe_allow_html=True)
            with st.expander("⬆️ Clasificados · Ascensos", expanded=False):
                asc_f = [(nom_f[SF["asc_directo"][0]], "campeón"), (nom_f[SF["asc_directo"][1]], "2°")]
                if SF["asc_reducido"] is not None:
                    asc_f.append((nom_f[SF["asc_reducido"]], "reducido"))
                st.markdown(lista_equipos_html(asc_f) + (
                    '' if SF["asc_reducido"] is not None else
                    '<div style="font-size:.8rem;opacity:.65">El tercer ascenso sale del '
                    'reducido.</div>'), unsafe_allow_html=True)

    seccion("Clubes", "Elegí un club para ver su ficha y buscar sus partidos", "#1e5aa8")
    cat = st.segmented_control("Categoría",
                               ["Primera División", "Primera Nacional", "Federal A", "Primera B"],
                               default="Primera División", key="cat_clubes")
    cat = cat or "Primera División"
    lista = sorted({"Primera División": S["nombres"], "Primera Nacional": SB["nombres"],
                    "Federal A": S["federal"], "Primera B": S["primera_b"]}[cat], key=norm)
    elegido = st.selectbox("Club", lista, index=None, placeholder="Elegí un club…",
                           key=f"club_sel_{cat}")
    if elegido:
        with st.container(border=True):
            render_ficha(elegido, "clubes")
    st.markdown('<div class="mlab" style="margin-top:14px">'
                f'{esc(cat)} · {len(lista)} clubes</div><div class="cgrid">'
                + "".join(f'<div class="ct">{crest(n, 52)}<span>{esc(n)}</span></div>' for n in lista)
                + "</div>", unsafe_allow_html=True)

# ============================================================================
# HISTORIAL
# ============================================================================
with tab_h:
    seccion("Historial", "Campeones de cada temporada y cambios de categoría", "#b7860b")
    if S["movimientos"]:
        mv = S["movimientos"]
        with st.expander(f"📋 Cambios de categoría para la temporada {S['temp']}", expanded=False):
            st.markdown(
                '<div class="catgrid">'
                f'<div><div class="mlab up">⬆️ Ascendieron a Primera</div>'
                f'{lista_equipos_html([(n, "directo") for n in mv["directos"]] + [(mv["reducido"], "reducido")])}</div>'
                f'<div><div class="mlab down">⬇️ Descendieron a la Primera Nacional</div>'
                f'{lista_equipos_html([(n, "") for n in mv["bajan_p"]])}</div>'
                f'<div><div class="mlab down">⬇️ Descendieron al Federal A</div>'
                f'{lista_equipos_html([(n, "") for n in mv["bajan_b_fed"]])}</div>'
                f'<div><div class="mlab down">⬇️ Descendieron a la Primera B</div>'
                f'{lista_equipos_html([(n, "") for n in mv["bajan_b_pb"]])}</div>'
                f'<div><div class="mlab up">⬆️ Ingresaron desde el Federal A</div>'
                f'{lista_equipos_html([(n, "") for n in mv["entran_fed"]])}</div>'
                f'<div><div class="mlab up">⬆️ Ingresaron desde la Primera B</div>'
                f'{lista_equipos_html([(n, "") for n in mv["entran_pb"]])}</div>'
                f'</div><div style="margin-top:6px;font-size:.88rem">🔁 {esc(mv["promo_texto"])}</div>',
                unsafe_allow_html=True)
    if S["campeones"]:
        with st.expander("🏆 Campeones por temporada", expanded=False):
            df_c = pd.DataFrame(S["campeones"],
                                columns=["Temporada", "Primera División", "Primera Nacional"])
            df_c.insert(1, "Escudo P", [ESCUDOS.get(n) for n in df_c["Primera División"]])
            df_c.insert(3, "Escudo B", [ESCUDOS.get(n) for n in df_c["Primera Nacional"]])
            st.dataframe(df_c, hide_index=True, width="stretch", column_config={
                "Escudo P": st.column_config.ImageColumn(" ", width=40),
                "Escudo B": st.column_config.ImageColumn(" ", width=40)})
    if not S["movimientos"] and not S["campeones"]:
        st.info("Cuando termine la primera temporada vas a ver acá los campeones y los "
                "cambios de categoría.")
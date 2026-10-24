"""Ciudad, provincia y liga local de los clubes del interior que juegan en Primera, Primera Nacional
y Federal A (los del Regional Amateur ya traen estos datos en datos/datos_regional.py).

Formato: nombre del club -> (ciudad, provincia, liga). Los nombres de las ligas siguen el mismo criterio
que el JSON del Regional ("Liga Cordobesa", "Liga de Pergamino"...), así que si un club desciende hasta
el Regional se queda en su misma liga. Los marcados con "# ?" son los que conviene revisar.
"""

DATOS_INTERIOR = {
    # ---- Primera ----
    "Talleres": ("Córdoba", "Córdoba", "Liga Cordobesa"),
    "Belgrano": ("Córdoba", "Córdoba", "Liga Cordobesa"),
    "Instituto": ("Córdoba", "Córdoba", "Liga Cordobesa"),
    "Independiente Rivadavia": ("Mendoza", "Mendoza", "Liga Mendocina"),
    "Gimnasia (Mendoza)": ("Mendoza", "Mendoza", "Liga Mendocina"),
    "Central Córdoba (SdE)": ("Santiago del Estero", "Santiago del Estero", "Liga Santiagueña"),
    "Atlético Tucumán": ("San Miguel de Tucumán", "Tucumán", "Liga Tucumana"),
    "Estudiantes (Río Cuarto)": ("Río Cuarto", "Córdoba", "Liga de Río Cuarto"),
    "Aldosivi": ("Mar del Plata", "Buenos Aires", "Liga Marplatense"),
    # ---- Primera Nacional ----
    "Godoy Cruz": ("Godoy Cruz", "Mendoza", "Liga Mendocina"),
    "Deportivo Maipú": ("Maipú", "Mendoza", "Liga Mendocina"),
    "San Martín (San Juan)": ("San Juan", "San Juan", "Liga Sanjuanina"),
    "San Martín (Tucumán)": ("San Miguel de Tucumán", "Tucumán", "Liga Tucumana"),
    "Racing (Córdoba)": ("Córdoba", "Córdoba", "Liga Cordobesa"),
    "Patronato": ("Paraná", "Entre Ríos", "Liga Paranaense"),
    "Atlético de Rafaela": ("Rafaela", "Santa Fe", "Liga Rafaelina"),
    "Gimnasia (Jujuy)": ("San Salvador de Jujuy", "Jujuy", "Liga Jujeña"),
    "Güemes": ("Santiago del Estero", "Santiago del Estero", "Liga Santiagueña"),
    "Mitre (SdE)": ("Santiago del Estero", "Santiago del Estero", "Liga Santiagueña"),
    "Central Norte": ("Salta", "Salta", "Liga Salteña"),
    "Gimnasia y Tiro": ("Salta", "Salta", "Liga Salteña"),
    "Chaco For Ever": ("Resistencia", "Chaco", "Liga Chaqueña"),
    "Deportivo Madryn": ("Puerto Madryn", "Chubut", "Liga del Valle (Trelew)"),
    "Agropecuario": ("Carlos Casares", "Buenos Aires", "Liga de Carlos Casares"),
    "Ciudad de Bolívar": ("San Carlos de Bolívar", "Buenos Aires", "Liga de Bolívar"),
    # ---- Federal A ----
    "9 de Julio (Rafaela)": ("Rafaela", "Santa Fe", "Liga Rafaelina"),
    "Sportivo Las Parejas": ("Las Parejas", "Santa Fe", "Liga Cañadense"),                      # ?
    "Gimnasia (CdU)": ("Concepción del Uruguay", "Entre Ríos", "Liga de Concepción del Uruguay"),
    "Atlético Escobar": ("Escobar", "Buenos Aires", "Liga de Escobar"),
    "Defensores de Belgrano (VR)": ("Villa Ramallo", "Buenos Aires", "Liga Nicoleña"),          # ?
    "Douglas Haig": ("Pergamino", "Buenos Aires", "Liga de Pergamino"),
    "El Linqueño": ("Lincoln", "Buenos Aires", "Liga Deportiva del Oeste (Junín)"),
    "Gimnasia (Chivilcoy)": ("Chivilcoy", "Buenos Aires", "Liga de Chivilcoy"),                 # ?
    "Independiente (Chivilcoy)": ("Chivilcoy", "Buenos Aires", "Liga de Chivilcoy"),            # ?
    "Sportivo Belgrano": ("San Francisco", "Córdoba", "Liga de San Francisco"),
    "Argentino (Monte Maíz)": ("Monte Maíz", "Córdoba", "Liga de Bell Ville"),
    "Atenas (Río Cuarto)": ("Río Cuarto", "Córdoba", "Liga de Río Cuarto"),
    "Bartolomé Mitre (Posadas)": ("Posadas", "Misiones", "Liga Posadeña"),
    "Boca Unidos": ("Corrientes", "Corrientes", "Liga Correntina"),
    "Defensores de Vilelas": ("Vilelas", "Chaco", "Liga Chaqueña"),
    "Sarmiento (Resistencia)": ("Resistencia", "Chaco", "Liga Chaqueña"),
    "San Martín (Formosa)": ("Formosa", "Formosa", "Liga Formoseña"),
    "Sol de América (Formosa)": ("Formosa", "Formosa", "Liga Formoseña"),
    "Juventud Antoniana": ("Salta", "Salta", "Liga Salteña"),
    "Sarmiento (La Banda)": ("La Banda", "Santiago del Estero", "Liga Santiagueña"),
    "Tucumán Central": ("San Miguel de Tucumán", "Tucumán", "Liga Tucumana"),
    "San Martín (Mendoza)": ("Mendoza", "Mendoza", "Liga Mendocina"),
    "Huracán Las Heras": ("Las Heras", "Mendoza", "Liga Mendocina"),
    "FADEP": ("Mendoza", "Mendoza", "Liga Mendocina"),                                          # ?
    "Juventud Unida Universitario": ("San Luis", "San Luis", "Liga Sanluiseña"),
    "Cipolletti": ("Cipolletti", "Río Negro", "Liga del Alto Valle (Cipolletti)"),
    "Sol de Mayo": ("Viedma", "Río Negro", "Liga de Viedma"),
    "Costa Brava": ("General Conesa", "Río Negro", "Liga de Viedma"),                           # ?
    "Deportivo Rincón": ("Rincón de los Sauces", "Neuquén", "Liga del Neuquén"),                # ?
    "Guillermo Brown": ("Puerto Madryn", "Chubut", "Liga del Valle (Trelew)"),
    "Germinal": ("Rawson", "Chubut", "Liga del Valle (Trelew)"),
    "Alvarado": ("Mar del Plata", "Buenos Aires", "Liga Marplatense"),
    "Kimberley": ("Mar del Plata", "Buenos Aires", "Liga Marplatense"),
    "Círculo Deportivo": ("Nicanor Otamendi", "Buenos Aires", "Liga Marplatense"),
    "Olimpo": ("Bahía Blanca", "Buenos Aires", "Liga del Sur (Bahía Blanca)"),
    "Villa Mitre": ("Bahía Blanca", "Buenos Aires", "Liga del Sur (Bahía Blanca)"),
    "Ramón Santamarina": ("Tandil", "Buenos Aires", "Liga Tandilense"),
}


_REG = None


def datos_club(nombre):
    """{'ciudad', 'provincia', 'liga'} del club, o None si no es del interior.

    Sirve para cualquier club del interior: Primera, Primera Nacional, Federal A y Regional Amateur."""
    global _REG
    if nombre in DATOS_INTERIOR:
        c, p, lg = DATOS_INTERIOR[nombre]
        return {"ciudad": c, "provincia": p, "liga": lg}
    if _REG is None:
        from datos.datos_regional import REGIONAL
        _REG = {x["nombre"]: {"ciudad": x["ciudad"], "provincia": x["provincia"], "liga": x["liga"]}
                for x in REGIONAL}
    return _REG.get(nombre)

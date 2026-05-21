import geopandas as gpd
import folium
from folium.plugins import MarkerCluster
import pandas as pd

# =============================================
# MAPA WEB INTERACTIVO — BIOBÍO
# Accesibilidad a servicios de salud
# =============================================

# Hospitales
hospitales_data = {
    'nombre': [
        'Hospital Regional de Concepción',
        'Hospital Las Higueras Talcahuano',
        'Hospital de Los Angeles',
        'Hospital de Chillán',
        'Hospital de Cañete'
    ],
    'lat': [-36.8270, -36.7120, -37.4695, -36.6063, -37.8014],
    'lon': [-73.0497, -73.1170, -72.3562, -72.1034, -73.4051],
    'camas': [700, 350, 280, 450, 120]
}

# Postas con distancias calculadas en día 4
postas_data = {
    'nombre': [
        'Posta Quilaco', 'Posta Antuco', 'Posta Alto Biobío',
        'Posta Santa Bárbara', 'Posta Mulchén', 'Posta Quilleco',
        'Posta Curanilahue', 'Posta Los Álamos'
    ],
    'lat': [-37.6833, -37.3333, -38.0000,
            -37.6667, -37.7167, -37.5000,
            -37.4667, -37.6333],
    'lon': [-71.7500, -71.5333, -71.5500,
            -72.0167, -72.4333, -72.1667,
            -73.3500, -73.4667],
    'dist_km': [58.6, 74.4, 92.3, 37.2, 28.3, 17.1, 37.5, 19.5],
    'hospital_cercano': [
        'Hospital de Los Angeles', 'Hospital de Los Angeles',
        'Hospital de Los Angeles', 'Hospital de Los Angeles',
        'Hospital de Los Angeles', 'Hospital de Los Angeles',
        'Hospital de Cañete', 'Hospital de Cañete'
    ]
}

# Crea el mapa centrado en el Biobío
m = folium.Map(
    location=[-37.2, -72.5],
    zoom_start=8,
    tiles='CartoDB positron'
)

# Carga y agrega el límite del Biobío
chile = gpd.read_file("DPA_2023/COMUNAS/COMUNAS_v1.shp")
biobio = chile[chile['REGION'] == 'Biobío']

folium.GeoJson(
    biobio,
    name='Comunas Biobío',
    style_function=lambda x: {
        'fillColor': '#f0f4f0',
        'color': '#666',
        'weight': 0.8,
        'fillOpacity': 0.5
    },
    tooltip=folium.GeoJsonTooltip(
        fields=['COMUNA', 'SUPERFICIE'],
        aliases=['Comuna:', 'Superficie (km²):'],
        style="font-family: Arial; font-size: 12px;"
    )
).add_to(m)

# Agrega hospitales
for i, row in enumerate(zip(
    hospitales_data['nombre'], hospitales_data['lat'],
    hospitales_data['lon'], hospitales_data['camas']
)):
    nombre, lat, lon, camas = row
    folium.Marker(
        location=[lat, lon],
        popup=folium.Popup(f"""
            <b>{nombre}</b><br>
            Camas aprox: {camas}<br>
            <i>Hospital de alta complejidad</i>
        """, max_width=200),
        tooltip=nombre,
        icon=folium.Icon(color='green', icon='plus-sign')
    ).add_to(m)

# Agrega postas con color según distancia
for i in range(len(postas_data['nombre'])):
    dist = postas_data['dist_km'][i]
    color = 'red' if dist > 70 else 'orange' if dist > 40 else 'blue'

    folium.CircleMarker(
        location=[postas_data['lat'][i], postas_data['lon'][i]],
        radius=8,
        color=color,
        fill=True,
        fill_opacity=0.8,
        popup=folium.Popup(f"""
            <b>{postas_data['nombre'][i]}</b><br>
            Distancia al hospital: <b>{dist} km</b><br>
            Hospital más cercano: {postas_data['hospital_cercano'][i]}<br>
            <hr>
            {'⚠️ Acceso crítico' if dist > 70 else '⚠️ Acceso limitado' if dist > 40 else '✓ Acceso moderado'}
        """, max_width=220),
        tooltip=f"{postas_data['nombre'][i]} — {dist} km"
    ).add_to(m)

# Leyenda
leyenda = """
<div style="position: fixed; bottom: 30px; right: 30px; z-index: 1000;
     background: white; padding: 12px 16px; border-radius: 8px;
     border: 1px solid #ccc; font-family: Arial; font-size: 12px;">
    <b>Accesibilidad a salud</b><br><br>
    <span style="color:green">★</span> Hospital<br>
    <span style="color:red">●</span> Posta crítica (>70 km)<br>
    <span style="color:orange">●</span> Acceso limitado (40–70 km)<br>
    <span style="color:blue">●</span> Acceso moderado (<40 km)<br>
</div>
"""
m.get_root().html.add_child(folium.Element(leyenda))

# Control de capas
folium.LayerControl().add_to(m)

# Guarda el mapa
m.save('mapa-interactivo-salud.html')
print("Mapa interactivo guardado como mapa-interactivo-salud.html")
print("Ábrelo en tu navegador para verlo")

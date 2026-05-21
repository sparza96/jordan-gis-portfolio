import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# =============================================
# ANÁLISIS DE COBERTURA DE SERVICIOS DE SALUD
# Inspirado en tu trabajo real en DETSur
# =============================================

# Hospitales principales del Biobío (coordenadas reales)
hospitales_data = {
    'nombre': [
        'Hospital Regional de Concepción',
        'Hospital Las Higueras Talcahuano',
        'Hospital de Los Angeles',
        'Hospital de Chillán',
        'Hospital de Cañete'
    ],
    'lat': [-36.8270, -36.7120, -37.4695, -36.6063, -37.8014],
    'lon': [-73.0497, -73.1170, -72.3562, -72.1034, -73.4051]
}

# Postas rurales del Biobío (puntos representativos)
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
            -73.3500, -73.4667]
}

# Crea GeoDataFrames
gdf_hospitales = gpd.GeoDataFrame(
    hospitales_data,
    geometry=[Point(lon, lat) for lon, lat in zip(hospitales_data['lon'], hospitales_data['lat'])],
    crs='EPSG:4326'
).to_crs(epsg=32719)

gdf_postas = gpd.GeoDataFrame(
    postas_data,
    geometry=[Point(lon, lat) for lon, lat in zip(postas_data['lon'], postas_data['lat'])],
    crs='EPSG:4326'
).to_crs(epsg=32719)

# Carga límite del Biobío
chile = gpd.read_file("DPA_2023/COMUNAS/COMUNAS_v1.shp")
biobio = chile[chile['REGION'] == 'Biobío'].to_crs(epsg=32719)

# =============================================
# CALCULA DISTANCIA DE CADA POSTA AL HOSPITAL
# MÁS CERCANO
# =============================================
def distancia_hospital_mas_cercano(posta, hospitales):
    distancias = hospitales.geometry.distance(posta)
    idx_min = distancias.idxmin()
    return distancias.min() / 1000, hospitales.loc[idx_min, 'nombre']

gdf_postas['dist_km'], gdf_postas['hospital_cercano'] = zip(
    *gdf_postas.geometry.apply(lambda p: distancia_hospital_mas_cercano(p, gdf_hospitales))
)

print("=== DISTANCIA DE POSTAS AL HOSPITAL MÁS CERCANO ===\n")
for _, row in gdf_postas.sort_values('dist_km', ascending=False).iterrows():
    print(f"{row['nombre']:<25} → {row['dist_km']:>6.1f} km  ({row['hospital_cercano']})")

print(f"\nPosta más alejada: {gdf_postas.loc[gdf_postas['dist_km'].idxmax(), 'nombre']}")
print(f"Distancia máxima: {gdf_postas['dist_km'].max():.1f} km")
print(f"Distancia promedio: {gdf_postas['dist_km'].mean():.1f} km")

# =============================================
# GENERA BUFFERS DE COBERTURA (50km)
# =============================================
gdf_hospitales['geometry_buffer'] = gdf_hospitales.geometry.buffer(50000)
buffers = gdf_hospitales.set_geometry('geometry_buffer')

# =============================================
# MAPA FINAL
# =============================================
fig, ax = plt.subplots(figsize=(10, 12))

# Región del Biobío
biobio.plot(ax=ax, color='#f0f4f0', edgecolor='#999', linewidth=0.5)

# Buffers de cobertura 50km
buffers.plot(ax=ax, color='#378ADD', alpha=0.15, edgecolor='#378ADD', linewidth=1)

# Hospitales
gdf_hospitales.plot(ax=ax, color='#1D9E75', markersize=80, zorder=5, marker='*')

# Postas — color por distancia
gdf_postas.plot(
    ax=ax, column='dist_km', cmap='RdYlGn_r',
    markersize=60, zorder=4, legend=True,
    legend_kwds={'label': 'Distancia al hospital (km)', 'orientation': 'horizontal', 'pad': 0.01}
)

# Etiquetas hospitales
for _, row in gdf_hospitales.iterrows():
    ax.annotate(row['nombre'].replace('Hospital ', ''),
                xy=(row.geometry.x, row.geometry.y),
                xytext=(6, 6), textcoords='offset points',
                fontsize=6, color='#0F6E56', fontweight='bold')

# Etiquetas postas
for _, row in gdf_postas.iterrows():
    ax.annotate(f"{row['nombre'].replace('Posta ', '')}\n{row['dist_km']:.0f}km",
                xy=(row.geometry.x, row.geometry.y),
                xytext=(4, 4), textcoords='offset points',
                fontsize=5, color='#333')

# Leyenda manual
h1 = mpatches.Patch(color='#1D9E75', label='Hospital')
h2 = mpatches.Patch(color='#378ADD', alpha=0.3, label='Cobertura 50km')
h3 = mpatches.Patch(color='#E24B4A', label='Posta > 100km')
h4 = mpatches.Patch(color='#63B32E', label='Posta < 50km')
ax.legend(handles=[h1, h2, h3, h4], loc='lower left', fontsize=8)

ax.set_title('Biobío — Accesibilidad a servicios de salud\nDistancia de postas rurales al hospital más cercano',
             fontsize=13, fontweight='bold', pad=15)
ax.set_axis_off()

plt.tight_layout()
plt.savefig('mapa-biobio-salud.png', dpi=150, bbox_inches='tight')
print("\nMapa guardado como mapa-biobio-salud.png")

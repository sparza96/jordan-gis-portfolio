import geopandas as gpd
import folium
from folium.plugins import MarkerCluster
from shapely.geometry import Point
import matplotlib.pyplot as plt
import pandas as pd

# =============================================
# PROYECTO INTEGRADOR SEMANA 1
# Mapa interactivo completo del Biobío
# Combina todo lo aprendido en días 1-6
# =============================================

# Carga y reproyecta (lección día 6)
chile = gpd.read_file("DPA_2023/COMUNAS/COMUNAS_v1.shp")
biobio = chile[chile['REGION'] == 'Biobío'].to_crs(epsg=32719)

# Calcula área real en km² (lección día 3)
biobio['area_km2'] = biobio.geometry.area / 1_000_000

# Clasifica comunas por tamaño
def clasificar(area):
    if area > 1500:
        return 'Grande (>1500 km²)'
    elif area > 500:
        return 'Mediana (500-1500 km²)'
    else:
        return 'Pequeña (<500 km²)'

biobio['categoria'] = biobio['area_km2'].apply(clasificar)

# Estadísticas generales
print("=== PROYECTO INTEGRADOR SEMANA 1 ===")
print(f"\nTotal comunas: {len(biobio)}")
print(f"Superficie total: {biobio['area_km2'].sum():,.1f} km²")
print(f"Comuna más grande: {biobio.loc[biobio['area_km2'].idxmax(), 'COMUNA']} ({biobio['area_km2'].max():.1f} km²)")
print(f"Comuna más pequeña: {biobio.loc[biobio['area_km2'].idxmin(), 'COMUNA']} ({biobio['area_km2'].min():.1f} km²)")
print(f"Superficie promedio: {biobio['area_km2'].mean():.1f} km²")

print("\n=== DISTRIBUCIÓN POR CATEGORÍA ===")
print(biobio.groupby('categoria')['COMUNA'].count().to_string())

# =============================================
# MAPA ESTÁTICO — resumen visual (día 2 y 3)
# =============================================
biobio_plot = biobio.copy()

colores = {
    'Grande (>1500 km²)': '#1D9E75',
    'Mediana (500-1500 km²)': '#378ADD',
    'Pequeña (<500 km²)': '#E24B4A'
}
biobio_plot['color'] = biobio_plot['categoria'].map(colores)

fig, axes = plt.subplots(1, 2, figsize=(16, 10))

# Mapa izquierdo: por categoría
ax1 = axes[0]
for categoria, color in colores.items():
    subset = biobio_plot[biobio_plot['categoria'] == categoria]
    subset.plot(ax=ax1, color=color, edgecolor='white', linewidth=0.5, label=categoria)

for _, row in biobio_plot.iterrows():
    ax1.annotate(
        row['COMUNA'],
        xy=(row.geometry.centroid.x, row.geometry.centroid.y),
        fontsize=4.5, ha='center', color='black'
    )

ax1.set_title('Biobío — Comunas por categoría de superficie',
              fontsize=12, fontweight='bold')
ax1.legend(loc='lower left', fontsize=8)
ax1.set_axis_off()

# Mapa derecho: gradiente por área
ax2 = axes[1]
biobio_plot.plot(
    ax=ax2,
    column='area_km2',
    cmap='YlOrRd',
    legend=True,
    legend_kwds={'label': 'Área (km²)', 'orientation': 'vertical'},
    edgecolor='white',
    linewidth=0.5
)
ax2.set_title('Biobío — Gradiente de superficie',
              fontsize=12, fontweight='bold')
ax2.set_axis_off()

plt.suptitle('Región del Biobío — Análisis territorial completo',
             fontsize=14, fontweight='bold', y=1.01)
plt.tight_layout()
plt.savefig('proyecto-semana1-estatico.png', dpi=150, bbox_inches='tight')
print("\nMapa estático guardado.")

# =============================================
# MAPA INTERACTIVO — Folium (día 5)
# =============================================
biobio_wgs = biobio.to_crs(epsg=4326)

m = folium.Map(location=[-37.2, -72.5], zoom_start=8, tiles='CartoDB positron')

# Choropleth por área
folium.Choropleth(
    geo_data=biobio_wgs,
    data=biobio_wgs,
    columns=['COMUNA', 'area_km2'],
    key_on='feature.properties.COMUNA',
    fill_color='YlOrRd',
    fill_opacity=0.7,
    line_opacity=0.5,
    legend_name='Superficie (km²)',
    name='Superficie comunal'
).add_to(m)

# Tooltips con información detallada
folium.GeoJson(
    biobio_wgs,
    name='Información comunal',
    style_function=lambda x: {
        'fillOpacity': 0,
        'color': 'transparent'
    },
    tooltip=folium.GeoJsonTooltip(
        fields=['COMUNA', 'area_km2', 'categoria'],
        aliases=['Comuna:', 'Superficie (km²):', 'Categoría:'],
        style="font-family: Arial; font-size: 13px;"
    )
).add_to(m)

# Marcadores con estadísticas en el centro de cada comuna
for _, row in biobio_wgs.iterrows():
    centroid = row.geometry.centroid
    folium.CircleMarker(
        location=[centroid.y, centroid.x],
        radius=4,
        color='white',
        fill=True,
        fill_color=colores[row['categoria']],
        fill_opacity=0.9,
        popup=folium.Popup(f"""
            <b>{row['COMUNA']}</b><br>
            Superficie: <b>{row['area_km2']:.1f} km²</b><br>
            Categoría: {row['categoria']}<br>
            Provincia: {row['PROVINCIA']}
        """, max_width=220)
    ).add_to(m)

# Leyenda
leyenda = """
<div style="position: fixed; bottom: 30px; right: 30px; z-index: 1000;
     background: white; padding: 14px 18px; border-radius: 10px;
     border: 1px solid #ccc; font-family: Arial; font-size: 12px;
     box-shadow: 2px 2px 6px rgba(0,0,0,0.2);">
    <b>Región del Biobío</b><br>
    <b>Análisis territorial</b><br><br>
    <span style="color:#1D9E75">●</span> Grande (>1.500 km²)<br>
    <span style="color:#378ADD">●</span> Mediana (500–1.500 km²)<br>
    <span style="color:#E24B4A">●</span> Pequeña (<500 km²)<br><br>
    <i>Click en comunas para más info</i>
</div>
"""
m.get_root().html.add_child(folium.Element(leyenda))

folium.LayerControl().add_to(m)
m.save('proyecto-semana1-interactivo.html')
print("Mapa interactivo guardado.")
print("\n✅ Proyecto Semana 1 completado.")
print("Archivos generados:")
print("  - proyecto-semana1-estatico.png")
print("  - proyecto-semana1-interactivo.html")

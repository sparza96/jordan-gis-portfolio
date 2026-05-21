import geopandas as gpd
import matplotlib.pyplot as plt

# Carga el shapefile completo
chile = gpd.read_file("DPA_2023/COMUNAS/COMUNAS_v1.shp")

# Reproyecta a UTM 19S (metros reales para Chile)
chile_utm = chile.to_crs(epsg=32719)

# Calcula área real en km²
chile_utm['area_km2'] = chile_utm.geometry.area / 1_000_000

# Filtra solo el Biobío
biobio = chile_utm[chile_utm['REGION'] == 'Biobío']

# Muestra las 10 comunas más grandes
print("=== TOP 10 COMUNAS MÁS GRANDES DEL BIOBÍO ===")
top10 = biobio[['COMUNA', 'area_km2']].sort_values('area_km2', ascending=False).head(10)
print(top10.to_string(index=False))
print(f"\nTotal comunas en el Biobío: {len(biobio)}")
print(f"Superficie total región: {biobio['area_km2'].sum():,.1f} km²")

# Genera mapa del Biobío coloreado por área
fig, ax = plt.subplots(figsize=(8, 10))

biobio.plot(
    ax=ax,
    column='area_km2',
    cmap='YlGn',
    legend=True,
    legend_kwds={'label': 'Área (km²)', 'orientation': 'horizontal'},
    edgecolor='white',
    linewidth=0.5
)

# Etiqueta cada comuna
for idx, row in biobio.iterrows():
    ax.annotate(
        row['COMUNA'],
        xy=(row.geometry.centroid.x, row.geometry.centroid.y),
        fontsize=5,
        ha='center',
        color='black'
    )

ax.set_title('Región del Biobío — Comunas por superficie', fontsize=14, fontweight='bold')
ax.set_axis_off()

plt.tight_layout()
plt.savefig('mapa-biobio-area.png', dpi=150, bbox_inches='tight')
print("\nMapa guardado como mapa-biobio-area.png")

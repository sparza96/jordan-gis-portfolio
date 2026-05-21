import geopandas as gpd
import matplotlib.pyplot as plt

# Carga el shapefile
chile = gpd.read_file("DPA_2023/COMUNAS/COMUNAS_v1.shp")

# Reproyecta a coordenadas planas para Chile (metros reales)
chile = chile.to_crs(epsg=32719)

# Mapa coloreado por región
fig, ax = plt.subplots(figsize=(10, 16))

chile.plot(
    ax=ax,
    column='REGION',
    categorical=True,
    legend=True,
    legend_kwds={'loc': 'lower left', 'fontsize': 6},
    edgecolor='white',
    linewidth=0.3
)

ax.set_title('Chile — Comunas por Región', fontsize=16, fontweight='bold', pad=20)
ax.set_axis_off()

plt.tight_layout()
plt.savefig('mapa-chile-comunas.png', dpi=150, bbox_inches='tight')
print("Mapa guardado como mapa-chile-comunas.png")

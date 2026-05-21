import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# =============================================
# DÍA 10 — AUTOMATIZACIÓN DE GEOPROCESOS
# Sin QGIS GUI — todo desde Python
# Replica flujos de trabajo de Arauco
# =============================================

print("=== AUTOMATIZACIÓN DE GEOPROCESOS ===\n")

# Carga datos base
chile = gpd.read_file("DPA_2023/COMUNAS/COMUNAS_v1.shp")
biobio = chile[chile['REGION'] == 'Biobío'].to_crs(epsg=32719)
biobio['area_km2'] = biobio.geometry.area / 1_000_000

# =============================================
# GEOPROCESO 1 — BUFFER
# Zona de influencia de 30km alrededor
# de Los Angeles (capital provincial)
# =============================================
print("▶ Geoproceso 1: Buffer")

los_angeles = biobio[biobio['COMUNA'] == 'Los Angeles'].copy()
buffer_30km = los_angeles.copy()
buffer_30km['geometry'] = los_angeles.geometry.buffer(30000)
buffer_30km['tipo'] = 'Buffer 30km Los Angeles'

print(f"  Buffer creado: {buffer_30km.geometry.area.values[0]/1_000_000:.1f} km² de cobertura")

# =============================================
# GEOPROCESO 2 — CLIP
# Recortar el Biobío al área del buffer
# =============================================
print("▶ Geoproceso 2: Clip")

import warnings
warnings.filterwarnings('ignore')

biobio_clip = gpd.clip(biobio, buffer_30km)
print(f"  Comunas dentro del buffer: {len(biobio_clip)}")
print(f"  Comunas: {', '.join(biobio_clip['COMUNA'].tolist())}")

# =============================================
# GEOPROCESO 3 — INTERSECCIÓN
# Qué porcentaje de cada comuna queda
# dentro del buffer
# =============================================
print("▶ Geoproceso 3: Intersección y cálculo de cobertura")

interseccion = gpd.overlay(biobio, buffer_30km[['geometry']], how='intersection')
interseccion['area_intersec_km2'] = interseccion.geometry.area / 1_000_000

cobertura = interseccion.merge(
    biobio[['COMUNA', 'area_km2']],
    on='COMUNA',
    suffixes=('_intersec', '_total')
)
cobertura = cobertura.rename(columns={'area_km2_total': 'area_km2'})
cobertura['pct_cobertura'] = (cobertura['area_intersec_km2'] / cobertura['area_km2'] * 100).round(1)
cobertura = cobertura.sort_values('pct_cobertura', ascending=False)

print(f"\n  {'COMUNA':<20} {'Área total':>12} {'En buffer':>10} {'Cobertura':>10}")
print(f"  {'-'*55}")
for _, row in cobertura.iterrows():
    print(f"  {row['COMUNA']:<20} {row['area_km2']:>10.1f}km² {row['area_intersec_km2']:>8.1f}km² {row['pct_cobertura']:>9.1f}%")

# =============================================
# GEOPROCESO 4 — DISSOLVE
# Une todas las comunas de la provincia
# de Biobío en un solo polígono
# =============================================
print("\n▶ Geoproceso 4: Dissolve por provincia")

provincias = biobio.dissolve(by='PROVINCIA', aggfunc={
    'area_km2': 'sum',
    'COMUNA': 'count'
}).reset_index()
provincias.columns = ['PROVINCIA', 'geometry', 'area_total_km2', 'n_comunas']

print(f"\n  {'PROVINCIA':<15} {'Comunas':>8} {'Área total':>12}")
print(f"  {'-'*38}")
for _, row in provincias.iterrows():
    print(f"  {row['PROVINCIA']:<15} {row['n_comunas']:>8} {row['area_total_km2']:>10.1f}km²")

# =============================================
# GEOPROCESO 5 — SPATIAL JOIN
# Une atributos de provincias a comunas
# =============================================
print("\n▶ Geoproceso 5: Spatial Join")

puntos_ciudades = gpd.GeoDataFrame({
    'ciudad': ['Concepción', 'Los Angeles', 'Chillán', 'Cañete', 'Lebu'],
    'poblacion': [223803, 123445, 191343, 24000, 28000],
    'geometry': [
        Point(-73.0497, -36.8270),
        Point(-72.3562, -37.4695),
        Point(-72.1034, -36.6063),
        Point(-73.4051, -37.8014),
        Point(-73.6500, -37.6000)
    ]
}, crs='EPSG:4326').to_crs(epsg=32719)

join_result = gpd.sjoin(puntos_ciudades, biobio[['COMUNA', 'PROVINCIA', 'geometry']],
                         how='left', predicate='within')

print(f"\n  {'CIUDAD':<15} {'POBLACIÓN':>10} {'COMUNA':>15} {'PROVINCIA':>12}")
print(f"  {'-'*55}")
for _, row in join_result.iterrows():
    print(f"  {row['ciudad']:<15} {row['poblacion']:>10,} {row['COMUNA']:>15} {row['PROVINCIA']:>12}")

# =============================================
# MAPA FINAL — todos los geoprocesos
# =============================================
fig, axes = plt.subplots(2, 2, figsize=(14, 14))

# 1. Buffer y clip
ax1 = axes[0, 0]
biobio.plot(ax=ax1, color='#f0f4f0', edgecolor='#999', linewidth=0.5)
buffer_30km.plot(ax=ax1, color='#378ADD', alpha=0.3, edgecolor='#378ADD', linewidth=1.5)
biobio_clip.plot(ax=ax1, color='#1D9E75', alpha=0.7, edgecolor='white', linewidth=0.5)
ax1.set_title('Buffer 30km + Clip\nLos Ángeles', fontweight='bold', fontsize=10)
ax1.set_axis_off()

# 2. Cobertura por intersección
ax2 = axes[0, 1]
cobertura_gdf = biobio.merge(cobertura[['COMUNA', 'pct_cobertura']], on='COMUNA', how='left')
cobertura_gdf['pct_cobertura'] = cobertura_gdf['pct_cobertura'].fillna(0)
cobertura_gdf.plot(ax=ax2, column='pct_cobertura', cmap='YlOrRd',
                   legend=True, edgecolor='white', linewidth=0.5,
                   legend_kwds={'label': '% en buffer', 'orientation': 'horizontal'})
ax2.set_title('Cobertura del buffer\npor comuna (%)', fontweight='bold', fontsize=10)
ax2.set_axis_off()

# 3. Dissolve provincias
ax3 = axes[1, 0]
provincias.plot(ax=ax3, column='PROVINCIA', categorical=True,
                legend=True, edgecolor='white', linewidth=1,
                legend_kwds={'fontsize': 8, 'loc': 'lower left'})
for _, row in provincias.iterrows():
    centroid = row.geometry.centroid
    ax3.annotate(f"{row['PROVINCIA']}\n{row['area_total_km2']:.0f} km²",
                xy=(centroid.x, centroid.y), ha='center', fontsize=7)
ax3.set_title('Dissolve por Provincia', fontweight='bold', fontsize=10)
ax3.set_axis_off()

# 4. Spatial join ciudades
ax4 = axes[1, 1]
biobio.plot(ax=ax4, color='#f0f4f0', edgecolor='#999', linewidth=0.5)
puntos_ciudades.plot(ax=ax4, color='#D85A30', markersize=puntos_ciudades['poblacion']/2000,
                     zorder=5, alpha=0.8)
for _, row in join_result.iterrows():
    ax4.annotate(f"{row['ciudad']}\n{row['poblacion']:,}",
                xy=(row.geometry.x, row.geometry.y),
                xytext=(5, 5), textcoords='offset points', fontsize=7)
ax4.set_title('Spatial Join\nCiudades + Comunas', fontweight='bold', fontsize=10)
ax4.set_axis_off()

plt.suptitle('Automatización de Geoprocesos — Biobío\nBuffer · Clip · Intersección · Dissolve · Spatial Join',
             fontsize=12, fontweight='bold')
plt.tight_layout()
plt.savefig('dia-10-geoprocesos.png', dpi=150, bbox_inches='tight')
print("\n✅ Mapa guardado como dia-10-geoprocesos.png")
print("✅ Día 10 completado — 5 geoprocesos automatizados")

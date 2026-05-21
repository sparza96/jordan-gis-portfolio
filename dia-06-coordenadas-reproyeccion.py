import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

# =============================================
# DÍA 6 — SISTEMAS DE COORDENADAS
# El conocimiento que separa amateur de pro
# =============================================

# Carga el Biobío
chile = gpd.read_file("DPA_2023/COMUNAS/COMUNAS_v1.shp")
biobio = chile[chile['REGION'] == 'Biobío']

print("=== SISTEMAS DE COORDENADAS ===\n")
print(f"CRS original: {biobio.crs}")
print(f"Unidad: grados (latitud/longitud)\n")

# =============================================
# COMPARACIÓN: ÁREA EN GRADOS vs METROS
# =============================================
biobio_grados = biobio.copy()
biobio_utm = biobio.to_crs(epsg=32719)
biobio_mercator = biobio.to_crs(epsg=3857)

# Área en distintos sistemas
biobio_grados['area_grados'] = biobio_grados.geometry.area
biobio_utm['area_km2'] = biobio_utm.geometry.area / 1_000_000
biobio_mercator['area_mercator'] = biobio_mercator.geometry.area / 1_000_000

print("=== COMPARACIÓN DE ÁREAS POR SISTEMA ===\n")
print(f"{'COMUNA':<20} {'Grados²':>12} {'UTM km²':>12} {'Mercator km²':>14}")
print("-" * 62)

comunas_muestra = ['Concepción', 'Los Angeles', 'Alto Biobío', 'Talcahuano']
for comuna in comunas_muestra:
    g = biobio_grados[biobio_grados['COMUNA'] == comuna]['area_grados'].values[0]
    u = biobio_utm[biobio_utm['COMUNA'] == comuna]['area_km2'].values[0]
    m = biobio_mercator[biobio_mercator['COMUNA'] == comuna]['area_mercator'].values[0]
    print(f"{comuna:<20} {g:>12.6f} {u:>12.1f} {m:>14.1f}")

print("\n⚠️  El área en grados no tiene sentido físico real.")
print("✓  UTM 19S (EPSG:32719) es el sistema correcto para Chile.")
print("✗  Mercator distorsiona áreas — nunca lo uses para medir.\n")

# =============================================
# DISTANCIA: ERROR SIN REPROYECTAR
# =============================================
from shapely.geometry import Point

conc_grados = Point(-73.0497, -36.8270)
losangeles_grados = Point(-72.3562, -37.4695)

conc_utm = gpd.GeoSeries([conc_grados], crs=4326).to_crs(32719).iloc[0]
losangeles_utm = gpd.GeoSeries([losangeles_grados], crs=4326).to_crs(32719).iloc[0]

dist_grados = conc_grados.distance(losangeles_grados)
dist_utm = conc_utm.distance(losangeles_utm) / 1000

print("=== DISTANCIA CONCEPCIÓN → LOS ÁNGELES ===\n")
print(f"En grados (INCORRECTO):  {dist_grados:.4f} '¿unidades?'")
print(f"En UTM km (CORRECTO):    {dist_utm:.1f} km")
print(f"\nSi usaras grados para un buffer de '50km'")
print(f"estarías creando una zona de {dist_grados*50/dist_utm*50:.0f} km reales — error brutal.\n")

# =============================================
# MAPA COMPARATIVO: 3 PROYECCIONES
# =============================================
fig = plt.figure(figsize=(15, 8))
gs = gridspec.GridSpec(1, 3, figure=fig)

proyecciones = [
    (biobio_grados, 'EPSG:4326 — WGS84\n(Grados, incorrecto para medir)', '#E24B4A'),
    (biobio_utm, 'EPSG:32719 — UTM 19S\n(Metros, correcto para Chile)', '#1D9E75'),
    (biobio_mercator, 'EPSG:3857 — Web Mercator\n(Distorsionado, solo para web)', '#378ADD'),
]

for i, (gdf, titulo, color) in enumerate(proyecciones):
    ax = fig.add_subplot(gs[i])
    gdf.plot(ax=ax, color=color, alpha=0.6, edgecolor='white', linewidth=0.5)
    ax.set_title(titulo, fontsize=9, fontweight='bold', pad=10)
    ax.set_axis_off()

fig.suptitle('Región del Biobío — Comparación de sistemas de coordenadas',
             fontsize=13, fontweight='bold', y=1.02)

plt.tight_layout()
plt.savefig('mapa-proyecciones.png', dpi=150, bbox_inches='tight')
print("Mapa comparativo guardado como mapa-proyecciones.png")

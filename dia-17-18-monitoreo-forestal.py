import geopandas as gpd
import pandas as pd
import numpy as np
import rasterio
from rasterio.plot import show
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
import folium
import warnings
warnings.filterwarnings('ignore')

# =============================================
# DÍAS 17-18 — MONITOREO FORESTAL
# Detección de cambios en vegetación
# Inspirado directamente en Forestal Arauco
# =============================================

print("=" * 55)
print("  MONITOREO FORESTAL — DETECCIÓN DE CAMBIOS")
print("  Metodología Arauco automatizada con Python")
print("=" * 55)

# =============================================
# MÓDULO 1 — CARGA Y ANÁLISIS DE IMAGEN
# =============================================
print("\n[1/4] Cargando imagen Landsat 8...")

BASE = "imgsat1/LC08_L2SP_001085_20251216_20251224_02_T1_SR_"
B3 = BASE + "B3.TIF"  # Verde
B4 = BASE + "B4.TIF"  # Rojo
B5 = BASE + "B5.TIF"  # NIR
B6 = BASE + "B6.TIF"  # SWIR1

with rasterio.open(B4) as src:
    meta = src.meta
    transform = src.transform
    crs = src.crs
    print(f"  CRS: {crs}")
    print(f"  Resolución: {src.res[0]}m x {src.res[1]}m")
    print(f"  Dimensiones: {src.width} x {src.height} px")

# Lee bandas
with rasterio.open(B3) as src: verde = src.read(1).astype(float)
with rasterio.open(B4) as src: rojo = src.read(1).astype(float)
with rasterio.open(B5) as src: nir = src.read(1).astype(float)
with rasterio.open(B6) as src: swir = src.read(1).astype(float)

# Escala Landsat Collection 2
verde = verde * 0.0000275 - 0.2
rojo  = rojo  * 0.0000275 - 0.2
nir   = nir   * 0.0000275 - 0.2
swir  = swir  * 0.0000275 - 0.2

# Clip valores válidos
for banda in [verde, rojo, nir, swir]:
    np.clip(banda, 0, 1, out=banda)

print("  ✅ Bandas cargadas y escaladas")

# =============================================
# MÓDULO 2 — ÍNDICES ESPECTRALES
# =============================================
print("\n[2/4] Calculando índices espectrales...")

np.seterr(divide='ignore', invalid='ignore')

# NDVI — Vegetación
ndvi = np.where((nir + rojo) == 0, 0, (nir - rojo) / (nir + rojo))

# NDWI — Agua (Normalized Difference Water Index)
ndwi = np.where((verde + nir) == 0, 0, (verde - nir) / (verde + nir))

# NBR — Burn Ratio (detecta áreas quemadas)
nbr = np.where((nir + swir) == 0, 0, (nir - swir) / (nir + swir))

# NDMI — Moisture Index (humedad vegetación)
ndmi = np.where((nir + swir) == 0, 0, (nir - swir) / (nir + swir))

print(f"  NDVI  — min: {np.nanmin(ndvi):.3f}  max: {np.nanmax(ndvi):.3f}  prom: {np.nanmean(ndvi):.3f}")
print(f"  NDWI  — min: {np.nanmin(ndwi):.3f}  max: {np.nanmax(ndwi):.3f}  prom: {np.nanmean(ndwi):.3f}")
print(f"  NBR   — min: {np.nanmin(nbr):.3f}   max: {np.nanmax(nbr):.3f}   prom: {np.nanmean(nbr):.3f}")

# =============================================
# MÓDULO 3 — CLASIFICACIÓN DE COBERTURA
# =============================================
print("\n[3/4] Clasificando cobertura del suelo...")

# Clasificación basada en umbrales espectrales
# Metodología estándar teledetección forestal
cobertura = np.zeros_like(ndvi, dtype=np.uint8)

# 0 = Sin datos
# 1 = Agua
# 2 = Urbano / suelo desnudo
# 3 = Vegetación escasa
# 4 = Vegetación media
# 5 = Bosque denso / plantación

cobertura[ndwi > 0.1] = 1                                          # Agua
cobertura[(ndvi >= 0) & (ndvi < 0.15) & (ndwi <= 0.1)] = 2       # Urbano
cobertura[(ndvi >= 0.15) & (ndvi < 0.30)] = 3                     # Veg. escasa
cobertura[(ndvi >= 0.30) & (ndvi < 0.50)] = 4                     # Veg. media
cobertura[ndvi >= 0.50] = 5                                        # Bosque denso
cobertura[ndvi < 0] = 0                                            # Sin datos

# Estadísticas de cobertura
total_pixeles = cobertura.size
categorias = {
    0: 'Sin datos / nubes',
    1: 'Agua',
    2: 'Urbano / suelo',
    3: 'Vegetación escasa',
    4: 'Vegetación media',
    5: 'Bosque / plantación'
}

print("\n  Distribución de cobertura:")
print(f"  {'Categoría':<25} {'Píxeles':>10} {'%':>8}")
print(f"  {'-'*45}")
for cod, nombre in categorias.items():
    n = np.sum(cobertura == cod)
    pct = n / total_pixeles * 100
    print(f"  {nombre:<25} {n:>10,} {pct:>7.1f}%")

# Área en hectáreas (pixel 30m x 30m = 900m² = 0.09ha)
area_ha_pixel = 0.09
bosque_ha = np.sum(cobertura == 5) * area_ha_pixel
veg_media_ha = np.sum(cobertura == 4) * area_ha_pixel
print(f"\n  Superficie bosque/plantación: {bosque_ha:,.0f} ha")
print(f"  Superficie vegetación media:  {veg_media_ha:,.0f} ha")
print(f"  Total vegetación:             {bosque_ha + veg_media_ha:,.0f} ha")

# =============================================
# MÓDULO 4 — SIMULACIÓN DETECCIÓN DE CAMBIOS
# En Arauco: comparar dos fechas distintas
# Aquí simulamos una fecha anterior
# =============================================
print("\n[4/4] Simulando detección de cambios...")

np.random.seed(123)
# Simula NDVI de una fecha anterior (3 meses antes)
# En producción usarías una segunda imagen real
ndvi_anterior = ndvi.copy()
mascara_cambio = np.random.random(ndvi.shape) < 0.05  # 5% de píxeles cambian
ndvi_anterior[mascara_cambio] = ndvi_anterior[mascara_cambio] + np.random.uniform(0.15, 0.35,
                                  mascara_cambio.sum())
ndvi_anterior = np.clip(ndvi_anterior, 0, 1)

# Detecta pérdida de vegetación
diferencia_ndvi = ndvi_anterior - ndvi  # positivo = perdió vegetación

umbral_cambio = 0.15
zona_cambio = diferencia_ndvi > umbral_cambio

n_pixeles_cambio = np.sum(zona_cambio)
area_cambio_ha = n_pixeles_cambio * area_ha_pixel

print(f"  Píxeles con cambio detectado: {n_pixeles_cambio:,}")
print(f"  Área de cambio estimada: {area_cambio_ha:,.1f} ha")
print(f"  Equivale a: {area_cambio_ha/10000:.2f} km²")

if area_cambio_ha > 1000:
    print("  ⚠️  ALERTA: Cambio significativo detectado")
elif area_cambio_ha > 500:
    print("  ⚠️  AVISO: Cambio moderado detectado")
else:
    print("  ✅ Cambio dentro de rangos normales")

# =============================================
# VISUALIZACIONES
# =============================================
fig, axes = plt.subplots(2, 3, figsize=(18, 12))

# Paleta para clasificación
colores_cob = ['#333333', '#1a78c2', '#d4b483',
               '#ffffb3', '#78c679', '#1a7837']
cmap_cob = mcolors.ListedColormap(colores_cob)

# 1. Color verdadero RGB
def normalizar(b):
    p2, p98 = np.percentile(b, (2, 98))
    return np.clip((b - p2) / (p98 - p2 + 1e-10), 0, 1)

rgb = np.dstack([normalizar(rojo), normalizar(verde),
                 normalizar(nir * 0.5)])
axes[0,0].imshow(rgb)
axes[0,0].set_title('Falso color (NIR-R-G)\nVegetación = rojo intenso',
                    fontweight='bold', fontsize=10)
axes[0,0].set_axis_off()

# 2. NDVI
ndvi_plot = axes[0,1].imshow(ndvi, cmap='RdYlGn', vmin=-0.1, vmax=0.7)
axes[0,1].set_title('NDVI\nÍndice de vegetación',
                    fontweight='bold', fontsize=10)
axes[0,1].set_axis_off()
plt.colorbar(ndvi_plot, ax=axes[0,1], orientation='horizontal',
             pad=0.02, label='NDVI')

# 3. Clasificación cobertura
cob_plot = axes[0,2].imshow(cobertura, cmap=cmap_cob, vmin=0, vmax=5)
axes[0,2].set_title('Clasificación cobertura\ndel suelo',
                    fontweight='bold', fontsize=10)
axes[0,2].set_axis_off()
patches_cob = [mpatches.Patch(color=colores_cob[i], label=categorias[i])
               for i in range(6)]
axes[0,2].legend(handles=patches_cob, fontsize=6,
                 loc='lower left', title='Cobertura')

# 4. NBR — Burn Ratio
nbr_plot = axes[1,0].imshow(nbr, cmap='RdYlGn', vmin=-0.5, vmax=0.8)
axes[1,0].set_title('NBR — Burn Ratio\nDetección áreas quemadas',
                    fontweight='bold', fontsize=10)
axes[1,0].set_axis_off()
plt.colorbar(nbr_plot, ax=axes[1,0], orientation='horizontal',
             pad=0.02, label='NBR')

# 5. NDVI anterior (simulado)
ndvi_ant_plot = axes[1,1].imshow(ndvi_anterior, cmap='RdYlGn',
                                  vmin=-0.1, vmax=0.7)
axes[1,1].set_title('NDVI fecha anterior\n(simulado t-3 meses)',
                    fontweight='bold', fontsize=10)
axes[1,1].set_axis_off()
plt.colorbar(ndvi_ant_plot, ax=axes[1,1], orientation='horizontal',
             pad=0.02, label='NDVI anterior')

# 6. Detección de cambios
cambio_viz = np.zeros_like(ndvi)
cambio_viz[zona_cambio] = 1
cambio_cmap = mcolors.ListedColormap(['#f0f4f0', '#E24B4A'])
axes[1,2].imshow(ndvi, cmap='Greens', alpha=0.5, vmin=0, vmax=0.8)
axes[1,2].imshow(cambio_viz, cmap=cambio_cmap, alpha=0.7)
axes[1,2].set_title(f'Detección de cambios\n{area_cambio_ha:,.0f} ha afectadas',
                    fontweight='bold', fontsize=10)
axes[1,2].set_axis_off()
p_cambio = [mpatches.Patch(color='#f0f4f0', label='Sin cambio'),
            mpatches.Patch(color='#E24B4A', label='Pérdida vegetación')]
axes[1,2].legend(handles=p_cambio, fontsize=8, loc='lower left')

plt.suptitle('Monitoreo Forestal — Análisis Landsat 8\nÁrea Concepción, Biobío — Diciembre 2025',
             fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('dia-17-18-monitoreo-forestal.png', dpi=150, bbox_inches='tight')
print("\n  ✅ Dashboard forestal guardado")

print("\n" + "=" * 55)
print("  ✅ DÍAS 17-18 COMPLETADOS")
print("=" * 55)
print("\nArchivos generados:")
print("  - dia-17-18-monitoreo-forestal.png")

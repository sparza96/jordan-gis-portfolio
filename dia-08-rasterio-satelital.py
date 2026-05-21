import rasterio
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from rasterio.plot import show

# =============================================
# DÍA 8 — RASTERIO + IMAGEN LANDSAT 8
# Análisis de imagen satelital real
# Área: Concepción, Biobío — Diciembre 2025
# =============================================

# Rutas de las bandas
BASE = "imgsat1/LC08_L2SP_001085_20251216_20251224_02_T1_SR_"
B2 = BASE + "B2.TIF"   # Azul
B3 = BASE + "B3.TIF"   # Verde
B4 = BASE + "B4.TIF"   # Rojo
B5 = BASE + "B5.TIF"   # NIR (infrarrojo cercano)

# =============================================
# PASO 1 — EXPLORAR LA IMAGEN
# =============================================
with rasterio.open(B4) as src:
    print("=== METADATA DE LA IMAGEN ===")
    print(f"CRS: {src.crs}")
    print(f"Resolución: {src.res} metros")
    print(f"Dimensiones: {src.width} x {src.height} píxeles")
    print(f"Área cubierta: {src.bounds}")
    print(f"Tipo de dato: {src.dtypes[0]}")

# =============================================
# PASO 2 — CALCULAR NDVI
# NDVI = (NIR - Rojo) / (NIR + Rojo)
# Rango: -1 a 1
# < 0   → agua o nubes
# 0-0.2 → suelo desnudo o urbano
# 0.2-0.5 → vegetación escasa
# > 0.5 → vegetación densa (bosque)
# =============================================
with rasterio.open(B4) as src:
    rojo = src.read(1).astype(float)
    perfil = src.profile

with rasterio.open(B5) as src:
    nir = src.read(1).astype(float)

# Escala Landsat Collection 2 Level-2
# Los valores vienen escalados, hay que convertirlos
rojo = rojo * 0.0000275 - 0.2
nir  = nir  * 0.0000275 - 0.2

# Evitar división por cero
np.seterr(divide='ignore', invalid='ignore')
ndvi = np.where(
    (nir + rojo) == 0,
    0,
    (nir - rojo) / (nir + rojo)
)

print(f"\n=== ESTADÍSTICAS NDVI ===")
print(f"NDVI mínimo:  {np.nanmin(ndvi):.3f}")
print(f"NDVI máximo:  {np.nanmax(ndvi):.3f}")
print(f"NDVI promedio: {np.nanmean(ndvi):.3f}")
print(f"NDVI mediana:  {np.nanmedian(ndvi):.3f}")

# Clasificación
total = ndvi.size
agua    = np.sum(ndvi < 0) / total * 100
urbano  = np.sum((ndvi >= 0) & (ndvi < 0.2)) / total * 100
veg_esc = np.sum((ndvi >= 0.2) & (ndvi < 0.5)) / total * 100
bosque  = np.sum(ndvi >= 0.5) / total * 100

print(f"\n=== COBERTURA DEL SUELO (estimada) ===")
print(f"Agua / nubes:        {agua:.1f}%")
print(f"Urbano / suelo:      {urbano:.1f}%")
print(f"Vegetación escasa:   {veg_esc:.1f}%")
print(f"Bosque / veg. densa: {bosque:.1f}%")

# =============================================
# PASO 3 — IMAGEN COLOR VERDADERO (RGB)
# =============================================
with rasterio.open(B4) as src: r = src.read(1).astype(float)
with rasterio.open(B3) as src: g = src.read(1).astype(float)
with rasterio.open(B2) as src: b = src.read(1).astype(float)

def normalizar(banda):
    p2, p98 = np.percentile(banda, (2, 98))
    return np.clip((banda - p2) / (p98 - p2), 0, 1)

rgb = np.dstack([normalizar(r), normalizar(g), normalizar(b)])

# =============================================
# PASO 4 — MAPA COMPARATIVO
# =============================================
fig, axes = plt.subplots(1, 3, figsize=(18, 7))

# RGB — color verdadero
axes[0].imshow(rgb)
axes[0].set_title('Color verdadero (RGB)\nBandas 4-3-2', fontsize=11, fontweight='bold')
axes[0].set_axis_off()

# NDVI
ndvi_plot = axes[1].imshow(ndvi, cmap='RdYlGn', vmin=-0.2, vmax=0.8)
axes[1].set_title('NDVI — Índice de vegetación\nRojo=suelo | Verde=bosque', fontsize=11, fontweight='bold')
axes[1].set_axis_off()
plt.colorbar(ndvi_plot, ax=axes[1], orientation='horizontal', pad=0.02, label='NDVI')

# NDVI clasificado
colores_ndvi = ['#1a78c2', '#d4b483', '#ffffb3', '#78c679', '#1a7837']
cmap_clasif = mcolors.ListedColormap(colores_ndvi)
bounds = [-1, 0, 0.2, 0.35, 0.5, 1]
norm = mcolors.BoundaryNorm(bounds, cmap_clasif.N)

ndvi_class = axes[2].imshow(ndvi, cmap=cmap_clasif, norm=norm)
axes[2].set_title('NDVI Clasificado\nCobertura del suelo', fontsize=11, fontweight='bold')
axes[2].set_axis_off()

cbar = plt.colorbar(ndvi_class, ax=axes[2], orientation='horizontal', pad=0.02)
cbar.set_ticks([-0.5, 0.1, 0.275, 0.425, 0.75])
cbar.set_ticklabels(['Agua', 'Urbano', 'Veg. escasa', 'Veg. media', 'Bosque'], fontsize=7)

plt.suptitle('Análisis Landsat 8 — Área Concepción, Biobío\n16 Diciembre 2025',
             fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('dia-08-ndvi-concepcion.png', dpi=150, bbox_inches='tight')
print("\nMapa guardado como dia-08-ndvi-concepcion.png")
print("\n✅ Día 8 completado — primer análisis de imagen satelital real")
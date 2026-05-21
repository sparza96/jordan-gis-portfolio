import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point, LineString
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from sqlalchemy import create_engine, text
import warnings
warnings.filterwarnings('ignore')

# =============================================
# DÍA 11 — AUTOMATIZACIÓN AVANZADA
# Flujos de trabajo encadenados
# Inspirado en procesos reales de Arauco
# =============================================

print("=== AUTOMATIZACIÓN AVANZADA DE GEOPROCESOS ===\n")

# Conexión a base de datos
engine = create_engine('postgresql://postgres:postgres123@localhost:5432/gis_jordan')

# Carga datos base
chile = gpd.read_file("DPA_2023/COMUNAS/COMUNAS_v1.shp")
biobio = chile[chile['REGION'] == 'Biobío'].to_crs(epsg=32719)
biobio['area_km2'] = biobio.geometry.area / 1_000_000

# =============================================
# FLUJO 1 — DETECCIÓN AUTOMÁTICA DE ZONAS
# DE RIESGO (simulando monitoreo Arauco)
# =============================================
print("▶ Flujo 1: Detección automática de zonas de riesgo\n")

# Simula puntos de eventos detectados
# (en Arauco vendrían de imágenes satelitales)
np.random.seed(42)
n_eventos = 50

# Genera puntos aleatorios dentro del Biobío
bounds = biobio.total_bounds
eventos = []
while len(eventos) < n_eventos:
    x = np.random.uniform(bounds[0], bounds[2])
    y = np.random.uniform(bounds[1], bounds[3])
    punto = Point(x, y)
    if biobio.geometry.contains(punto).any():
        eventos.append(punto)

tipos = np.random.choice(
    ['Incendio', 'Tala ilegal', 'Toma terreno', 'Daño plantación'],
    size=n_eventos,
    p=[0.3, 0.25, 0.2, 0.25]
)

gdf_eventos = gpd.GeoDataFrame({
    'tipo': tipos,
    'severidad': np.random.choice(['Alta', 'Media', 'Baja'], n_eventos, p=[0.2, 0.5, 0.3]),
    'fecha': pd.date_range('2024-01-01', periods=n_eventos, freq='7D'),
    'geometry': eventos
}, crs='EPSG:32719')

# Spatial join para saber en qué comuna ocurrió cada evento
eventos_comunas = gpd.sjoin(gdf_eventos, biobio[['COMUNA', 'PROVINCIA', 'geometry']],
                             how='left', predicate='within')

print("  Resumen de eventos detectados:")
resumen = eventos_comunas.groupby(['tipo', 'severidad']).size().unstack(fill_value=0)
print(resumen.to_string())

print("\n  Comunas con más eventos:")
top_comunas = eventos_comunas.groupby('COMUNA').size().sort_values(ascending=False).head(5)
print(top_comunas.to_string())

# =============================================
# FLUJO 2 — ÍNDICE DE RIESGO COMPUESTO
# =============================================
print("\n▶ Flujo 2: Cálculo de índice de riesgo por comuna\n")

# Cuenta eventos por comuna y severidad
eventos_por_comuna = eventos_comunas.groupby('COMUNA').agg(
    n_eventos=('tipo', 'count'),
    n_alta=('severidad', lambda x: (x == 'Alta').sum()),
    n_media=('severidad', lambda x: (x == 'Media').sum()),
).reset_index()

# Calcula índice de riesgo ponderado
eventos_por_comuna['indice_riesgo'] = (
    eventos_por_comuna['n_alta'] * 3 +
    eventos_por_comuna['n_media'] * 2 +
    (eventos_por_comuna['n_eventos'] - eventos_por_comuna['n_alta'] - eventos_por_comuna['n_media']) * 1
)

# Une al GeoDataFrame
biobio_riesgo = biobio.merge(eventos_por_comuna, on='COMUNA', how='left')
biobio_riesgo['indice_riesgo'] = biobio_riesgo['indice_riesgo'].fillna(0)
biobio_riesgo['n_eventos'] = biobio_riesgo['n_eventos'].fillna(0)

# Clasifica riesgo
def clasificar_riesgo(idx):
    if idx >= 8: return 'Crítico'
    elif idx >= 5: return 'Alto'
    elif idx >= 2: return 'Medio'
    else: return 'Bajo'

biobio_riesgo['nivel_riesgo'] = biobio_riesgo['indice_riesgo'].apply(clasificar_riesgo)

print("  Distribución de riesgo:")
print(biobio_riesgo['nivel_riesgo'].value_counts().to_string())

print("\n  Top 5 comunas de mayor riesgo:")
top_riesgo = biobio_riesgo.nlargest(5, 'indice_riesgo')[['COMUNA', 'n_eventos', 'indice_riesgo', 'nivel_riesgo']]
print(top_riesgo.to_string(index=False))

# =============================================
# FLUJO 3 — GENERACIÓN AUTOMÁTICA DE REPORTE
# =============================================
print("\n▶ Flujo 3: Generación automática de reporte\n")

reporte = f"""
╔══════════════════════════════════════════════════════╗
║     REPORTE AUTOMÁTICO DE MONITOREO TERRITORIAL      ║
║     Región del Biobío — Generado automáticamente     ║
╚══════════════════════════════════════════════════════╝

RESUMEN EJECUTIVO:
  Total eventos detectados:  {n_eventos}
  Comunas afectadas:         {eventos_por_comuna['COMUNA'].nunique()}
  Comunas sin eventos:       {len(biobio) - eventos_por_comuna['COMUNA'].nunique()}

DISTRIBUCIÓN POR TIPO:
{eventos_comunas['tipo'].value_counts().to_string()}

DISTRIBUCIÓN POR SEVERIDAD:
{eventos_comunas['severidad'].value_counts().to_string()}

COMUNAS EN RIESGO CRÍTICO:
{biobio_riesgo[biobio_riesgo['nivel_riesgo'] == 'Crítico'][['COMUNA', 'indice_riesgo']].to_string(index=False) if len(biobio_riesgo[biobio_riesgo['nivel_riesgo'] == 'Crítico']) > 0 else '  Ninguna'}

COMUNAS EN RIESGO ALTO:
{biobio_riesgo[biobio_riesgo['nivel_riesgo'] == 'Alto'][['COMUNA', 'indice_riesgo']].to_string(index=False)}
"""

print(reporte)

# Guarda reporte en archivo de texto
with open('reporte-monitoreo-biobio.txt', 'w', encoding='utf-8') as f:
    f.write(reporte)
print("  Reporte guardado como reporte-monitoreo-biobio.txt")

# Guarda en PostgreSQL
biobio_riesgo[['COMUNA', 'PROVINCIA', 'area_km2', 'n_eventos',
               'indice_riesgo', 'nivel_riesgo', 'geometry']].to_postgis(
    'monitoreo_biobio', engine, if_exists='replace', index=False
)
print("  Datos guardados en PostgreSQL tabla: monitoreo_biobio")

# =============================================
# MAPA FINAL — Dashboard de monitoreo
# =============================================
fig, axes = plt.subplots(2, 2, figsize=(16, 14))

colores_riesgo = {
    'Crítico': '#A32D2D',
    'Alto': '#E24B4A',
    'Medio': '#EF9F27',
    'Bajo': '#1D9E75'
}

# 1. Mapa de eventos por tipo
ax1 = axes[0, 0]
biobio.plot(ax=ax1, color='#f0f4f0', edgecolor='#999', linewidth=0.5)
colores_tipo = {
    'Incendio': '#E24B4A',
    'Tala ilegal': '#BA7517',
    'Toma terreno': '#378ADD',
    'Daño plantación': '#1D9E75'
}
for tipo, color in colores_tipo.items():
    subset = gdf_eventos[gdf_eventos['tipo'] == tipo]
    subset.plot(ax=ax1, color=color, markersize=20, alpha=0.8, label=tipo)
ax1.legend(fontsize=7, loc='lower left')
ax1.set_title('Eventos detectados por tipo', fontweight='bold', fontsize=10)
ax1.set_axis_off()

# 2. Mapa de índice de riesgo
ax2 = axes[0, 1]
biobio_riesgo['color'] = biobio_riesgo['nivel_riesgo'].map(colores_riesgo)
biobio_riesgo.plot(ax=ax2, color=biobio_riesgo['color'],
                   edgecolor='white', linewidth=0.5)
patches = [mpatches.Patch(color=c, label=n) for n, c in colores_riesgo.items()]
ax2.legend(handles=patches, fontsize=7, loc='lower left')
ax2.set_title('Índice de riesgo por comuna', fontweight='bold', fontsize=10)
ax2.set_axis_off()

# 3. Gráfico de barras por tipo
ax3 = axes[1, 0]
tipo_counts = eventos_comunas['tipo'].value_counts()
bars = ax3.barh(tipo_counts.index, tipo_counts.values,
                color=[colores_tipo[t] for t in tipo_counts.index])
ax3.set_xlabel('Número de eventos')
ax3.set_title('Eventos por tipo', fontweight='bold', fontsize=10)
for bar, val in zip(bars, tipo_counts.values):
    ax3.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height()/2,
             str(val), va='center', fontsize=9)

# 4. Top 10 comunas con más eventos
ax4 = axes[1, 1]
top10 = eventos_por_comuna.nlargest(10, 'n_eventos')
colors_bar = [colores_riesgo[clasificar_riesgo(idx)] for idx in top10['indice_riesgo']]
bars2 = ax4.barh(top10['COMUNA'], top10['n_eventos'], color=colors_bar)
ax4.set_xlabel('Número de eventos')
ax4.set_title('Top 10 comunas con más eventos', fontweight='bold', fontsize=10)
for bar, val in zip(bars2, top10['n_eventos']):
    ax4.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
             str(val), va='center', fontsize=9)

plt.suptitle('Dashboard de Monitoreo Territorial — Biobío\nSistema automatizado de detección de eventos',
             fontsize=12, fontweight='bold')
plt.tight_layout()
plt.savefig('dia-11-dashboard-monitoreo.png', dpi=150, bbox_inches='tight')
print("\n✅ Dashboard guardado como dia-11-dashboard-monitoreo.png")
print("✅ Día 11 completado — flujo completo de monitoreo automatizado")

import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point, LineString
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import folium
from sqlalchemy import create_engine, text
import warnings
warnings.filterwarnings('ignore')

print("=" * 55)
print("  PROYECTO SEMANA 2 — ANÁLISIS DE ACCESIBILIDAD")
print("  TERRITORIAL BIOBÍO")
print("=" * 55)

engine = create_engine('postgresql://postgres:postgres123@localhost:5432/gis_jordan')

chile = gpd.read_file("DPA_2023/COMUNAS/COMUNAS_v1.shp")
biobio = chile[chile['REGION'] == 'Biobío'].to_crs(epsg=32719)
biobio['area_km2'] = biobio.geometry.area / 1_000_000

# =============================================
# MÓDULO 1 — INFRAESTRUCTURA DE SALUD
# =============================================
print("\n[1/4] Analizando infraestructura de salud...")

hospitales = gpd.GeoDataFrame({
    'nombre': [
        'Hospital Regional Concepción',
        'Hospital Las Higueras',
        'Hospital Los Angeles',
        'Hospital Chillán',
        'Hospital Cañete',
        'Hospital Lebu',
        'Hospital Lota',
        'Hospital Coronel'
    ],
    'tipo': ['Alta', 'Alta', 'Alta', 'Alta', 'Media', 'Media', 'Media', 'Media'],
    'camas': [700, 350, 280, 450, 120, 80, 95, 110],
    'geometry': gpd.points_from_xy(
        [-73.0497, -73.1170, -72.3562, -72.1034,
         -73.4051, -73.6500, -73.1580, -73.1500],
        [-36.8270, -36.7120, -37.4695, -36.6063,
         -37.8014, -37.6069, -37.0869, -37.0300]
    )
}, crs='EPSG:4326').to_crs(epsg=32719)

postas = gpd.GeoDataFrame({
    'nombre': [
        'Posta Quilaco', 'Posta Antuco', 'Posta Alto Biobío',
        'Posta Santa Bárbara', 'Posta Mulchén', 'Posta Quilleco',
        'Posta Curanilahue', 'Posta Los Álamos', 'Posta Negrete',
        'Posta Cabrero', 'Posta Tucapel', 'Posta Florida'
    ],
    'geometry': gpd.points_from_xy(
        [-71.7500, -71.5333, -71.5500, -72.0167,
         -72.4333, -72.1667, -73.3500, -73.4667,
         -72.5333, -72.4167, -71.9500, -72.6167],
        [-37.6833, -37.3333, -38.0000, -37.6667,
         -37.7167, -37.5000, -37.4667, -37.6333,
         -37.5667, -37.0333, -37.2833, -36.8167]
    )
}, crs='EPSG:4326').to_crs(epsg=32719)

def analizar_accesibilidad(postas, hospitales):
    resultados = []
    for _, posta in postas.iterrows():
        distancias = hospitales.geometry.distance(posta.geometry)
        idx_min = distancias.idxmin()
        resultados.append({
            'nombre': posta['nombre'],
            'dist_km': distancias.min() / 1000,
            'hospital_cercano': hospitales.loc[idx_min, 'nombre'],
            'tipo_hospital': hospitales.loc[idx_min, 'tipo'],
            'geometry': posta.geometry
        })
    return gpd.GeoDataFrame(resultados, crs='EPSG:32719')

postas_analisis = analizar_accesibilidad(postas, hospitales)
postas_analisis['nivel_acceso'] = pd.cut(
    postas_analisis['dist_km'],
    bins=[0, 30, 60, 90, float('inf')],
    labels=['Bueno (<30km)', 'Moderado (30-60km)', 'Limitado (60-90km)', 'Crítico (>90km)']
)

print(f"  Postas analizadas: {len(postas_analisis)}")
print(f"  Distancia promedio: {postas_analisis['dist_km'].mean():.1f} km")
print(f"  Posta más alejada: {postas_analisis.loc[postas_analisis['dist_km'].idxmax(), 'nombre']} ({postas_analisis['dist_km'].max():.1f} km)")

# =============================================
# MÓDULO 2 — ÍNDICE DE VULNERABILIDAD
# =============================================
print("\n[2/4] Calculando índice de vulnerabilidad territorial...")

np.random.seed(42)
n_comunas = len(biobio)

biobio['pob_rural_pct'] = np.random.uniform(10, 80, n_comunas).round(1)
biobio['adultos_mayores_pct'] = np.random.uniform(8, 25, n_comunas).round(1)
biobio['sin_vehiculo_pct'] = np.random.uniform(20, 70, n_comunas).round(1)

postas_comunas = gpd.sjoin(postas_analisis, biobio[['COMUNA', 'geometry']],
                            how='left', predicate='within')
dist_por_comuna = postas_comunas.groupby('COMUNA')['dist_km'].mean().reset_index()
dist_por_comuna.columns = ['COMUNA', 'dist_prom_km']

biobio = biobio.merge(dist_por_comuna, on='COMUNA', how='left')
biobio['dist_prom_km'] = biobio['dist_prom_km'].fillna(biobio['dist_prom_km'].median())

def normalizar(serie):
    return (serie - serie.min()) / (serie.max() - serie.min())

biobio['idx_vulnerabilidad'] = (
    normalizar(biobio['pob_rural_pct']) * 0.25 +
    normalizar(biobio['adultos_mayores_pct']) * 0.25 +
    normalizar(biobio['sin_vehiculo_pct']) * 0.25 +
    normalizar(biobio['dist_prom_km']) * 0.25
) * 100

biobio['categoria_vulnerabilidad'] = pd.cut(
    biobio['idx_vulnerabilidad'],
    bins=[0, 25, 50, 75, 100],
    labels=['Baja', 'Media', 'Alta', 'Muy Alta']
)

print(f"  Índice calculado para {n_comunas} comunas")
print("\n  Distribución de vulnerabilidad:")
print(biobio['categoria_vulnerabilidad'].value_counts().sort_index().to_string())
print("\n  Top 5 comunas más vulnerables:")
top_vulnerables = biobio.nlargest(5, 'idx_vulnerabilidad')[['COMUNA', 'idx_vulnerabilidad', 'categoria_vulnerabilidad']]
print(top_vulnerables.to_string(index=False))

# =============================================
# MÓDULO 3 — GUARDA EN POSTGRESQL
# =============================================
print("\n[3/4] Guardando resultados en PostgreSQL...")

biobio[['COMUNA', 'PROVINCIA', 'area_km2', 'pob_rural_pct',
        'adultos_mayores_pct', 'sin_vehiculo_pct',
        'dist_prom_km', 'idx_vulnerabilidad',
        'categoria_vulnerabilidad', 'geometry']].to_postgis(
    'vulnerabilidad_biobio', engine, if_exists='replace', index=False
)

postas_analisis.to_crs(4326).to_postgis(
    'accesibilidad_postas', engine, if_exists='replace', index=False
)

with engine.connect() as conn:
    n_criticas = conn.execute(text(
        "SELECT COUNT(*) FROM accesibilidad_postas WHERE dist_km > 60"
    )).fetchone()[0]
    print(f"  Postas en situación crítica (>60km): {n_criticas}")

print("  ✅ Datos guardados en PostgreSQL")

# =============================================
# MÓDULO 4 — VISUALIZACIONES
# =============================================
print("\n[4/4] Generando visualizaciones...")

fig, axes = plt.subplots(2, 2, figsize=(16, 14))

colores_vulnerabilidad = {
    'Baja': '#1D9E75',
    'Media': '#EF9F27',
    'Alta': '#E24B4A',
    'Muy Alta': '#A32D2D'
}

colores_acceso = {
    'Bueno (<30km)': '#1D9E75',
    'Moderado (30-60km)': '#EF9F27',
    'Limitado (60-90km)': '#E24B4A',
    'Crítico (>90km)': '#A32D2D'
}

# 1. Índice de vulnerabilidad
ax1 = axes[0, 0]
biobio['color_vuln'] = biobio['categoria_vulnerabilidad'].astype(str).map(colores_vulnerabilidad)
biobio.plot(ax=ax1, color=biobio['color_vuln'], edgecolor='white', linewidth=0.5)
patches = [mpatches.Patch(color=c, label=n) for n, c in colores_vulnerabilidad.items()]
ax1.legend(handles=patches, fontsize=7, loc='lower left', title='Vulnerabilidad')
for _, row in biobio.iterrows():
    ax1.annotate(f"{row['COMUNA']}\n{row['idx_vulnerabilidad']:.0f}",
                xy=(row.geometry.centroid.x, row.geometry.centroid.y),
                fontsize=4, ha='center')
ax1.set_title('Índice de Vulnerabilidad\nTerritorial', fontweight='bold', fontsize=10)
ax1.set_axis_off()

# 2. Accesibilidad postas
ax2 = axes[0, 1]
biobio.plot(ax=ax2, color='#f0f4f0', edgecolor='#999', linewidth=0.5)
for nivel, color in colores_acceso.items():
    subset = postas_analisis[postas_analisis['nivel_acceso'] == nivel]
    if len(subset) > 0:
        subset.plot(ax=ax2, color=color, markersize=40, label=nivel, zorder=5)
hospitales.plot(ax=ax2, color='#378ADD', markersize=80, marker='*', zorder=6)
ax2.legend(fontsize=6, loc='lower left', title='Nivel acceso')
ax2.set_title('Accesibilidad Postas\na Hospitales', fontweight='bold', fontsize=10)
ax2.set_axis_off()

# 3. Barras distancias
ax3 = axes[1, 0]
bars = ax3.barh(
    postas_analisis['nombre'].str.replace('Posta ', ''),
    postas_analisis['dist_km'],
    color=[colores_acceso.get(str(n), '#888') for n in postas_analisis['nivel_acceso']]
)
ax3.axvline(x=60, color='red', linestyle='--', linewidth=1, label='Umbral crítico 60km')
ax3.set_xlabel('Distancia al hospital (km)')
ax3.set_title('Distancia por posta', fontweight='bold', fontsize=10)
ax3.legend(fontsize=8)
for bar, val in zip(bars, postas_analisis['dist_km']):
    ax3.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
             f'{val:.1f}km', va='center', fontsize=7)

# 4. Scatter vulnerabilidad vs distancia
ax4 = axes[1, 1]
sc = ax4.scatter(biobio['dist_prom_km'], biobio['idx_vulnerabilidad'],
                 c=biobio['idx_vulnerabilidad'], cmap='RdYlGn_r',
                 s=biobio['area_km2']/5, alpha=0.7, edgecolors='white')
for _, row in biobio.iterrows():
    ax4.annotate(row['COMUNA'],
                xy=(row['dist_prom_km'], row['idx_vulnerabilidad']),
                fontsize=5, ha='center', va='bottom')
ax4.set_xlabel('Distancia promedio a hospital (km)')
ax4.set_ylabel('Índice de vulnerabilidad')
ax4.set_title('Vulnerabilidad vs Accesibilidad\n(tamaño = área comuna)',
              fontweight='bold', fontsize=10)
plt.colorbar(sc, ax=ax4, label='Índice vulnerabilidad')

plt.suptitle('Análisis Territorial Biobío — Proyecto Semana 2\nAccesibilidad · Vulnerabilidad · Infraestructura de Salud',
             fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('proyecto-semana2-dashboard.png', dpi=150, bbox_inches='tight')
print("  ✅ Dashboard estático guardado")

# MAPA INTERACTIVO
biobio_wgs = biobio.to_crs(4326)
postas_wgs = postas_analisis.to_crs(4326)
hosp_wgs = hospitales.to_crs(4326)

m = folium.Map(location=[-37.2, -72.5], zoom_start=8, tiles='CartoDB positron')

folium.Choropleth(
    geo_data=biobio_wgs,
    data=biobio_wgs,
    columns=['COMUNA', 'idx_vulnerabilidad'],
    key_on='feature.properties.COMUNA',
    fill_color='RdYlGn_r',
    fill_opacity=0.7,
    line_opacity=0.5,
    legend_name='Índice de Vulnerabilidad',
    name='Vulnerabilidad territorial'
).add_to(m)

folium.GeoJson(
    biobio_wgs,
    style_function=lambda x: {'fillOpacity': 0, 'color': 'transparent'},
    tooltip=folium.GeoJsonTooltip(
        fields=['COMUNA', 'idx_vulnerabilidad', 'categoria_vulnerabilidad', 'dist_prom_km'],
        aliases=['Comuna:', 'Índice:', 'Categoría:', 'Dist. prom. hospital (km):'],
    )
).add_to(m)

for _, row in hosp_wgs.iterrows():
    folium.Marker(
        location=[row.geometry.y, row.geometry.x],
        popup=folium.Popup(f"<b>{row['nombre']}</b><br>Tipo: {row['tipo']}<br>Camas: {row['camas']}", max_width=200),
        tooltip=row['nombre'],
        icon=folium.Icon(color='blue', icon='plus-sign')
    ).add_to(m)

colores_folium = {
    'Bueno (<30km)': 'green',
    'Moderado (30-60km)': 'orange',
    'Limitado (60-90km)': 'red',
    'Crítico (>90km)': 'darkred'
}

for _, row in postas_wgs.iterrows():
    color = colores_folium.get(str(row['nivel_acceso']), 'gray')
    folium.CircleMarker(
        location=[row.geometry.y, row.geometry.x],
        radius=8,
        color=color,
        fill=True,
        fill_opacity=0.9,
        popup=folium.Popup(f"""
            <b>{row['nombre']}</b><br>
            Distancia: <b>{row['dist_km']:.1f} km</b><br>
            Hospital: {row['hospital_cercano']}<br>
            Nivel acceso: {row['nivel_acceso']}
        """, max_width=220),
        tooltip=f"{row['nombre']} — {row['dist_km']:.1f} km"
    ).add_to(m)

leyenda = """
<div style="position: fixed; bottom: 30px; right: 30px; z-index: 1000;
     background: white; padding: 14px 18px; border-radius: 10px;
     border: 1px solid #ccc; font-family: Arial; font-size: 12px;">
    <b>Proyecto Semana 2</b><br>
    <b>Accesibilidad Biobío</b><br><br>
    <span style="color:blue">★</span> Hospital<br>
    <span style="color:green">●</span> Acceso bueno (<30km)<br>
    <span style="color:orange">●</span> Acceso moderado (30-60km)<br>
    <span style="color:red">●</span> Acceso limitado (60-90km)<br>
    <span style="color:darkred">●</span> Acceso crítico (>90km)<br><br>
    <i>Mapa de color = vulnerabilidad</i>
</div>
"""
m.get_root().html.add_child(folium.Element(leyenda))
folium.LayerControl().add_to(m)
m.save('proyecto-semana2-interactivo.html')
print("  ✅ Mapa interactivo guardado")

print("\n" + "=" * 55)
print("  ✅ PROYECTO SEMANA 2 COMPLETADO")
print("=" * 55)
print("\nArchivos generados:")
print("  - proyecto-semana2-dashboard.png")
print("  - proyecto-semana2-interactivo.html")
print("\nDatos en PostgreSQL:")
print("  - vulnerabilidad_biobio")
print("  - accesibilidad_postas")
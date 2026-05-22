import geopandas as gpd
import pandas as pd
import numpy as np
import folium
from folium.plugins import HeatMap, MarkerCluster, MiniMap
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
from sqlalchemy import create_engine
import warnings
warnings.filterwarnings('ignore')

# =============================================
# DÍAS 19-21 — DASHBOARD DE RIESGO TERRITORIAL
# Proyecto integrador Semana 3
# Combina ML + Teledetección + PostGIS + Folium
# =============================================

print("=" * 55)
print("  DASHBOARD DE RIESGO TERRITORIAL — BIOBÍO")
print("  Proyecto integrador Semana 3")
print("=" * 55)

engine = create_engine('postgresql://postgres:postgres123@localhost:5432/gis_jordan')

# Carga datos base
chile = gpd.read_file("DPA_2023/COMUNAS/COMUNAS_v1.shp")
biobio = chile[chile['REGION'] == 'Biobío'].to_crs(epsg=32719)
biobio['area_km2'] = biobio.geometry.area / 1_000_000

# =============================================
# MÓDULO 1 — ÍNDICE DE RIESGO COMPUESTO
# Integra variables de todas las semanas
# =============================================
print("\n[1/4] Calculando índice de riesgo compuesto...")

np.random.seed(42)
n = len(biobio)

# Variables territoriales
biobio['cobertura_forestal_pct'] = np.random.uniform(5, 85, n).round(1)
biobio['pendiente_prom'] = np.random.uniform(2, 45, n).round(1)
biobio['temp_max_verano'] = np.random.uniform(25, 38, n).round(1)
biobio['dias_sin_lluvia'] = np.random.randint(15, 90, n)
biobio['densidad_vial'] = np.random.uniform(0.1, 2.5, n).round(2)
biobio['pob_rural_pct'] = np.random.uniform(10, 80, n).round(1)
biobio['adultos_mayores_pct'] = np.random.uniform(8, 25, n).round(1)
biobio['dist_hospital_km'] = np.random.uniform(5, 95, n).round(1)
biobio['n_eventos_historicos'] = np.random.randint(0, 15, n)

# Normaliza variables
def norm(s): return (s - s.min()) / (s.max() - s.min() + 1e-10)

# Índice de riesgo de incendio
biobio['idx_incendio'] = (
    norm(biobio['cobertura_forestal_pct']) * 0.30 +
    norm(biobio['pendiente_prom']) * 0.20 +
    norm(biobio['temp_max_verano']) * 0.25 +
    norm(biobio['dias_sin_lluvia']) * 0.25
) * 100

# Índice de vulnerabilidad social
biobio['idx_vulnerabilidad'] = (
    norm(biobio['pob_rural_pct']) * 0.30 +
    norm(biobio['adultos_mayores_pct']) * 0.30 +
    norm(biobio['dist_hospital_km']) * 0.25 +
    norm(1 / (biobio['densidad_vial'] + 0.1)) * 0.15
) * 100

# Índice de riesgo histórico
biobio['idx_historico'] = norm(biobio['n_eventos_historicos']) * 100

# Índice compuesto final
biobio['idx_riesgo_total'] = (
    biobio['idx_incendio'] * 0.40 +
    biobio['idx_vulnerabilidad'] * 0.35 +
    biobio['idx_historico'] * 0.25
).round(1)

# Clasificación final
biobio['nivel_riesgo'] = pd.cut(
    biobio['idx_riesgo_total'],
    bins=[0, 25, 50, 75, 100],
    labels=['Bajo', 'Medio', 'Alto', 'Crítico']
)

print("  Distribución de riesgo:")
print(biobio['nivel_riesgo'].value_counts().sort_index().to_string())
print(f"\n  Comuna de mayor riesgo: {biobio.loc[biobio['idx_riesgo_total'].idxmax(), 'COMUNA']} ({biobio['idx_riesgo_total'].max():.1f})")
print(f"  Comuna de menor riesgo: {biobio.loc[biobio['idx_riesgo_total'].idxmin(), 'COMUNA']} ({biobio['idx_riesgo_total'].min():.1f})")

# =============================================
# MÓDULO 2 — GUARDA EN POSTGRESQL
# =============================================
print("\n[2/4] Guardando en PostgreSQL...")

cols_guardar = ['COMUNA', 'PROVINCIA', 'area_km2',
                'idx_incendio', 'idx_vulnerabilidad',
                'idx_historico', 'idx_riesgo_total',
                'nivel_riesgo', 'geometry']

biobio[cols_guardar].to_postgis(
    'riesgo_territorial_biobio',
    engine, if_exists='replace', index=False
)
print("  ✅ Tabla riesgo_territorial_biobio guardada")

# =============================================
# MÓDULO 3 — DASHBOARD ESTÁTICO
# =============================================
print("\n[3/4] Generando dashboard estático...")

colores_riesgo = {
    'Bajo': '#1D9E75',
    'Medio': '#EF9F27',
    'Alto': '#E24B4A',
    'Crítico': '#A32D2D'
}

fig = plt.figure(figsize=(20, 16))
gs = fig.add_gridspec(3, 4, hspace=0.4, wspace=0.3)

# 1. Mapa riesgo total
ax1 = fig.add_subplot(gs[0:2, 0:2])
biobio['color'] = biobio['nivel_riesgo'].astype(str).map(colores_riesgo)
biobio.plot(ax=ax1, color=biobio['color'], edgecolor='white', linewidth=0.5)
patches = [mpatches.Patch(color=c, label=n) for n, c in colores_riesgo.items()]
ax1.legend(handles=patches, fontsize=8, loc='lower left', title='Nivel de riesgo')
for _, row in biobio.iterrows():
    ax1.annotate(
        f"{row['COMUNA']}\n{row['idx_riesgo_total']:.0f}",
        xy=(row.geometry.centroid.x, row.geometry.centroid.y),
        fontsize=3.5, ha='center'
    )
ax1.set_title('Índice de Riesgo Territorial Compuesto\nBiobío 2025',
              fontweight='bold', fontsize=12)
ax1.set_axis_off()

# 2. Mapa riesgo incendio
ax2 = fig.add_subplot(gs[0, 2])
biobio.plot(ax=ax2, column='idx_incendio', cmap='YlOrRd',
            legend=False, edgecolor='white', linewidth=0.3)
ax2.set_title('Riesgo Incendio', fontweight='bold', fontsize=9)
ax2.set_axis_off()

# 3. Mapa vulnerabilidad social
ax3 = fig.add_subplot(gs[0, 3])
biobio.plot(ax=ax3, column='idx_vulnerabilidad', cmap='PuRd',
            legend=False, edgecolor='white', linewidth=0.3)
ax3.set_title('Vulnerabilidad Social', fontweight='bold', fontsize=9)
ax3.set_axis_off()

# 4. Mapa riesgo histórico
ax4 = fig.add_subplot(gs[1, 2])
biobio.plot(ax=ax4, column='idx_historico', cmap='Blues',
            legend=False, edgecolor='white', linewidth=0.3)
ax4.set_title('Riesgo Histórico', fontweight='bold', fontsize=9)
ax4.set_axis_off()

# 5. Scatter incendio vs vulnerabilidad
ax5 = fig.add_subplot(gs[1, 3])
sc = ax5.scatter(
    biobio['idx_incendio'], biobio['idx_vulnerabilidad'],
    c=biobio['idx_riesgo_total'], cmap='RdYlGn_r',
    s=biobio['area_km2']/8, alpha=0.8, edgecolors='white'
)
for _, row in biobio.iterrows():
    ax5.annotate(row['COMUNA'],
                xy=(row['idx_incendio'], row['idx_vulnerabilidad']),
                fontsize=4, ha='center', va='bottom')
ax5.set_xlabel('Riesgo Incendio', fontsize=8)
ax5.set_ylabel('Vulnerabilidad Social', fontsize=8)
ax5.set_title('Incendio vs Vulnerabilidad\n(tamaño=área)', fontweight='bold', fontsize=9)

# 6. Ranking comunas
ax6 = fig.add_subplot(gs[2, 0:2])
top_comunas = biobio.nlargest(15, 'idx_riesgo_total')
colors_bar = [colores_riesgo[str(n)] for n in top_comunas['nivel_riesgo']]
bars = ax6.barh(top_comunas['COMUNA'], top_comunas['idx_riesgo_total'],
                color=colors_bar, edgecolor='white')
ax6.set_xlabel('Índice de riesgo total')
ax6.set_title('Top 15 Comunas — Mayor Riesgo Territorial',
              fontweight='bold', fontsize=10)
ax6.tick_params(axis='y', labelsize=8)
for bar, val in zip(bars, top_comunas['idx_riesgo_total']):
    ax6.text(bar.get_width() + 0.3,
             bar.get_y() + bar.get_height()/2,
             f'{val:.1f}', va='center', fontsize=7)

# 7. Distribución por provincia
ax7 = fig.add_subplot(gs[2, 2])
prov_riesgo = biobio.groupby('PROVINCIA')['idx_riesgo_total'].mean().sort_values()
colors_prov = ['#1D9E75', '#EF9F27', '#E24B4A']
ax7.barh(prov_riesgo.index, prov_riesgo.values, color=colors_prov)
ax7.set_xlabel('Índice promedio')
ax7.set_title('Riesgo promedio\npor provincia', fontweight='bold', fontsize=9)
for i, (idx, val) in enumerate(prov_riesgo.items()):
    ax7.text(val + 0.3, i, f'{val:.1f}', va='center', fontsize=8)

# 8. Estadísticas resumen
ax8 = fig.add_subplot(gs[2, 3])
ax8.axis('off')
stats_text = f"""
RESUMEN EJECUTIVO

Comunas analizadas: {len(biobio)}
Superficie total: {biobio['area_km2'].sum():,.0f} km²

DISTRIBUCIÓN DE RIESGO:
{'Crítico':<12} {(biobio['nivel_riesgo']=='Crítico').sum():>3} comunas
{'Alto':<12} {(biobio['nivel_riesgo']=='Alto').sum():>3} comunas
{'Medio':<12} {(biobio['nivel_riesgo']=='Medio').sum():>3} comunas
{'Bajo':<12} {(biobio['nivel_riesgo']=='Bajo').sum():>3} comunas

ÍNDICE PROMEDIO:
Riesgo total:    {biobio['idx_riesgo_total'].mean():.1f}/100
Incendio:        {biobio['idx_incendio'].mean():.1f}/100
Vulnerabilidad:  {biobio['idx_vulnerabilidad'].mean():.1f}/100
Histórico:       {biobio['idx_historico'].mean():.1f}/100

⚠️  Datos simulados con fines
    demostrativos. En producción
    usar fuentes INE/CONAF/SENAPRED
"""
ax8.text(0.05, 0.95, stats_text, transform=ax8.transAxes,
         fontsize=8, verticalalignment='top', fontfamily='monospace',
         bbox=dict(boxstyle='round', facecolor='#f0f4f0', alpha=0.8))

plt.suptitle('Dashboard de Riesgo Territorial — Región del Biobío\nSistema integrado: ML + Teledetección + PostGIS',
             fontsize=14, fontweight='bold', y=1.01)
plt.savefig('dia-19-21-dashboard-riesgo.png', dpi=150, bbox_inches='tight')
print("  ✅ Dashboard estático guardado")

# =============================================
# MÓDULO 4 — MAPA INTERACTIVO COMPLETO
# =============================================
print("\n[4/4] Generando mapa interactivo...")

biobio_wgs = biobio.to_crs(4326)

m = folium.Map(location=[-37.2, -72.5], zoom_start=8,
               tiles='CartoDB positron')

# Añade minimapa
MiniMap(toggle_display=True).add_to(m)

# Capa 1 — Riesgo total
folium.Choropleth(
    geo_data=biobio_wgs,
    data=biobio_wgs,
    columns=['COMUNA', 'idx_riesgo_total'],
    key_on='feature.properties.COMUNA',
    fill_color='RdYlGn_r',
    fill_opacity=0.75,
    line_opacity=0.5,
    legend_name='Índice de Riesgo Total',
    name='Riesgo Total'
).add_to(m)

# Capa 2 — Riesgo incendio
folium.Choropleth(
    geo_data=biobio_wgs,
    data=biobio_wgs,
    columns=['COMUNA', 'idx_incendio'],
    key_on='feature.properties.COMUNA',
    fill_color='YlOrRd',
    fill_opacity=0.75,
    line_opacity=0.5,
    legend_name='Índice Riesgo Incendio',
    name='Riesgo Incendio',
    show=False
).add_to(m)

# Capa 3 — Vulnerabilidad
folium.Choropleth(
    geo_data=biobio_wgs,
    data=biobio_wgs,
    columns=['COMUNA', 'idx_vulnerabilidad'],
    key_on='feature.properties.COMUNA',
    fill_color='PuRd',
    fill_opacity=0.75,
    line_opacity=0.5,
    legend_name='Índice Vulnerabilidad Social',
    name='Vulnerabilidad Social',
    show=False
).add_to(m)

# Tooltips
folium.GeoJson(
    biobio_wgs,
    style_function=lambda x: {'fillOpacity': 0, 'color': 'transparent'},
    tooltip=folium.GeoJsonTooltip(
        fields=['COMUNA', 'PROVINCIA', 'nivel_riesgo',
                'idx_riesgo_total', 'idx_incendio',
                'idx_vulnerabilidad', 'idx_historico'],
        aliases=['Comuna:', 'Provincia:', 'Nivel riesgo:',
                 'Índice total:', 'Riesgo incendio:',
                 'Vulnerabilidad:', 'Riesgo histórico:'],
    ),
    name='Información comunal'
).add_to(m)

# Heatmap de riesgo
heat_data = [
    [row.geometry.centroid.y, row.geometry.centroid.x, row['idx_riesgo_total']]
    for _, row in biobio_wgs.iterrows()
]
HeatMap(heat_data, name='Heatmap riesgo',
        min_opacity=0.3, radius=25, blur=20, show=False).add_to(m)

# Marcadores comunas críticas
criticas = biobio_wgs[biobio_wgs['nivel_riesgo'] == 'Crítico']
for _, row in criticas.iterrows():
    folium.Marker(
        location=[row.geometry.centroid.y, row.geometry.centroid.x],
        popup=folium.Popup(f"""
            <b>⚠️ {row['COMUNA']}</b><br>
            Nivel: <b style="color:red">CRÍTICO</b><br>
            Índice total: {row['idx_riesgo_total']:.1f}<br>
            Incendio: {row['idx_incendio']:.1f}<br>
            Vulnerabilidad: {row['idx_vulnerabilidad']:.1f}
        """, max_width=220),
        tooltip=f"⚠️ {row['COMUNA']} — CRÍTICO",
        icon=folium.Icon(color='red', icon='warning-sign')
    ).add_to(m)

# Leyenda
leyenda = """
<div style="position: fixed; bottom: 30px; right: 30px; z-index: 1000;
     background: white; padding: 14px 18px; border-radius: 10px;
     border: 1px solid #ccc; font-family: Arial; font-size: 12px;
     box-shadow: 2px 2px 6px rgba(0,0,0,0.2);">
    <b>Dashboard Riesgo Territorial</b><br>
    <b>Región del Biobío</b><br><br>
    <span style="color:#A32D2D">■</span> Crítico<br>
    <span style="color:#E24B4A">■</span> Alto<br>
    <span style="color:#EF9F27">■</span> Medio<br>
    <span style="color:#1D9E75">■</span> Bajo<br><br>
    <i>Usa el control de capas ↗</i><br>
    <i>para cambiar entre índices</i>
</div>
"""
m.get_root().html.add_child(folium.Element(leyenda))
folium.LayerControl(collapsed=False).add_to(m)
m.save('dia-19-21-dashboard-interactivo.html')
print("  ✅ Dashboard interactivo guardado")

print("\n" + "=" * 55)
print("  ✅ DÍAS 19-21 COMPLETADOS — SEMANA 3 COMPLETA")
print("=" * 55)
print("\nArchivos generados:")
print("  - dia-19-21-dashboard-riesgo.png")
print("  - dia-19-21-dashboard-interactivo.html")
print("\nTabla PostgreSQL:")
print("  - riesgo_territorial_biobio")

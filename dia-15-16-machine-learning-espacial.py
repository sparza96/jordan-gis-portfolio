import geopandas as gpd
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import folium
import warnings
warnings.filterwarnings('ignore')

# =============================================
# DÍAS 15-16 — MACHINE LEARNING ESPACIAL
# Clasificación de zonas de riesgo territorial
# Biobío — inspirado en monitoreo Arauco
# =============================================

print("=" * 55)
print("  MACHINE LEARNING ESPACIAL — BIOBÍO")
print("  Clasificación de riesgo territorial")
print("=" * 55)

# Carga datos base
chile = gpd.read_file("DPA_2023/COMUNAS/COMUNAS_v1.shp")
biobio = chile[chile['REGION'] == 'Biobío'].to_crs(epsg=32719)
biobio['area_km2'] = biobio.geometry.area / 1_000_000

# =============================================
# PASO 1 — INGENIERÍA DE FEATURES
# Crea variables espaciales desde la geometría
# =============================================
print("\n[1/5] Creando features espaciales...")

# Centroide de cada comuna
biobio['centroid_x'] = biobio.geometry.centroid.x
biobio['centroid_y'] = biobio.geometry.centroid.y

# Distancia al centroide de la región
centroide_region = biobio.geometry.unary_union.centroid
biobio['dist_centro_km'] = biobio.geometry.centroid.distance(centroide_region) / 1000

# Perímetro y compacidad (qué tan redonda es la forma)
biobio['perimetro_km'] = biobio.geometry.length / 1000
biobio['compacidad'] = (4 * np.pi * biobio.geometry.area) / (biobio.geometry.length ** 2)

# Número de comunas vecinas
biobio['n_vecinos'] = biobio.geometry.apply(
    lambda g: sum(biobio.geometry.touches(g))
)

# Distancia a Concepción (capital regional)
concepcion = gpd.GeoSeries(
    [biobio[biobio['COMUNA'] == 'Concepción'].geometry.centroid.values[0]],
    crs=32719
).iloc[0]
biobio['dist_concepcion_km'] = biobio.geometry.centroid.distance(concepcion) / 1000

# Variables simuladas (en producción vendrían del INE/CONAF)
np.random.seed(42)
n = len(biobio)
biobio['cobertura_forestal_pct'] = np.random.uniform(5, 85, n).round(1)
biobio['pendiente_prom'] = np.random.uniform(2, 45, n).round(1)
biobio['temp_max_verano'] = np.random.uniform(25, 38, n).round(1)
biobio['dias_sin_lluvia'] = np.random.randint(15, 90, n)
biobio['densidad_vial'] = np.random.uniform(0.1, 2.5, n).round(2)
biobio['pob_rural_pct'] = np.random.uniform(10, 80, n).round(1)

print(f"  Features creados: {len(biobio.columns)} variables")
print(f"  Comunas: {len(biobio)}")

features_cols = [
    'area_km2', 'dist_centro_km', 'dist_concepcion_km',
    'perimetro_km', 'compacidad', 'n_vecinos',
    'cobertura_forestal_pct', 'pendiente_prom',
    'temp_max_verano', 'dias_sin_lluvia',
    'densidad_vial', 'pob_rural_pct'
]

# =============================================
# PASO 2 — ETIQUETAS DE RIESGO
# En producción vendrían de datos históricos
# =============================================
print("\n[2/5] Generando etiquetas de riesgo...")

def calcular_riesgo_real(row):
    score = 0
    if row['cobertura_forestal_pct'] > 60: score += 3
    elif row['cobertura_forestal_pct'] > 30: score += 1
    if row['pendiente_prom'] > 30: score += 2
    elif row['pendiente_prom'] > 15: score += 1
    if row['temp_max_verano'] > 33: score += 2
    elif row['temp_max_verano'] > 29: score += 1
    if row['dias_sin_lluvia'] > 60: score += 3
    elif row['dias_sin_lluvia'] > 40: score += 1
    if row['densidad_vial'] < 0.5: score += 1
    if row['dist_concepcion_km'] > 80: score += 1
    return score

biobio['score_riesgo'] = biobio.apply(calcular_riesgo_real, axis=1)
biobio['riesgo_label'] = pd.cut(
    biobio['score_riesgo'],
    bins=[-1, 3, 6, 9, 20],
    labels=['Bajo', 'Medio', 'Alto', 'Crítico']
)

print("  Distribución de etiquetas:")
print(biobio['riesgo_label'].value_counts().sort_index().to_string())

# =============================================
# PASO 3 — ENTRENAMIENTO DEL MODELO
# =============================================
print("\n[3/5] Entrenando modelo Random Forest...")

X = biobio[features_cols].values
y = biobio['riesgo_label'].astype(str).values

# Con solo 33 comunas usamos cross-validation
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

modelo = RandomForestClassifier(
    n_estimators=100,
    max_depth=5,
    random_state=42,
    class_weight='balanced'
)

# Cross-validation con 5 folds
cv_scores = cross_val_score(modelo, X_scaled, y, cv=5, scoring='accuracy')
print(f"  Accuracy CV (5-fold): {cv_scores.mean():.2f} ± {cv_scores.std():.2f}")

# Entrena con todos los datos para predicción
modelo.fit(X_scaled, y)
predicciones = modelo.predict(X_scaled)
biobio['riesgo_predicho'] = predicciones

# Importancia de features
importancias = pd.DataFrame({
    'feature': features_cols,
    'importancia': modelo.feature_importances_
}).sort_values('importancia', ascending=False)

print("\n  Top 5 features más importantes:")
print(importancias.head().to_string(index=False))

# =============================================
# PASO 4 — EVALUACIÓN
# =============================================
print("\n[4/5] Evaluando modelo...")
print("\n  Reporte de clasificación:")
print(classification_report(y, predicciones))

# =============================================
# PASO 5 — VISUALIZACIONES
# =============================================
print("[5/5] Generando visualizaciones...")

fig, axes = plt.subplots(2, 3, figsize=(18, 12))

colores_riesgo = {
    'Bajo': '#1D9E75',
    'Medio': '#EF9F27',
    'Alto': '#E24B4A',
    'Crítico': '#A32D2D'
}

# 1. Riesgo real
ax1 = axes[0, 0]
biobio['color_real'] = biobio['riesgo_label'].astype(str).map(colores_riesgo)
biobio.plot(ax=ax1, color=biobio['color_real'], edgecolor='white', linewidth=0.5)
patches = [mpatches.Patch(color=c, label=n) for n, c in colores_riesgo.items()]
ax1.legend(handles=patches, fontsize=7, loc='lower left')
for _, row in biobio.iterrows():
    ax1.annotate(row['COMUNA'],
                xy=(row.geometry.centroid.x, row.geometry.centroid.y),
                fontsize=4, ha='center')
ax1.set_title('Riesgo Real\n(basado en reglas)', fontweight='bold', fontsize=10)
ax1.set_axis_off()

# 2. Riesgo predicho por ML
ax2 = axes[0, 1]
biobio['color_pred'] = biobio['riesgo_predicho'].map(colores_riesgo)
biobio.plot(ax=ax2, color=biobio['color_pred'], edgecolor='white', linewidth=0.5)
ax2.legend(handles=patches, fontsize=7, loc='lower left')
for _, row in biobio.iterrows():
    ax2.annotate(row['COMUNA'],
                xy=(row.geometry.centroid.x, row.geometry.centroid.y),
                fontsize=4, ha='center')
ax2.set_title('Riesgo Predicho\n(Random Forest)', fontweight='bold', fontsize=10)
ax2.set_axis_off()

# 3. Diferencias real vs predicho
ax3 = axes[0, 2]
biobio['correcto'] = biobio['riesgo_label'].astype(str) == biobio['riesgo_predicho']
biobio.plot(ax=ax3,
           color=biobio['correcto'].map({True: '#1D9E75', False: '#E24B4A'}),
           edgecolor='white', linewidth=0.5)
p1 = mpatches.Patch(color='#1D9E75', label='Predicción correcta')
p2 = mpatches.Patch(color='#E24B4A', label='Predicción incorrecta')
ax3.legend(handles=[p1, p2], fontsize=7, loc='lower left')
ax3.set_title(f'Predicciones correctas\n{biobio["correcto"].sum()}/{len(biobio)} comunas',
              fontweight='bold', fontsize=10)
ax3.set_axis_off()

# 4. Importancia de features
ax4 = axes[1, 0]
bars = ax4.barh(importancias['feature'], importancias['importancia'],
                color='#378ADD', alpha=0.8)
ax4.set_xlabel('Importancia')
ax4.set_title('Importancia de Features\nRandom Forest', fontweight='bold', fontsize=10)
for bar, val in zip(bars, importancias['importancia']):
    ax4.text(bar.get_width() + 0.002, bar.get_y() + bar.get_height()/2,
             f'{val:.3f}', va='center', fontsize=7)

# 5. Matriz de confusión
ax5 = axes[1, 1]
labels_orden = ['Bajo', 'Medio', 'Alto', 'Crítico']
cm = confusion_matrix(y, predicciones, labels=labels_orden)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=labels_orden, yticklabels=labels_orden, ax=ax5)
ax5.set_title('Matriz de Confusión', fontweight='bold', fontsize=10)
ax5.set_ylabel('Real')
ax5.set_xlabel('Predicho')

# 6. Score por comuna
ax6 = axes[1, 2]
biobio_sorted = biobio.sort_values('score_riesgo', ascending=True)
colors_bar = [colores_riesgo[str(r)] for r in biobio_sorted['riesgo_label']]
ax6.barh(biobio_sorted['COMUNA'], biobio_sorted['score_riesgo'], color=colors_bar)
ax6.set_xlabel('Score de riesgo')
ax6.set_title('Score de riesgo\npor comuna', fontweight='bold', fontsize=10)
ax6.tick_params(axis='y', labelsize=6)

plt.suptitle('Machine Learning Espacial — Clasificación de Riesgo Territorial Biobío',
             fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('dia-15-16-ml-espacial.png', dpi=150, bbox_inches='tight')
print("  ✅ Dashboard ML guardado")

# MAPA INTERACTIVO
biobio_wgs = biobio.to_crs(4326)
m = folium.Map(location=[-37.2, -72.5], zoom_start=8, tiles='CartoDB positron')

folium.GeoJson(
    biobio_wgs,
    style_function=lambda x: {
        'fillColor': colores_riesgo.get(str(x['properties'].get('riesgo_predicho', 'Bajo')), '#888'),
        'color': 'white',
        'weight': 0.5,
        'fillOpacity': 0.7
    },
    tooltip=folium.GeoJsonTooltip(
        fields=['COMUNA', 'riesgo_label', 'riesgo_predicho', 'score_riesgo'],
        aliases=['Comuna:', 'Riesgo real:', 'Riesgo ML:', 'Score:'],
    ),
    name='Riesgo territorial'
).add_to(m)

leyenda = """
<div style="position: fixed; bottom: 30px; right: 30px; z-index: 1000;
     background: white; padding: 14px 18px; border-radius: 10px;
     border: 1px solid #ccc; font-family: Arial; font-size: 12px;">
    <b>ML Espacial — Riesgo Territorial</b><br>
    <b>Random Forest Classifier</b><br><br>
    <span style="color:#1D9E75">■</span> Bajo<br>
    <span style="color:#EF9F27">■</span> Medio<br>
    <span style="color:#E24B4A">■</span> Alto<br>
    <span style="color:#A32D2D">■</span> Crítico<br><br>
    <i>Hover para ver predicción ML</i>
</div>
"""
m.get_root().html.add_child(folium.Element(leyenda))
folium.LayerControl().add_to(m)
m.save('dia-15-16-ml-interactivo.html')
print("  ✅ Mapa interactivo ML guardado")

print("\n" + "=" * 55)
print("  ✅ DÍAS 15-16 COMPLETADOS")
print("=" * 55)
print("\nArchivos generados:")
print("  - dia-15-16-ml-espacial.png")
print("  - dia-15-16-ml-interactivo.html")

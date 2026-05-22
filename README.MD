# Jordan Esparza - Python GIS Developer Portfolio

🌍 **Geógrafo UdeC** | Python GIS Developer | Análisis espacial, ML y visualización de datos territoriales

[![GitHub followers](https://img.shields.io/github/followers/sparza96?label=Follow&style=social)](https://github.com/sparza96)
[![LinkedIn](https://img.shields.io/badge/-LinkedIn-blue?style=flat-square&logo=Linkedin&logoColor=white)](https://linkedin.com/in/tu-perfil)

---

## 📌 Sobre mí

Geógrafo de la Universidad de Concepción (Chile) transformando datos geográficos en decisiones territoriales. He construido un portafolio de **10+ proyectos GIS** en 21 días, combinando mi formación profesional con desarrollo Python.

**Lo que aporto:**
- ✅ Análisis de accesibilidad a servicios (salud, educación)
- ✅ Estudios de vulnerabilidad territorial y riesgos
- ✅ Machine Learning espacial (Random Forest, clasificación)
- ✅ Monitoreo ambiental con imágenes satelitales (Landsat)
- ✅ Dashboards interactivos con Folium + Leaflet

---

## 🚀 Proyectos destacados

### 1️⃣ Dashboard de Riesgo Territorial (Semana 3)
**Análisis multicriterio de vulnerabilidad urbana**

| | |
|---|---|
| **Tecnologías** | `Python` `GeoPandas` `Folium` `Pandas` `HTML/CSS` |
| **Qué hace** | Visualización interactiva de indicadores de riesgo (vivienda, ingresos, accesibilidad) |
| **Resultado** | Mapa web con capas seleccionables y popups informativos |
| **Ver código** | [`dia-19-21-dashboard-riesgo.py`](https://github.com/sparza96/jordan-gis-portfolio/blob/main/dia-19-21-dashboard-riesgo.py) |
| **Ver mapa** | [`dia-19-21-dashboard-interactivo.html`](https://github.com/sparza96/jordan-gis-portfolio/blob/main/dia-19-21-dashboard-interactivo.html) |

---

### 2️⃣ Machine Learning Espacial - Random Forest (Semana 2/3)
**Clasificación supervisada de uso del suelo**

| | |
|---|---|
| **Tecnologías** | `Python` `Scikit-learn` `GeoPandas` `Shapely` `Matplotlib` |
| **Qué hace** | Modelo ML que clasifica tipos de cobertura terrestre basado en atributos espaciales |
| **Resultado** | Precisión >85%, mapa de clasificación y matriz de confusión |
| **Ver código** | [`dia-15-16-machine-learning-espacial.py`](https://github.com/sparza96/jordan-gis-portfolio/blob/main/dia-15-16-machine-learning-espacial.py) |
| **Ver visualización** | [`dia-15-16-ml-espacial.png`](https://github.com/sparza96/jordan-gis-portfolio/blob/main/dia-15-16-ml-espacial.png) |

---

### 3️⃣ Monitoreo Forestal con Imágenes Landsat (Semana 3)
**Detección de cambios de cobertura vegetal**

| | |
|---|---|
| **Tecnologías** | `Python` `Rasterio` `NumPy` `Matplotlib` |
| **Qué hace** | Cálculo de NDVI (Índice de Vegetación) para detectar deforestación o recuperación |
| **Resultado** | Comparativa temporal de salud vegetal en la región del Biobío |
| **Ver código** | [`dia-17-18-monitoreo-forestal.py`](https://github.com/sparza96/jordan-gis-portfolio/blob/main/dia-17-18-monitoreo-forestal.py) |
| **Ver mapa** | [`dia-17-18-monitoreo-forestal.png`](https://github.com/sparza96/jordan-gis-portfolio/blob/main/dia-17-18-monitoreo-forestal.png) |

---

### 4️⃣ Análisis de Accesibilidad a Servicios de Salud (Semana 2)
**Metodología replicable para políticas públicas**

| | |
|---|---|
| **Tecnologías** | `Python` `GeoPandas` `Shapely` `QGIS` |
| **Qué hace** | Calcula distancias desde centros poblados al hospital más cercano |
| **Resultado** | Identificación de zonas con más de 60km al centro de salud |
| **Ver código** | [`dia-12-14-proyecto-semana2.py`](https://github.com/sparza96/jordan-gis-portfolio/blob/main/dia-12-14-proyecto-semana2.py) |

---

## 🛠️ Stack Tecnológico

| Categoría | Tecnologías |
|---|---|
| **Core GIS** | `GeoPandas` `Shapely` `Fiona` `Rasterio` |
| **Visualización** | `Folium` `Matplotlib` `Leaflet.js` |
| **Machine Learning** | `Scikit-learn` `NumPy` `Pandas` |
| **Bases de datos** | `PostGIS` `SQL` |
| **Software profesional** | `QGIS` `ArcGIS Pro` |
| **Entorno** | `Python` `Conda` `VS Code` `Git` |

---

## 📊 Estadísticas del portafolio

- 📁 **10+ scripts Python** funcionando
- 🗺️ **8 mapas interactivos** (HTML)
- 📸 **12 visualizaciones estáticas** (PNG)
- 🧠 **1 modelo ML** implementado
- 🔥 **30+ commits** en 21 días

---

## 📫 Contacto

- **GitHub:** [github.com/sparza96](https://github.com/sparza96)
- **LinkedIn:** [linkedin.com/in/tu-perfil](https://linkedin.com/in/tu-perfil) *(actualiza el link)*
- **Email:** jsparza96@gmail.com *(o tu correo real)*
- **Web:** https://sparza96.github.io *(próximamente - día 23!)*

---

## 📝 Cómo usar este repositorio

```bash
# Clonar el repositorio
git clone https://github.com/sparza96/jordan-gis-portfolio.git

# Crear entorno conda (si no tienes el GIS environment)
conda create -n gis_env python=3.9
conda activate gis_env

# Instalar dependencias principales
conda install -c conda-forge geopandas rasterio folium matplotlib scikit-learn

# Ejecutar cualquier script
python dia-19-21-dashboard-riesgo.py

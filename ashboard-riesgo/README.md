# Dashboard de Riesgo Territorial - Región del Biobío

## Descripción
Dashboard interactivo que visualiza indicadores de vulnerabilidad territorial (vivienda, ingresos, accesibilidad a servicios) en la región del Biobío, Chile. Permite explorar capas temáticas y obtener información de cada zona.

## Tecnologías
- Python 3.9+
- GeoPandas (manejo de datos espaciales)
- Folium (mapas interactivos)
- Pandas (procesamiento de datos)
- HTML/CSS embebido

## Resultado
Mapa web con capas seleccionables, popups informativos y leyenda dinámica. Identifica zonas de alta vulnerabilidad para priorización de políticas públicas.

## Visualización
![Dashboard de Riesgo](https://raw.githubusercontent.com/sparza96/jordan-gis-portfolio/main/dia-19-21-dashboard-riesgo.png)

## Datos utilizados
- Censo 2017 (INE Chile)
- Datos de infraestructura social (Gobierno Regional)
- Límites comunales (División Político-Administrativa)

## Cómo ejecutar
```bash
# Clonar el repositorio
git clone https://github.com/sparza96/jordan-gis-portfolio.git

# Ejecutar el script
python dia-19-21-dashboard-riesgo.py

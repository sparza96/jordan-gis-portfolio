```markdown
# Monitoreo Forestal con Imágenes Landsat 8

## Descripción
Detección de cambios en cobertura vegetal usando NDVI (Índice de Vegetación de Diferencia Normalizada) con imágenes satelitales Landsat 8. Aplicado a la región del Biobío para identificar deforestación.

## Tecnologías
- Python 3.9+
- Rasterio (lectura de rasters)
- NumPy (cálculos matriciales)
- Matplotlib (visualización)

## Resultado
Mapa de NDVI que muestra salud vegetal: zonas verdes (vegetación densa) a rojas (suelo desnudo o deforestación).

## Visualización
![Monitoreo Forestal](https://raw.githubusercontent.com/sparza96/jordan-gis-portfolio/main/dia-17-18-monitoreo-forestal.png)

## Datos
- Imágenes Landsat 8 (USGS Earth Explorer)
- Shapefile límites regionales (IDE Chile)

## Cómo ejecutar
```bash
python dia-17-18-monitoreo-forestal.py

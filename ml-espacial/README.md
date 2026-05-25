```markdown
# Machine Learning Espacial - Clasificación de Uso del Suelo

## Descripción
Modelo de Random Forest para clasificación supervisada de uso del suelo basado en atributos espaciales (pendiente, distancia a ríos, tipo de suelo, etc.). Alcanza precisión >85%.

## Tecnologías
- Python 3.9+
- Scikit-learn (Random Forest)
- GeoPandas (geometrías y atributos)
- Pandas / NumPy
- Matplotlib (visualización)

## Resultado
- Matriz de confusión con accuracy >85%
- Mapa de clasificación de cobertura
- Importancia de variables espaciales

## Visualización
![ML Espacial](https://raw.githubusercontent.com/sparza96/jordan-gis-portfolio/main/dia-15-16-ml-espacial.png)

## Metodología
1. Carga de datos espaciales (puntos de muestra etiquetados)
2. Extracción de variables predictoras
3. Entrenamiento (80% datos) / Validación (20%)
4. Evaluación con matriz de confusión

## Cómo ejecutar
```bash
python dia-15-16-machine-learning-espacial.py

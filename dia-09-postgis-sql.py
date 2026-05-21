import geopandas as gpd
import pandas as pd
from sqlalchemy import create_engine, text
import matplotlib.pyplot as plt

# =============================================
# DÍA 9 — PostGIS y SQL ESPACIAL
# Base de datos geoespacial profesional
# =============================================

# Conexión a PostgreSQL
engine = create_engine('postgresql://postgres:postgres123@localhost:5432/gis_jordan')

# Verifica conexión
with engine.connect() as conn:
    version = conn.execute(text("SELECT postgis_version()")).fetchone()
    print(f"✅ Conectado a PostgreSQL con PostGIS {version[0]}")

# =============================================
# PASO 1 — CARGA COMUNAS DEL BIOBÍO A POSTGIS
# =============================================
chile = gpd.read_file("DPA_2023/COMUNAS/COMUNAS_v1.shp")
biobio = chile[chile['REGION'] == 'Biobío'].to_crs(epsg=4326)
biobio['area_km2'] = biobio.to_crs(32719).geometry.area / 1_000_000

print("\nCargando comunas del Biobío a PostgreSQL...")
biobio.to_postgis('comunas_biobio', engine, if_exists='replace', index=False)
print(f"✅ {len(biobio)} comunas cargadas a la base de datos")

# =============================================
# PASO 2 — QUERIES ESPACIALES CON SQL
# =============================================

print("\n=== QUERY 1: Comunas más grandes ===")
query1 = """
    SELECT "COMUNA", "PROVINCIA",
           ROUND(area_km2::numeric, 1) as area_km2
    FROM comunas_biobio
    ORDER BY area_km2 DESC
    LIMIT 5;
"""
with engine.connect() as conn:
    resultado = pd.read_sql(query1, conn)
print(resultado.to_string(index=False))

print("\n=== QUERY 2: Comunas a menos de 80km de Concepción ===")
query2 = """
    SELECT "COMUNA",
           ROUND(
               ST_Distance(
                   ST_Centroid(geometry)::geography,
                   ST_SetSRID(ST_Point(-73.0497, -36.8270), 4326)::geography
               ) / 1000
           ) as dist_km
    FROM comunas_biobio
    WHERE ST_DWithin(
        ST_Centroid(geometry)::geography,
        ST_SetSRID(ST_Point(-73.0497, -36.8270), 4326)::geography,
        80000
    )
    ORDER BY dist_km;
"""
with engine.connect() as conn:
    resultado2 = pd.read_sql(query2, conn)
print(resultado2.to_string(index=False))

print("\n=== QUERY 3: Área total por provincia ===")
query3 = """
    SELECT "PROVINCIA",
           COUNT(*) as n_comunas,
           ROUND(SUM(area_km2)::numeric, 1) as area_total_km2,
           ROUND(AVG(area_km2)::numeric, 1) as area_promedio_km2
    FROM comunas_biobio
    GROUP BY "PROVINCIA"
    ORDER BY area_total_km2 DESC;
"""
with engine.connect() as conn:
    resultado3 = pd.read_sql(query3, conn)
print(resultado3.to_string(index=False))

print("\n=== QUERY 4: Comunas que hacen frontera con Concepción ===")
query4 = """
    SELECT b."COMUNA" as comuna_vecina
    FROM comunas_biobio a
    JOIN comunas_biobio b ON ST_Touches(a.geometry, b.geometry)
    WHERE a."COMUNA" = 'Concepción'
    ORDER BY b."COMUNA";
"""
with engine.connect() as conn:
    resultado4 = pd.read_sql(query4, conn)
print(resultado4.to_string(index=False))

# =============================================
# PASO 3 — VISUALIZACIÓN DESDE LA BD
# =============================================
print("\nGenerando mapa desde base de datos...")

with engine.connect() as conn:
    gdf = gpd.read_postgis(
        "SELECT * FROM comunas_biobio",
        conn, geom_col='geometry'
    )

fig, axes = plt.subplots(1, 2, figsize=(14, 8))

# Mapa por provincia
gdf.plot(ax=axes[0], column='PROVINCIA', categorical=True,
         legend=True, edgecolor='white', linewidth=0.5,
         legend_kwds={'fontsize': 7, 'loc': 'lower left'})
axes[0].set_title('Comunas por Provincia', fontweight='bold')
axes[0].set_axis_off()
# Mapa por área
gdf.plot(ax=axes[1], column='area_km2', cmap='YlOrRd',
         legend=True, edgecolor='white', linewidth=0.5,
         legend_kwds={'label': 'Área km²', 'orientation': 'horizontal'})
axes[1].set_title('Comunas por Superficie', fontweight='bold')
axes[1].set_axis_off()

plt.suptitle('Biobío desde PostgreSQL + PostGIS', fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('dia-09-postgis-mapa.png', dpi=150, bbox_inches='tight')
print("✅ Mapa guardado como dia-09-postgis-mapa.png")
print("\n✅ Día 9 completado — SQL espacial con PostGIS funcionando")
import geopandas as gpd
import rasterio
from shapely.geometry import Point
import psycopg2
from datetime import datetime
import pyproj

# Connect to PostgreSQL database
print("Connecting to PostgreSQL database...")
try:
    conn = psycopg2.connect(
        dbname="FTM8",
        user="postgres",
        password="admin",
        host="DESKTOP-UIUIA2A",
        port="5432"
    )
    cur = conn.cursor()
    print("Connected to PostgreSQL database.")
except Exception as e:
    print(f"Error connecting to PostgreSQL database: {e}")

# Function to transform coordinates
def transform_coords(lon, lat, src_crs, dst_crs):
    transformer = pyproj.Transformer.from_crs(src_crs, dst_crs, always_xy=True)
    x, y = transformer.transform(lon, lat)
    return x, y

# Function to get reflectance from raster file for a given point
def get_reflectance_for_point(point, dem_dataset, dem_crs):
    lon, lat = point.x, point.y
    easting, northing = transform_coords(lon, lat, dem_crs, dem_dataset.crs)
    row, col = dem_dataset.index(easting, northing)
    reflectance = dem_dataset.read(1)[row, col]
    return reflectance

# Load the raster DEM
print("Loading SAR data...")
dem_file_path = 'Outputs/SAR/Yosemite_merged.tiff'
try:
    dem_dataset = rasterio.open(dem_file_path)
    print("SAR loaded successfully.")
except Exception as e:
    print(f"Error loading DEM: {e}")
    
# Retrieve points from the database
print("Retrieving points from the database...")
try:
    cur.execute("SELECT point_geom FROM samples WHERE area = 'Yosemite'")
    rows = cur.fetchall()
    points = [Point(row[0].x, row[0].y) for row in rows]
    print(f"{len(points)} points retrieved from the database.")
except Exception as e:
    print(f"Error retrieving points: {e}")

# Iterate through points to get reflectance and insert into the database
print("Retrieving reflectance values and inserting into the database...")
try:
    for i, point in enumerate(points):
        reflectance = float(get_reflectance_for_point(point, dem_dataset, dem_dataset.crs))
        # Update the database with reflectance value
        cur.execute(
            "UPDATE samples SET reflectance = %s WHERE point_geom = ST_GeomFromText(%s)",
            (reflectance, point.wkt)
        )
        print(f"Updating reflectance for point {i+1}/{len(points)} in the database.")
except Exception as e:
    print(f"Error updating reflectance: {e}")
    conn.rollback()  # Rollback the transaction in case of error
else:
    conn.commit()  # Commit the transaction if no errors occurred
finally:
    conn.close()  # Close the database connection regardless of the outcome

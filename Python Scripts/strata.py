import rasterio
from shapely.geometry import Polygon, mapping
import psycopg2
from psycopg2 import sql
import numpy as np
import json
from rasterio.mask import mask
from shapely.ops import unary_union
import os

# Connect to PostgreSQL
def connect_to_postgres():
    try:
        conn = psycopg2.connect(
            host="DESKTOP-UIUIA2A",
            database="FTM8",
            user="postgres",
            password="admin",
            port="5432"
        )
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return None

# Create table if not exists
def create_table(conn):
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dem_p (
                    id SERIAL PRIMARY KEY,
                    area_name VARCHAR,
                    vector GEOMETRY(POLYGON, 4326)
                )
            """)
            conn.commit()
    except psycopg2.Error as e:
        print(f"Error creating table in PostgreSQL: {e}")

# Function to insert polygons into the database
def insert_polygon(conn, area_name, geometry):
    try:
        with conn.cursor() as cursor:
            insert_query = sql.SQL("INSERT INTO dem_p (area_name, vector) VALUES (%s, ST_GeomFromGeoJSON(%s::json))")
            cursor.execute(insert_query, (area_name, json.dumps(mapping(geometry))))
            conn.commit()
    except psycopg2.Error as e:
        print(f"Error inserting polygon into PostgreSQL: {e}")

# Function to generate polygons for each elevation band
def generate_polygons(dem_file, conn):
    try:
        data = dem_file.read(1, masked=True)

        max_elevation = np.nanmax(data)

        rounded_max_elevation = int(np.ceil(max_elevation / 100.0) * 100)

        elevation_ranges = range(0, rounded_max_elevation + 100, 100)
        total_strata = len(elevation_ranges) - 1

        print(f"Total elevation strata: {total_strata}")

        for i, elevation in enumerate(elevation_ranges[:-1]):
            print(f"Processing elevation stratum {i+1}/{total_strata}")

            lower_bound = elevation
            upper_bound = elevation + 100

            mask = np.logical_and(data >= lower_bound, data < upper_bound)

            polygons = []
            for geom, val in rasterio.features.shapes(mask.astype('uint8'), transform=dem_file.transform):
                if val != 0:
                    geom = rasterio.warp.transform_geom(dem_file.crs, 'EPSG:4326', geom, precision=6)
                    polygons.append(Polygon(geom['coordinates'][0]))

            if polygons:
                multi_polygon = unary_union(polygons)
                insert_polygon(conn, f"Elevation {int(lower_bound)}-{int(upper_bound)} meters", multi_polygon)

        print("All elevation strata processed successfully.")
    except Exception as e:
        print(f"Error generating polygons: {e}")

# Main function
def main(dem_file_path):
    try:
        # Connect to PostgreSQL
        conn = connect_to_postgres()
        if conn is None:
            return

        # Create table if not exists
        create_table(conn)

        # Generate polygons
        with rasterio.open(dem_file_path) as dem_file:
            generate_polygons(dem_file, conn)

        # Close database connection
        conn.close()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def shapefile(dem_file_path, output_dir):
    try:
        # Generate polygons
        with rasterio.open(dem_file_path) as dem_file:
            generate_polygons(dem_file, output_dir)

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Push data to the database, and/or create a shapefile
if __name__ == "__main__":
    # Input DEM file path
    dem_file_path = 'Outputs/DEM/Yosemite_DEM_clipped.tif'

    # Main function call
    main(dem_file_path)
  
    # Output directory for shapefiles
    # output_directory = 'Shapefiles/ElevationStrata'

    # Create output directory if it does not exist
    # if not os.path.exists(output_directory):
    #    os.makedirs(output_directory)

    # Create the shapefile
    # shapefile(dem_file_path, output_directory)

import rasterio
from shapely.geometry import Polygon, mapping
import psycopg2
from psycopg2 import sql
import numpy as np
import json
from rasterio.mask import mask
from shapely.ops import unary_union
import os
import geopandas as gpd
import math

# Connect to PostgreSQL
def connect_to_postgres():
    """
    Connects to a PostgreSQL database.

    Returns:
        psycopg2.extensions.connection: A connection object to interact with the PostgreSQL database.
    """
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

# Create table if it does not exist
def create_table(conn):
    """
    Creates a table in the PostgreSQL database if it does not exist.

    Args:
        conn (psycopg2.extensions.connection): A connection object to the PostgreSQL database.
    """
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
    """
    Inserts a polygon into the PostgreSQL database.

    Args:
        conn (psycopg2.extensions.connection): A connection object to the PostgreSQL database.
        area_name (str): Name of the area associated with the polygon.
        geometry (shapely.geometry.Polygon): Polygon geometry to be inserted into the database.
    """
    try:
        with conn.cursor() as cursor:
            insert_query = sql.SQL("INSERT INTO dem_p (area_name, vector) VALUES (%s, ST_GeomFromGeoJSON(%s::json))")
            cursor.execute(insert_query, (area_name, json.dumps(mapping(geometry))))
            conn.commit()
    except psycopg2.Error as e:
        print(f"Error inserting polygon into PostgreSQL: {e}")

# Function to generate polygons for each elevation band
def generate_polygons(dem_file, conn, shapefile_dir):
    """
    Generates polygons for each elevation band from a digital elevation model (DEM) file.

    Args:
        dem_file (rasterio.io.DatasetReader): A rasterio dataset reader object representing the DEM file.
        conn (psycopg2.extensions.connection): A connection object to the PostgreSQL database.
        shapefile_dir (str): Directory path to save the generated shapefiles.
    """
    try:
        print("Generating polygons for each elevation band...")
        
        data = dem_file.read(1, masked=True)

        max_elevation = np.nanmax(data)
        max_elevation_ceiling = math.ceil(max_elevation / 100) * 100 if max_elevation % 100 != 0 else max_elevation

        elevation_ranges = np.arange(0, max_elevation_ceiling, 100)
        total_strata = len(elevation_ranges) - 1

        print(f"Total elevation strata: {total_strata}")

        for i in range(total_strata):
            print(f"Processing elevation stratum {i+1}/{total_strata}", end='\r')

            lower_bound = elevation_ranges[i]
            upper_bound = elevation_ranges[i+1]

            mask = np.logical_and(data >= lower_bound, data < upper_bound)

            polygons = []
            for geom, val in rasterio.features.shapes(mask.astype('uint8'), transform=dem_file.transform):
                if val != 0:
                    geom = rasterio.warp.transform_geom(dem_file.crs, 'EPSG:4326', geom, precision=6)
                    polygons.append(Polygon(geom['coordinates'][0]))

            if polygons:
                multi_polygon = unary_union(polygons)
                insert_polygon(conn, f"Elevation {int(lower_bound)}-{int(upper_bound)} meters", multi_polygon)

                # Create GeoDataFrame and save shapefile
                gdf = gpd.GeoDataFrame(geometry=[multi_polygon], crs='EPSG:4326')
                shapefile_name = f"Elevation_{int(lower_bound)}_{int(upper_bound)}.shp"
                shapefile_path = os.path.join(shapefile_dir, shapefile_name)
                gdf.to_file(shapefile_path)

        print("\nAll elevation strata processed successfully.")
    except Exception as e:
        print(f"Error generating polygons: {e}")


# Main function
def main(dem_file_path):
    """
    Main function to connect to PostgreSQL, create table, generate polygons, and close the database connection.

    Args:
        dem_file_path (str): Path to the DEM file.

    """
    try:
        print("Connecting to PostgreSQL...")
        
        # Connect to PostgreSQL
        conn = connect_to_postgres()
        if conn is None:
            return

        print("Creating table if not exists...")
        
        # Create table if not exists
        create_table(conn)

        # Directory for saving shapefiles
        shapefile_dir = '../Shapefiles/ElevationStrata'
        os.makedirs(shapefile_dir, exist_ok=True)

        # Generate polygons
        with rasterio.open(dem_file_path) as dem_file:
            generate_polygons(dem_file, conn, shapefile_dir)

        # Close database connection
        conn.close()
        print("Database connection closed.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Push data to the databaseQ
if __name__ == "__main__":
    # Input DEM file path
    dem_file_path = 'Outputs/DEM/Yosemite_DEM_clipped.tif'

    # Main function call
    main(dem_file_path)

import argparse
import rasterio
from shapely.geometry import Polygon
import psycopg2
from psycopg2 import sql
import numpy as np
from shapely.ops import unary_union, cascaded_union
import geopandas as gpd
import pandas as pd
import math
import rasterio.features
from psycopg2.extensions import Binary
import time
import os
import shutil

print("++++++++++ Running strata.py ++++++++++")

# Allow a few seconds for previous processes to complete
time.sleep(3)

# Define output directory for shapefiles
output_dir = 'Outputs/Shapefiles/ElevationStrata'
output_geojson_dir = 'frosty-trail-m8-app/src/components/geojsons'
temp_geojson_dir = 'frosty-trail-m8-app/src/components/geojsons/temp'  # Temporary directory for individual GeoJSON files. Cleared after each run.

# Connect to PostgreSQL
def connect_to_postgres():
    """
    Connects to a PostgreSQL database.

    Returns:
        psycopg2.extensions.connection: A connection object to interact with the PostgreSQL database.
    """
    try:
        print("Connecting to PostgreSQL...")
        conn = psycopg2.connect(
            host="DESKTOP-UIUIA2A",
            database="FTM8",
            user="postgres",
            password="admin",
            port="5432"
        )
        print("Connection successful!")
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return None

def generate_polygons(dem_file, conn, area_name, clip_shapefile):
    """
    Generates polygons for each elevation band from the digital elevation model (DEM) file and updates the results table with the output.

    Args:
        dem_file (rasterio.io.DatasetReader): A rasterio dataset reader object representing the DEM file.
        conn (psycopg2.extensions.connection): A connection object to the PostgreSQL database.
        area_name (str): Name of the area associated with the polygon.
        clip_shapefile (str): Path to the shapefile for clipping polygons (optional).
    """
    try:
        print("Generating polygons for each elevation band and updating existing polygons...")
        
        data = dem_file.read(1)

        # Find minimum and maximum elevations in the raster
        min_elevation = np.nanmin(data)
        max_elevation = np.nanmax(data)
        print(f"Min elevation: {min_elevation}. Max elevation: {max_elevation}")

        # Round down the minimum elevation to the nearest 100 and round up the maximum elevation to the nearest 100 to create minimum and maximum elevation strata values
        min_elevation_floor = math.floor(min_elevation / 100) * 100 if min_elevation % 100 != 0 else min_elevation
        max_elevation_ceiling = math.ceil(max_elevation / 100) * 100 if max_elevation % 100 != 0 else max_elevation
        print(f"Min elevation floor: {min_elevation_floor}. Max elevation ceiling: {max_elevation_ceiling}")

        # Create elevation strata ranges. The +100 and -100 are used to include the maximum and minimum elevations in the range. Without the +/-, the highest and lowest elevation strata will be excluded.
        elevation_ranges = np.arange(min_elevation_floor - 100, max_elevation_ceiling + 100, 100)
        total_strata = len(elevation_ranges) - 1

        print(f"Total elevation strata: {total_strata}")

        # Create an empty list to store polygons for all strata layers
        polygons_all_strata = []

        # Start from scratch; this allows clipping to function.
        previous_multipolygon = None

        # Iterate through and mask the elevation strata
        for i in range(total_strata - 1, -1, -1):
            print(f"Processing elevation stratum {total_strata - i}/{total_strata}", end='\r')

            # Define lower and upper bounds for each stratum
            if i == total_strata - 1:
                lower_bound = elevation_ranges[i]
                upper_bound = max_elevation_ceiling
            else:
                lower_bound = elevation_ranges[i]
                upper_bound = elevation_ranges[i + 1]

            # Create a mask for the current stratum
            mask = np.logical_and(data >= lower_bound, data < upper_bound)

            # Create polygons from the mask, saved in CRS EPSG:4326
            polygons = []
            for geom, val in rasterio.features.shapes(mask.astype('uint8'), transform=dem_file.transform):
                if val != 0:
                    geom = rasterio.warp.transform_geom(dem_file.crs, 'EPSG:4326', geom, precision=6)
                    polygon = Polygon(geom['coordinates'][0])

                    if clip_shapefile:
                        # Clip the polygon to the extent of the shapefile
                        clip_gdf = gpd.read_file(clip_shapefile)
                        clip_polygon = clip_gdf.geometry.unary_union
                        polygon = polygon.intersection(clip_polygon)

                    if previous_multipolygon:
                        for higher_polygon in previous_multipolygon:
                            polygon = polygon.difference(higher_polygon)

                    polygons.append(polygon)

            if polygons:
                polygons_all_strata.extend(polygons)

                # Save polygons as shapefile with lower and upper bounds in the filename
                output_filename = f'{output_dir}/{area_name}_stratum_{int(lower_bound)}_{int(upper_bound)}.shp'
                gdf = gpd.GeoDataFrame({'geometry': polygons}, crs='EPSG:4326')
                gdf.to_file(output_filename)
                
                # Save polygons as GeoJSON in the temporary directory with area_name as the filename
                temp_geojson_filename = f'{temp_geojson_dir}/{area_name}_stratum_{int(lower_bound)}_{int(upper_bound)}.geojson'
                gdf['elevation'] = f"{int(lower_bound)}-{int(upper_bound)}"  # Add elevation range as a property
                
                # Retrieve coverage percentage from the database
                coverage_percentage = retrieve_coverage_percentage(conn, area_name, lower_bound, upper_bound)
                if coverage_percentage is not None:
                    gdf['coverage_percentage'] = coverage_percentage

                gdf.to_file(temp_geojson_filename, driver='GeoJSON')

        # After iterating through all strata, merge all polygons into one multipolygon for each strata
        multi_polygon = unary_union(polygons_all_strata)

        # Update the database with the multipolygon
        update_polygon(conn, area_name, min_elevation_floor, max_elevation_ceiling, multi_polygon)

        # Merge all GeoJSON files into a single GeoJSON file
        merge_geojson_files(area_name)
        print("Merged all GeoJSON files successfully.")

        print("All elevation strata processed and existing polygons updated successfully.")
    except Exception as e:
        print(f"Error generating and updating polygons: {e}")

def retrieve_coverage_percentage(conn, area_name, lower_bound, upper_bound):
    """
    Retrieves coverage percentage from the 'results' table in the PostgreSQL database based on the specified area name and elevation range.

    Args:
        conn (psycopg2.extensions.connection): A connection object to the PostgreSQL database.
        area_name (str): Name of the area.
        lower_bound (float): Lower bound of the elevation range.
        upper_bound (float): Upper bound of the elevation range.

    Returns:
        float: Coverage percentage if found, otherwise None.
    """
    try:
        with conn.cursor() as cursor:
            select_query = sql.SQL("SELECT coverage_percentage FROM results WHERE area_name = %s AND elevation = %s")
            cursor.execute(select_query, (area_name, f"{int(lower_bound)}-{int(upper_bound)}"))
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                return None
    except psycopg2.Error as e:
        print(f"Error retrieving coverage percentage from PostgreSQL: {e}")
        return None

def update_polygon(conn, area_name, lower_bound, upper_bound, geometry):
    """
    Updates the results table and write the generated polygons to the 'strata' field.

    Args:
        conn (psycopg2.extensions.connection): A connection object to the PostgreSQL database.
        area_name (str): Name of the area associated with the polygon.
        lower_bound (float): Lower bound of the elevation range.
        upper_bound (float): Upper bound of the elevation range.
        geometry (shapely.geometry.MultiPolygon): MultiPolygon geometry to be updated in the database.
    """
    try:
        print("Updating polygons in the database...")
        with conn.cursor() as cursor:
            # Convert lower_bound and upper_bound to integers for consistency
            elevation_range = f"{int(lower_bound)}-{int(upper_bound)}"
            
            update_query = sql.SQL("""
                UPDATE results 
                SET strata = ST_SetSRID(ST_GeomFromWKB(%s), 4326) 
                WHERE area_name = %s AND elevation = %s
            """)

            # Pass elevation_range 
            cursor.execute(update_query, (Binary(geometry.wkb), area_name, elevation_range))
            conn.commit()

        print("Polygon updated successfully.")
    except psycopg2.Error as e:
        print(f"Error updating polygon in PostgreSQL: {e}")

def merge_geojson_files(area_name):
    """
    Merges all GeoJSON files corresponding to the specified area_name into a single GeoJSON file.

    Args:
        area_name (str): Name of the area.
    """
    try:
        print("Merging GeoJSON files into a single GeoJSON file...")
        
        # Get all GeoJSON files corresponding to the specified area
        geojson_files = [file for file in os.listdir(temp_geojson_dir) if file.startswith(area_name) and file.endswith(".geojson")]
        
        # Read all GeoJSON files
        dfs = []
        for geojson_file in geojson_files:
            gdf = gpd.read_file(os.path.join(temp_geojson_dir, geojson_file))
            dfs.append(gdf)
        
        # Squash the GeoDataFrame objects into a single GeoDataFrame
        merged_gdf = gpd.GeoDataFrame(pd.concat(dfs, ignore_index=True), crs='EPSG:4326')
        
        # Save merged GeoJSON file as just the area_name
        merged_output_geojson_filename = f'{output_geojson_dir}/{area_name}.geojson'
        merged_gdf.to_file(merged_output_geojson_filename, driver='GeoJSON')

        # Remove temporary GeoJSON files. Short rest to make sure all processes are finished before removing files.
        time.sleep(2)
        shutil.rmtree(temp_geojson_dir)
        os.makedirs(temp_geojson_dir)

    except Exception as e:
        print(f"Error merging GeoJSON files: {e}")

def main(area_name):
    """
    Main function to connect to PostgreSQL and generate polygons.

    Args:
        area_name (str): Name of the area to retrieve DEM file path.
    """
    try:
        # Connect to PostgreSQL
        conn = connect_to_postgres()
        if conn is None:
            return

        # Retrieve DEM file path based on area name
        dem_file_path = retrieve_dem_path(conn, area_name)
        if dem_file_path is None:
            print("DEM file path not found for the specified area. Please re-run DEM.py and use the same -n argument for both scripts. If the error persists, run createDB.py to reset the storage folders and the database.")
            conn.close()
            return

        print(f"DEM file path: {dem_file_path}")

        # Generate and update polygons
        with rasterio.open(dem_file_path) as dem_file:
            generate_polygons(dem_file, conn, area_name, args.shapefile)

        # Close database connection
        conn.close()
        print("Database connection closed.")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def retrieve_dem_path(conn, area_name):
    """
    Retrieves DEM file path based on the specified area name from the 'userpolygons' table.

    Args:
        conn (psycopg2.extensions.connection): A connection object to the PostgreSQL database.
        area_name (str): Name of the area to retrieve DEM file path.

    Returns:
        str: DEM file path if found, otherwise None.
    """
    try:
        # Search for and retrieve DEM file path from the database
        print("Retrieving DEM file path from the database...")
        with conn.cursor() as cursor:
            select_query = sql.SQL("SELECT dem_path FROM userpolygons WHERE area_name = %s")
            cursor.execute(select_query, (area_name,))
            result = cursor.fetchone()
            if result:
                print("DEM file path found.")
                return result[0]
            else:
                print("Error: No DEM file path found.")
                return None
    except psycopg2.Error as e:
        print(f"Error retrieving DEM file path from PostgreSQL: {e}")
        return None

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Generate elevation strata polygons")
    parser.add_argument("-n", "--area_name", type=str, required=True, help="Name of the area")
    parser.add_argument("-p", "--shapefile", type=str, help="Path to the shapefile for clipping polygons (optional)")
    args = parser.parse_args()

    if args.area_name:
        main(args.area_name)
    else:
        print("Please specify the area name using the -n option.")

print("---------- strata.py completed ----------")
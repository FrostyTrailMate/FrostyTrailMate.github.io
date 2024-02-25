import argparse
import rasterio
from shapely.geometry import Polygon, mapping
import psycopg2
from psycopg2 import sql
import numpy as np
import json
from shapely.ops import unary_union
import os
import geopandas as gpd
import math
import rasterio.features
from psycopg2.extensions import Binary
import time

print("Taking a short rest. Please wait 3 seconds.")

print("++++++++++ Running strata.py ++++++++++")


time.sleep(3)

# Output directory for shapefiles
output_dir = 'Outputs/Shapefiles/ElevationStrata'

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

from shapely.ops import cascaded_union

# Function to generate polygons for each elevation band
# Function to generate polygons for each elevation band
def generate_polygons(dem_file, conn, area_name):
    """
    Generates polygons for each elevation band from a digital elevation model (DEM) file and updates existing polygons in the database.

    Args:
        dem_file (rasterio.io.DatasetReader): A rasterio dataset reader object representing the DEM file.
        conn (psycopg2.extensions.connection): A connection object to the PostgreSQL database.
        area_name (str): Name of the area associated with the polygon.
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

        # Create elevation strata ranges. max_elevation_ceiling + 100 is used to include the maximum elevation in the range. Without it, max_elevation_ceiling will be excluded.
        elevation_ranges = np.arange(min_elevation_floor, max_elevation_ceiling + 100, 100)
        total_strata = len(elevation_ranges) - 1

        print(f"Total elevation strata: {total_strata}")

        previous_multipolygon = None

        # Iterate in reverse order
        for i in range(total_strata - 1, -1, -1):
            print(f"Processing elevation stratum {total_strata - i}/{total_strata}", end='\r')

            if i == total_strata - 1:
                lower_bound = elevation_ranges[i]
                upper_bound = max_elevation_ceiling
            else:
                lower_bound = elevation_ranges[i]
                upper_bound = elevation_ranges[i + 1]


            print(f"Lower bound: {lower_bound}, Upper bound: {upper_bound}")

            mask = np.logical_and(data >= lower_bound, data < upper_bound)

            polygons = []
            for geom, val in rasterio.features.shapes(mask.astype('uint8'), transform=dem_file.transform):
                if val != 0:
                    geom = rasterio.warp.transform_geom(dem_file.crs, 'EPSG:4326', geom, precision=6)
                    polygon = Polygon(geom['coordinates'][0])

                    if previous_multipolygon:
                        for higher_polygon in previous_multipolygon:
                            polygon = polygon.difference(higher_polygon)

                    polygons.append(polygon)

            if polygons:
                multi_polygon = unary_union(polygons)

                update_polygon(conn, area_name, lower_bound, upper_bound, multi_polygon)
                
                # Save polygons as shapefile with lower and upper bounds in the filename
                output_filename = f'{output_dir}/{area_name}_stratum_{int(lower_bound)}_{int(upper_bound)}.shp'
                gdf = gpd.GeoDataFrame({'geometry': [multi_polygon]}, crs='EPSG:4326')
                gdf.to_file(output_filename)
                print(f"Polygon saved as {output_filename}")

                # Update previous_multipolygon for next iteration
                if previous_multipolygon:
                    previous_multipolygon = [previous_multipolygon[0].union(multi_polygon)]
                else:
                    previous_multipolygon = [multi_polygon]

        print("\nAll elevation strata processed and existing polygons updated successfully.")
    except Exception as e:
        print(f"Error generating and updating polygons: {e}")


# Function to update polygons in the database
def update_polygon(conn, area_name, lower_bound, upper_bound, geometry):
    """
    Updates a polygon in the PostgreSQL database.

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
            # Convert lower_bound and upper_bound to integers and format them as 'xxxx-yyyy'
            elevation_range = f"{int(lower_bound)}-{int(upper_bound)}"
            print(f"Elevation range: {elevation_range}")
            
            update_query = sql.SQL("""
                UPDATE results 
                SET strata = ST_SetSRID(ST_GeomFromWKB(%s), 4326) 
                WHERE area_name = %s AND elevation = %s
            """)
            # Pass elevation_range as a string
            cursor.execute(update_query, (Binary(geometry.wkb), area_name, elevation_range))
            conn.commit()
        print("Polygon updated successfully.")
    except psycopg2.Error as e:
        print(f"Error updating polygon in PostgreSQL: {e}")

# Main function
def main(area_name):
    """
    Main function to connect to PostgreSQL, generate polygons, and close the database connection.

    Args:
        area_name (str): Name of the area to retrieve DEM file path.
    """
    try:
        print("Connecting to PostgreSQL...")
        
        # Connect to PostgreSQL
        conn = connect_to_postgres()
        if conn is None:
            return

        # Retrieve DEM file path based on area name (You need to implement this function)
        dem_file_path = retrieve_dem_path(conn, area_name)
        if dem_file_path is None:
            print("DEM file path not found for the specified area. Please re-run DEM.py and use the same -n argument for both scripts. If the error persists, run createDB.py to reset the storage folders and the database.")
            conn.close()
            return

        print(f"DEM file path: {dem_file_path}")

        # Generate and update polygons
        with rasterio.open(dem_file_path) as dem_file:
            generate_polygons(dem_file, conn, area_name)

        # Close database connection
        conn.close()
        print("Database connection closed.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Function to retrieve DEM file path based on area name
def retrieve_dem_path(conn, area_name):
    """
    Retrieves DEM file path based on the specified area name from the PostgreSQL database.

    Args:
        conn (psycopg2.extensions.connection): A connection object to the PostgreSQL database.
        area_name (str): Name of the area to retrieve DEM file path.

    Returns:
        str: DEM file path if found, otherwise None.
    """
    try:
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
    args = parser.parse_args()

    if args.area_name:
        main(args.area_name)
    else:
        print("Please specify the area name using the -n option.")

print("---------- strata.py completed ----------")
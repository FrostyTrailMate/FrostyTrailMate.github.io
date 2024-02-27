import argparse
import geopandas as gpd
import rasterio
from shapely.geometry import Point, box
import psycopg2
from datetime import datetime
import signal
import sys
import os

print("++++++++++ Running sampling.py ++++++++++")

import signal
import argparse
import sys

def signal_handler(sig, frame):
    """
    Signal handler function for interrupt (Ctrl+C). Allows the sampling process to be stopped and rolled back.

    Args:
        sig (int): Signal number.
        frame (frame): Current stack frame.

    Returns:
        None
    """
    print("\nWriting process interrupted. Rolling back changes...")
    conn.rollback()  # Rollback the transaction to remove the added points
    conn.close() 
    print("Changes rolled back. Exiting...")
    sys.exit(0)

# Set the interrupt signal handler
signal.signal(signal.SIGINT, signal_handler)

def parse_args():
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(description='Generate sample points within a specified area.')
    parser.add_argument('-n', '--name', required=True, help='Name of the search area')
    parser.add_argument('-p', '--shapefile', type=str, help='Relative path to a shapefile')
    parser.add_argument('-d', '--distance', type=float, default=0.005, help='Distance between sampling points (default: 0.005)')
    return parser.parse_args()

# Load command-line arguments
args = parse_args()


# Set the datetime at the start of processing
current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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
    sys.exit(1)

# Query database for DEM file path
try:
    cur.execute("SELECT dem_processed FROM userpolygons WHERE area_name = %s", (args.name,))
    result = cur.fetchone()
    if result:
        dem_file_path = result[0]
        print("DEM file path retrieved from the database:", dem_file_path)
    else:
        print("DEM file path not found in the database.")
        sys.exit(1)
except Exception as e:
    print(f"Error querying database for DEM file path: {e}")
    sys.exit(1)

# Load the raster DEM and get its bounding box coordinates
print("Loading DEM and retrieving bounding box coordinates...")
try:
    dem_dataset = rasterio.open(dem_file_path)
    minx, miny, maxx, maxy = dem_dataset.bounds
    
    # Generate points within the boundary box for the user's -d argument
    print("Generating points within the boundary box...")
    spacing = args.distance
    boundary_box = box(minx, miny, maxx, maxy)
    points = []

    x = minx
    while x < maxx:
        y = miny
        while y < maxy:
            point = Point(x, y)
            if boundary_box.contains(point):
                points.append(point)
            y += spacing
        x += spacing

    print(f"{len(points)} points generated.")

    # Insert data into the database
    print("Inserting data into the database...")
    for i, point in enumerate(points):
        elevation = float(next(dem_dataset.sample([(point.x, point.y)]))[0])  # Extract the first element of the array
        area_name = args.name
        point_geom = point.wkb_hex  # Convert Shapely geometry to WKB format
        
        # Insert the data into the database
        cur.execute(
            "INSERT INTO samples (datetime, area_name, point_geom, elevation) VALUES (%s, %s, ST_GeomFromWKB(%s::geometry), %s)",
            (current_datetime, area_name, point_geom, elevation)
        )
        print(f"\rWriting point {i+1}/{len(points)} to database.", end='', flush=True)
    
    print("Database write completed.")
    conn.commit()

    # Export sample points to a shapefile for testing purposes
    output_dir = 'Outputs/Shapefiles/SamplePoints'
    os.makedirs(output_dir, exist_ok=True)
    sample_points_gdf = gpd.GeoDataFrame(geometry=points)
    sample_points_gdf.to_file(os.path.join(output_dir, f'{args.name}_sample_points.shp'), driver='ESRI Shapefile')

# Rollback the transaction and close the database connection if an error occurs
except Exception as e:
    print(f"\nError inserting point: {e}")
    conn.rollback() 
    conn.close()

finally:
    if 'dem_dataset' in locals():
        dem_dataset.close()  # Close the raster dataset
    conn.close()  

print("---------- sampling.py completed ----------")

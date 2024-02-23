import argparse
import geopandas as gpd
import rasterio
from shapely.geometry import Point, box, mapping
import psycopg2
from datetime import datetime
import pyproj
import signal
import sys

print("Running sampling.py...")

# Define a signal handler for interrupt (Ctrl+C)
def signal_handler(sig, frame):
    print("\nWriting process interrupted. Rolling back changes...")
    conn.rollback()  # Rollback the transaction to remove the added points
    conn.close()  # Close the database connection
    print("Changes rolled back. Exiting...")
    sys.exit(0)

# Set the interrupt signal handler
signal.signal(signal.SIGINT, signal_handler)

# Function to get elevation from raster file for a given point
def get_elevation_for_point(point, dem_dataset, dem_crs):
    """
    Get elevation for a given point from a digital elevation model (DEM) dataset.

    Parameters:
    - point (shapely.geometry.Point): The point for which elevation is to be retrieved.
    - dem_dataset (rasterio.io.DatasetReader): The raster dataset containing elevation data.
    - dem_crs (CRS): The coordinate reference system (CRS) of the DEM dataset.

    Returns:
    - float: The elevation value at the given point.
    """
    lon, lat = point.x, point.y
    easting, northing = transform_coords(lon, lat, dem_crs, dem_dataset.crs)
    row, col = dem_dataset.index(easting, northing)
    elevation = dem_dataset.read(1)[row, col]
    return elevation

# Function to transform coordinates
def transform_coords(lon, lat, src_crs, dst_crs):
    """
    Transform coordinates from one coordinate reference system (CRS) to another.

    Parameters:
    - lon (float): Longitude coordinate.
    - lat (float): Latitude coordinate.
    - src_crs (CRS): Source CRS.
    - dst_crs (CRS): Destination CRS.

    Returns:
    - tuple: Transformed (x, y) coordinates.
    """
    transformer = pyproj.Transformer.from_crs(src_crs, dst_crs, always_xy=True)
    x, y = transformer.transform(lon, lat)
    return x, y

def parse_args():
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
        dbname="FTM8_dyn",
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
    dem_crs = dem_dataset.crs
    print("Bounding box coordinates retrieved from the DEM file.")
    
    # Generate points within the boundary box
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
        elevation = float(get_elevation_for_point(point, dem_dataset, dem_crs))
        area_name = args.name
        point_geom = point.wkb_hex  # Convert Shapely geometry to WKB format
        # Insert the data into the database
        cur.execute(
            "INSERT INTO samples (datetime, area_name, point_geom, elevation) VALUES (%s, %s, ST_GeomFromWKB(%s::geometry), %s)",
            (current_datetime, area_name, point_geom, elevation)
        )
        print(f"\rWriting point {i+1}/{len(points)} to database.", end='', flush=True)
    
    print("\nDatabase write completed.")  # Add a newline after completion
    conn.commit()  # Commit the transaction if no errors occurred

except Exception as e:
    print(f"\nError inserting point: {e}")
    conn.rollback()  # Rollback the transaction in case of error

finally:
    if 'dem_dataset' in locals():
        dem_dataset.close()  # Close the raster dataset if it was opened
    conn.close()  # Close the database connection regardless of the outcome

print("sampling.py completed.")

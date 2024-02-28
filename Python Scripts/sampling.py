import argparse
import geopandas as gpd
import rasterio
from shapely.geometry import Point, box
import psycopg2
from datetime import datetime
import signal
import sys
import os


def signal_handler(sig, frame, conn):
    """
    Signal handler function for interrupt (Ctrl+C). Allows the sampling process to be stopped and rolled back.

    Args:
        sig (int): Signal number.
        frame (frame): Current stack frame.
        conn (psycopg2.connection): PostgreSQL database connection.

    Returns:
        None
    """
    print("\nWriting process interrupted. Rolling back changes...")
    conn.rollback()  # Rollback the transaction to remove the added points
    conn.close() 
    print("Changes rolled back. Exiting...")
    sys.exit(0)

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

def connect_to_database():
    """
    Connect to PostgreSQL database.

    Returns:
        tuple: Tuple containing database connection (psycopg2.connection) and cursor (psycopg2.cursor).
    """
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
        return conn, cur
    except Exception as e:
        print(f"Error connecting to PostgreSQL database: {e}")
        sys.exit(1)

def query_dem_file_path(cur, area_name):
    """
    Query database for DEM file path.

    Args:
        cur (psycopg2.cursor): PostgreSQL database cursor.
        area_name (str): Name of the search area.

    Returns:
        str: DEM file path.
    """
    try:
        cur.execute("SELECT dem_processed FROM userpolygons WHERE area_name = %s", (area_name,))
        result = cur.fetchone()
        if result:
            dem_file_path = result[0]
            print("DEM file path retrieved from the database:", dem_file_path)
            return dem_file_path
        else:
            print("DEM file path not found in the database.")
            sys.exit(1)
    except Exception as e:
        print(f"Error querying database for DEM file path: {e}")
        sys.exit(1)

def load_dem_and_get_bounds(dem_file_path):
    """
    Load the raster DEM and get its bounding box coordinates.

    Args:
        dem_file_path (str): Path to the DEM file.

    Returns:
        tuple: Tuple containing bounding box coordinates (minx, miny, maxx, maxy) and raster dataset (rasterio.io.DatasetReader).
    """
    print("Loading DEM and retrieving bounding box coordinates...")
    try:
        dem_dataset = rasterio.open(dem_file_path)
        minx, miny, maxx, maxy = dem_dataset.bounds
        return minx, miny, maxx, maxy, dem_dataset
    except Exception as e:
        print(f"Error loading DEM: {e}")
        sys.exit(1)

def generate_sample_points(minx, miny, maxx, maxy, spacing):
    """
    Generate sample points within the bounding box.

    Args:
        minx (float): Minimum x-coordinate of the bounding box.
        miny (float): Minimum y-coordinate of the bounding box.
        maxx (float): Maximum x-coordinate of the bounding box.
        maxy (float): Maximum y-coordinate of the bounding box.
        spacing (float): Distance between sampling points.

    Returns:
        list: List of generated sample points (shapely.geometry.Point).
    """
    print("Generating points within the boundary box...")
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
    return points

def clip_points_by_shapefile(points, shapefile_path):
    """
    Clip sample points by a shapefile.

    Args:
        points (list): List of sample points (shapely.geometry.Point).
        shapefile_path (str): Path to the shapefile for clipping.

    Returns:
        list: List of clipped sample points.
    """
    print("Clipping sample points by shapefile...")
    try:
        shapefile_gdf = gpd.read_file(shapefile_path)
        clipped_points = [point for point in points if shapefile_gdf.geometry.contains(point).any()]
        print(f"{len(clipped_points)} points retained after clipping.")
        return clipped_points
    except Exception as e:
        print(f"Error clipping points by shapefile: {e}")
        sys.exit(1)

def insert_data_into_database(cur, conn, current_datetime, area_name, points, dem_dataset):
    """
    Insert data into the database.

    Args:
        cur (psycopg2.cursor): PostgreSQL database cursor.
        conn (psycopg2.connection): PostgreSQL database connection.
        current_datetime (str): Current datetime string.
        area_name (str): Name of the search area.
        points (list): List of sample points (shapely.geometry.Point).
        dem_dataset (rasterio.io.DatasetReader): Raster dataset.

    Returns:
        None
    """
    print("Inserting data into the database...")
    for i, point in enumerate(points):
        elevation = float(next(dem_dataset.sample([(point.x, point.y)]))[0])  # Extract the first element of the array
        point_geom = point.wkb_hex  # Convert Shapely geometry to WKB format
        
        # Insert the data into the database
        cur.execute(
            "INSERT INTO samples (datetime, area_name, point_geom, elevation) VALUES (%s, %s, ST_GeomFromWKB(%s::geometry), %s)",
            (current_datetime, area_name, point_geom, elevation)
        )
        print(f"\rWriting point {i+1}/{len(points)} to database.", end='', flush=True)
    
    print("\nDatabase write completed.")
    conn.commit()

def export_sample_points_to_shapefile(points, area_name):
    """
    Export sample points to a shapefile for testing purposes.

    Args:
        points (list): List of sample points (shapely.geometry.Point).
        area_name (str): Name of the search area.

    Returns:
        None
    """
    output_dir = 'Outputs/Shapefiles/SamplePoints'
    os.makedirs(output_dir, exist_ok=True)
    sample_points_gdf = gpd.GeoDataFrame(geometry=points)
    sample_points_gdf.to_file(os.path.join(output_dir, f'{area_name}_sample_points.shp'), driver='ESRI Shapefile')

def main():
    print("++++++++++ Running sampling.py ++++++++++")
    signal.signal(signal.SIGINT, lambda sig, frame: signal_handler(sig, frame, conn))

    args = parse_args()
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn, cur = connect_to_database()
    dem_file_path = query_dem_file_path(cur, args.name)
    minx, miny, maxx, maxy, dem_dataset = load_dem_and_get_bounds(dem_file_path)
    points = generate_sample_points(minx, miny, maxx, maxy, args.distance)
    
    if args.shapefile:
        clipped_points = clip_points_by_shapefile(points, args.shapefile)
        insert_data_into_database(cur, conn, current_datetime, args.name, clipped_points, dem_dataset)
        export_sample_points_to_shapefile(clipped_points, args.name)
    else:
        insert_data_into_database(cur, conn, current_datetime, args.name, points, dem_dataset)
        export_sample_points_to_shapefile(points, args.name)

    if 'dem_dataset' in locals():
        dem_dataset.close()  # Close the raster dataset
    conn.close()

    print("---------- sampling.py completed ----------")

if __name__ == "__main__":
    main()

import argparse
import psycopg2
import rasterio
from shapely.wkb import loads
from shapely.geometry import Point
from math import ceil
from datetime import datetime
import time

print("Running snow_detect.py...")
time.sleep(5)
# Function to parse command line arguments
def parse_arguments():
    parser = argparse.ArgumentParser(description="Snow detection script")
    parser.add_argument("-n", "--area_name", type=str, help="Name of the search area")
    return parser.parse_args()

# Database connection parameters
dbname = 'FTM8_dyn'
user = 'postgres'
password = 'admin'
host = 'DESKTOP-UIUIA2A'
port = '5432'

# Generate datetime for processed timestamp
current_datetime = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

# Function to connect to PostgreSQL
def connect_to_db():
    """
    Connect to the PostgreSQL database.

    Returns:
        psycopg2.connection: A connection object representing the connection to the database.
        None: If connection cannot be established.
    """
    try:
        print("Connecting to PostgreSQL database...")
        conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
        return conn
    except psycopg2.Error as e:
        print("Error connecting to PostgreSQL database:", e)
        return None

# Function to update processed timestamp in userpolygons table
def update_processed_timestamp(conn, area_name):
    """
    Update the processed timestamp in the userpolygons table.

    Args:
        conn (psycopg2.connection): A connection object representing the connection to the database.
        area_name (str): Name of the search area.
    """
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE userpolygons SET sar_processed = %s WHERE sar_processed IS NULL and area_name = %s", (current_datetime, area_name))
        conn.commit()
        cursor.close()
        print("Process completed. Exiting.")
    except psycopg2.Error as e:
        print("Error updating processed timestamp:", e)

# Function to process points and raster
def process_points_and_raster(conn, area_name):
    """
    Process points and raster images.

    Args:
        conn (psycopg2.connection): A connection object representing the connection to the database.
        area_name (str): Name of the search area.
    """
    try:
        cursor = conn.cursor()

        # Get sar_path for the given area_name
        print("Finding raster images to process...")
        cursor.execute("SELECT sar_path FROM userpolygons WHERE area_name = %s AND sar_processed IS NULL", (area_name,))
        sar_paths = cursor.fetchall()
        num_rasters = len(sar_paths)
        print("sar_paths:", sar_paths)
        raster_count = 0

        if not sar_paths:
            print("No raster images found to process.")
            return

        for sar_path in sar_paths:
            raster_count += 1
            raster_path = sar_path[0]
            print(f"Processing raster {raster_count}/{num_rasters}:", sar_path[0], end="\r")

            # Open raster file and project to EPSG:4326
            with rasterio.open(raster_path) as src:
                # Access sample points from samples table for the given area_name
                cursor.execute("SELECT point_geom, elevation FROM samples WHERE area_name = %s", (area_name,))
                sample_rows = cursor.fetchall()
                num_samples = len(sample_rows)
                sample_count = 0
                print(f"Found {num_samples} sample points for area: {area_name}.")

                if not sample_rows:
                    print(f"No sample points found for area {area_name}.")
                    continue

                max_elevation = max([row[1] for row in sample_rows])
                print(f"Max elevation: {max_elevation}")
                elevation_intervals = list(range(0, ceil(max_elevation / 100) * 100, 100))

                for interval_start, interval_end in zip(elevation_intervals, elevation_intervals[1:]):
                    total_points = 0
                    detected_points = 0

                    # Count total points within elevation strata
                    for sample_row in sample_rows:
                        sample_count += 1
                        point_geom = loads(sample_row[0], hex=True)
                        if interval_start <= sample_row[1] < interval_end:
                            total_points += 1

                            # Get corresponding value from raster
                            row, col = src.index(point_geom.x, point_geom.y)
                            value = src.read(1, window=((row, row+1), (col, col+1)))

                            # Count points within pixel value range
                            if -15 <= value <= -10:
                                detected_points += 1

                    # Calculate coverage percentage
                    if total_points > 0:
                        coverage_percentage = (detected_points / total_points) * 100
                    else:
                        coverage_percentage = 0

                    # Write results to results table
                    print(f"Writing results for elevation interval {interval_start}-{interval_end}...", end='\r')
                    cursor.execute("INSERT INTO results (elevation, coverage_percentage, datetime, total_points, detected_points, area_name) VALUES (%s, %s, %s, %s, %s, %s)",
                                   (f"{interval_start}-{interval_end}", round(coverage_percentage, 2), current_datetime, total_points, detected_points, area_name))

                    conn.commit()
                    
                print(f"Processed {sample_count} sample points for raster {raster_count}/{num_rasters}.")
            print(f"Raster {raster_count}/{num_rasters} processing complete.")
    except psycopg2.Error as e:
        print("Error processing points and raster:", e)

    cursor.close()

def main():
    """
    Main function to execute the program.
    """
    # Parse command line arguments
    args = parse_arguments()

    # Connect to PostgreSQL
    conn = connect_to_db()
    if conn is None:
        return

    # Process points and raster
    process_points_and_raster(conn, args.area_name)

    # Update processed timestamp
    update_processed_timestamp(conn, area_name=args.area_name)

    # Close database connection
    conn.close()

if __name__ == "__main__":
    main()

print("snow_detect.py completed.")

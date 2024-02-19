import psycopg2
import rasterio
from shapely.wkb import loads
from shapely.geometry import Point
from math import ceil
from datetime import datetime

# Database connection parameters
dbname = 'FTM8'
user = 'postgres'
password = 'admin'
host = 'DESKTOP-UIUIA2A'
port = '5432'

# Function to connect to PostgreSQL
def connect_to_db():
    try:
        print("Connecting to PostgreSQL database...")
        conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
        return conn
    except psycopg2.Error as e:
        print("Error connecting to PostgreSQL database:", e)
        return None

# Function to update processed timestamp in sar_raw table
def update_processed_timestamp(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE sar_raw SET processed = %s", (datetime.now(),))
        conn.commit()
        cursor.close()
        print("Processed timestamp updated in sar_raw table.")
    except psycopg2.Error as e:
        print("Error updating processed timestamp:", e)

# Function to process points and raster
def process_points_and_raster(conn):
    try:
        cursor = conn.cursor()

        # Step 1: Iterate through rows in sar_raw table
        print("Finding raster images to process...")
        cursor.execute("SELECT path FROM sar_raw WHERE processed IS NULL")
        rows = cursor.fetchall()
        num_rasters = len(rows)
        raster_count = 0

        for row in rows:
            raster_count += 1
            raster_path = row[0]
            print(f"Processing raster {raster_count}/{num_rasters}:", raster_path, end="\r")

            # Open raster file and project to EPSG:4326
            with rasterio.open(raster_path) as src:
                # Step 2: Access sample points from samples table
                cursor.execute("SELECT point_geom, elevation FROM samples")
                sample_rows = cursor.fetchall()
                num_samples = len(sample_rows)
                sample_count = 0
                print(f"Found {num_samples} sample points.")

                max_elevation = max([row[1] for row in sample_rows])
                print(f"Max elevation: {max_elevation}")
                elevation_intervals = list(range(0, ceil(max_elevation / 100) * 100, 100))

                for interval_start, interval_end in zip(elevation_intervals, elevation_intervals[1:]):
                    total_points = 0
                    detected_points = 0

                    # Step 5: Count total points within elevation strata
                    for sample_row in sample_rows:
                        sample_count += 1
                        point_geom = loads(sample_row[0], hex=True)
                        if interval_start <= sample_row[1] < interval_end:
                            total_points += 1

                            # Step 3: Get corresponding value from raster
                            row, col = src.index(point_geom.x, point_geom.y)
                            value = src.read(1, window=((row, row+1), (col, col+1)))

                            # Step 5.1: Count points within pixel value range
                            if -15 <= value <= -10:
                                detected_points += 1

                    # Step 6: Calculate coverage percentage
                    if total_points > 0:
                        coverage_percentage = (detected_points / total_points) * 100
                    else:
                        coverage_percentage = 0

                    # Step 7: Write results to results table
                    print(f"Writing results for elevation interval {interval_start}-{interval_end}...", end='\r')
                    cursor.execute("INSERT INTO results (elevation, coverage_percentage, ddatetime, total_points, detected_points, area_name) VALUES (%s, %s, %s, %s, %s, %s)",
                                   (f"{interval_start}-{interval_end}", round(coverage_percentage, 2), datetime.now().strftime("%Y/%m/%d %H:00"), total_points, detected_points, 'Yosemite'))

                    conn.commit()

                print(f"Processed {sample_count} sample points for raster {raster_count}/{num_rasters}.")
            print(f"Raster {raster_count}/{num_rasters} processing complete.")
    except psycopg2.Error as e:
        print("Error processing points and raster:", e)

    cursor.close()

def main():
    # Connect to PostgreSQL
    conn = connect_to_db()
    if conn is None:
        return

    # Process points and raster
    process_points_and_raster(conn)

    # Update processed timestamp
    update_processed_timestamp(conn)

    # Close database connection
    conn.close()

if __name__ == "__main__":
    main()

import psycopg2
import rasterio
import numpy as np
import math
from shapely.geometry import Polygon
from shapely.wkb import dumps
from datetime import datetime
from rasterio.mask import mask
from shapely.ops import unary_union

print("Running snow_detect.py...")

# Database connection parameters
dbname = 'FTM8'
user = 'postgres'
password = 'admin'
host = 'DESKTOP-UIUIA2A'
port = '5432'

# Generate datetime for processed timestamp
current_datetime = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

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
        cursor.execute("UPDATE sar_raw SET processed = %s WHERE processed IS NULL", (current_datetime,))
        conn.commit()
        cursor.close()
        print("Process completed. Exiting.")
    except psycopg2.Error as e:
        print("Error updating processed timestamp:", e)

# Function to project point geometry to EPSG:4326
def project_to_4326(point_geom):
    # Assuming point_geom is in EPSG:4326, so no transformation is needed
    return point_geom

# Function to insert polygon into results table
def insert_polygon(conn, elevation_stratum, polygon):
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO results (elevation, vector) VALUES (%s, ST_GeomFromText(%s, 4326))",
                       (elevation_stratum, dumps(polygon)))
        conn.commit()
        cursor.close()
    except psycopg2.Error as e:
        print("Error inserting polygon:", e)

# Function to process points and raster
def process_points_and_raster(conn):
    try:
        cursor = conn.cursor()

        # Iterate through rows in sar_raw table
        print("Finding raster images to process...")
        cursor.execute("SELECT path FROM sar_raw WHERE processed IS NULL")
        rows = cursor.fetchall()
        num_rasters = len(rows)
        raster_count = 0

        if not rows:
            print("No raster images found to process.")
            return

        for row in rows:
            raster_count += 1
            raster_path = row[0]
            print(f"Processing raster {raster_count}/{num_rasters}:", raster_path, end="\r")

            # Open raster file and project to EPSG:4326
            with rasterio.open(raster_path) as src:
                # Access sample points from samples table
                cursor.execute("SELECT point_geom, elevation FROM samples")
                sample_rows = cursor.fetchall()
                num_samples = len(sample_rows)
                sample_count = 0
                print(f"Found {num_samples} sample points.")

                max_elevation = max([row[1] for row in sample_rows])
                print(f"Max elevation: {max_elevation}")
                elevation_intervals = list(range(0, math.ceil(max_elevation / 100) * 100, 100))

                for interval_start, interval_end in zip(elevation_intervals, elevation_intervals[1:]):
                    total_points = 0
                    detected_points = 0

                    # Count total points within elevation strata
                    for sample_row in sample_rows:
                        sample_count += 1
                        point_geom = project_to_4326(sample_row[0])  # Project to EPSG:4326
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
                    cursor.execute("INSERT INTO results (elevation, coverage_percentage, ddatetime, total_points, detected_points, area_name) VALUES (%s, %s, %s, %s, %s, %s)",
                                   (f"{interval_start}-{interval_end}", round(coverage_percentage, 2), current_datetime, total_points, detected_points, 'Yosemite'))

                    conn.commit()

                print(f"Processed {sample_count} sample points for raster {raster_count}/{num_rasters}.")
            print(f"Raster {raster_count}/{num_rasters} processing complete.")
    except psycopg2.Error as e:
        print("Error processing points and raster:", e)

    cursor.close()

# Function to generate polygons for each elevation band
def generate_polygons(dem_file, conn):
    try:
        print("Generating polygons for each elevation band...")
        
        data = dem_file.read(1, masked=True)

        print("Mask shape:", data.shape)

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

            print("Mask shape:", mask.shape)

            if np.isnan(mask).any():
                print("Warning: Mask contains NaN values.")
                # Handle NaN values here (e.g., replace NaN with a default value)
                mask = np.nan_to_num(mask, nan=0)  # Replace NaN with 0

            polygons = []
            for geom, val in rasterio.features.shapes(mask.astype('uint8'), transform=dem_file.transform):
                if val != 0:
                    geom = rasterio.warp.transform_geom(dem_file.crs, 'EPSG:4326', geom, precision=6)
                    polygons.append(Polygon(geom['coordinates'][0]))

            if polygons:
                multi_polygon = unary_union(polygons)
                insert_polygon(conn, f"Elevation {int(lower_bound)}-{int(upper_bound)} meters", multi_polygon)

        print("\nAll elevation strata processed successfully.")
    except Exception as e:
        print(f"Error generating polygons: {e}")



def main():
    # Connect to PostgreSQL
    conn = connect_to_db()
    if conn is None:
        return

    # Process points and raster
    process_points_and_raster(conn)

    # Open DEM file and generate polygons
    with rasterio.open('Outputs/DEM/Yosemite_DEM_reprojected.tif') as dem_file:
        generate_polygons(dem_file, conn)

    # Update processed timestamp
    update_processed_timestamp(conn)

    # Close database connection
    conn.close()

if __name__ == "__main__":
    main()

print("snow_detect.py completed.")

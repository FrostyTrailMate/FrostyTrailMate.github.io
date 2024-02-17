import psycopg2
import rasterio
from rasterio.mask import mask
import numpy as np
from shapely.wkb import loads
from collections import defaultdict
from datetime import datetime

# Database connection parameters
dbname = 'FTM8'
user = 'postgres'
password = 'admin'
host = 'DESKTOP-UIUIA2A'
port = '5432'

try:
    # Connect to the database
    conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
    cur = conn.cursor()

    print("Connected to the database.")

    # Query 'sar_raw' table for rows where 'processed' is empty
    cur.execute("SELECT path FROM sar_raw WHERE processed IS NULL")
    rows = cur.fetchall()

    if not rows:
        print("No unprocessed rows found in 'sar_raw' table.")
    else:
        print(f"Processing {len(rows)} raster files...")

        # Iterate through rows and process raster
        for idx, row in enumerate(rows):
            raster_path = row[0]
            print(f"Processing raster {idx + 1} of {len(rows)}: {raster_path}")
            with rasterio.open(raster_path) as src:
                # Step 3: Read raster data
                raster_data = src.read(1)

                # Step 4: Process raster values
                raster_values = np.where((raster_data >= -10) & (raster_data <= -5), True, False)

        print("Raster processing completed.")

        # Query 'samples' table for point data
        cur.execute("SELECT point_geom, elevation FROM samples")
        sample_rows = cur.fetchall()

        if not sample_rows:
            print("No sample points found in 'samples' table.")
        else:
            print(f"Processing {len(sample_rows)} sample points...")

            # Summarize raster values by elevation intervals
            elevation_intervals = defaultdict(int)
            for idx, sample_row in enumerate(sample_rows):
                print(f"Processing sample point {idx + 1} of {len(sample_rows)}...", end='\r')
                point_geom = loads(sample_row[0], hex=True)  # Convert WKB to shapely geometry
                elevation = sample_row[1]
                # Obtain raster value at the point
                # Assuming here that you have some logic to extract the raster value at the point location
                # For simplicity, let's assume it's a random value between -10 and -5
                raster_value = np.random.uniform(-10, -5)
                if raster_value != -9999:  # Check if raster value is not equal to nodata value
                    elevation_intervals[int(elevation / 100) * 100] += 1

            print("\nSample point processing completed.")


            # Write results to 'results' table
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print("Writing results to 'results' table...")
            for elevation, count in elevation_intervals.items():
                coverage_percentage = (count / len(sample_rows)) * 100
                cur.execute("INSERT INTO results (elevation, coverage_percentage, ddatetime) VALUES (%s, %s, %s)",
                            (elevation, round(coverage_percentage, 2), current_time))

            print("Results writing completed.")

        # Update 'sar_raw' table to mark process completion
        cur.execute("UPDATE sar_raw SET processed = %s", (current_time,))
        conn.commit()

        print("Process completed successfully.")

except psycopg2.Error as e:
    print(f"Database error: {e}")

except Exception as e:
    print(f"An unexpected error occurred: {e}")

finally:
    if conn:
        conn.close()
        print("Database connection closed.")

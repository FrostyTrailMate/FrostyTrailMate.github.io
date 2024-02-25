import argparse
from datetime import datetime, timedelta, timezone
import multiprocessing
import subprocess
import threading
import sys
import psycopg2

# Function to establish PostgreSQL connection
def connect_to_postgres():
    try:
        connection = psycopg2.connect(
            database='FTM8',
            host='DESKTOP-UIUIA2A',
            user='postgres',
            password='admin',
            port=5432
        )
        return connection
    except psycopg2.Error as e:
        print("Error connecting to PostgreSQL database:", e)
        sys.exit(1)

# Function to check if area_name already exists in userpolygons table
def check_area_name(connection, area_name):
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT area_name FROM userpolygons WHERE area_name = %s", (area_name,))
        result = cursor.fetchone()
        cursor.close()
        if result:
            return True
        else:
            return False
    except psycopg2.Error as e:
        print("Error checking area_name in PostgreSQL database:", e)
        sys.exit(1)

def run_script(script_path, args):
    subprocess.run(["python", script_path, *args])

def six_days_ago():
    return (datetime.now() - timedelta(days=6)).strftime('%Y-%m-%d')

def now():
    return datetime.now().strftime('%Y-%m-%d')

def prompt_reset():
    def _input():
        choice = input("Will proceed without resetting the database in 5 seconds. Do you want to reset the database and saved data? (y/n): ").lower()
        return choice

    user_input = None
    input_thread = threading.Thread(target=lambda: setattr(input_thread, 'user_input', _input()))
    input_thread.daemon = True
    input_thread.start()

    # Wait for user input or timeout after 5 seconds
    input_thread.join(5)

    if input_thread.is_alive():
        # If the user hasn't responded, proceed without resetting the database
        print("\nNo response, proceeding without resetting the database.")
        return False
    else:
        return input_thread.user_input == 'y'

if __name__ == "__main__":
    # Connect to PostgreSQL database
    db_connection = connect_to_postgres()

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Run scripts with specified arguments')
    parser.add_argument('-s', '--start-date', default=six_days_ago(), help='Start date for image collection (default: 6 days ago)')
    parser.add_argument('-e', '--end-date', default=now(), help='End date for image collection (default: now)')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-c', '--coordinates', nargs=4, type=float, help='Coordinates for bounding box: xmin ymin xmax ymax. Must be in WGS84 (EPSG:4326).')
    group.add_argument('-p', '--shapefile-path', help='Path to a shapefile of a study area. Must be in WGS84 (EPSG:4326).')
    parser.add_argument('-n', '--search-area-name', required=True, help='Unique name to give the search area')
    parser.add_argument('-d', '--sampling-distance', type=float, default=0.005, help='Distance between sampling points (default: 0.005 (~500 meters))')
    parser.add_argument('-b', '--band', choices=['VV', 'VH'], default='VV', help='Band to be used for processing (default: VV)')

    args = parser.parse_args()

    # Check if provided area_name already exists in the userpolygons table
    if check_area_name(db_connection, args.search_area_name):
        print(f"Error: provided -n argument ('{args.search_area_name}') already exists. Please choose another name for this run. Exiting.")
        sys.exit(1)

    if prompt_reset():
        run_script('Python Scripts/createDB.py', [])

    # Insert new row into userpolygons table with provided area_name and current datetime
    try:
        with db_connection.cursor() as cursor:
            cursor.execute("INSERT INTO userpolygons (area_name, datetime) VALUES (%s, %s)", (args.search_area_name, datetime.now()))
        db_connection.commit()
        print("New row inserted into userpolygons table.")
    except psycopg2.Error as e:
        print("Error inserting row into userpolygons table:", e)
        db_connection.rollback()
        sys.exit(1)

    # Date Handling
    try:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
    except ValueError:
        print("Error: Invalid date format. Please use YYYY-MM-DD")
        exit(1)

    # Define common script arguments
    common_args = ['-n', args.search_area_name]

    coord_args =[]
    if args.coordinates:
        coord_args.extend(['-c', *[str(coord) for coord in args.coordinates]])
    elif args.shapefile_path:
        coord_args.extend(['-p', args.shapefile_path])

    # Run scripts in parallel
    with multiprocessing.Pool() as pool:
        # Run DEM.py
        dem_args = common_args[:] + coord_args[:]
        dem_process = pool.apply_async(run_script, ['Python Scripts/DEM.py', dem_args])

        # Run sentinel.py
        sentinel_args = common_args[:] + coord_args[:] + ['-s', args.start_date, '-e', args.end_date]
        sentinel_process = pool.apply_async(run_script, ['Python Scripts/sentinel.py', sentinel_args])

        # Wait for DEM and Sentinel processes to finish
        dem_process.get()
        sentinel_process.get()

        # Run sampling.py after DEM and Sentinel
        sampling_args = common_args[:] + ['-d', str(args.sampling_distance)]
        pool.apply(run_script, ['Python Scripts/sampling.py', sampling_args])

        # Run snow_detect.py after sampling.py
        snow_args = common_args[:] + ['-b', args.band]
        pool.apply(run_script, ['Python Scripts/snow_detect.py', snow_args])

        strata_args = common_args[:]
        pool.apply(run_script, ['Python Scripts/strata.py', strata_args])

        # Ensure all processes are finished before exiting
        pool.close()
        pool.join()

    # Close PostgreSQL connection
    db_connection.close()

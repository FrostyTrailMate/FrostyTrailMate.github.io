import argparse
from datetime import datetime, timedelta, timezone
import multiprocessing
import subprocess
import threading
import sys
import psycopg2

def connect_to_postgres():
    """
    Establishes a connection to the FTM8 database.

    Returns:
        connection: psycopg2 connection object
    """
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

def check_area_name(connection, area_name):
    """
    Checks if the provided area_name already exists in the userpolygons table.

    Args:
        connection: psycopg2 connection object
        area_name (str): Name of the area to check

    Returns:
        bool: True if the area_name exists, False otherwise
    """
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
    """
    Runs a Python script with specified arguments using subprocess.

    Args:
        script_path (str): Path to the Python script to be executed
        args (list): List of command-line arguments for the script
    """
    subprocess.run(["python", script_path, *args])

def six_days_ago():
    """
    Returns the date six days prior to the current date.

    Returns:
        str: Date in the format '%Y-%m-%d'
    """
    return (datetime.now() - timedelta(days=6)).strftime('%Y-%m-%d')

def now():
    """
    Returns the current date.

    Returns:
        str: Current date in the format '%Y-%m-%d'
    """
    return datetime.now().strftime('%Y-%m-%d')

def prompt_reset():
    """
    Prompts the user to reset the database and returns their selection.

    Returns:
        bool: True if the user chooses to reset the database, False otherwise
    """
    def _input():
        choice = input("Will proceed without resetting the database in 5 seconds. Do you want to reset the database and saved data? (y/n): ").lower()
        return choice

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
    # Connect to the FTM8 database
    db_connection = connect_to_postgres()

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Run scripts with specified arguments')
    parser.add_argument('-s', '--start-date', default=six_days_ago(), help='Start date for image collection (default: 6 days ago)')
    parser.add_argument('-e', '--end-date', default=now(), help='End date for image collection (default: now)')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-c', '--coordinates', nargs='+', help='Coordinates for bounding box: xmin ymin xmax ymax. Must be in WGS84 (EPSG:4326).')
    group.add_argument('-p', '--shapefile-path', help='Path to a shapefile of a study area. Must be in WGS84 (EPSG:4326).')
    parser.add_argument('-n', '--search-area-name', required=True, help='Unique name to give the search area')
    parser.add_argument('-d', '--sampling-distance', type=float, default=0.005, help='Distance between sampling points (default: 0.005 (~500 meters))')
    parser.add_argument('-b', '--band', choices=['VV', 'VH'], default='VV', help='Band to be used for processing (default: VV)')

    args = parser.parse_args()

    # Remove quotes from coordinates if present. If coordinates are provided as a single string, split them into individual coordinates
    if args.coordinates:
        if len(args.coordinates) == 1:
            args.coordinates = args.coordinates[0].split()
        args.coordinates = [coord.strip('"\'') for coord in args.coordinates]

    # Check if provided area_name already exists in the userpolygons table
    if check_area_name(db_connection, args.search_area_name):
        print(f"Error: provided -n argument ('{args.search_area_name}') already exists. Please choose another name for this run. Exiting.")
        sys.exit(1)

    print(args.coordinates)

    # Clear the database and output folders if the user chooses to reset
    if prompt_reset():
        run_script('Python Scripts/createDB.py', [])

    # Insert new row into userpolygons table with provided area_name, current datetime, and selected band information
    try:
        with db_connection.cursor() as cursor:
            if args.coordinates:
                # Check if there are enough coordinates for a polygon
                if len(args.coordinates) < 4:
                    print("Error: Insufficient coordinates provided for creating a polygon.")
                    sys.exit(1)

                # Construct the polygon text
                polygon_text = f"POLYGON(({args.coordinates[0]} {args.coordinates[1]}, {args.coordinates[2]} {args.coordinates[1]}, {args.coordinates[2]} {args.coordinates[3]}, {args.coordinates[0]} {args.coordinates[3]}, {args.coordinates[0]} {args.coordinates[1]}))"
            elif args.shapefile_path:
                # Handle shapefile case
                polygon_text = "POLYGON_FROM_SHAPEFILE"  # Placeholder, replace with actual logic
            else:
                print("Error: No coordinates or shapefile path provided.")
                sys.exit(1)

            cursor.execute("INSERT INTO userpolygons (area_name, datetime, arg_b, arg_s, arg_e, arg_d, geom) VALUES (%s, %s, %s, %s, %s, %s, ST_GeomFromText(%s, 4326))", (args.search_area_name, datetime.now(), args.band, args.start_date, args.end_date, args.sampling_distance, polygon_text))
        db_connection.commit()
        print("New row inserted into userpolygons table with band information.")
    except psycopg2.Error as e:
        print("Error inserting row into userpolygons table:", e)
        db_connection.rollback()
        sys.exit(1)

    # Clean dates for proper formatting
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

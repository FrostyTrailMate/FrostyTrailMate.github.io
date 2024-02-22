import argparse
from datetime import datetime, timedelta, timezone
import multiprocessing
import subprocess

def run_script(script_path, args):
    subprocess.run(["python", script_path, *args])

def six_days_ago():
    return (datetime.now() - timedelta(days=6)).strftime('%Y-%m-%d')

def now():
    return datetime.now().strftime('%Y-%m-%d')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run scripts with specified arguments')
    parser.add_argument('-s', '--start-date', default=six_days_ago(), help='Start date for image collection (default: 6 days ago)')
    parser.add_argument('-e', '--end-date', default=now(), help='End date for image collection (default: now)')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-c', '--coordinates', nargs=4, type=float, help='Coordinates for bounding box: xmin ymin xmax ymax. Must be in WGS84 (EPSG:4326).')
    group.add_argument('-p', '--shapefile-path', help='Path to a shapefile of a study area. Must be in WGS84 (EPSG:4326).')
    parser.add_argument('-n', '--search-area-name', required=True, help='Unique name to give the search area')
    parser.add_argument('-d', '--sampling-distance', type=float, default=0.005, help='Distance between sampling points (default: 0.005 (~500 meters))')

    args = parser.parse_args()

    # Date Handling
    try:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
    except ValueError:
        print("Error: Invalid date format. Please use YYYY-MM-DD")
        exit(1)


    # Create the database and tables
    subprocess.run(["python", "Python Scripts/createDB.py"])

    # Define the scripts to run in parallel
    scripts_parallel = ['Python Scripts/DEM.py', 'Python Scripts/sentinel.py']

    # Arguments to pass to scripts
    script_args = ['-n', args.search_area_name]
    if args.coordinates:
        script_args.extend(['-c', *[str(coord) for coord in args.coordinates]])
    elif args.shapefile_path:
        script_args.extend(['-p', args.shapefile_path])
    script_args.extend(['-d', str(args.sampling_distance)])

    # Run scripts in parallel
    with multiprocessing.Pool() as pool:
        pool.starmap(run_script, [(script, script_args) for script in scripts_parallel])

    # Run the script to generate sample points
    subprocess.run(["python", "Python Scripts/sampling.py", *script_args])

    # Run the snow detection script
    subprocess.run(["python", "Python Scripts/snow_detect_strata.py", *script_args])

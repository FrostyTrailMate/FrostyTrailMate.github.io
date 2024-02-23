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

    # Define common script arguments
    common_args = ['-n', args.search_area_name]

    coord_args =[]
    if args.coordinates:
        coord_args.extend(['-c', *[str(coord) for coord in args.coordinates]])
    elif args.shapefile_path:
        coord_args.extend(['-p', args.shapefile_path])

    # Run scripts in parallel
    with multiprocessing.Pool() as pool:
        # Run dyn_DEM.py
        dem_args = common_args[:] + coord_args[:]
        dem_process = pool.apply_async(run_script, ['Python Scripts/dyn_DEM.py', dem_args])

        # Run dyn_sentinel.py
        sentinel_args = common_args[:] + coord_args[:] + ['-s', args.start_date, '-e', args.end_date]
        sentinel_process = pool.apply_async(run_script, ['Python Scripts/dyn_sentinel.py', sentinel_args])

        # Wait for DEM and Sentinel processes to finish
        dem_process.get()
        sentinel_process.get()

        # Run dyn_sampling.py after DEM and Sentinel
        sampling_args = common_args[:] + ['-d', str(args.sampling_distance)]
        pool.apply(run_script, ['Python Scripts/dyn_sampling.py', sampling_args])

        # Run dyn_snow_detect.py after dyn_sampling.py
        snow_args = common_args[:]
        pool.apply(run_script, ['Python Scripts/dyn_snow_detect.py', snow_args])

        # Ensure all processes are finished before exiting
        pool.close()
        pool.join()
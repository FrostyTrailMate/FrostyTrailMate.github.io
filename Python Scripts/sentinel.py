import argparse
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
import os
import geopandas as gpd
from sentinelhub import SHConfig, CRS, BBox, DataCollection, SentinelHubRequest, MimeType, bbox_to_dimensions, BBoxSplitter
from sentinelhub.geo_utils import bbox_to_dimensions, to_utm_bbox
import rasterio
from rasterio.merge import merge
import sys
from datetime import datetime, timedelta
import concurrent.futures
import signal
import psycopg2 
import shutil
import time
import rasterio.warp

print("++++++++++ Running sentinel.py ++++++++++")

def clear_temp_folder():
    """
    Clears the temporary folder 'Outputs/SAR/temp'.
    """
    shutil.rmtree('Outputs/SAR/temp', ignore_errors=True)
    os.makedirs('Outputs/SAR/temp', exist_ok=True)
    print("Temporary raster files cleared.")

def six_days_ago():
    """
    Calculates the date six days before the current date.
    
    Returns:
        str: A string representing the date six days ago in the format 'YYYY-MM-DD'.
    """
    return (datetime.now() - timedelta(days=6)).strftime('%Y-%m-%d')

def now():
    """
    This function retrieves the current date.
    
    Returns:
        str: A string representing the current date in the format 'YYYY-MM-DD'.
    """
    return datetime.now().strftime('%Y-%m-%d')


# --- Argument Parsing ---
parser = argparse.ArgumentParser(description='Download and process Sentinel-1 SAR data.')
parser.add_argument('-s', '--start_date', type=str,
                    help='Start date for image collection (YYYY-MM-DD)', default = six_days_ago())
parser.add_argument('-e', '--end_date', type=str,
                    help='End date for image collection (YYYY-MM-DD)', default = now())
parser.add_argument('-n', '--name', type=str,
                    help='Name of the search area (provided by the user)', required=True)

group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('-c', '--coordinates', type=str, nargs='+',
                   help='Coordinates for bounding box (e.g., "-119.5 37.5 -119.0 37.0")')
group.add_argument('-p', '--shapefile', type=str,
                   help='Relative path to a shapefile')

args = parser.parse_args()

# Signal handler function to handle interrupt signal (Ctrl+C)
interrupted = False

def signal_handler(sig, frame):
    """
    Handles the interrupt signal (Ctrl+C) gracefully.

    This function is a signal handler that catches the interrupt signal (Ctrl+C) 
    and sets a global flag `interrupted` to indicate that the process has been interrupted.
    It also attempts to perform cleanup tasks such as clearing temporary files before exiting.

    Args:
        sig (int): The signal number.
        frame (object): The current execution frame.

    """
    global interrupted
    interrupted = True
    print("Process interrupted. Cancelling pending tasks...")
    time.sleep(5)  # Wait for 5 seconds before clearing temporary files
    # Clear the files within the 'Outputs/SAR/temp' folder
    temp_folder = 'Outputs/SAR/temp'
    try:
        clear_temp_folder
    except Exception as e:
        print(f"Error clearing temporary files: {e}")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# SentinelHub client credentials. 
print('Please change the client_id, client_secret, and instance_id in "Python Scripts/sentinel.py" to your own credentials.')
client_id = '4a2d8911-d323-4ad8-a7fc-29cb9600a99f'
client_secret = 'qwXyvZPpyaj5Q2lfLlVs6dyMs5mhIz7I'
instance_id = '9484b56d-2e58-43f2-acf2-79bfa89d4160'

# Set up Sentinel Hub configuration
print("Setting up Sentinel Hub configuration...")
config = SHConfig()
config.sh_client_id = client_id
config.sh_client_secret = client_secret
config.instance_id = instance_id
config.save()

# Create a session
print("Creating OAuth session...")
client = BackendApplicationClient(client_id=client_id)
oauth = OAuth2Session(client=client)

# Get token for the session
print("Fetching OAuth token...")
token = oauth.fetch_token(token_url='https://services.sentinel-hub.com/auth/realms/main/protocol/openid-connect/token',
                          client_secret=client_secret, include_client_id=True)
if token:
    print("OAuth token obtained successfully. Authentication successful.")
else:
    print("Error: Failed to obtain OAuth token.")
    exit(1)

# Use the obtained token in the headers for Sentinel Hub requests
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token['access_token']}"
}

# Bounding Box Handling
if args.coordinates:
    try:
        coords = [float(x) for x in args.coordinates]
        # Ensure at least four coordinates (for a rectangle)
        if len(coords) < 4:
            raise ValueError("At least four coordinates are needed for a bounding box. Use the format: -c xmin ymin xmax ymax")

        minx, miny, maxx, maxy = coords[0], coords[1], coords[2], coords[3]
        bbox = BBox((minx, miny, maxx, maxy), crs=CRS.WGS84)
    except ValueError:
        print("Error: Invalid coordinates format.")
        exit(1)
elif args.shapefile:
    shapefile_path = args.shapefile
    try:
        gdf = gpd.read_file(shapefile_path)
        minx, miny, maxx, maxy = gdf.total_bounds
        bbox = BBox((minx, miny, maxx, maxy), crs=CRS.WGS84)
    except FileNotFoundError:
        print(f"Error: Shapefile not found: {shapefile_path}")
        exit(1)

# Convert bounding box to UTM projection
print("Converting bounding box to UTM projection...")
utm_bbox = to_utm_bbox(bbox)

# Define evalscript. This is used to tell Sentinel Hub what data is required. Raster values are returned in decibles (dB) via the evaluatePixel() function.
print("Defining evalscript...")
evalscript = """
//VERSION=3
function setup() {
  return {
    input: [
      {
        bands: ["VV", "VH"]
      }
    ],
    output: [
      {
        id: "default",
        bands: 2,
        sampleType: "FLOAT32"
      }
    ]
  };
}

function evaluatePixel(samples) {
   return [10 * Math.log(samples.VV) / Math.LN10, 10 * Math.log(samples.VH) / Math.LN10];
}
"""

# Define spatial resolution in meters per pixel
resolution = 10 

# Split bounding box into smaller sub-boxes with individual size limited to 2500 pixels
split_size = (2500, 2500)
print("Splitting bounding box into smaller sub-boxes...")
bbox_splitter = BBoxSplitter([utm_bbox], utm_bbox.crs, split_size=split_size)
sub_bbox_list = bbox_splitter.get_bbox_list()

start_date = datetime.fromisoformat(args.start_date)
end_date = datetime.fromisoformat(args.end_date)

# Function to make requests for a single sub-box with interruption check
def request_images_for_sub_box(sub_bbox, evalscript, data_folder, index):
    """Requests images for a single sub-box with interruption check.

    Args:
        sub_bbox (sentinelhub.BBox): Bounding box of the sub-box.
        evalscript (str): Evalscript to be used for the Sentinel Hub request.
        data_folder (str): Path to the folder where the images will be saved.
        index (int): Index of the sub-box.

    Returns:
        None
    """
    global interrupted
    sys.stdout.write(f"\rRequesting sub-box {index+1}/{len(sub_bbox_list)}..."), sys.stdout.flush()
    sys.stdout.flush()

    # Check if the process is interrupted. Remove temporary files and and recreate the temp folder.
    if interrupted:
        print("Process interrupted. Exiting...")
        shutil.rmtree(data_folder, ignore_errors=True)
        os.makedirs(data_folder, exist_ok=True)
        sys.exit(0)

    # Send search parameters to Sentinel Hub and retrieve the sub-box
    try:
        request_image = SentinelHubRequest(
            evalscript=evalscript,
            config=config,
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=DataCollection.SENTINEL1_IW,
                    time_interval=(start_date, end_date),
                    other_args={
                        "processing": {
                            "speckleFilter": {
                                "type": "LEE",
                                "windowSizeX": 3,
                                "windowSizeY": 3
                            },
                        },
                    }
                )
            ],
            responses=[
                SentinelHubRequest.output_response('default', MimeType.TIFF)
            ],
            bbox=sub_bbox,
            size=bbox_to_dimensions(sub_bbox, resolution=resolution),
            data_folder=data_folder
        )
        request_image.get_data(save_data=True)
    except Exception as e:
        print(f"Error occurred while requesting sub-box {index+1}: {e}")
        clear_temp_folder()

# Function to download images for multiple sub-boxes using multithreading, with interruption check
def download_images_multi_thread(sub_bbox_list, evalscript, data_folder):
    """Downloads images for multiple sub-boxes using multithreading with interruption check.

    Args:
        sub_bbox_list (list): List of sub-boxes.
        evalscript (str): Evalscript to be used for the Sentinel Hub request.
        data_folder (str): Path to the folder where the images will be saved.

    Returns:
        None
    """
    max_workers = 5
    global interrupted
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(request_images_for_sub_box, sub_bbox, evalscript, data_folder, i): i for i, sub_bbox in enumerate(sub_bbox_list)}
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error occurred: {e}")
                if interrupted:
                    print("\nProcess interrupted. Exiting...")
                    executor.shutdown(wait=False)  # Shut down executor immediately upon interruption
                    sys.exit(0)

# Make requests for each sub-box using multithreading
data_folder = 'Outputs/SAR/temp'
download_images_multi_thread(sub_bbox_list, evalscript, data_folder)

# Define the function to search for image files in all subdirectories
def find_image_files(data_folder):
    """Finds image files in all subdirectories. Necessary to merge the downloaded images.

    Args:
        data_folder (str): Path to the folder containing image files.

    Returns:
        list: List of paths to image files.
    """
    image_files = []
    for root, dirs, files in os.walk(data_folder):
        for file in files:
            if file.endswith('.tiff'):
                image_files.append(os.path.join(root, file))
    return image_files

# Find all downloaded image files in the 'Outputs/SAR/temp' folder
image_files = find_image_files(data_folder)

# Check if any images were downloaded
if not image_files:
    print("No image files found. Exiting...")
    exit()

# Merge all downloaded images
print("\nMerging downloaded images...")
merged_image, out_trans = merge(image_files)

# Save the merged image to 'Outputs/SAR'
merged_image_path = os.path.join('Outputs/SAR', f'{args.name}_merged.tiff')

# Define the appropriate UTM CRS for the merged image
utm_zone = (utm_bbox.crs.epsg % 100) if (utm_bbox.crs.epsg % 100 != 0) else 60
ogc_string = utm_bbox.crs.ogc_string()
utm_hemisphere = 'N' if '+north' in ogc_string else 'S'
crs_string = f'+proj=utm +zone={utm_zone} +ellps=WGS84 +datum=WGS84 +units=m +no_defs'
print(f"CRS of the merged image: {crs_string}")

# Save the merged image
with rasterio.open(merged_image_path, 'w', driver='GTiff', 
                   height = merged_image.shape[1], width=merged_image.shape[2], 
                   count = merged_image.shape[0], 
                   dtype = merged_image.dtype, 
                   crs = crs_string,
                   transform = out_trans) as dst:
    dst.write(merged_image)
print(f"Merged image saved to: {merged_image_path}")

# Reproject merged image from UTM to WGS84 (EPSG:4326)
print("Reprojecting merged image to WGS84 for compatibility...")
reprojected_image_path = 'Outputs/SAR/'+f'{args.name}_merged_WGS84.tiff'  # Define the path for the reprojected image
with rasterio.open(merged_image_path) as src:
    transform, width, height = rasterio.warp.calculate_default_transform(
        src.crs, 'EPSG:4326', src.width, src.height, *src.bounds)
    kwargs = src.meta.copy()
    kwargs.update({
        'crs': 'EPSG:4326',
        'transform': transform,
        'width': width,
        'height': height
    })

    with rasterio.open(reprojected_image_path, 'w', **kwargs) as dst:
        for i in range(1, src.count + 1):
            rasterio.warp.reproject(
                source=rasterio.band(src, i),
                destination=rasterio.band(dst, i),
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=transform,
                dst_crs='EPSG:4326',
                resampling=rasterio.enums.Resampling.nearest)
    time.sleep(3)
print("Reprojection completed. Merged image saved in WGS84 (EPSG:4326) format: ", reprojected_image_path)

def update_database(image_path, time_collected, area_name):
    """
    Updates the PostgreSQL database with the locations of the files and the times collected. Uses area_name to determine the row to update.

    Args:
        image_path (str): Path to the image file.
        time_collected (datetime): Timestamp indicating when the image was collected.
        area_name (str): Name of the search area.

    Returns:
        None
    """
    try:
        print("Connecting to database...")
        connection = psycopg2.connect(
            user="postgres",
            password="admin",
            host="DESKTOP-UIUIA2A",
            port="5432",
            database="FTM8"
        )

        cursor = connection.cursor()
        
        # Allow a few seconds for previous processes to complete
        time.sleep(3)

        # SQL query to update data in the table
        update_query = "UPDATE userpolygons SET sar_path = %s, datetime = %s WHERE area_name = %s"
        
        # Data to be updated
        record_to_update = (image_path, time_collected, area_name)

        # Execute the SQL command
        cursor.execute(update_query, record_to_update)

        # Commit changes in the database
        connection.commit()
        print("Data updated successfully in PostgreSQL.")

    except (Exception, psycopg2.Error) as error:
        print("Error while updating data in PostgreSQL:", error)

    finally:
        # Close database connection
        if connection:
            connection.commit()
            cursor.close()
            connection.close()
            print("Closed database connection.")

# Update data in PostgreSQL database
time_now = datetime.now()
update_database(reprojected_image_path, time_now, args.name)

# Clear the folder 'Outputs/SAR/temp' at the end of the script to prevent problems with future script runs.
clear_temp_folder()

print("---------- sentinel.py completed ----------")
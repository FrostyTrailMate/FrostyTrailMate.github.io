from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
import os
import geopandas as gpd
from sentinelhub import SHConfig, CRS, BBox, DataCollection, SentinelHubRequest, MimeType, bbox_to_dimensions, BBoxSplitter
from sentinelhub.geo_utils import bbox_to_dimensions, to_utm_bbox
import rasterio
from rasterio.merge import merge
import sys
from datetime import datetime, timedelta, timezone
import concurrent.futures
import signal
import psycopg2 
import shutil
import time

print("Running sentinel.py...")

# Signal handler function to handle interrupt signal (Ctrl+C)
interrupted = False
def signal_handler(sig, frame):
    """Signal handler function to handle interrupt signal (Ctrl+C) during the downloads process.

    Args:
        sig (int): Signal number.
        frame (frame): Current stack frame.

    Returns:
        None
    """
    global interrupted
    interrupted = True
    print("Process interrupted. Cancelling pending tasks...")
    time.sleep(5)  # Wait for 5 seconds before clearing temporary files
    # Clear the files within the 'Outputs/SAR/temp' folder
    temp_folder = 'Outputs/SAR/temp'
    try:
        # Create an empty temporary directory
        os.makedirs(temp_folder, exist_ok=True)
        # Use shutil.rmtree() to delete the contents of the directory
        shutil.rmtree(temp_folder)
        print("Temporary raster files cleared.")
        os.makedirs(temp_folder, exist_ok=True)  # Recreate the empty directory
    except Exception as e:
        print(f"Error clearing temporary files: {e}")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Your client credentials
client_id = '81df2eab-5abf-48d8-9cb1-d682d83c2d04' # Carolina's Client ID
client_secret = 'MZI1MGRIwvyillNAAspvliPK0FQl3CUL' # Carolina's Client Secret
instance_id = 'h3cQpRZyfMiBZp8fsjpcdpLrR4dH8dPx' # Carolina's instance ID

# Set up Sentinel Hub configuration
print("Setting up Sentinel Hub configuration...")
config = SHConfig()
config.sh_client_id = client_id
config.sh_client_secret = client_secret
config.instance_id = instance_id
config.save()
print(config)

# Create a session
print("Creating OAuth session...")
client = BackendApplicationClient(client_id=client_id)
oauth = OAuth2Session(client=client)

# Get token for the session
print("Fetching OAuth token...")
token = oauth.fetch_token(token_url='https://services.sentinel-hub.com/auth/realms/main/protocol/openid-connect/token',
                          client_secret=client_secret, include_client_id=True)

print(token)

# Use the obtained token in the headers for Sentinel Hub requests
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token['access_token']}"
}

# Read the shapefile and get its bounding box
print("Reading shapefile and getting bounding box...")
shapefile_path = 'Shapefiles/Yosemite_Boundary_4326.shp'
gdf = gpd.read_file(shapefile_path)
minx, miny, maxx, maxy = gdf.total_bounds
bbox = BBox((minx, miny, maxx, maxy), crs=CRS.WGS84)

# Convert bounding box to UTM projection
print("Converting bounding box to UTM projection...")
utm_bbox = to_utm_bbox(bbox)

# Define evalscript
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

# Define resolution in meters per pixel
resolution = 10  # Adjust the resolution as needed

# Split bounding box into smaller sub-boxes with size limited to 2500 pixels
split_size = (2500, 2500)
print("Splitting bounding box into smaller sub-boxes... Press Ctrl+C to interrupt the download process.")
bbox_splitter = BBoxSplitter([utm_bbox], utm_bbox.crs, split_size=split_size)
sub_bbox_list = bbox_splitter.get_bbox_list()

end_date = datetime.now(timezone.utc)
start_date = end_date - timedelta(days=5)

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

    # Check if the process is interrupted
    if interrupted:
        print("Process interrupted. Exiting...")
        sys.exit(0)

    # Define the filename based on the bounding box coordinates
    filename = os.path.join(data_folder, f"image_{index}.tif")
    # Check if the file already exists locally
    if os.path.exists(filename):
        print(f"File for sub-box {index+1} already exists locally. Skipping...")
    else:
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
                                    "windowSizeX": 7,
                                    "windowSizeY": 7
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

# Function to download images for multiple sub-boxes using multithreading with interruption check
def download_images_multi_thread(sub_bbox_list, evalscript, data_folder):
    """Downloads images for multiple sub-boxes using multithreading with interruption check.

    Args:
        sub_bbox_list (list): List of sub-boxes.
        evalscript (str): Evalscript to be used for the Sentinel Hub request.
        data_folder (str): Path to the folder where the images will be saved.

    Returns:
        None
    """
    global interrupted
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
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
merged_image_path = os.path.join('Outputs/SAR', f'Yosemite_merged.tiff')

with rasterio.open(merged_image_path, 'w', driver='GTiff', 
                   height=merged_image.shape[1], width=merged_image.shape[2], 
                   count=merged_image.shape[0], 
                   dtype=merged_image.dtype, 
                   crs='+proj=utm +zone=11 +ellps=WGS84 +datum=WGS84 +units=m +no_defs', 
                   transform=out_trans) as dst:
    dst.write(merged_image)
print(f"Merged image saved to: {merged_image_path}")

import rasterio.warp

# Reproject merged image from UTM11N to WGS84 (EPSG:4326)
print("Reprojecting merged image to WGS84...")
reprojected_image_path = 'Outputs/SAR/Yosemite_merged_WGS84.tiff'  # Define the path for the reprojected image
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
print("Reprojection completed. Merged image saved in WGS84 (EPSG:4326) format.")

# Function to insert data into PostgreSQL database
def insert_data_into_database(image_path, time_collected):
    """Inserts data into PostgreSQL database.

    Args:
        image_path (str): Path to the image file.
        time_collected (datetime): Timestamp indicating when the image was collected.

    Returns:
        None
    """
    connection = psycopg2.connect(
        user="postgres",
        password="admin",
        host="DESKTOP-UIUIA2A",
        port="5432",
        database="FTM8"
    )

    cursor = connection.cursor()
    
    # SQL query to insert data into the table
    insert_query = "INSERT INTO sar_raw (path, time_collected) VALUES (%s, %s)"
    
    # Data to be inserted
    record_to_insert = (image_path, time_collected)

    try:
        # Execute the SQL command
        cursor.execute(insert_query, record_to_insert)

        # Commit your changes in the database
        connection.commit()
        print("Data inserted successfully into PostgreSQL")

    except (Exception, psycopg2.Error) as error:
        print("Error while inserting data into PostgreSQL", error)

    finally:
        # Closing database connection
        if connection:
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")

# Insert data into PostgreSQL database
insert_data_into_database(reprojected_image_path, datetime.now())


# Clear the folder 'Outputs/SAR/temp' at the end of the script
import shutil
shutil.rmtree('Outputs/SAR/temp', ignore_errors=True)
os.makedirs('Outputs/SAR/temp', exist_ok=True)
print("Temporary raster files cleared.")

print("sentinel.py completed.")
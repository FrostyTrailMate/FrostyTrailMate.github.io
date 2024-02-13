from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
import requests
import os
import json
import geopandas as gpd
from sentinelhub import SHConfig, CRS, BBox, DataCollection, SentinelHubRequest, MimeType, bbox_to_dimensions, BBoxSplitter
from sentinelhub.geo_utils import bbox_to_dimensions, to_utm_bbox
import rasterio
from rasterio.merge import merge
from rasterio.transform import Affine
from rasterio.enums import Resampling
import sys
from datetime import datetime, timedelta, timezone
import psycopg2
import concurrent.futures
import time
import threading

# Your client credentials
client_id = '33054a13-b0b8-45c0-b2f5-bc9e9dc8db25'
client_secret = 'qBwcx5AQtfsLZKxZUlCIcYRQVLtzXof5'

# Set up Sentinel Hub configuration
print("Setting up Sentinel Hub configuration...")
config = SHConfig()
config.sh_client_id = client_id
config.sh_client_secret = client_secret

# Create a session
print("Creating OAuth session...")
client = BackendApplicationClient(client_id=client_id)
oauth = OAuth2Session(client=client)

# Get token for the session
print("Fetching OAuth token...")
token = oauth.fetch_token(token_url='https://services.sentinel-hub.com/auth/realms/main/protocol/openid-connect/token',
                          client_secret=client_secret, include_client_id=True)

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
        sampleType: "AUTO"
      }
    ]
  };
}

function evaluatePixel(samples) {
  return [samples.VV, samples.VH];
}
"""

# Define resolution in meters per pixel
resolution = 10  # Adjust the resolution as needed

# Split bounding box into smaller sub-boxes with size limited to 2500 pixels
split_size = (2500, 2500)
print("Splitting bounding box into smaller sub-boxes...")
bbox_splitter = BBoxSplitter([utm_bbox], utm_bbox.crs, split_size=split_size)
sub_bbox_list = bbox_splitter.get_bbox_list()

end_date = datetime.now(timezone.utc)
start_date = end_date - timedelta(days=5)

# Define function to make requests for a single sub-box
def request_images_for_sub_box(sub_bbox, evalscript, data_folder, index):
    sys.stdout.write(f"\rRequesting sub-box {index+1}/{len(sub_bbox_list)}...")
    sys.stdout.flush()

    # Define the filename based on the bounding box coordinates
    filename = os.path.join(data_folder, f"image_{index}.tif")
    # Check if the file already exists locally
    if os.path.exists(filename):
        print(f"File for sub-box {index+1} already exists locally. Skipping...")
    else:
        request_image = SentinelHubRequest(
            evalscript=evalscript,
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
        
        # Introduce a delay to avoid rate limit
        time.sleep(.5)  # Adjust the delay as needed

# Define function to download images for multiple sub-boxes using multithreading
def download_images_multi_thread(sub_bbox_list, evalscript, data_folder):
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:  # Alter number of connections if needed. 4 works well
        futures = []
        for i, sub_bbox in enumerate(sub_bbox_list):
            futures.append(executor.submit(request_images_for_sub_box, sub_bbox, evalscript, data_folder, i))
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error occurred: {e}")

# Make requests for each sub-box using multithreading
data_folder = 'Outputs/SAR/temp'
download_images_multi_thread(sub_bbox_list, evalscript, data_folder)

# Define the function to search for image files in all subdirectories
def find_image_files(data_folder):
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

# Extract date of image capture
date_of_image_capture = image_files[0].split('_')[-1].split('.')[0]

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

# Function to insert data into PostgreSQL database
def insert_data_into_database(image_path, time_collected):
    connection = psycopg2.connect(
        user="postgres",
        password="admin",
        host="DESKTOP-UIUIA2A",
        port="5432",
        database="FTM8"
    )

    cursor = connection.cursor()
    
    # SQL query to insert data into the table
    insert_query = """INSERT INTO sar_raw (path, time_collected) VALUES (%s, %s)"""
    
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
insert_data_into_database(merged_image_path, datetime.now())

# Clear the folder 'Outputs/SAR/temp' at the end of the script
import shutil
shutil.rmtree('Outputs/SAR/temp', ignore_errors=True)
print("Temporary raster files cleared.")

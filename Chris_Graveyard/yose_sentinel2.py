import os
from datetime import datetime, timedelta
import json
import requests
import geopandas as gpd
from shapely.geometry import shape, Polygon, mapping    
from sentinelhub import SHConfig, DataCollection, SentinelHubRequest, bbox_to_dimensions, DownloadRequest, SentinelHubCatalog
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

import psycopg2

# Set up Sentinel Hub configuration
client_id = 'b15c8cd5-e24c-4eb4-894f-4ad544e6a59f'
client_secret = 'WRewj3YLfo0jb81YSA9duxrupDvxn2EX'

# Create a session
client = BackendApplicationClient(client_id=client_id)
oauth = OAuth2Session(client=client)

# Get token for the session
token = oauth.fetch_token(token_url='https://services.sentinel-hub.com/auth/realms/main/protocol/openid-connect/token',
                          client_secret=client_secret, include_client_id=True)

# Define paths
shapefile_path = 'Shapefiles/Yosemite_Boundary_4326.zip'
output_folder = 'Output/SAR_raw'

# Connect to PostgreSQL database
try:
    conn = psycopg2.connect(dbname="FTM8", user="postgres", password="admin", host="26.54.17.86", port="5432")
    cursor = conn.cursor()

    # Check if SAR_raw table exists, if not create it
    cursor.execute("CREATE TABLE IF NOT EXISTS SAR_raw (path_row VARCHAR, capture_datetime TIMESTAMP, file_path VARCHAR)")
except psycopg2.OperationalError as e:
    print(f"Failed to connect to PostgreSQL database: {e}")
    exit(1)

def download_and_save_image(bbox, capture_datetime):
    try:
        # Define download folder and filename
        file_path = os.path.join(output_folder, f'SAR_{capture_datetime.strftime("%Y%m%dT%H%M%S")}.tif')

        # Create request
        request = SentinelHubRequest(
            data_folder=output_folder,
            evalscript='''//VERSION=3
                function setup() {
                    return {
                        input: [{
                            bands: ["VV", "VH"]
                        }],
                        output: {
                            bands: 2
                        }
                    };
                }

                function evaluatePixel(sample) {
                    return [sample.VV, sample.VH];
                }''',
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=DataCollection.SENTINEL1_IW,
                    time_interval=(capture_datetime - timedelta(days=1), capture_datetime),
                    mosaicking_order='mostRecent',
                    other_args={
                        'resolution': '10m',
                        'processing': {
                            'orthorectify': True
                        }
                    }
                )
            ],
            responses=[
                SentinelHubRequest.output_response('default', 'tiff')
            ],
            bbox=bbox,
            size=bbox_to_dimensions(bbox, resolution=10)
        )

        # Download the image
        request.save_data()

        return file_path, True  # Return file path and success status
    except Exception as e:
        print(f"Failed to download and save image: {e}")
        return None, False  # Return None and failure status

def check_and_download_new_images():
    try:
        # Load shapefile
        print("Loading shapefile...")
        gdf = gpd.read_file(shapefile_path)
        
        # Extract bounding box coordinates
        print("Extracting bounding box coordinates...")
        bbox_coords = gdf.total_bounds
        
        # Get yesterday's date
        print("Calculating yesterday's date...")
        yesterday = datetime.now() - timedelta(days=1)

        # Set up Sentinel Hub config
        print("Setting up Sentinel Hub configuration...")
        config = SHConfig()
        config.instance_id = '44b8b66c-925c-4ab5-a776-b1f48364172d'  # Set instance ID

        # Define search filter
        search_filter = {
            "type": "AndFilter",
            "config": [
                {
                    "type": "GeometryFilter",
                    "field_name": "geometry",
                    "config": {
                        "type": "BoundingBox",
                        "coordinates": [[
                            [bbox_coords[0], bbox_coords[1]],  # Lower-left corner
                            [bbox_coords[0], bbox_coords[3]],  # Upper-left corner
                            [bbox_coords[2], bbox_coords[3]],  # Upper-right corner
                            [bbox_coords[2], bbox_coords[1]],  # Lower-right corner
                            [bbox_coords[0], bbox_coords[1]]   # Close the polygon
                        ]]
                    }
                }
            ]
        }
        print("Before catalog search")
        catalog = SentinelHubCatalog(config=config)
        tiles = catalog.search(
            DataCollection.SENTINEL1_IW,
            bbox=bbox_coords,
            time=(yesterday, datetime.now()),
            filter=search_filter
        )
        print("After catalog search")

        # Iterate over search results
        print("Iterating over search results...")
        for tile_info in tiles:
            capture_datetime = tile_info['properties']['date']
            bbox = tile_info['geometry']['coordinates'][0]
            tile_polygon = Polygon(bbox)
            print("Tile Polygon:", tile_polygon)
            print("Boundary Polygon:", Polygon(bbox_coords))

            if Polygon(bbox_coords).intersects(tile_polygon.boundary):  # Check for intersection
                print("Intersection found. Downloading and saving image...")
                file_path, success = download_and_save_image(bbox, capture_datetime)
                if success and file_path:
                    print("Image downloaded and saved successfully.")
                    path_row = f"{tile_info['properties']['path']}-{tile_info['properties']['row']}"
                    # Insert record into database
                    cursor.execute("INSERT INTO SAR_raw (path_row, capture_datetime, file_path) VALUES (%s, %s, %s)", (path_row, capture_datetime, file_path))
                    conn.commit()
                else:
                    print("Failed to download and save the image.")
            else:
                print("No intersection found.")
    except Exception as e:
        print(f"Error occurred while checking and downloading new images: {e}")


if __name__ == "__main__":
    check_and_download_new_images()

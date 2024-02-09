import os
from datetime import datetime, timedelta
import json
import requests
import geopandas as gpd
from shapely.geometry import shape
from sentinelhub import SHConfig, DataCollection, SentinelHubRequest, bbox_to_dimensions, DownloadRequest
import psycopg2

# Set up Sentinel Hub configuration
config = SHConfig()
config.instance_id = '44b8b66c-925c-4ab5-a776-b1f48364172d'

# Define paths
shapefile_path = 'Shapefiles/Yosemite_Boundary.zip'
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
                    data_collection=DataCollection.SENTINEL1_GRD,
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

        return file_path
    except Exception as e:
        print(f"Failed to download and save image: {e}")
        return None

def check_and_download_new_images():
    try:
        # Load shapefile
        gdf = gpd.read_file(shapefile_path)
        boundary = shape(gdf['geometry'].iloc[0])

        # Get yesterday's date
        yesterday = datetime.now() - timedelta(days=1)

        # Check for new images
        request_url = f'https://services.sentinel-hub.com/api/v1/process/tiles?timeFrom={yesterday.strftime("%Y-%m-%d")}&timeTo={datetime.now().strftime("%Y-%m-%d")}&tileService=sentinel-1&zoomLevel=2&tileResolution=64&geohash={boundary.centroid.y},{boundary.centroid.x}&instance_id={config.instance_id}'
        # https://services.sentinel-hub.com/api/v1/process/tiles?timeFrom=2024-02-08&timeTo=2024-02-09&tileService=sentinel-1-grd&zoomLevel=2&tileResolution=64&geohash=4192049.3984367144,275015.10698296566&instance_id=44b8b66c-925c-4ab5-a776-b1f48364172d
        response = requests.get(request_url)
        if response.status_code == 200:
            tiles = response.json()
            for tile in tiles:
                capture_datetime = datetime.strptime(tile['properties']['datetime'], '%Y-%m-%dT%H:%M:%SZ')
                bbox = tile['bbox']
                if boundary.intersects(shape({
                    "type": "Polygon",
                    "coordinates": [[
                        [bbox[0], bbox[1]],
                        [bbox[0], bbox[3]],
                        [bbox[2], bbox[3]],
                        [bbox[2], bbox[1]],
                        [bbox[0], bbox[1]]
                    ]]
                })):
                    file_path = download_and_save_image(bbox, capture_datetime)
                    if file_path:
                        path_row = f"{tile['properties']['path']}-{tile['properties']['row']}"
                        # Insert record into database
                        cursor.execute("INSERT INTO SAR_raw (path_row, capture_datetime, file_path) VALUES (%s, %s, %s)", (path_row, capture_datetime, file_path))
                        conn.commit()
        else:
            print("Failed to retrieve tiles from Sentinel Hub API")
            print(request_url)
            print(response.content)
    except Exception as e:
        print(f"Error occurred while checking and downloading new images: {e}")

if __name__ == "__main__":
    check_and_download_new_images()

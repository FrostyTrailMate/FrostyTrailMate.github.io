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

from sentinelhub import SHConfig, SentinelHubRequest, SentinelHubCatalog, bbox_to_dimensions, DownloadRequest, DataCollection

from datetime import datetime, timedelta

from shapely.geometry import Polygon

def check_and_download_new_images():
    try:
        # Load shapefile
        gdf = gpd.read_file(shapefile_path)
        
        # Extract bounding box coordinates
        bbox_coords = gdf.total_bounds
        
        # Create a Polygon from the bounding box coordinates
        boundary_polygon = Polygon.from_bounds(*bbox_coords)

        # Get yesterday's date
        yesterday = datetime.now() - timedelta(days=1)

        # Set up Sentinel Hub config
        config = SHConfig()
        config.instance_id = '44b8b66c-925c-4ab5-a776-b1f48364172d'  # Set instance ID

        # Define search parameters
        catalog = SentinelHubCatalog(config=config)
        tiles = catalog.search(
            DataCollection.SENTINEL1_IW,
            bbox=bbox_coords,
            time=(yesterday, datetime.now()),
            filter={
                "type": "OrFilter",
                "config": [
                    {
                        "type": "GeometryFilter",
                        "field_name": "geometry",
                        "config": {
                            "type": "Polygon",
                            "coordinates": [boundary_polygon.exterior.coords[:]]
                        }
                    }
                ]
            }
        )

        # Iterate over search results
        for tile_info in tiles:
            capture_datetime = tile_info['properties']['date']
            bbox = tile_info['geometry']['coordinates'][0]
            tile_polygon = Polygon(bbox)
            if boundary_polygon.intersects(tile_polygon):  # Check for intersection
                file_path = download_and_save_image(bbox, capture_datetime)
                if file_path:
                    path_row = f"{tile_info['properties']['path']}-{tile_info['properties']['row']}"
                    # Insert record into database
                    cursor.execute("INSERT INTO SAR_raw (path_row, capture_datetime, file_path) VALUES (%s, %s, %s)", (path_row, capture_datetime, file_path))
                    conn.commit()
    except Exception as e:
        print(f"Error occurred while checking and downloading new images: {e}")


if __name__ == "__main__":
    check_and_download_new_images()

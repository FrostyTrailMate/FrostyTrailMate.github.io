import os
import json
from datetime import datetime, timedelta
import geopandas as gpd
from shapely.geometry import mapping
import requests
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
from sentinelsat import SentinelAPI
from osgeo import ogr, osr

# Your client credentials
client_id = '33054a13-b0b8-45c0-b2f5-bc9e9dc8db25'
client_secret = 'qBwcx5AQtfsLZKxZUlCIcYRQVLtzXof5'

# Create a session
client = BackendApplicationClient(client_id=client_id)
oauth = OAuth2Session(client=client)

# Get token for the session
token = oauth.fetch_token(token_url='https://services.sentinel-hub.com/auth/realms/main/protocol/openid-connect/token',
                          client_secret=client_secret, include_client_id=True)

# Define function to check if image already exists in the database
def image_exists_in_db(sRow, sPath, sSlice, datetime):
    # Code to check if image exists in the database
    pass

# Define function to connect to the database and store information about the imagery
def store_image_info_in_db(datetime, sRow, sPath, sSlice, sArea, raster_path):
    # Code to connect to the database and store information
    pass

# Define function to collect Sentinel-1 GRD IW data from Sentinel Hub
def collect_sentinel1_data(bbox_shapefile, output_folder):
    # Load shapefile
    gdf = gpd.read_file(bbox_shapefile)
    bbox = gdf.geometry.bounds.iloc[0]

    # Convert bbox to EPSG:4326
    source = osr.SpatialReference()
    source.ImportFromEPSG(4326)
    target = osr.SpatialReference()
    target.ImportFromEPSG(3857) # WGS 84 / Pseudo-Mercator
    transform = osr.CoordinateTransformation(source, target)
    min_lon, min_lat = transform.TransformPoint(bbox[0], bbox[1])[:2]
    max_lon, max_lat = transform.TransformPoint(bbox[2], bbox[3])[:2]

    # Define time range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=5)

    # Define search parameters
    search_params = {
        'platformname': 'Sentinel-1',
        'producttype': 'GRD',
        'sensoroperationalmode': 'IW',
        'ingestiondate': (start_date.date(), end_date.date()),
        'bbox': (min_lon, min_lat, max_lon, max_lat),
        'sortby': 'ingestiondate',
        'limit': 1
    }

    # Connect to Sentinel Hub API
    api = SentinelAPI(client_id, client_secret)

    # Search for imagery
    try:
        products = api.query(**search_params)
    except Exception as e:
        print(f"Error occurred while querying Sentinel Hub API: {str(e)}")
        return

    if not products:
        print("No imagery found within the specified time frame and bounding box.")
        return

    for product_id in products:
        product_info = api.get_product_odata(product_id)
        datetime_str = product_info['date']
        sRow = product_info['s2datatake']
        sPath = product_info['s2datatake']
        sSlice = product_info['s2datatake']
        sArea = os.path.basename(bbox_shapefile)
        raster_path = os.path.join(output_folder, f"{product_id}.tiff")

        # Check if image already exists in the database
        if image_exists_in_db(sRow, sPath, sSlice, datetime_str):
            print(f"Image already exists in the database: {product_id}")
            continue

        # Download the image
        try:
            api.download(product_id, directory_path=output_folder)
        except Exception as e:
            print(f"Error occurred while downloading image {product_id}: {str(e)}")
            continue

        # Store information about the imagery in the database
        store_image_info_in_db(datetime_str, sRow, sPath, sSlice, sArea, raster_path)
        print(f"Image {product_id} downloaded and information stored in the database.")

# Define paths
shapefile_path = 'Shapefiles/Yosemite_Boundary_4326.shp'
output_folder = 'Outputs/SAR'

# Collect Sentinel-1 GRD IW data
collect_sentinel1_data(shapefile_path, output_folder)

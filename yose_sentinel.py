import psycopg2
from psycopg2 import sql
from datetime import datetime, timedelta
import os
from sentinelhub import SHConfig, DataCollection, SentinelHubRequest, bbox_to_dimensions
import geopandas as gpd
import pandas as pd
import rasterio
from shapely.geometry import box

# Set up Sentinel Hub configuration
config = SHConfig()
config.instance_id = '44b8b66c-925c-4ab5-a776-b1f48364172d'  # Replace with your Sentinel Hub instance ID

# Function to check if image already exists in the database
def check_image_existence(datetime_value):
    connection = psycopg2.connect(user="postgres",
                                  password="admin",
                                  host="DESKTOP-UIUIA2A",
                                  port="5432",
                                  database="FTM8")
    cursor = connection.cursor()
    query = sql.SQL("SELECT * FROM your_table WHERE datetime = %s;")
    cursor.execute(query, (datetime_value,))
    exists = cursor.fetchone() is not None
    cursor.close()
    connection.close()
    return exists

# Function to download Sentinel-1 data
def download_sentinel_data(bbox, crs, time_range, output_path, clip_shapefile):
    resolution = 10  # Resolution in meters

    bbox_gdf = gpd.GeoDataFrame(geometry=[box(*bbox)], crs=crs)
    bbox_gdf = bbox_gdf.to_crs('EPSG:4326')  # Transform to WGS84 for bbox_to_dimensions
    bbox_transformed = bbox_gdf.geometry[0].bounds

    image_width, image_height = bbox_to_dimensions(bbox_transformed, crs=crs, resolution=resolution)

    request_params = {
        'data_collection': DataCollection.SENTINEL1_GRD,
        'bbox': bbox,
        'time': time_range,
        'width': image_width,
        'height': image_height,
        'config': config,
    }

    request = SentinelHubRequest(**request_params)
    data = request.get_data()

    # Read the shapefile to extract the clip geometry
    clip_gdf = gpd.read_file(clip_shapefile)
    clip_bounds = clip_gdf.geometry.total_bounds

    # Transform the clip bounds to the CRS of the data
    transform_bounds = rasterio.warp.transform_bounds(clip_gdf.crs, request.get_crs(), *clip_bounds)

    # Clip the data to the transformed clip bounds
    clipped_data = [rasterio.mask.mask(data_item, [rasterio.features.geometry_mask([transform_bounds], 
                                    out_shape=(data_item.shape[1], data_item.shape[2]),
                                    transform=data_item.transform,
                                    invert=False)]) for data_item in data]

    # Save the clipped data if it doesn't already exist
    output_path = 'Outputs/SAR_raw'
    
    for idx, time_slice in enumerate(clipped_data):
        datetime_value = time_slice.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        if not check_image_existence(datetime_value):
            image_path = os.path.join(output_path, f'Yosemite_{idx}.tif') #### Change output file name - Chris
            with rasterio.open(image_path, 'w', **time_slice[0]) as dst:
                dst.write(time_slice[1])
            print(f'Saved clipped image {image_path}')
            # Insert datetime into the database
            insert_datetime(datetime_value)
        else:
            print(f"Image already obtained for datetime: {datetime_value}")

# Function to insert datetime into the database   #### NEED TO UPDATE THIS - Chris
def insert_datetime(datetime_value):
    connection = psycopg2.connect(user="postgres",
                                  password="admin",
                                  host="DESKTOP-UIUIA2A",
                                  port="5432",
                                  database="FTM8")
    cursor = connection.cursor()
    query = sql.SQL("INSERT INTO your_table (datetime) VALUES (%s);")
    cursor.execute(query, (datetime_value,))
    connection.commit()
    cursor.close()
    connection.close()

# Read the shapefile to extract the bounding box
yosemite_boundary_shapefile = 'Shapefiles/Yosemite_Boundary.shp'
yosemite_boundary_gdf = gpd.read_file(yosemite_boundary_shapefile)
yosemite_bbox = yosemite_boundary_gdf.total_bounds
yosemite_crs = yosemite_boundary_gdf.crs

# Determine date ranges
today = datetime.today()
yesterday = datetime.now() - timedelta(1)
most_recent_range = (yesterday, today)
most_recent_september_start = datetime(today.year, 9, 1) if today.month >= 9 else datetime(today.year - 1, 9, 1)
most_recent_september_end = datetime(today.year, 9, 30) if today.month >= 9 else datetime(today.year - 1, 9, 30)
most_recent_september_range = (most_recent_september_start, most_recent_september_end)


# Output paths - UPDATE - Chris
most_recent_september_output = 'most_recent_september_image.tif'
most_recent_output = 'most_recent_image.tif'

# Download Sentinel-1 data for the most recent September and clip to Yosemite Boundary
download_sentinel_data(yosemite_bbox, yosemite_crs, most_recent_september_range, most_recent_september_output, yosemite_boundary_shapefile)

# Download Sentinel-1 data for the most recent period and clip to Yosemite Boundary
download_sentinel_data(yosemite_bbox, yosemite_crs, most_recent_range, most_recent_output, yosemite_boundary_shapefile)


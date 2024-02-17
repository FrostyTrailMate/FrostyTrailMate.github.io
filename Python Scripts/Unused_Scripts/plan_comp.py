import os
import sys
import requests
import psycopg2
import pystac_client
import planetary_computer
import numpy as np
import geopandas as gpd
import datetime
import rasterio
from rasterio.mask import mask
from shapely.geometry import box, mapping
from tqdm import tqdm
from osgeo import gdal, osr, ogr

# Set Planetary Computer SDK subscription key and get expiry date
os.environ["PC_SDK_SUBSCRIPTION_KEY"] = "257070e40b1948a390778f44a1bf178a"

# Function to download assets with progress tracking
def download_asset_with_progress(asset_href, asset_filename):
    if not os.path.exists(asset_filename):
        response = requests.get(asset_href, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024
        t = tqdm(total=total_size, unit='B', unit_scale=True, desc=os.path.basename(asset_filename), leave=False)
        with open(asset_filename, 'wb') as f:
            for data in response.iter_content(block_size):
                t.update(len(data))
                f.write(data)
        t.close()
        if total_size != 0 and t.n != total_size:
            print("Error downloading asset!")
    else:
        print(f"Asset {asset_filename} already exists. Skipping download.")

def download_asset_with_progress_and_size_check(asset_href, asset_filename):
    if not os.path.exists(asset_filename):
        response = requests.head(asset_href)
        content_length_mb = int(response.headers.get('content-length', 0)) / (1024 * 1024)
        if content_length_mb < 10:
            print(f"Asset {asset_filename} is less than 10 megabytes in size. Skipping download.")
            return

        download_asset_with_progress(asset_href, asset_filename)
    else:
        print(f"Asset {asset_filename} already exists. Skipping download.")

# Function to invert raster
def invert_raster(raster_path):
    with rasterio.open(raster_path, 'r+') as src:
        data = src.read(1)  # Read the raster band
        inverted_data = np.where(data != 0, 0, 1)  # Invert non-zero values
        src.write(inverted_data, 1)  # Write the inverted data back to the raster band

# Open the Planetary Computer STAC API
print("Connecting to Planetary Computer STAC API...")
catalog = pystac_client.Client.open(
    "https://planetarycomputer.microsoft.com/api/stac/v1",
    modifier=planetary_computer.sign_inplace,
)

# Create search query and return number of results
print("Performing search query...")
yosemite_boundary = gpd.read_file('Shapefiles/Yosemite_Boundary_4326.shp')
bbox_of_interest = yosemite_boundary.total_bounds.tolist() 

end_date = datetime.datetime.now()
start_date = end_date - datetime.timedelta(days=60)
time_of_interest = f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"

search = catalog.search(
    collections=["sentinel-1-rtc"],
    bbox=bbox_of_interest,
    datetime=time_of_interest,
)

# Define the minimum coverage ratio required (e.g., 0.5 for 50%)
min_coverage_ratio = 0.5

# Calculate the area of the bounding box of interest
bbox_area = (bbox_of_interest[2] - bbox_of_interest[0]) * (bbox_of_interest[3] - bbox_of_interest[1])

filtered_items = []
for item in search.items():
    item_bbox = item.to_dict()['bbox']
    # Calculate the intersection area
    intersection_area = max(0, min(bbox_of_interest[2], item_bbox[2]) - max(bbox_of_interest[0], item_bbox[0])) * \
                        max(0, min(bbox_of_interest[3], item_bbox[3]) - max(bbox_of_interest[1], item_bbox[1]))
    # Calculate coverage ratio
    coverage_ratio = intersection_area / bbox_area
    # Check if coverage ratio is above the threshold
    if coverage_ratio >= min_coverage_ratio:
        filtered_items.append(item)

print(f"Returned {len(filtered_items)} Items covering at least {min_coverage_ratio * 100}% of the study area")

if not filtered_items:
    print("No suitable imagery found. Exiting...")
    sys.exit()

# Sort filtered items based on acquisition datetime
sorted_items = sorted(filtered_items, key=lambda x: x.datetime, reverse=True)

# Set the output folder
output_folder = 'Outputs/SAR'

# Create the output folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# Connect to PostgreSQL database
print("Connecting to PostgreSQL database...")
conn = psycopg2.connect(
    dbname="FTM8",
    user="postgres",
    password="admin",
    host="DESKTOP-UIUIA2A",
    port="5432"
)

# Create a cursor object using the cursor() method
cursor = conn.cursor()

# Check if the most recent imagery has already been downloaded
most_recent_item = sorted_items[0]
image_id = f"{most_recent_item.id}_vh.tif"  # Adjust this if needed based on your image naming convention

# SQL query to check if the image has already been downloaded
sql_check = "SELECT COUNT(*) FROM sar_raw WHERE image = %s"
cursor.execute(sql_check, (image_id,))
count = cursor.fetchone()[0]

if count > 0:
    print(f"The most recent image ({image_id}) has already been downloaded. Exiting...")
    sys.exit()
else:
    print(f"The most recent image ({image_id}) has not been downloaded yet. Proceeding with download...")

# Download the assets of the most recent item to the output folder
print("Downloading assets...")
asset_paths = {}
for asset_key, asset in most_recent_item.assets.items():
    asset_href = asset.href
    asset_filename = os.path.join(output_folder, f"{most_recent_item.id}_{asset_key}.tif")
    try:
        print(f"Downloading asset: {asset_key}")
        download_asset_with_progress_and_size_check(asset_href, asset_filename)
        asset_paths[asset_key] = asset_filename
    except Exception as e:
        print(f"Failed to download asset: {asset_key}. Error: {str(e)}")

print(f"Downloaded assets of the most recent item to: {output_folder}")

# Check the orbit state
orbit_state = most_recent_item.properties.get("sar:orbit_state", None)

# Invert the raster if the orbit state is descending
if orbit_state == "DESCENDING":
    for asset_key, asset_path in asset_paths.items():
        invert_raster(asset_path)
        print(f"Inverted raster: {asset_path}")

# Function to clip raster using GDAL
def clip_raster(raster_path, output_path, shapefile_path):
    # Open raster dataset
    raster_ds = gdal.Open(raster_path)
    if raster_ds is None:
        print(f"Failed to open raster dataset: {raster_path}")
        return False

    # Get raster spatial reference
    raster_proj = raster_ds.GetProjection()
    raster_srs = osr.SpatialReference()
    raster_srs.ImportFromWkt(raster_proj)

    # Open shapefile and get its spatial reference
    shapefile_ds = ogr.Open(shapefile_path)
    if shapefile_ds is None:
        print(f"Failed to open shapefile: {shapefile_path}")
        return False

    shapefile_layer = shapefile_ds.GetLayer()
    shapefile_srs = shapefile_layer.GetSpatialRef()

    # Reproject shapefile if needed
    if not raster_srs.IsSame(shapefile_srs):
        transform = osr.CoordinateTransformation(shapefile_srs, raster_srs)
        geom_transformed = ogr.Geometry(ogr.wkbMultiPolygon)
        for feature in shapefile_layer:
            geom = feature.GetGeometryRef()
            geom.Transform(transform)
            geom_transformed.AddGeometry(geom)
        shapefile_layer = None  # Close shapefile
    else:
        geom_transformed = shapefile_layer.GetGeometryRef()

    # Clip raster using shapefile geometry
    gdal.Translate(output_path, raster_ds, format='GTiff', projWin=geom_transformed.GetEnvelope())

    raster_ds = None  # Close raster dataset

    return True

# Function to reproject raster using GDAL
def reproject_raster(input_path, output_path, target_epsg):
    # Open input raster dataset
    input_ds = gdal.Open(input_path)
    if input_ds is None:
        print(f"Failed to open input raster dataset: {input_path}")
        return False

    # Get input raster spatial reference
    input_proj = input_ds.GetProjection()
    input_srs = osr.SpatialReference()
    input_srs.ImportFromWkt(input_proj)

    # Create transformation from input to target CRS
    target_srs = osr.SpatialReference()
    target_srs.ImportFromEPSG(target_epsg)
    transform = osr.CoordinateTransformation(input_srs, target_srs)

    # Get input raster dimensions
    width = input_ds.RasterXSize
    height = input_ds.RasterYSize

    # Create output raster dataset
    output_ds = gdal.GetDriverByName('GTiff').Create(output_path, width, height, input_ds.RasterCount)
    output_ds.SetProjection(target_srs.ExportToWkt())
    output_ds.SetGeoTransform(input_ds.GetGeoTransform())

    # Reproject each band
    for i in range(1, input_ds.RasterCount + 1):
        band = input_ds.GetRasterBand(i)
        output_band = output_ds.GetRasterBand(i)
        gdal.ReprojectImage(input_ds, output_ds, input_srs.ExportToWkt(), target_srs.ExportToWkt(), gdal.GRA_NearestNeighbour)

    # Close datasets
    input_ds = None
    output_ds = None

    return True

# Reproject the downloaded raster to EPSG:4326
print("Reprojecting raster to EPSG:4326...")
reprojected_asset_paths = {}
for asset_key, asset_path in asset_paths.items():
    try:
        reprojected_asset_path = os.path.join(output_folder, f"{most_recent_item.id}_{asset_key}_reprojected.tif")
        if reproject_raster(asset_path, reprojected_asset_path, 4326):
            reprojected_asset_paths[asset_key] = reprojected_asset_path
            print(f"Reprojected asset: {asset_key} to: {reprojected_asset_path}")
        else:
            print(f"Failed to reproject asset: {asset_key}")
    except Exception as e:
        print(f"Failed to reproject asset: {asset_key}. Error: {str(e)}")

# Clip the reprojected raster to the study area boundary
print("Clipping reprojected rasters...")
clipped_asset_paths = {}
for asset_key, asset_path in reprojected_asset_paths.items():
    try:
        # Check if the asset has been successfully reprojected
        if not os.path.exists(asset_path):
            print(f"Asset {asset_key} has not been reprojected. Skipping clipping.")
            continue
        
        # Check the file size
        file_size_mb = os.path.getsize(asset_path) / (1024 * 1024)
        if file_size_mb <= 1:
            print(f"Asset {asset_key} is less than or equal to 1 megabyte in size. Skipping clipping.")
            continue

        clipped_asset_path = os.path.join(output_folder, f"{most_recent_item.id}_{asset_key}_clipped.tif")

        if clip_raster(asset_path, clipped_asset_path, 'Shapefiles/Yosemite_Boundary_4326.shp'):
            clipped_asset_paths[asset_key] = clipped_asset_path
            print(f"Clipped asset: {asset_key} to: {clipped_asset_path}")
        else:
            print(f"Failed to clip asset: {asset_key}")
    except Exception as e:
        print(f"Failed to clip asset: {asset_key}. Error: {str(e)}")

# Insert information into the 'sar_raw' table
print("Inserting data into the 'sar_raw' table...")
for asset_key, asset_path in clipped_asset_paths.items():
    date_time_downloaded = datetime.datetime.now()
    date_time_captured = most_recent_item.datetime
    relative_orbit_number = most_recent_item.properties["sar:orbit_number"]
    slice_number = most_recent_item.properties["sar:slice_number"]
    polarizations = most_recent_item.properties["sar:polarizations"]
    platform = most_recent_item.properties["platform"]
    
    # SQL query to insert data into the 'sar_raw' table
    sql = f"""INSERT INTO sar_raw (time_collected, datetime, sOrbit, sSlice, polarizations, sArea, path, image, platform)
              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
    
    # Execute the SQL command
    cursor.execute(sql, (date_time_downloaded, date_time_captured, relative_orbit_number, slice_number, polarizations, 'Yosemite', asset_path, f"{most_recent_item.id}_{asset_key}.tif", platform))

# Commit changes to the database
conn.commit()

# Close the cursor and database connection
cursor.close()
conn.close()

print("Data inserted into the 'sar_raw' table successfully.")

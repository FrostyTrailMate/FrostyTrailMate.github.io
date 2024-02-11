import ee
import zipfile
import os
from datetime import datetime, timedelta
import pytz
import time

# Authentication with Google Earth Engine
print("Authenticating with Google Earth Engine...")
try:
    ee.Initialize()
    print("Authentication successful.")
except Exception as e:
    print(f"Error authenticating with Google Earth Engine: {e}")

# Define output folder
print("Creating output folder...")
output_folder = "Outputs/SAR"
try:
    os.makedirs(output_folder, exist_ok=True)
    print(f"Output folder created: {output_folder}")
except Exception as e:
    print(f"Error creating output folder: {e}")

# Define shapefile path and EPSG code
print("Defining shapefile path and EPSG code...")
shapefile_path = os.path.join("Shapefiles", "Yosemite_Boundary_4326.zip")
epsg_code = 4326

# Function to clip images to shapefile
print("Defining function to clip images to shapefile...")
def clip_to_shapefile(image, shapefile_path):
    try:
        # Extract shapefile from the ZIP file
        with zipfile.ZipFile(shapefile_path, 'r') as zip_ref:
            zip_ref.extractall("Shapefiles")
            extracted_files = zip_ref.namelist()

        # Find the shapefile within the extracted files
        shapefile_name = None
        for file in extracted_files:
            if file.endswith(".shp"):
                shapefile_name = file
                break

        if shapefile_name:
            shapefile_path = os.path.join("Shapefiles", shapefile_name)

            # Read shapefile geometry
            geometry = ee.FeatureCollection(shapefile_path).geometry()

            # Clip image to geometry
            return image.clip(geometry)
        else:
            print("Error: Shapefile not found in ZIP file.")
            return None
    except Exception as e:
        print(f"Error clipping image to shapefile: {e}")
        return None

# Define Sentinel-1 collection and filters
print("Defining Sentinel-1 collection and filters...")
try:
    sentinel1_collection = ee.ImageCollection('COPERNICUS/S1_GRD')
    today = datetime.now(pytz.utc)  # Use pytz.utc for timezone awareness
    yesterday = today - timedelta(days=1)
    print("Sentinel-1 collection defined successfully.")
except Exception as e:
    print(f"Error defining Sentinel-1 collection and filters: {e}")

# Filter by date
print("Filtering by date...")
try:
    filtered_collection = sentinel1_collection.filterDate(
        yesterday.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")
    )
    print("Filtering successful.")
except Exception as e:
    print(f"Error filtering collection: {e}")

# Download new images
print("Preparing image download...")
try:
    for image in filtered_collection.getInfo()['features']:
        image_id = image['id']
        output_path = os.path.join(output_folder, f"{image_id}.tif")

        # Check if image already exists
        print(f"Checking if image {image_id} already exists...")
        if not os.path.exists(output_path):
            print(f"Downloading image: {image_id}")
            try:
                image = ee.Image(image_id)
                clipped_image = clip_to_shapefile(image, shapefile_path)
                if clipped_image:
                    task = ee.batch.Export.image.toLocal(image=clipped_image, description=image_id, scale=10, fileFormat='GeoTIFF')
                    task.start()  # Start the export task
                    print(f"Export task started for image {image_id}")
                    # Poll the task until completion
                    while task.active():
                        print("Exporting...")
                        time.sleep(10)  # Wait for 10 seconds before checking task status again
                    print(f"Image {image_id} downloaded and clipped successfully.")
                else:
                    print(f"Error clipping image {image_id}.")
            except Exception as e:
                print(f"Error downloading image {image_id}: {e}")
        else:
            print(f"Image {image_id} already exists")
    print("Image download process completed.")
except Exception as e:
    print(f"Error preparing image download: {e}")


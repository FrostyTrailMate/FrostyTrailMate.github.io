from datetime import datetime, timedelta
from sentinelhub import SHConfig, WmsRequest, CRS, MimeType, DataCollection, CustomUrlParam, BBox
import shapely.geometry
import fiona
import geopandas as gpd

# Store your Sentinel Hub instance ID securely (e.g., environment variable)
config = SHConfig()
config.instance_id = ("44b8b66c-925c-4ab5-a776-b1f48364172d")  # Replace with your environment variable name

# Output folder and shapefile path
output_folder = "Outputs/SAR"
shapefile_path = "Shapefiles/Yosemite_Boundary_4326.zip"

# Function to read bbox from shapefile, download Sentinel-1 GRD imagery, and clip
def download_and_clip(date):
    # Today's and yesterday's date
    today = date.strftime("%Y-%m-%d")
    yesterday = (date - timedelta(days=1)).strftime("%Y-%m-%d")

    # Read the shapefile using gpd
    gdf = gpd.read_file(shapefile_path, driver="zip")  # Assuming zipped shapefile

    # Option 1: Extract geometry directly from gdf
    try:
        # If "geometry" column exists, use it directly
        shape = gdf["geometry"].iloc[0]  # Access the first feature's geometry
    except KeyError:
        # If "geometry" column doesn't exist, use traditional approach
        shape = gdf.iloc[0].__geo_interface__["properties"]["geometry"]  # Alternative access

    # Get the bounding box and create GeoJSON
    bbox = shape.bounds
    bbox = BBox(bbox, crs=CRS.WGS84)
    geojson = shapely.geometry.mapping(shape)
    
    # Checks
    print("bbox:", bbox)
    print("today:", today)
    print("yesterday:", yesterday)

    # Define the WMS request with CustomUrlParam for evalscript
    request = WmsRequest(
        data_collection=DataCollection.SENTINEL1_IW,
        layer="IW",
        bbox=bbox,
        time=(yesterday, today),
        custom_url_params={
            CustomUrlParam.EVALSCRIPT: "//VERSION=3\nfunction setup() { return { bands: [\"VV\", \"VH\"], output: { bands: 2}}; }\nfunction evaluatePixel(sample) { return [sample.VV, sample.VH]; }"
        },
        width=512,
        height=512,
        image_format=MimeType.TIFF,
        config=config
    )



    # Download the Sentinel-1 imagery
    print(request.get_url())
    image = request.get_data(bbox)

    # Clip the image using the created GeoJSON
    clipped_image = image.clip(geojson)

    # Save the clipped image
    output_path = f"{output_folder}/{today}.tif"
    clipped_image.save(output_path)
    print(f"Saved image for {today} to {output_path}")

# Run the download and clip for today
today = datetime.today()
download_and_clip(today)

# Schedule the script to run daily using cron or equivalent
# Replace 'python your_script.py' with the actual command
# 0 0 * * * python your_script.py

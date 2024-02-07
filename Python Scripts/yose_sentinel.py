import psycopg2
from psycopg2 import sql
from datetime import datetime
import os
from sentinelhub import SHConfig, DataCollection, SentinelHubRequest
import geopandas as gpd

# Set up Sentinel Hub configuration
config = SHConfig()
config.instance_id = '44b8b66c-925c-4ab5-a776-b1f48364172d'  # Replace with your Sentinel Hub instance ID

# Function to check if image already exists in the database
def check_image_existence(datetime_value):
    connection = psycopg2.connect(user="your_username",
                                  password="your_password",
                                  host="your_host",
                                  port="your_port",
                                  database="your_database")
    cursor = connection.cursor()
    query = sql.SQL("SELECT * FROM your_table WHERE datetime = %s;")
    cursor.execute(query, (datetime_value,))
    exists = cursor.fetchone() is not None
    cursor.close()
    connection.close()
    return exists

# Function to download Sentinel-1 data
def download_sentinel_data(bbox, time_range, output_path, clip_shapefile):
    resolution = 10  # Resolution in meters
    image_width, image_height = bbox_to_dimensions(bbox, resolution=resolution)

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

    # Clip the data to the specified shapefile boundary
    clip_gdf = gpd.read_file(clip_shapefile)
    clipped_data = data.clip(clip_gdf.geometry)

    # Save the clipped data if it doesn't already exist
    output_path = '/Outputs/SAR/'
    
    for idx, time_slice in enumerate(clipped_data):
        datetime_value = time_slice.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        if not check_image_existence(datetime_value):
            image_path = os.path.join(output_path, f'sentinel1_clipped_image_{idx}.tif')
            time_slice.save(image_path)
            print(f'Saved clipped image {image_path}')
            # Insert datetime into the database
            insert_datetime(datetime_value)
        else:
            print(f"Image already obtained for datetime: {datetime_value}")

# Function to insert datetime into the database
def insert_datetime(datetime_value):
    connection = psycopg2.connect(user="your_username",
                                  password="your_password",
                                  host="your_host",
                                  port="your_port",
                                  database="your_database")
    cursor = connection.cursor()
    query = sql.SQL("INSERT INTO your_table (datetime) VALUES (%s);")
    cursor.execute(query, (datetime_value,))
    connection.commit()
    cursor.close()
    connection.close()

# Read the shapefile to extract the bounding box
yosemite_boundary_shapefile = '/Shapefiles/Yosemite_Boundary.shp'
yosemite_boundary_gdf = gpd.read_file(yosemite_boundary_shapefile)
yosemite_bbox = yosemite_boundary_gdf.total_bounds

# Determine the most recent September
today = datetime.today()
most_recent_september_start = datetime(today.year, 9, 1) if today.month >= 9 else datetime(today.year - 1, 9, 1)
most_recent_september_end = datetime(today.year, 9, 30)
most_recent_september_range = (most_recent_september_start, most_recent_september_end)

# Output paths
most_recent_september_output = 'most_recent_september_image.tif'
most_recent_output = 'most_recent_image.tif'

# Download Sentinel-1 data for the most recent September and clip to Yosemite Boundary
download_sentinel_data(yosemite_bbox, most_recent_september_range, most_recent_september_output, yosemite_boundary_shapefile)

# Download Sentinel-1 data for the most recent period and clip to Yosemite Boundary
download_sentinel_data(yosemite_bbox, most_recent_range, most_recent_output, yosemite_boundary_shapefile)

# Perform further analysis and comparison with DEM elevations
# (This part depends on your specific requirements and analysis methods)

# Example: Create a DataFrame with information about each area
data = {
    'Longitude': [yosemite_bbox[0], yosemite_bbox[2]],
    'Latitude': [yosemite_bbox[1], yosemite_bbox[3]],
    'Elevation (DEM)': [elevation_at_point(lon, lat) for lon, lat in zip([yosemite_bbox[0], yosemite_bbox[2]], [yosemite_bbox[1], yosemite_bbox[3]])],
    'Most Recent September Snow': ['Yes', 'No'],  # Placeholder values, actual snow detection might require more sophisticated methods
    'Most Recent Snow': ['No', 'Yes'],  # Placeholder values
}

df = pd.DataFrame(data)
print(df)
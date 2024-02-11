import os
import datetime
from sentinelsat import SentinelAPI
from zipfile import ZipFile
import geopandas as gpd

# Define your username and password
username = 'sohisjkegkas'
password = '!&f8@tZ,.%kQYW,'

# Connect to the Sentinel API
api = SentinelAPI(username, password, 'https://api.daac.asf.alaska.edu/services/search/')

# Define the area of interest using a shapefile
aoi_path = 'Shapefiles/Yosemite_Boundary_4326.zip'
aoi_name = os.path.splitext(os.path.basename(aoi_path))[0]

# Define output folder
output_folder = 'Outputs/SAR'

def get_aoi_envelope(aoi_geometry):
    envelope = aoi_geometry.envelope
    return envelope

def download_sentinel_imagery(aoi_envelope, output_folder):
    # Set the date range for the search
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)

    # Build the query parameters
    query = {
        'platformname': 'Sentinel-1',
        'producttype': 'GRD',
        'date': (yesterday, today),
        'footprint': f"Intersects({aoi_envelope.wkt})"
    }

    # Print the query URL before making the API call
    print(f"Query URL: {api.build_query_url(query)}")

    # Search for Sentinel-1 GRD imagery within the specified date range and AOI envelope
    products = api.query(aoi_envelope, **query)  # Unpack query dictionary

    # Download the found products
    api.download_all(products, directory_path=output_folder)

def main():
    # Extract AOI from shapefile
    with ZipFile(aoi_path, 'r') as zip_ref:
        zip_ref.extractall('Shapefiles')
    
    # Read AOI shapefile
    aoi_shp_path = f'Shapefiles/{aoi_name}.shp'
    aoi_gdf = gpd.read_file(aoi_shp_path)
    
    # Get envelope of AOI
    aoi_envelope = get_aoi_envelope(aoi_gdf.geometry)
    
    # Download Sentinel-1 GRD imagery
    download_sentinel_imagery(aoi_envelope, output_folder)

    # Clean up extracted files
    os.remove(f'Shapefiles/{aoi_name}.shp')
    os.remove(f'Shapefiles/{aoi_name}.shx')
    os.remove(f'Shapefiles/{aoi_name}.dbf')

if __name__ == "__main__":
    main()

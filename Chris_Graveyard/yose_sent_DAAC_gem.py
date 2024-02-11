import os
import zipfile
from datetime import datetime, timedelta
import requests
from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt
import fiona
import urllib.parse

# ------------------------------------------------
# Configuration & Setup
# ------------------------------------------------

# Your ASF DAAC credentials
asf_username = "sohisjkegkas" 
asf_password = "!&f8@tZ,.%kQYW,"

# Output and Shapefile Locations
output_folder = "Outputs/SAR"
shapefile_path = "Shapefiles/Yosemite_Boundary_4326.shp"

# Create the output folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# ------------------------------------------------
# Helper Functions
# ------------------------------------------------

def extract_shapefile_bounds(shapefile_path):
    """Extracts bounding box coordinates (as WKT POLYGON) from a shapefile"""
    with fiona.open(shapefile_path, 'r') as shapefile:
        bounds = shapefile.bounds  
        wkt_polygon = f"POLYGON(({bounds[0]} {bounds[1]}, {bounds[2]} {bounds[1]}, {bounds[2]} {bounds[3]}, {bounds[0]} {bounds[3]}, {bounds[0]} {bounds[1]}))"
        return wkt_polygon

# ------------------------------------------------
# Main Logic
# ------------------------------------------------

def collect_imagery():
    # Connect to ASF API
    api = SentinelAPI(asf_username, asf_password, 'https://api.daac.asf.alaska.edu')

    # Get clipping geometry from the shapefile
    area_of_interest = extract_shapefile_bounds(shapefile_path)
    print("Area of Interest (WKT Polygon):", area_of_interest)

    # Calculate search period (yesterday to today)
    yesterday = datetime.now() - timedelta(days=1)
    today = datetime.now()

    # Construct Query Parameters
    query_params = {
        'platform': 'Sentinel-1',
        'intersectsWith': f'"polygon({area_of_interest})"',
        'start': yesterday.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'end': today.strftime('%Y-%m-%dT%H:%M:%SZ')
    }
    encoded_query = urllib.parse.urlencode(query_params)

    # Query for Sentinel-1 GRD images
    products = api.query(encoded_query)

    # Download new images 
    if products: 
        api.download_all(products, directory_path=output_folder)
        print("New Sentinel-1 GRD imagery downloaded!")
    else:
        print("No new Sentinel-1 GRD imagery found within the last day.")

# ------------------------------------------------
# Scheduling (Run Once a Day)
# ------------------------------------------------
# Refer to the earlier instructions for setting up scheduling on your OS.

# ------------------------------------------------
# Run the Function (initially to test)
# ------------------------------------------------
collect_imagery() 

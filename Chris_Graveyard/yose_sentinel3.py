import os
from datetime import datetime, timedelta
import json
import requests
import geopandas as gpd
from shapely.geometry import shape, Polygon, mapping    
from sentinelhub import SHConfig, DataCollection, SentinelHubRequest, bbox_to_dimensions, DownloadRequest, SentinelHubCatalog
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

# Your client credentials
client_id = 'b15c8cd5-e24c-4eb4-894f-4ad544e6a59f'
client_secret = 'WRewj3YLfo0jb81YSA9duxrupDvxn2EX'

# Create a session
client = BackendApplicationClient(client_id=client_id)
oauth = OAuth2Session(client=client)

# Define paths
shapefile_path = 'Shapefiles/Yosemite_Boundary_4326.zip'
output_folder = 'Outputs/SAR'

# Get token for the session
token = oauth.fetch_token(token_url='https://services.sentinel-hub.com/auth/realms/main/protocol/openid-connect/token',
                          client_secret=client_secret, include_client_id=True)

def download_and_save_image(bbox, capture_datetime, output_folder):
    url = "https://services.sentinel-hub.com/api/v1/process"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + token['access_token']
    }

    # Define download folder and filename
    file_path = os.path.join(output_folder, f'SAR_{capture_datetime.strftime("%Y%m%dT%H%M%S")}.tif')

    # Set up variables
    timestart = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
    timeend = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    gdf = gpd.read_file(shapefile_path)
    bbox = gdf.total_bounds
    spatial_resolution = 10
    data = {}
    try:
        # Get the bounds of the GeoDataFrame
        bounds = gdf.total_bounds

        # Calculate height and width
        height = bounds[3] - bounds[1]
        width = bounds[2] - bounds[0]

        # Calculate width and height in pixels
        width_pixels = int(width / spatial_resolution)
        height_pixels = int(height / spatial_resolution)

        # Adjusting width and height to a multiple of 10 to match the default resolution
        width_pixels -= width_pixels % 10
        height_pixels -= height_pixels % 10

        # Update the request with width and height in pixels
        data["output"]["width"] = width_pixels
        data["output"]["height"] = height_pixels

        print("Height:", height_pixels, " pixels")
        print("Width:", width_pixels, " pixels")

        # Create request
        data = {
            "input": {
                "bounds": {
                    "bbox": [
                        bbox[0],
                        bbox[1],
                        bbox[2],
                        bbox[3]
                    ]
                },
                "data": [
                    {
                        "dataFilter": {
                            "timeRange": {
                                "from": timestart,
                                "to": timeend
                            }
                        },
                        "type": "sentinel-1-grd"
                    }
                ]
            },
            "output": {
                "width": 6100,
                "height": 7710,
                "responses": [
                    {
                        "identifier": "default",
                        "format": {
                            "type": "image/tiff"
                        }
                    }
                ]
            },
            "evalscript": "//VERSION=3\n\nfunction setup() {\n  return {\n    input: [\"VV\", \"VH\"],\n    output: { bands: 2 }\n  };\n}\n\nfunction evaluatePixel(sample) {\n  return [sample.VV, sample.VH];\n}"
        }

        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raise error for non-OK responses
        
        # Save the image
        with open(file_path, 'wb') as f:
            f.write(response.content)
        
        print("Image saved:", file_path)

    except Exception as e:
        print(f"Error occurred while checking and downloading new images: {e}")

# Example usage
download_and_save_image(bbox=None, capture_datetime=datetime.now(), output_folder=output_folder)
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
import requests
import os
import json
import geopandas as gpd
from sentinelhub import SHConfig, CRS, BBox, DataCollection, DownloadRequest, SentinelHubDownloadClient, SentinelHubRequest, bbox_to_dimensions, MimeType, MosaickingOrder
import datetime

# Your client credentials
client_id = '33054a13-b0b8-45c0-b2f5-bc9e9dc8db25'
client_secret = 'qBwcx5AQtfsLZKxZUlCIcYRQVLtzXof5'

# Set up Sentinel Hub configuration. WE WILL NEED TO CHANGE THE LOCATION THAT SHConfig SEARCHES FOR THE config FILE! -Chris
config = SHConfig()
config
config.sh_client_id = client_id
config.sh_client_secret = client_secret

# Create a session
client = BackendApplicationClient(client_id=client_id)
oauth = OAuth2Session(client=client)

# Get token for the session
token = oauth.fetch_token(token_url='https://services.sentinel-hub.com/auth/realms/main/protocol/openid-connect/token',
                          client_secret=client_secret, include_client_id=True)

# Use the obtained token in the headers for Sentinel Hub requests
url = "https://services.sentinel-hub.com/api/v1/process"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token['access_token']}"  # Use the access token obtained from OAuth2 authentication
}

# Read the shapefile and get its bounding box
shapefile_path = 'Shapefiles/Yosemite_Boundary_4326.shp'
gdf = gpd.read_file(shapefile_path)
bbox = gdf.total_bounds.tolist()

# Define evalscript
evalscript = """
//VERSION=3\n\nfunction setup() {\n  return {\n    input: [\n      {\n        bands: [\"VV\",\"VH\"]\n      }\n    ],\n    output: [\n      {\n        id: \"default\",\n        bands: 2,\n        sampleType: \"AUTO\"\n      }\n    ],\n    mosaicking: \"SIMPLE\"\n  };\n}\n\nfunction evaluatePixel(samples) {\n  return [samples[0].VV, samples[0].VH];\n}\n
"""

# Create BBox instance
bbox_instance = BBox(bbox, crs=CRS.WGS84)

request_image = SentinelHubRequest(
    evalscript=evalscript,
    input_data=[
        SentinelHubRequest.input_data(
            data_collection=DataCollection.SENTINEL1_IW,
            time_interval=('2024-01-01', '2024-02-11'),
            other_args={
                "processing": {
                    "speckleFilter": {
                        "type": "LEE",
                        "windowSizeX": 3,
                        "windowSizeY": 3
                    },
                    },
                }
        )
    ],
    responses=[
        SentinelHubRequest.output_response('default', MimeType.TIFF)
    ],
    bbox=bbox_instance,  # Use the BBox instance here
    size=[512, 512],
    data_folder='Outputs/SAR'  # Specify the data_folder parameter here
)

image_response = request_image.get_data(save_data=True)

print(
    "The output directory has been created and a tiff file with VV and VH bands was saved into the following structure:\n"
)

for folder, _, filenames in os.walk(request_image.data_folder):
    for filename in filenames:
        print(os.path.join(folder, filename))

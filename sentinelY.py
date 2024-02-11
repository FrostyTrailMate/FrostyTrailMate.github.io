from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
import requests
import os
import json
import geopandas as gpd

# Your client credentials
client_id = '33054a13-b0b8-45c0-b2f5-bc9e9dc8db25'
client_secret = 'qBwcx5AQtfsLZKxZUlCIcYRQVLtzXof5'

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

data = {
    "input": {
        "bounds": {
            "bbox": bbox
        },
        "data": [
            {
                "dataFilter": {
                    "timeRange": {
                        "from": "2024-01-11T00:00:00Z",
                        "to": "2024-02-11T23:59:59Z"
                    }
                },
                "processing": {
                    "speckleFilter": {
                        "type": "LEE",
                        "windowSizeX": 1,
                        "windowSizeY": 1
                    }
                },
                "type": "sentinel-1-grd"
            }
        ]
    },
    "output": {
        "width": 512,
        "height": 512,
        "responses": [
            {
                "identifier": "default",
                "format": {
                    "type": "image/tiff"
                }
            }
        ]
    },
    "evalscript": "//VERSION=3\n\nfunction setup() {\n  return {\n    input: [\n      {\n        bands: [\"VV\",\"VH\"],                  \n      }\n    ],\n    output: [\n      {\n        id: \"default\",\n        bands: 2,\n        sampleType: \"AUTO\",        \n      },    \n    ],\n    mosaicking: \"ORBIT\",\n  };\n}\n\n\nfunction evaluatePixel(samples) {\n    // Your javascript code here\n    return {\n      default: [],\n    };\n  }\n\n"
}

response = requests.post(url, headers=headers, json=data)

# Handle response
if response.status_code == 200:
    print("Request successful.")
    content_type = response.headers.get('Content-Type')
    if content_type == 'application/json':
        try:
            # Parse the response to extract download URL(s) if available
            response_data = response.json()
            if 'data' in response_data:
                for index, tile in enumerate(response_data['data']):
                    if 'tileDownloadLinks' in tile:
                        for band, download_link in tile['tileDownloadLinks'].items():
                            # Download the tile to a file
                            file_name = f"tile_{index}_{band}.tiff"
                            with open(file_name, 'wb') as f:
                                print(f"Downloading tile {index} for band {band}...")
                                tile_response = requests.get(download_link)
                                f.write(tile_response.content)
                            print(f"Tile {index} for band {band} downloaded successfully.")
        except json.decoder.JSONDecodeError:
            print("Response is not in JSON format. Response content:")
            print(response.content)
    else:
        # If the content type is not JSON, assume it's binary and save it to a file
        file_name = "response_file.tiff"  # You might want to change this to reflect the actual file format
        with open(file_name, 'wb') as f:
            f.write(response.content)
        print(f"Response saved to {file_name}.")
else:
    print("Error:", response.text)

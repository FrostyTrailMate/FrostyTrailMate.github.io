import os
import requests
from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt
from datetime import date

# Copernicus API credentials
API_USERNAME = 'sebastian_suarez14@outlook.com'
API_PASSWORD = 'Rapsusklei2*'

# Define the search query parameters
SEARCH_URL = 'https://apihub.copernicus.eu/apihub/search'
OUTPUT_FOLDER = 'D:/Users/sebas/Desktop'

def download_latest_yosemite_data(output_folder):
    # Convert the coordinates of Yosemite National Park to WKT format
    yosemite_geojson = {
        "type": "Polygon",
        "coordinates": [[
            [-119.538026, 37.865613],
            [-119.538026, 38.187107],
            [-119.09427, 38.187107],
            [-119.09427, 37.865613],
            [-119.538026, 37.865613]
        ]]
    }
    footprint = geojson_to_wkt(yosemite_geojson)

    # Construct the query parameters
    query_params = {
        'platformname': 'Sentinel-1',
        'q': f'footprint:"Intersects({footprint})"',
        'orderby': 'ingestiondate desc',
        'rows': 1
    }

    # Authenticate with Copernicus API
    auth = (API_USERNAME, API_PASSWORD)

    try:
        # Send the request with an increased timeout
        response = requests.get(SEARCH_URL, auth=auth, params=query_params, timeout=30)
        response.raise_for_status()  # Raise an error for bad response status codes

        # Extract the product URL from the response
        product_url = response.json()['products'][0]['url']

        # Download the product
        api = SentinelAPI(API_USERNAME, API_PASSWORD)
        api.download(product_url, directory_path=output_folder)

        print("Download successful!")
    except Exception as e:
        print(f"Error: {e}")

def main():
    download_latest_yosemite_data(OUTPUT_FOLDER)

if __name__ == "__main__":
    main()

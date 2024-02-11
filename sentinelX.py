import os
from datetime import datetime, timedelta
import geopandas as gpd
import requests
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
from sentinelsat import SentinelAPI
from osgeo import osr

# Suppress future warnings and deprecation warnings
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=DeprecationWarning)

# Your client credentials
client_id = '33054a13-b0b8-45c0-b2f5-bc9e9dc8db25'
client_secret = 'qBwcx5AQtfsLZKxZUlCIcYRQVLtzXof5'

# Create a session
client = BackendApplicationClient(client_id=client_id)
oauth = OAuth2Session(client=client)

# Get token for the session
token = oauth.fetch_token(token_url='https://services.sentinel-hub.com/auth/realms/main/protocol/openid-connect/token',
                          client_secret=client_secret, include_client_id=True)

# Define function to collect Sentinel-1 GRD IW data from Sentinel Hub
def collect_sentinel1_data(bbox_shapefile, output_folder):
    # Load shapefile
    gdf = gpd.read_file(bbox_shapefile)
    bbox = gdf.total_bounds  # total_bounds returns (minx, miny, maxx, maxy)

    # Define time range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=5)

    # Construct URL manually
    url = "https://services.sentinel-hub.com/api/v1/process"
    url += f"?collection=sentinel-1-grd&bbox={','.join(str(coord) for coord in bbox)}"
    url += f"&time={start_date.isoformat()}Z/{end_date.isoformat()}Z"
    url += "&evalscript=cmV0dXJuIFtBQkNERUZHSElKS0xNTk9QUVJTVFVWV1hZWmNkZWZnaGlqa2xtbm9wcXJzdHV2d3h5ent8fXx8fXx8fHwKUE9TfFNFVFRJTkdTfEZPT1RFUiwgc2V0VGltZW91dChTTVRQKQp7CiAgICBtYXgoKSB7CiAgICAgICAgcmV0dXJuIFtTVEFURU1FTlQtVU5JQ09ERSwgc2VuZGVyXQogICAgfQp9Cg"
    print("Querying Sentinel Hub API with URL:", url)

    # Connect to Sentinel Hub API
    api = SentinelAPI(client_id, client_secret)

    # Search for imagery
    retries = 3
    for attempt in range(retries):
        try:
            products = api.query(area=bbox, date=(start_date, end_date), platformname='Sentinel-1',
                                 producttype='GRD', sensoroperationalmode='IW')
            break  # If successful, exit loop
        except Exception as e:
            print(f"Error occurred while querying Sentinel Hub API (Attempt {attempt + 1}/{retries}): {str(e)}")
            if attempt == retries - 1:
                print("Max retries exceeded. Exiting.")
                return
            else:
                print("Retrying...")
                continue

    if not products:
        print("No imagery found within the specified time frame and bounding box.")
        return

    for product_id in products:
        product_info = api.get_product_odata(product_id)
        datetime_str = product_info['date']
        sRow = product_info['s2datatake']
        sPath = product_info['s2datatake']
        sSlice = product_info['s2datatake']
        sArea = os.path.basename(bbox_shapefile)
        raster_path = os.path.join(output_folder, f"{product_id}.tiff")

        # Download the image
        try:
            api.download(product_id, directory_path=output_folder)
        except Exception as e:
            print(f"Error occurred while downloading image {product_id}: {str(e)}")
            continue

        print(f"Image {product_id} downloaded.")

# Define paths
shapefile_path = 'Shapefiles/Yosemite_Boundary_4326.shp'
output_folder = 'Outputs/SAR'

# Collect Sentinel-1 GRD IW data
collect_sentinel1_data(shapefile_path, output_folder)

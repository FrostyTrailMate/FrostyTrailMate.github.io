import os
import requests
import geopandas as gpd
import rasterio
from rasterio.warp import reproject, calculate_default_transform, Resampling
from rasterio.mask import mask
import argparse
from shapely.geometry import Polygon
import psycopg2

def download_dem(api_token, envelope, output_folder, area_name, conn):
    """
    Download Digital Elevation Model (DEM) data from OpenTopography within the bounding box defined by the provided envelope.

    Parameters:
        api_token (str): The API token required to access OpenTopography services.
        envelope (GeoSeries): GeoSeries representing the envelope of the search area.
        output_folder (str): The directory where the downloaded DEM and clipped DEM files will be saved.
        area_name (str): Name of the search area.
        conn: psycopg2 connection object for database operations.

    Returns:
        None

    Raises:
        Exception: If an error occurs during the download or processing of the DEM data.
    """
    try:
        xmin, ymin, xmax, ymax = envelope.total_bounds

        url = f'https://portal.opentopography.org/API/globaldem?demtype=NASADEM&south={ymin}&north={ymax}&west={xmin}&east={xmax}&outputFormat=GTiff&API_Key={api_token}'

        print("Downloading DEM data...")
        response = requests.get(url, stream=True)

        if response.status_code == 200:
            dem_downloaded_file = os.path.join(output_folder, f'{area_name}_DEM_raw.tif')
            with open(dem_downloaded_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            print("DEM data downloaded successfully.")

            # Clip downloaded DEM to envelope boundary
            dem_clipped_file = os.path.join(output_folder, f'{area_name}_DEM_4326.tif')
            with rasterio.open(dem_downloaded_file) as src:
                out_image, out_transform = mask(src, envelope.geometry, crop=True)
                out_meta = src.meta.copy()

                out_meta.update({"driver": "GTiff",
                                 "height": out_image.shape[1],
                                 "width": out_image.shape[2],
                                 "transform": out_transform,
                                 "crs": 'EPSG:4326'})

                with rasterio.open(dem_clipped_file, "w", **out_meta) as dest:
                    dest.write(out_image)

            print("DEM data clipped and saved successfully.")

            # Save paths to database
            with conn.cursor() as cur:
                cur.execute("INSERT INTO userpolygons (area_name, dem_path, dem_processed) VALUES (%s, %s, %s)",
                            (area_name, dem_downloaded_file, dem_clipped_file))
                conn.commit()

        else:
            print(f"Failed to download DEM data. Status code: {response.status_code}")

    except Exception as e:
        print(f"Error occurred: {e}")


def main():
    parser = argparse.ArgumentParser(description='Download DEM data from OpenTopography.')
    parser.add_argument('-n', '--name', type=str, help='Name of the search area', required=True)
    parser.add_argument('-c', '--coordinates', type=float, nargs=4, help='Bounding box coordinates (xmin, ymin, xmax, ymax)')
    args = parser.parse_args()

    if args.coordinates:
        xmin, ymin, xmax, ymax = args.coordinates
        envelope = gpd.GeoSeries([Polygon([(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)])])
    else:
        raise ValueError("Bounding box coordinates are required")

    output_folder = 'Outputs/DEM'
    os.makedirs(output_folder, exist_ok=True)

    # Connect to PostgreSQL database
    conn = psycopg2.connect(
        dbname="FTM8_dyn",
        user="postgres",
        password="admin",
        host="DESKTOP-UIUIA2A",
        port="5432"
    )

    # API token
    api_token = '8ff3b062b8621b8a71a957083bba09e0'

    # Download DEM data
    download_dem(api_token, envelope, output_folder, args.name, conn)

    # Close database connection
    conn.close()

    print("DEM.py completed.")

if __name__ == "__main__":
    main()
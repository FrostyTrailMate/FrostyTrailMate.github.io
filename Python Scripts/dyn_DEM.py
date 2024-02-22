import os
import requests
import geopandas as gpd
import rasterio
from rasterio.warp import reproject, calculate_default_transform, Resampling
from rasterio.mask import mask
import argparse
from shapely.geometry import Polygon

def download_dem(api_token, envelope, output_folder):
    """
    Download Digital Elevation Model (DEM) data from OpenTopography within the bounding box defined by the provided envelope.

    Parameters:
        api_token (str): The API token required to access OpenTopography services.
        envelope (GeoSeries): GeoSeries representing the envelope of the search area.
        output_folder (str): The directory where the downloaded DEM and clipped DEM files will be saved.

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
            dem_file = os.path.join(output_folder, 'Yosemite_DEM.tif')
            with open(dem_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            print("DEM data downloaded successfully.")

            # Reprojecting DEM data to EPSG:4326
            dem_reprojected_file = os.path.join(output_folder, 'Yosemite_DEM_reprojected.tif')
            with rasterio.open(dem_file) as src:
                transform, width, height = calculate_default_transform(
                    src.crs, {'init': 'EPSG:4326'}, src.width, src.height, *src.bounds)
                kwargs = src.meta.copy()
                kwargs.update({
                    'crs': 'EPSG:4326',
                    'transform': transform,
                    'width': width,
                    'height': height
                })

                with rasterio.open(dem_reprojected_file, 'w', **kwargs) as dst:
                    for i in range(1, src.count + 1):
                        reproject(
                            source=rasterio.band(src, i),
                            destination=rasterio.band(dst, i),
                            src_transform=src.transform,
                            src_crs=src.crs,
                            dst_transform=transform,
                            dst_crs={'init': 'EPSG:4326'},
                            resampling=Resampling.nearest)

            # Clip reprojected DEM to shapefile boundary
            dem_clipped_file = os.path.join(output_folder, 'Yosemite_DEM_clipped.tif')
            with rasterio.open(dem_reprojected_file) as src:
                out_image, out_transform = mask(src, envelope.geometry, crop=True)
                out_meta = src.meta.copy()

                out_meta.update({"driver": "GTiff",
                                 "height": out_image.shape[1],
                                 "width": out_image.shape[2],
                                 "transform": out_transform})

                with rasterio.open(dem_clipped_file, "w", **out_meta) as dest:
                    dest.write(out_image)

            print("DEM data reprojected, clipped, and saved successfully.")
        else:
            print(f"Failed to download DEM data. Status code: {response.status_code}")

    except Exception as e:
        print(f"Error occurred: {e}")



def main():
    parser = argparse.ArgumentParser(description='Download DEM data from OpenTopography.')
    parser.add_argument('-n', '--name', type=str, help='Name of the search area', required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-c', '--coordinates', type=float, nargs=4, help='Bounding box coordinates (xmin, ymin, xmax, ymax)')
    group.add_argument('-p', '--path', type=str, help='Relative path to a shapefile')

    args = parser.parse_args()

    if args.coordinates:
        xmin, ymin, xmax, ymax = args.coordinates
        envelope = gpd.GeoSeries([Polygon([(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)])])
    else:
        shapefile_path = args.path
        boundary = gpd.read_file(shapefile_path)
        envelope = boundary.envelope

    output_folder = f'Outputs/DEM_{args.name}'
    os.makedirs(output_folder, exist_ok=True)

    # API token
    api_token = '8ff3b062b8621b8a71a957083bba09e0'

    # Download DEM data
    download_dem(api_token, envelope, output_folder)

    print("DEM.py completed.")

if __name__ == "__main__":
    main()

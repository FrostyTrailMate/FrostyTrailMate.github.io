import os
import requests
import geopandas as gpd
import rasterio
from rasterio.mask import mask
from rasterio.warp import calculate_default_transform, reproject, Resampling
from zipfile import ZipFile

def download_dem(api_token, polygon_zipfile, output_folder):
    """
    Download Digital Elevation Model (DEM) data from OpenTopography within the bounding box defined by the provided polygon.

    Parameters:
        api_token (str): The API token required to access OpenTopography services.
        polygon_zipfile (str): The path to the ZIP file containing the polygon shapefile.
        output_folder (str): The directory where the downloaded DEM and clipped DEM files will be saved.

    Returns:
        None

    Raises:
        Exception: If an error occurs during the download or processing of the DEM data.
    """
    try:
        with ZipFile(polygon_zipfile, 'r') as zip_ref:
            zip_ref.extractall(output_folder)
        
        shapefile_name = None
        for file_name in zip_ref.namelist():
            if file_name.endswith('.shp'):
                shapefile_name = file_name
                break

        if shapefile_name is None:
            print("No shapefile found in the ZIP archive.")
            return

        boundary = gpd.read_file(os.path.join(output_folder, shapefile_name))
        envelope = boundary.envelope

        xmin, ymin, xmax, ymax = envelope.total_bounds

        url = f'https://portal.opentopography.org/API/usgsdem?datasetName=USGS30m&south={ymin}&north={ymax}&west={xmin}&east={xmax}&outputFormat=GTiff&API_Key={api_token}'

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
                transform, width, height = rasterio.warp.calculate_default_transform(
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

            print("DEM data reprojected and saved successfully.")
        else:
            print(f"Failed to download DEM data. Status code: {response.status_code}")

    except Exception as e:
        print(f"Error occurred: {e}")

# API token
api_token = '8ff3b062b8621b8a71a957083bba09e0'

# Input polygon zipfile
polygon_zipfile = 'Shapefiles/Yosemite_Boundary_4326.zip'

# Output folder
output_folder = 'Outputs/DEM'

os.makedirs(output_folder, exist_ok=True)

# Download DEM data
download_dem(api_token, polygon_zipfile, output_folder)

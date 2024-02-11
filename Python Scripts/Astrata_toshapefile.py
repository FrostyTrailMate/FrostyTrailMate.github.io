import os
import rasterio
from shapely.geometry import Polygon, mapping
import numpy as np
from rasterio.mask import mask
from shapely.ops import unary_union
from fiona import collection
from rasterio.warp import transform_geom

# Function to reproject geometries to EPSG:4326
def reproject_to_4326(geometry, src_crs):
    return transform_geom(src_crs, 'EPSG:4326', geometry)

# Function to generate polygons for each elevation band and write them to shapefiles
def generate_polygons(dem_file, output_dir):
    try:
        data = dem_file.read(1, masked=True)

        max_elevation = np.nanmax(data)

        rounded_max_elevation = int(np.ceil(max_elevation / 100.0) * 100)

        elevation_ranges = range(0, rounded_max_elevation + 100, 100)
        total_strata = len(elevation_ranges) - 1

        print(f"Total elevation strata: {total_strata}")

        for i, elevation in enumerate(elevation_ranges[:-1]):
            print(f"Processing elevation stratum {i+1}/{total_strata}")

            lower_bound = elevation
            upper_bound = elevation + 100

            mask = np.logical_and(data >= lower_bound, data < upper_bound)

            polygons = []
            for geom, val in rasterio.features.shapes(mask.astype('uint8'), transform=dem_file.transform):
                if val != 0:
                    geom = reproject_to_4326(geom, dem_file.crs)
                    polygons.append(Polygon(geom['coordinates'][0]))

            if polygons:
                multi_polygon = unary_union(polygons)
                schema = {'geometry': 'Polygon', 'properties': {'id': 'int'}}
                with collection(
                        os.path.join(output_dir, f"Yosemite_Elevation_{int(lower_bound)}_{int(upper_bound)}.shp"),
                        "w",
                        "ESRI Shapefile",
                        schema,
                        crs={'init': 'epsg:4326'}) as output:
                    output.write({'geometry': mapping(multi_polygon), 'properties': {'id': i}})

        print("All elevation strata processed successfully.")
    except Exception as e:
        print(f"Error generating polygons: {e}")

# Main function
def main(dem_file_path, output_dir):
    try:
        # Generate polygons
        with rasterio.open(dem_file_path) as dem_file:
            generate_polygons(dem_file, output_dir)

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    # Input DEM file path
    dem_file_path = 'Outputs/DEM/Yosemite_DEM_clipped.tif'
    
    # Output directory for shapefiles
    output_directory = 'Shapefiles/ElevationStrata'

    # Create output directory if it does not exist
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Main function call
    main(dem_file_path, output_directory)

import geopandas as gpd
from shapely.geometry import Point
from sqlalchemy import create_engine
import rasterio
from rasterio.transform import from_origin
from rasterio.enums import Resampling
import numpy as np
from datetime import datetime
import pandas as pd

# Read the shapefile
shapefile_path = 'Shapefiles/Yosemite_Boundary_4326.shp'
print("Reading shapefile...")
gdf = gpd.read_file(shapefile_path)

# Read the DEM file
dem_path = 'Outputs/DEM/Yosemite_DEM_clipped.tif'
print("Reading DEM...")
with rasterio.open(dem_path) as dem:
    dem_data = dem.read(1)
    transform = dem.transform
    dem_crs = dem.crs

# Extract the polygon from the shapefile
polygon = gdf.iloc[0]['geometry']
min_x, min_y, max_x, max_y = polygon.bounds

# Create systematic sampling points at 500 meter intervals
sampling_distance = 500 

# Create grid of points covering the bounding box of the polygon
x_coords = np.arange(min_x, max_x, sampling_distance)
y_coords = np.arange(min_y, max_y, sampling_distance)
xx, yy = np.meshgrid(x_coords, y_coords)
points = gpd.GeoDataFrame(geometry=[Point(x, y) for x, y in zip(xx.ravel(), yy.ravel())], crs=gdf.crs)

# Spatial join to keep only points inside the polygon
sampled_points_gdf = gpd.sjoin(points, gdf, op='within')

# Extract elevation for each point
elevations = []
for index, point in sampled_points_gdf.iterrows():
    px, py = ~transform * (point.geometry.x, point.geometry.y)
    row, col = map(int, [py, px])
    elevations.append(dem_data[row, col])

# Add elevation column to the GeoDataFrame
sampled_points_gdf['elevation'] = elevations

# Add metadata columns
sampled_points_gdf['datetime'] = datetime.now()
sampled_points_gdf['area'] = 'Yosemite'
sampled_points_gdf['shapefile_path'] = shapefile_path

# Keep only necessary columns
sampled_points_gdf = sampled_points_gdf[['datetime', 'area', 'geometry', 'shapefile_path', 'elevation']]

# Connect to PostgreSQL database (replace the connection parameters with your own)
db_user = 'postgres'
db_password = 'admin'
db_host = 'DESKTOP-UIUIA2A'
db_port = '5432'
db_name = 'FTM8'

connection_string = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
engine = create_engine(connection_string)

# Set SRID for the GeoDataFrame
sampled_points_gdf.crs = dem_crs
sampled_points_gdf.srid = dem_crs.to_epsg()  # Assuming dem_crs is a CRS object

# Write the sampled points to a PostgreSQL table
print("Writing sampled points to PostgreSQL table...")

# Use SQLAlchemy's to_sql method to insert the GeoDataFrame into PostgreSQL
sampled_points_gdf.to_sql('samples', engine, if_exists='append', index=False, dtype={'datetime': 'TIMESTAMP', 'area': 'TEXT', 'shapefile_path': 'TEXT', 'elevation': 'FLOAT'})

# Write the sampled points to a shapefile
print("Writing sampled points to shapefile...")
sampled_points_gdf.to_file('Yosemite_sample_points.shp', driver='ESRI Shapefile')

# Close the connection
print("Process completed!")

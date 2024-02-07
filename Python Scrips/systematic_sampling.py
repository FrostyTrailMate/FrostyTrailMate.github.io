### NEEDS SERIOUS EDITING ###

import geopandas as gpd
from shapely.geometry import Point
from sqlalchemy import create_engine

# Read the shapefile
shapefile_path = '/Shapefiles/Yosemite_Boundary.shp'
gdf = gpd.read_file(shapefile_path)

# Create systematic sampling points at 100 meter intervals
sampling_distance = 100  # in meters

# Create empty DataFrame to store sampled points
sampled_points = gpd.GeoDataFrame(columns=['geometry'])

# Iterate through each polygon in the shapefile
for index, row in gdf.iterrows():
    polygon = row['geometry']
    min_x, min_y, max_x, max_y = polygon.bounds
    
    # Create sampling points within each polygon
    x_coords = range(int(min_x), int(max_x), sampling_distance)
    y_coords = range(int(min_y), int(max_y), sampling_distance)
    for x in x_coords:
        for y in y_coords:
            point = Point(x, y)
            if polygon.contains(point):
                sampled_points = sampled_points.append({'geometry': point}, ignore_index=True)

# Connect to PostgreSQL database (replace the connection parameters with your own)
db_user = 'postgres'
db_password = 'admin'
db_host = 'DESKTOP-UIUIA2A'
db_port = '5432'
db_name = 'FTM8'

connection_string = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
engine = create_engine(connection_string)

# Write the sampled points to a PostgreSQL table
sampled_points.to_postgis('samples', engine, if_exists='replace', index=False, dtype={'geometry': 'POINT'})

# Add a column 'vectorType' to the PostgreSQL table
with engine.connect() as connection:
    connection.execute("ALTER TABLE samples ADD COLUMN vectorType TEXT")

# Close the connection
connection.close()

print("Sampling points created and written to the 'samples' table with 'vectorType' column.")

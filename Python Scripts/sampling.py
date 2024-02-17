import geopandas as gpd
import rasterio
from shapely.geometry import Point
import psycopg2
from datetime import datetime
import pyproj
import signal
import sys

# Define a signal handler for interrupt (Ctrl+C)
def signal_handler(sig, frame):
    print("\nWriting process interrupted. Rolling back changes...")
    conn.rollback()  # Rollback the transaction to remove the added points
    conn.close()  # Close the database connection
    print("Changes rolled back. Exiting...")
    sys.exit(0)

# Set the interrupt signal handler
signal.signal(signal.SIGINT, signal_handler)

# Function to get elevation from raster file for a given point
def get_elevation_for_point(point, dem_dataset, dem_crs):
    """
    Get elevation for a given point from a digital elevation model (DEM) dataset.

    Parameters:
    - point (shapely.geometry.Point): The point for which elevation is to be retrieved.
    - dem_dataset (rasterio.io.DatasetReader): The raster dataset containing elevation data.
    - dem_crs (CRS): The coordinate reference system (CRS) of the DEM dataset.

    Returns:
    - float: The elevation value at the given point.
    """
    lon, lat = point.x, point.y
    easting, northing = transform_coords(lon, lat, dem_crs, dem_dataset.crs)
    row, col = dem_dataset.index(easting, northing)
    elevation = dem_dataset.read(1)[row, col]
    return elevation

# Function to transform coordinates
def transform_coords(lon, lat, src_crs, dst_crs):
    """
    Transform coordinates from one coordinate reference system (CRS) to another.

    Parameters:
    - lon (float): Longitude coordinate.
    - lat (float): Latitude coordinate.
    - src_crs (CRS): Source CRS.
    - dst_crs (CRS): Destination CRS.

    Returns:
    - tuple: Transformed (x, y) coordinates.
    """
    transformer = pyproj.Transformer.from_crs(src_crs, dst_crs, always_xy=True)
    x, y = transformer.transform(lon, lat)
    return x, y

# Load the shapefile
print("Loading shapefile...")
shapefile_path = 'Shapefiles/Yosemite_Boundary_4326.shp'
try:
    gdf = gpd.read_file(shapefile_path)
    print("Shapefile loaded successfully.")
except Exception as e:
    print(f"Error loading shapefile: {e}")

# Load the raster DEM
print("Loading DEM...")
dem_file_path = 'Outputs/DEM/Yosemite_DEM_clipped.tif'
try:
    dem_dataset = rasterio.open(dem_file_path)
    print("DEM loaded successfully.")
except Exception as e:
    print(f"Error loading DEM: {e}")

# Function to generate points at every 500 meters within the boundary polygon
def generate_points_within_polygon(polygon, spacing):
    """
    Generate points at regular intervals within a polygon.

    This function generates points within the specified polygon at a regular interval determined by the spacing parameter.
    
    Parameters:
    - polygon (shapely.geometry.Polygon): The polygon within which points will be generated.
    - spacing (float): The distance between each generated point, typically in the same units as the polygon coordinates.

    Returns:
    - list: A list of Point objects representing the generated points.

    Note:
    - The function iterates over the bounding box of the polygon and generates points within it at the specified spacing.
    - Points are included in the output list only if they fall within the polygon boundary.
    - The generated points are evenly spaced within the polygon, but the actual distance between points may vary due to the irregular shape of the polygon.
    """
    minx, miny, maxx, maxy = polygon.bounds
    points = []
    x = minx
    while x < maxx:
        y = miny
        while y < maxy:
            point = Point(x, y)
            if polygon.contains(point):
                points.append(point)
            y += spacing
        x += spacing
    return points

# Generate points within the boundary polygon
print("Generating points within the boundary polygon...")
spacing = 0.005  # in degrees (~500 meters)
points = []
for index, row in gdf.iterrows():
    polygon = row['geometry']
    polygon_crs = gdf.crs
    points_within_polygon = generate_points_within_polygon(polygon, spacing)
    points.extend(points_within_polygon)

print(f"{len(points)} points generated.")


# Connect to PostgreSQL database
print("Connecting to PostgreSQL database...")
try:
    conn = psycopg2.connect(
        dbname="FTM8",
        user="postgres",
        password="admin",
        host="DESKTOP-UIUIA2A",
        port="5432"
    )
    cur = conn.cursor()
    print("Connected to PostgreSQL database.")
except Exception as e:
    print(f"Error connecting to PostgreSQL database: {e}")

# Insert data into the database
print("Inserting data into the database...")
try:
    for i, point in enumerate(points):
        elevation = float(get_elevation_for_point(point, dem_dataset, dem_dataset.crs))
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        area = "Yosemite"
        shapefile_path = shapefile_path
        point_geom = f"POINT({point.x} {point.y})"
        
        # Insert the data into the database
        cur.execute(
            "INSERT INTO samples (datetime, area, point_geom, elevation, shapefile_path) VALUES (%s, %s, %s, %s, %s)",
            (now, area, point_geom, elevation, shapefile_path)
        )
        print(f"\rWriting point {i+1}/{len(points)} to database.", end='', flush=True)
except Exception as e:
    print(f"\nError inserting point: {e}")
    conn.rollback()  # Rollback the transaction in case of error
else:
    print("\nDatabase write completed.")  # Add a newline after completion
    conn.commit()  # Commit the transaction if no errors occurred
finally:
    conn.close()  # Close the database connection regardless of the outcome



# Create a GeoDataFrame from the points
point_geoms = [Point(p.x, p.y) for p in points]
points_gdf = gpd.GeoDataFrame(geometry=point_geoms, crs=gdf.crs)

# Output shapefile path
output_shapefile_path = 'Outputs/Samples/Yosemite_Points.shp'

# Save the GeoDataFrame to a shapefile
try:
    points_gdf.to_file(output_shapefile_path)
    print("Points saved to shapefile successfully.")
except Exception as e:
    print(f"Error saving points to shapefile: {e}")

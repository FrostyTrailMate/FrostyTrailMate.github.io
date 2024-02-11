import os
import geopandas as gpd
from earthpy import clip as cl
from earthpy import io as eio
import earthpy.spatial as et
import psycopg2
import ee
import rasterio

# Connect to Earth Engine
ee.Authenticate()
ee.Initialize()

# Path to the shapefile containing the polygon boundary
shapefile_path = "Shapefiles/Yosemite_Boundary.shp"

# Path to where you want to save the DEM imagery. Create if it doesn't exist.
output_dir = "Outputs/DEM"
os.makedirs(output_dir, exist_ok=True)

# Read the shapefile
polygon = gpd.read_file(shapefile_path)

# Get the bounds of the polygon
xmin, ymin, xmax, ymax = polygon.total_bounds

# Definte the bounding box geometry
bbox = ee.Geometry.Rectangle([xmin, ymin, xmax, ymax])

# Select dataset
datasets = ee.ImageCollection("USGS/NED").filterBounds(bbox)
dataset = datasets.first()

# Download
download_task = ee.batch.Export.image.toDrive(
    image=dataset,
    description="Yosemite_DEM",
    folder=output_dir,
    scale=10,
    region=bbox
)
download_task.start

# Get the downloaded file path
downloaded_dem = os.path.join(output_dir, "Yosemite_DEM.tif")

# Clip the DEM using the polygon boundary
#clipped_dem, dem_extent = cl.clip_shp_to_raster(shapefile_path, downloaded_dem, nodata=-9999)
with rasterio.open(downloaded_dem) as src:
    # Clip using boundary polygon
    clipped_dem, transform = rasterio.mask(src, polygon.geomtery, crop=True)
    # Get metadata
    meta=src.meta.copy()

# Update metadata
    meta.update({"driver": "GTiff",
                 "height": clipped_dem.shape[1],
                 "width": clipped_dem.shape[2],
                 "transform": transform,
                 "crs": src.crs})
# Save it
clipped_dem_path = os.path.join(output_dir, "Yosemite_DEM.tif")
with rasterio.open(clipped_dem_path, "w", **meta) as dest:
    dest.write(clipped_dem)

# Print the path to the clipped DEM
print("Clipped DEM saved to:", clipped_dem_path)

# Set the output contour shapefile path ### If we make this more flexible, we'll need a different naming convention for the output shapefile. -Chris
contour_shp_path = os.path.join(output_dir, "Yosemite_contours.shp")

# Generate 100-meter elevation contours from the clipped DEM
print("Generating contours...")
contours = et.spatial.contour_from_raster(
    clipped_dem,
    output_path=contour_shp_path,
    interval=100,
    crs=dem_extent.spatialReference.ExportToWkt(),
)

# Connect to your PostgreSQL database
conn = psycopg2.connect(
    dbname="FTM8",
    user="postgres",
    password="admin",
    host="DESKTOP-UIUIA2A",
    port="5432"
)

# Create a cursor object
cur = conn.cursor()

# Insert contours into the database
# Fetch the last recorded id from the database
cur.execute("SELECT MAX(id) FROM dem_p")
last_id = cur.fetchone()[0]

# Insert contours into the database with the incremented id. ### I'm not sure we want a field per contour?? This might need edits. Chris
for contour in contours:
    cur.execute("INSERT INTO dem_p (vector, area_name) VALUES (%s, ST_GeomFromText(%s, 4326), 'Yosemite')", (contour.wkt,))

# Commit changes
conn.commit()

# Close cursor and connection
cur.close()
conn.close()

print("Contours saved to the database.")

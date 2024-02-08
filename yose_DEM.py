# Required imports
import os
import geopandas as gpd
import earthpy.spatial as et
import psycopg2

# Set the Earth Explorer M2M code
#m2m_code = "gpul8A@ScIhEe2DG!EGFgUUxKPnLREn@7@yCO6TFoo9!Z1FHnMu4OegGUEhaWpdx"

# Set the shapefile path and access the shapefile
shapefile_path = "Shapefiles/Yosemite_Boundary.shp"
boundary = gpd.read_file(shapefile_path)

# Imported DEM output directory
output_dir = "Outputs/DEM"
os.makedirs(output_dir, exist_ok=True)

# Set Earth Explorer API key
#et.set_key(api_key=m2m_code)




'''
# Download DEM data from Earth Explorer
print("Downloading DEM data...")
dem_path = et.data.get_data(
    product_id="AEAC29-5B68-4674-A3FB-E6E2D0A22EC0",
    destination_folder=output_dir,
    scene_id="LE07_L1TP_039030_20000907_20170126_01_T1",
)
'''
##### This code is more flexible than the above, but I'm not sure it will work-- we may need to make changes to how it downloads. We should test both. -Chris

dem_metadata = et.data.search_earthexplorer(
    geom=boundary,
    start_date="2000-01-01",
    end_date="2022-01-01",
    max_cloud_cover=10,
    product="DEM",
    output_dir=output_dir
)

if len(dem_metadata) == 0:
    print("No DEM data found for the specified area.")
    exit()
    
#####




# Clip the DEM to the bounding box
print("Clipping DEM...")
clipped_dem, dem_extent = et.spatial.clip_raster(dem_metadata, boundary.geometry, nodata=-9999)

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

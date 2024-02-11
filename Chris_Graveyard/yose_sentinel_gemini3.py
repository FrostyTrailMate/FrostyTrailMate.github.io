from datetime import datetime, timedelta
from sentinelhub import SHConfig, CRS, BBox, DataCollection, MimeType, WcsRequest
from shapely.geometry import shape, mapping
from os import path
import pyshp

# Configure Sentinel Hub access
config = SHConfig()
# Replace with your Sentinel Hub instance ID if needed
config.instance_id = "YOUR_INSTANCE_ID"

# Define output folder
output_folder = "Outputs/SAR"

# Define shapefile path
shapefile_path = path.join("Shapefiles", "Yosemite_Boundary_4326.zip")

# Read shapefile using pyshp
reader = pyshp.Reader(shapefile_path)
shape = reader.shapes()[0]  # Get the first shape

# Get the geometry object from the shape
shape_geom = shape.__geo_interface__  # Convert pyshp shape to shapely format

# Bounding box from shapefile
bbox = BBox(
    shape.bounds[0], shape.bounds[1], shape.bounds[2], shape.bounds[3], crs=CRS.WGS84
)

# Today's date and date from one week ago
today = datetime.utcnow().date()
week_ago = today - timedelta(days=7)

# Define Sentinel-1 IW data and evaluation script
data_collection = DataCollection.SENTINEL1_GRD
evalscript = """
//VERSION=3
function setup() {
  return {
    input: [{
      bands: ["VV"] // Select VV polarization
    }],
    mosaicking: Mosaicking.ORBIT,
    output: { id: "default", bands: 1 }
  };
}

function evaluatePixel(sample) {
  return [sample.VV];
}
"""

# Function to download and clip imagery
def download_and_clip(date):
    # Create WCS request with date and bounding box
    wcs_request = WcsRequest(
        data_collection=data_collection,
        time_interval=(date, date),
        evalscript=evalscript,
        bbox=bbox,
        output_format=MimeType.TIFF,
    )

    # Download image
    data = config.get_wcs_data(wcs_request)

    # Clip image to shapefile and save
    clipped_data = shape.intersection(data).bounds
    output_path = path.join(output_folder, f"S1_{date}.tif")
    with open(output_path, "wb") as f:
        f.write(data[clipped_data[1]:clipped_data[3], clipped_data[0]:clipped_data[2]])

# Loop through dates from the last week
for date in range(week_ago.year, today.year + 1):
    for month in range(1, 13):
        for day in range(1, 32):
            try:
                current_date = datetime(date, month, day).date()
                if current_date >= week_ago and current_date <= today:
                    download_and_clip(current_date)
                    print(f"Downloaded image for {current_date}")
            except:
                pass  # Skip errors and continue

print("Finished downloading Sentinel-1 imagery!")

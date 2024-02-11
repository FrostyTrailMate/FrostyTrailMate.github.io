import os
import asf_search as asf   
import fiona
from datetime import datetime, timedelta

#Global Variables
timestart = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
timeend = datetime.now().strftime('%Y-%m-%d')

shapefile_path = "Shapefiles/Yosemite_Boundary_4326.shp"
output_directory = "Outputs/SAR"

def extract_shapefile_bounds(shapefile_path):
    """Extracts bounding box coordinates (as WKT POLYGON) from a shapefile"""
    with fiona.open(shapefile_path, 'r') as shapefile:
        bounds = shapefile.bounds  
        wkt_polygon = f"POLYGON(({bounds[0]} {bounds[1]}, {bounds[2]} {bounds[1]}, {bounds[2]} {bounds[3]}, {bounds[0]} {bounds[3]}, {bounds[0]} {bounds[1]}))"
        return wkt_polygon

aoi = extract_shapefile_bounds(shapefile_path)    

opts = {
    "platform": "Sentinel-1",
    "processingLevel": "GRD",
    "start": "%s" % timestart,
    "end": "%s" % timeend,
    "download_site": "ASF",
    "nproc": 4
}

results =  asf.geo_search(intersectsWith=aoi, **opts)
print(f'{len(results)} results found')

# Create output directory if it doesn't exist
os.makedirs(output_directory, exist_ok=True)

# Download the images
'''for result in results:
    url = result['downloadUrl']
    datetime_str = result['date']  # Assuming 'date' holds the datetime of capture
    datetime_obj = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%SZ')
    filename = datetime_obj.strftime('%Y-%m-%d_%H-%M-%S') + '.zip'
    filepath = os.path.join(output_directory, filename)
    asf.download(url, filepath)
    print(f"Downloaded: {filename}")'''

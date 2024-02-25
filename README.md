The purpose of this project is to utilize Sentinel-1 SAR data to detect snow coverage on the ground in popular hiking areas.
The project was built and tested using Yosemite National Park in California in the United States.
 
Project Overview (in the order of operation)
1. Run all scripts (__main__.py)
   - Runs DEM.py and sentinel.py concurrently. Other scripts rely on a sequential approach, and are run individually. 
   - Arguments are parsed and passed only to the scripts that need them. 
   - List of arguments: 
      -s: the start date for image collection. Used in sentinel.py. Default: 6 days ago.
      -e: the end date for image collection. Used in sentinel.py. Default: today.
      -n: the name of the search area. Required. User-selectable. Must be unique. Used in all scripts.
      -c: coordinates for a bounding box. Either this argument or -p is required. Default format: xmin ymin xmax ymax. Usedi n DEM.py and Sentinel.py.
      -p: the relative path to a shapefile. Either this argument or -c is required. Used in DEM.py and sentinel.py.
      -d: the distance between sampling points. Default: .005 (about 500 meters). Used in sampling.py.
      -b: the SAR band to process for snow. Used in snow_detect.py. Can be either 'VV' or 'VH'. Default: VV
2. Collect and process DEM imagery ('Python Scripts/DEM.py'). Runs concurrently with sentinel.py.
   - Connect to the OpenTopography API and authenticate. It downloads updated NASA SRTM information at a 30m spatial resolution. Maximum 500 requests per day.
   - Uses -c or -p to get a bounding box, which it downloads the contents of.
   - Reproject the imagery to EPSG:4326 (WGS84). Although it appears to save in EPSG:4326 by default, the scripts work better by running it through a reprojection.
   - Clip the imagery to the study area shapefile (if applicable).
   - Record the location of the DEM files in the 'userpolygons' table.
3. Collect imagery data ('Python Scripts/sentinel.py'). Runs concurrently with DEM.py.
   - Create a signal handler so that the image download can be interrupted, and the acquired tiles will be automatically removed, as they may interfere with future image acquisition and merging.
   - Authenticate with the server, then create the variables for the bounding box coordinates and other image requirements. Bounding box coordinates are converted to UTM for use with Sentinel Hub.
   - Split the requested area into multiple 2500 x 2500 10-meter pixels. The server won't accept larger sub-boxes.
   - Collect and store raw Sentinel-1 imagery in a temporary folder, which is cleared at the end of the script
   - Send the requests to the server using 5 simultaneous connections. It is possible to use 6 usually without much trouble, but sometimes the images download too fast, and the server cuts off all the connections, meaning the process needs to be restarted. Five connections is safe.
   - Collects all images from the 'temp' folder and merges them
   - Reprojects the merged image into WGS84 (EPSG:4326) for compatibility
   - Records the datetime of acquisition in the database table 'userpolygons' in the field 'sar_processed'.
   - Clipping the image seems to increase the file size, so images are not clipped.
   - Removes the temprary files
4. Create sample points ('Python Scripts/sampling.py')
   - Uses a signal handler so that the point generation can be stopped mid-process (press ctrl + c), and the generated points will not be saved.
   - Check if the sampled points already exist by comparing the -n argument to the contents of the 'area_name' field in the 'samples' table of the database.
   - Using the DEM path from 'userpolygons', generates sample points at a user specified interval from the -d argument. 
   - Each point has an elevation from the underlying DEM saved to the 'elevation' field in the table 'samples' along with geometry data in the field 'point_geom'.
   - Save the sampling grid to the 'samples' table in the database, and disconnect.
5. Process Sentinel-1 SAR Imagery ('Python Scripts/snow_detect.py')
   - Connect to the database table 'userpolygons' and pull the Sentinel-1 SAR image path where the 'area_name' field matches the -n argument.
   - From the table 'samples', pull the sample points for which the field 'area_name' matches the -n argument.
   - Iterate through each sample point, and for each elevation strata of 100 meters (starting at the floor of the lowest elevation and going to the ceiling of the highest elevation, rounded to the respective closest 100 meters), count the number of points which have a raster value between -15 and -10 (the threshold values for snow detection).
   - Uses the band chosen by the user and provided as an argument in the __main__.py to detect the snow. By default it will use the VV polarization, but the user has the option to chose the VH polarization.
   - Save the number of positive detections, total points, and coverage percentage in each strata to the database table 'results'.
6. Create polygonal strata of the elevation topographic lines ('Python Scripts/strata.py')
   - Generate contour intervals (100 meters) and save them to a shapefile (for testing purposes) and to the database table 'results' (for website visualization).
7. Output
   - Create a webpage for visual display using JavaScript React and Node.js.
   - Create a FLask web application that serves an API endpoint (/api/results) to fetch data from a PostgreSQL database table (results). The data is retrieved and returned as JSON format through the API endpoint when a GET request received.
   - Create a table at the website that display the most relevant fields of the table served at the API endpoint.
   - Display results in an interactive geojson map (Polygon Layer: Snow Coverage % per Altitude; Polyline Layer: Hiking Trails at Yosemite's)
   - Create a graph to display the relation between the altitude and the % of snow coverage.
8. Databases Utilized
   - Table of user-selected polygon data and associated outputs from the various scripts (userpolygons).
   - Grid of sample points (samples).
   - Results by elevation interval (results).
   - Spatial Reference Systems (spatial_ref_sys). Installed by PostGIS.
9. Other files
    - requirements.txt: Contains a list of the python libraries and imports that are required for the project. Can be used as an installation file in pip or conda (only tested with these, may work with others). 
    - requirementsJS.txt: Contains a list of the javascript libraries that are required for the project. As of writing, all needs can be met by installing Node.js, available at nodejs.org. 
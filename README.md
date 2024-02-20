The purpose of this project is to utilize Sentinel-1 SAR data to detect snow coverage on the ground in popular hiking areas.
The project was built and tested using Yosemite National Park in California in the United States.
 
Project Overview (in the order of operation)
1. Preparation (no code)
   - A shapefile of the study area (Yosemite National Park, California, United States) was collected from ArcGIS Online.
2. Collect and process DEM imagery (DEM.py)
   - Connect to the OpenTopography API and authenticate. It downloads updated NASA SRTM information at a 30m spatial resolution. Maximum 500 requests per day.
   - Project the imagery to EPSG:4326 (WGS84)
   - Clip the imagery to the study area shapefile
   - Generate contour intervals (100 meters) and save them to a shapefile (for testing purposes) and to the database table 'dem_p'
3. Create sample points (sampling.py)
   - Create a signal handler so that the point generation can be stopped mid-process, and the generated points will not be saved
   - Check if the sampled points already exist
   - Using the shapefile from step 1, create a sampling grid of points at every 500 meters
   - Each point has an elevation from the underlying DEM saved to a field in the table 'samples' along with geometry data
   - Save the sampling grid to the DB
4. Collect imagery data (sentinel.py)
   - Create a signal handler so that the image download can be interrupted, and the acquired tiles will be automatically removed, as they may interfere with future image acquisition and merging
   - Authenticate with the server, then create the variables for the bounding box coordinates and other image requirements
   - Split the requested area into multiple 2500 x 2500 10-meter pixels. The server won't accept larger sub-boxes
   - Collect and store raw Sentinel-1 imagery in a temporary folder, which is cleared at the end of the script
   - Send the requests to the server using 5 simultaneous connections. It is possible to use 6 usually without much trouble, but sometimes the images download too fast, and the server cuts off all the connections, meaning the process needs to be restarted. Five connections is safer.
   - Collects all images from the 'temp' folder and merges them
   - Reprojects the merged image into WGS84 (EPSG:4326) for compatibility
   - Records the datetime of acquisition and the path to the folder in the database table 'sar_raw'
   - Clipping the image actually increased the file size, so the image was not clipped. This likely will be even less of an issue when the script is altered to allow the user to create their own bounding box
   - Removes the temprary files
5. Process Sentinel-1 SAR Imagery (snow_detect.py)
   - Connect to the database table 'sar_raw' and pull the Sentinel-1 SAR image path where the 'processed' field is null
   - From the table 'samples', pull the sample points
   - Iterate through each sample point, and for each elevation strata of 100 meters, count the number of points which have a raster value between -15 and -10, the threshold values for snow detection
   - Save results, divided into elevation strata, to the database table 'results'
6. Databases Utilized
   - Sentinel-1 file information (sar_raw)
   - Raw DEM file information (demraw)
   - Processed DEM files and strata (dem_p)
   - Grid of sample points (samples)
   - Results by elevation interval (results)
   - Spatial Reference Systems (spatial_ref_sys). Installed by PostGIS.
7. Output
   - Create a webpage for visual display
   - Display results in a table
   - Display results in a map
   - Display results in a graph
 
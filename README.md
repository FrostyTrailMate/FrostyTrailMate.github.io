The purpose of this project is to utilize Sentinel-1 SAR data to detect snow coverage on the ground in popular hiking areas.
The project was built and tested using Yosemite National Park in California in the United States.
 
Project Overview
1. Preparation (no code)
   - A shapefile of the study area was collected from ArcGIS Online.
2. Collect imagery data (yose_sentinel.py)
   - Automatically check for new Sentinel-1 imagery in the study area (as defined by shapefiles in the 'Shapefiles' project folder).
     - Check the imagery against the database to see if the imagery is new.
   - Collect and store raw imagery in a separate folder. Images are collected for the most recent Sentinel-1 data that covers the study area, and for the previous September (the most recent snow-free period). Images were clipped to the study area.
   - Collect and store DEM data in a separate folder. Images were clipped to the study area.
3. Collect and process DEM imagery (yose_DEM.py)
   - Connect to the USGS Earth Explorer API
   - Clip the imagery to the study area shapefile
   - Generate contour intervals (100 meters)
   - Connect to the database and save
4. Create sample points
   - Check if the sampled points already exist
   - Using the shape from step 1, create a multipoint sampling grid at every 100 meters
   - Save the sampling grid to the DB
5. Process Sentinel-1 SAR Imagery
   - Pull the Sentinel-1 SAR image from the database
   - Preprocess the image
   - Divide the data into training and processing
   - Train a random forest classifier
   - Test and obtain accuracy results
   - Save result to DB
6. Databases Utilized
   - Raw Sentinel-1 files
   - Raw DEM files
   - Processed Sentinel-1 files
   - Processed DEM files
   - Grid of sample points
   - Results by elevation interval
7. Output
   - Create a webpage for visual display
   - Display results in a table
   - Display results in a map
 

 
 

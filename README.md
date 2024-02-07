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
 3. Collect DEM imagery (yose_DEM.py)
      - Connect to the USGS Earth Explorer API
 4. Process DEM
    - Convert the DEM raster into a topographic strata (layers) of 100 meters.
    - Save to DB
 5. Process Sentinel-1 SAR Imagery
    - Divide the image into cells equivalent to the DEM layer (30m)
    - Calculate image reflectance difference between 'current' imagery and 'snow-free' (September) imagery
    - Save result to DB
 6. Databases
    - Raw Sentinel-1 files
    - Raw DEM files
    - Processed Sentinel-1 files
    - Processed DEM files
    - Results by elevation interval
7. Output
   - Create a webpage for visual display
   - Display results in a table
   - Display results in a map
 

 
 

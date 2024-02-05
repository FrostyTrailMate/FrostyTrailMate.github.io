# The purpose of this project is to utilize Sentinel-1 SAR data to detect snow coverage on the ground in popular hiking areas.
# The project was built and tested using Yosemite National Park in California in the United States.
# 
# Project Overview
# 1) Preparation
#     a) A shapefile of the study area was collected from ArcGIS Online.
# 2) Collect imagery data
#     a) Automatically check for new Sentinel-1 imagery in the study area (as defined by shapefiles in the 'Shapefiles' project folder).
#            I) Check the imagery against the database to see if the imagery is new.
#     b) Collect and store raw imagery in a separate folder. Images are collected for the most recent Sentinel-1 data that covers the study area,
#         and for the previous September (the most recent snow-free period). Images were clipped to the study area.
#     c) Collect and store DEM data in a separate folder. Images were clipped to the study area.
# 3) Process DEM
#     a) Convert the DEM raster into a topographic strata (layers) of 100 meters.
#     b) Save to DB
# 4) Process Sentinel-1 SAR Imagery
#     a) Divide the image into cells equivalent to the DEM layer (30m)
#     b) Calculate image reflectance difference between 'current' imagery and 'snow-free' (September) imagery
#     c) Save result to DB
# 5) Databases
#     a) Raw Sentinel-1 files
#     b) Raw DEM files
#     c) Processed Sentinel-1 files
#     d) Processed DEM files
# 
# 
# 
# 
#
# 
# 

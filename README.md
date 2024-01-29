The group topic for Sebastian Andrade, Carolina Cardoso, and myself (Chris Hubach) will be utilizing SAR data to detect snowpack elevations. Some of the steps that we have identified for this project include:

ETL:
Obtain SAR data from the Sentinel-1 API
Obtain DEM data from USGS Earth Explorer API or OpenTopography API
Generate random sample points based on the size of the sample area
Calculate if each point is covered in snow or is bare ground

CRUD:
Save calculation to database
Save results of study area to database

API:
Incorporate Leaflet into the user's selection of a custom bounding area
Allow the user to select a date
Display a table for the user to view results based on regular elevation intervals
Find a web host to provide the service on

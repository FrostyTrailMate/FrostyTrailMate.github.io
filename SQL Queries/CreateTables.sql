CREATE TABLE demraw (
    id_dem SERIAL PRIMARY KEY,
    delevation FLOAT,
    darea VARCHAR(30),
    ddatetime TIMESTAMP,
	draster RASTER);
	
CREATE TABLE results (
    id_res SERIAL PRIMARY KEY,
    elevation FLOAT,
    coverage_percentage FLOAT,
    ddatetime TIMESTAMP);
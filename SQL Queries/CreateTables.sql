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


/*Test of table localhost*/

/*CREATE TABLE resultstestapi (
    id_res SERIAL PRIMARY KEY,
	altitude INT,
    snowcover DECIMAL(10, 1),
	darea VARCHAR(30);
	rdate DATE);
	
INSERT INTO resultstestapi (id_res, altitude, snowcover, darea, rdate) VALUES
	(1, 100, 0.5, 'Yosemite National Park', '2021-01-01'),
	(2, 200, 10.5, 'Yosemite National Park', '2021-01-01'),
	(3, 300, 20.5, 'Yosemite National Park', '2021-01-01'),
	(4, 400, 30.5, 'Yosemite National Park', '2021-01-01'),
	(5, 500, 40.5, 'Yosemite National Park', '2021-01-01'),
	(6, 600, 50.5, 'Yosemite National Park', '2021-01-01'),
	(7, 700, 60.5, 'Yosemite National Park', '2021-01-01'),
	(8, 800, 70.5, 'Yosemite National Park', '2021-01-01'),
	(9, 900, 80.5, 'Yosemite National Park', '2021-01-01'),
	(10, 1000, 90.5, 'Yosemite National Park','2021-01-01');*/
import psycopg2
from psycopg2 import sql

# Database connection parameters
dbname = 'FTM8'
user = 'postgres'
password = 'admin'
host = 'DESKTOP-UIUIA2A'
port = '5432'

# Connect to default postgres database to create FTM8 database if it doesn't exist
default_conn_params = {
    'user': user,
    'password': password,
    'host': host,
    'port': port
}

try:
    conn = psycopg2.connect(**default_conn_params)
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
    conn.close()
except psycopg2.errors.DuplicateDatabase:
    print("Database already exists. Proceeding to drop and create tables.")
except Exception as e:
    print("Error creating database:", e)

# Connect to FTM8 database
conn_params = {
    'dbname': dbname,
    'user': user,
    'password': password,
    'host': host,
    'port': port
}

try:
    conn = psycopg2.connect(**conn_params)
    cursor = conn.cursor()
except Exception as e:
    print("Unable to connect to database:", e)
    exit()

# Define table creation queries
table_queries = [
    """
    DROP TABLE IF EXISTS sar_raw;
    CREATE TABLE sar_raw (
        id SERIAL PRIMARY KEY,
        datetime TIMESTAMP,
        time_collected TIMESTAMP NOT NULL,
        sOrbit INT,
        sSlice INT,
        sArea varchar,
        path varchar,
        image varchar,
        processed VARCHAR
    );
    """,
    """
    DROP TABLE IF EXISTS samples;
    CREATE TABLE samples (
        id SERIAL PRIMARY KEY,
        datetime TIMESTAMP NOT NULL,
        area VARCHAR NOT NULL,
        point_geom GEOMETRY(POINT, 4326) NOT NULL,
        elevation FLOAT NOT NULL,
        shapefile_path VARCHAR NOT NULL
    );
    """,
    """
    DROP TABLE IF EXISTS demraw;
    CREATE TABLE demraw (
        id_dem SERIAL PRIMARY KEY,
        delevation FLOAT,
        darea VARCHAR(30),
        ddatetime TIMESTAMP,
        draster RASTER
    );
    """,
    """
    DROP TABLE IF EXISTS DEM_p;
    CREATE TABLE DEM_p (
        id SERIAL PRIMARY KEY,
        vector GEOMETRY(MULTIPOLYGON, 4326),
        area_name VARCHAR(50) NOT NULL
    );
    """,
    """
    DROP TABLE IF EXISTS results;
    CREATE TABLE results (
        id_res SERIAL PRIMARY KEY NOT NULL,
        area_name VARCHAR,
        elevation VARCHAR NOT NULL,
        coverage_percentage FLOAT NOT NULL,
        ddatetime TIMESTAMP NOT NULL,
        detected_points INT NOT NULL,
        total_points INT NOT NULL
    );
    """
]

# Execute table creation queries
try:
    for query in table_queries:
        cursor.execute(query)
    print("Tables created successfully")
except Exception as e:
    print("Error creating tables:", e)

# Close connections
cursor.close()
conn.close()

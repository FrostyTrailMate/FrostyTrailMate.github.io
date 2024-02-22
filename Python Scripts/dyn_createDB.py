from sqlalchemy import create_engine, MetaData, text
import os
import shutil

print("Running createDB.py...")

# Database connection parameters
dbname = 'FTM8'
user = 'postgres'
password = 'admin'
host = 'DESKTOP-UIUIA2A'
port = '5432'

# Connection URL
connection_url = f'postgresql://{user}:{password}@{host}:{port}/{dbname}'

try:
    print("Connecting to FTM8 database...")
    engine = create_engine(connection_url)
    conn = engine.connect()
    print("Connected to FTM8 database.")
except Exception as e:
    print("Unable to connect to database:", e)
    exit()

metadata = MetaData()

# Define table dropping and creation queries
table_queries = [
    
    # Enable PostGIS extensions
    """
    CREATE EXTENSION IF NOT EXISTS postgis;
    """,
    """
    CREATE EXTENSION IF NOT EXISTS adminpack;
    """,
    """
    CREATE EXTENSION IF NOT EXISTS plpgsql;
    """,
    """
    CREATE EXTENSION IF NOT EXISTS postgis_raster;
    """,
    """
    DROP TABLE IF EXISTS public.sar_raw CASCADE;
    """,
    """
    CREATE TABLE public.requests (
        id SERIAL PRIMARY KEY, 
        datetime TIMESTAMP, 
        time_collected TIMESTAMP NOT NULL, 
        sOrbit INT, 
        sSlice INT, 
        sArea VARCHAR, 
        path VARCHAR, 
        image VARCHAR, 
        processed VARCHAR);
    """,
    """
    DROP TABLE IF EXISTS public.samples CASCADE;
    """,
    """
    CREATE TABLE public.samples (
        id SERIAL PRIMARY KEY,
        datetime TIMESTAMP NOT NULL,
        area VARCHAR NOT NULL FOREIGN KEY REFERENCES public.sar_raw(sArea),
        point_geom GEOMETRY(POINT, 4326) NOT NULL,
        elevation FLOAT NOT NULL,
        shapefile_path VARCHAR NOT NULL
    );
    """,
    """
    DROP TABLE IF EXISTS public.demraw CASCADE;
    """,
    """
    CREATE TABLE public.demraw (
        id_dem SERIAL PRIMARY KEY,
        delevation FLOAT,
        darea VARCHAR(30),
        ddatetime TIMESTAMP,
        draster RASTER
    );
    """,
    """
    DROP TABLE IF EXISTS public.DEM_p CASCADE;
    """,
    """
    CREATE TABLE public.DEM_p (
        id SERIAL PRIMARY KEY,
        vector GEOMETRY(MULTIPOLYGON, 4326),
        area_name VARCHAR(50) NOT NULL
    );
    """,
    """
    DROP TABLE IF EXISTS public.results CASCADE;
    """,
    """
    CREATE TABLE public.results (
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

# Execute table dropping and creation queries
try:
    print("Dropping and creating tables...")
    for query in table_queries:
        compiled_query = text(query)
        print("Executing query:", compiled_query)
        conn.execute(compiled_query)
    print("Tables dropped and created successfully.")
except Exception as e:
    print("Error dropping/creating tables:", e)

# Close connection
conn.commit()
conn.close()
print("Database connection closed.")

# Clear contents of the 'Output' folder
output_folder = 'Outputs'
try:
    shutil.rmtree(output_folder)
    print(f"Contents of '{output_folder}' cleared successfully.")
except FileNotFoundError:
    pass
except Exception as e:
    print("Error clearing contents of 'Output' folder:", e)

# Recreate subfolders
subfolders = ['DEM', 'Samples', 'SAR', os.path.join('SAR', 'temp')]
try:
    os.makedirs(output_folder, exist_ok=True)
    for folder in subfolders:
        os.makedirs(os.path.join(output_folder, folder), exist_ok=True)
    print("Output subfolders created successfully.")
except Exception as e:
    print("Error creating subfolders:", e)

print("createDB.py completed.")
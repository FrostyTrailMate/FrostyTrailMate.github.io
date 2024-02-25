from sqlalchemy import create_engine, MetaData, text
import os
import shutil

print("++++++++++ Running createDB.py ++++++++++")

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
    print("Connected.")
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
    
    # Drop and create tables
    """
    DROP TABLE IF EXISTS public.userpolygons CASCADE;
    """,
    """
    CREATE TABLE IF NOT EXISTS public.userpolygons (
        id SERIAL,
        area_name VARCHAR PRIMARY KEY,
        datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        geom GEOMETRY(POLYGON, 4326),
        dem_path VARCHAR,
        dem_processed VARCHAR,
        sar_path VARCHAR,
        sar_processed VARCHAR
    );
    """,
    """
    DROP TABLE IF EXISTS public.samples CASCADE;
    """,
    """
    CREATE TABLE public.samples (
        id SERIAL PRIMARY KEY,
        datetime TIMESTAMP NOT NULL,
        area_name VARCHAR NOT NULL,
        FOREIGN KEY(area_name) REFERENCES public.userpolygons(area_name),
        point_geom GEOMETRY(POINT, 4326) NOT NULL,
        elevation FLOAT NOT NULL
    );
    """,
    """
    DROP TABLE IF EXISTS public.results CASCADE;
    """,
    """
    CREATE TABLE public.results (
        id_res SERIAL PRIMARY KEY NOT NULL,
        area_name VARCHAR NOT NULL,
        FOREIGN KEY(area_name) REFERENCES public.userpolygons(area_name),
        elevation VARCHAR NOT NULL,
        coverage_percentage FLOAT NOT NULL,
        datetime TIMESTAMP NOT NULL,
        detected_points INT NOT NULL,
        total_points INT NOT NULL,
        strata GEOMETRY(MULTIPOLYGON, 4326)
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

# Save changes and close connection
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
subfolders = ['DEM', 'Samples', 'SAR', os.path.join('Shapefiles','ElevationStrata'), os.path.join('Shapefiles','SamplePoints'), os.path.join('SAR', 'temp')]
try:
    os.makedirs(output_folder, exist_ok=True)
    for folder in subfolders:
        os.makedirs(os.path.join(output_folder, folder), exist_ok=True)
    print("Output subfolders created successfully.")
except Exception as e:
    print("Error creating subfolders:", e)

print("---------- createDB.py completed -----------.")
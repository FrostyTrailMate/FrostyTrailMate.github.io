"""
This script defines a Flask application to handle requests related to querying database tables and creating entries.
"""

import traceback
from flask import Flask, jsonify, request, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import subprocess
import json
from sqlalchemy.exc import SQLAlchemyError
import os

# Set up atabase configuration
DB_CONFIG = {
    "database": "FTM8",
    "username": "editor_sebas",
    "password": "12345678",
    "host": "DESKTOP-UIUIA2A",
    "port": "5432"
}

# Create a Flask application
app = Flask(__name__)

# Enable Cross-Origin Resource Sharing (CORS) for all routes
CORS(app)

# Set the database connection URI
username = DB_CONFIG['username']
password = DB_CONFIG['password']
host = DB_CONFIG['host']
port = DB_CONFIG['port']
database = DB_CONFIG['database']
database_uri = f"postgresql://{username}:{password}@{host}:{port}/{database}"
app.config['SQLALCHEMY_DATABASE_URI'] = database_uri

# Create object to control SQLAlchemy from the Flask app
db = SQLAlchemy(app)

# Define the SQLAlchemy model for the results table
class results(db.Model):
    """
    SQLAlchemy model for 'results' table.

    Attributes:
        id_res (int): The primary key of the 'results' table.
        area_name (str): The name of the area.
        elevation (str): The elevation data.
        coverage_percentage (float): The percentage coverage.
        datetime (datetime.date): The date and time of the entry.
        detected_points (int): The number of detected points.
        total_points (int): The total number of points.
    """
    id_res = db.Column(db.Integer, primary_key=True)
    area_name = db.Column(db.String(30))
    elevation =  db.Column(db.String(30))
    coverage_percentage = db.Column(db.Float)
    datetime = db.Column(db.Date)
    detected_points = db.Column(db.Integer)
    total_points = db.Column(db.Integer)

# Define the route to fetch data from the 'results' table
@app.route('/api/results')
def get_results():
    """
    Endpoint to fetch all results from the 'results' table.

    Returns:
        json: JSON response containing all results from the 'results' table.
    """
    resultftm8 = results.query.order_by(results.id_res).all()
    data = [{'id_res': result.id_res,
             'area_name': result.area_name,
             'elevation': result.elevation,
             'coverage_percentage': result.coverage_percentage,
             'datetime': result.datetime,
             'detected_points': result.detected_points,
             'total_points': result.total_points}
            for result in resultftm8]
    return jsonify(data)

# Define the SQLAlchemy model for the userpolygons table
class userpolygons(db.Model):
    """
    SQLAlchemy model for 'userpolygons' table.

    Attributes:
        id (int): A serial (unique) identifier for the table.
        area_name (str): The name of the area. This is the primary key.
        datetime (timestamp): The date and time of the entry.
        geom (geometry): The geometry of the area.
        dem_path (str): The path to the DEM file.
        dem_processed (str): The path to the processed DEM file.
        sar_path (str): The path to the SAR file.
        sar_processed (str): The path to the processed SAR file.
        arg_s (str): The start date for the query.
        arg_e (str): The end date for the query.
        arg_b (str): The raster band for the query.
        arg_d (str): The distance for the query.
        arg_p (str): The path to a shapefile, which can be used in place of the -c argument on the __main__.py script.
    """
    id = db.Column(db.Integer)
    area_name = db.Column(db.String(), primary_key=True)
    datetime = db.Column(db.DateTime)
    geom = db.Column(db.String()) # Not used in the API, so it's processed as a string to prevent errors.
    dem_path = db.Column(db.String())
    dem_processed = db.Column(db.String())
    sar_path = db.Column(db.String())
    sar_processed = db.Column(db.String())
    arg_s = db.Column(db.String())
    arg_e = db.Column(db.String())
    arg_b = db.Column(db.String(2))
    arg_d = db.Column(db.String())
    arg_p = db.Column(db.String())
    
# Define the route to fetch data from the 'userpolygons' table
@app.route('/api/userpolygons')
def get_userpolygons():
    """
    Endpoint to fetch all entries from the 'userpolygons' table.

    Returns:
        json: JSON response containing all results from the 'userpolygons' table.
    """
    userftm8 = userpolygons.query.order_by(userpolygons.id).all()
    data = [{'id': userpolygon.id,
            'area_name': userpolygon.area_name,
            'datetime': userpolygon.datetime,
            'geom': userpolygon.geom,
            'dem_path': userpolygon.dem_path,
            'dem_processed': userpolygon.dem_processed,
            'sar_path': userpolygon.sar_path,
            'sar_processed': userpolygon.sar_processed,
            'arg_s': userpolygon.arg_s,
            'arg_e': userpolygon.arg_e,
            'arg_b': userpolygon.arg_b,
            'arg_d': userpolygon.arg_d,
            'arg_p': userpolygon.arg_p}
            for userpolygon in userftm8]
    return jsonify(data)

# Create additional error classes for the /api/create endpoint
class APIError(Exception):
    """Base class for API-related errors"""
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.status_code = status_code

class InvalidDataError(APIError):
    """Error for invalid data submitted by the user"""
    pass

class DatabaseError(APIError):
    """Error caused by an issue with the database"""
    pass

# Define the route to process user inputs and run the __main__.py script
@app.route('/api/create', methods=['POST'])
def create_entry():
    """
    Endpoint to run the __main__.py script with the provided data.

    Returns:
        json: JSON response indicating the success of the operation.

    Raises:
        ValueError: If any required field is missing in the request.
        Exception: For any other unexpected error during the process.
    """
    if request.method == 'POST':
        try:
            # Accessing data using request.json
            data = request.json
            print("Received JSON data:", data)
            startDate = data.get('startDate')
            endDate = data.get('endDate')
            coordinates = data.get('coordinates')
            areaName = data.get('areaName')
            distance = str(float(data.get('distance'))/ 100000)  # Convert aproximately distance from meters to °
            rasterBand = data.get('rasterBand')

            # Validate that all required fields are present
            if None in [startDate, endDate, coordinates, areaName, distance, rasterBand]:
                raise ValueError("Missing required fields")

            coordinates_str = json.dumps(coordinates)
            
            # Execute __main__.py using provided arguments
            subprocess.run(["python", "__main__.py", "-s", startDate, "-e", endDate, "-c", coordinates_str, "-n", areaName, "-d", distance, "-b", rasterBand])
            
            return jsonify({'message': 'Script executed successfully'}), 201
        except ValueError as ve:
            raise InvalidDataError(str(ve))
        except SQLAlchemyError as sqle: 
            raise DatabaseError("Error encountered while processing database query")  
        except Exception as e: 
            traceback.print_exc()
            raise APIError('Internal server error. Contact the administrator.', 500)
    else:
        raise APIError('Method not allowed', 405)

# Define the route to fetch the geojson file baesd on area_name (the -n argument)
@app.route('/api/geojson/<selected_area>')
def get_geojson(selected_area):
    """
    Endpoint to fetch the geojson file for the selected area.

    Args:
        selected_area (str): The name of the selected area.

    Returns:
        file: The geojson file for the selected area.
    """
    try:
        # Set up the routing to find the geojson file
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        geojson_dir = os.path.join(base_dir, 'components', 'geojsons') 
        file_path = os.path.join(geojson_dir, f'{selected_area}.geojson')

        if not os.path.exists(file_path):
             return jsonify({'error': 'GeoJSON file not found'}), 404

        return send_file(file_path, as_attachment=True, mimetype='application/json')

    except FileNotFoundError:
        return jsonify({'error': 'GeoJSON file not found'}), 404

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': 'An error occurred'}), 500 

# Define the route to reset the database and output folders
@app.route('/api/reset', methods=['POST'])
def resetDB():
    """
    Endpoint to run the createDB.py script with the provided data.

    Returns:
        json: JSON response indicating the success of the operation.

    Raises:
        Exception: For any unexpected error during the process.
    """
    if request.method == 'POST':
        try:
            # Execute subprocess for createDB.py
            subprocess.run(["python", "Python Scripts/createDB.py"])
            
            return jsonify({'message': 'Script executed successfully'}), 201
        except Exception as e: 
            traceback.print_exc()
            raise APIError('Internal server error.', 500)

# Define the route to handle API errors
@app.errorhandler(APIError)
def handle_api_error(error):
    response = jsonify({'error': error.message})
    response.status_code = error.status_code
    return response

if __name__ == '__main__':
    app.run(debug=True)
"""
This script defines a Flask application to handle requests related to querying results and creating entries.
"""

import traceback
from flask import Flask, jsonify, request, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import subprocess
import json
from sqlalchemy.exc import SQLAlchemyError
import os

# Database configuration
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

# Set the database connection URI in the app configuration
username = DB_CONFIG['username']
password = DB_CONFIG['password']
host = DB_CONFIG['host']
port = DB_CONFIG['port']
database = DB_CONFIG['database']
database_uri = f"postgresql://{username}:{password}@{host}:{port}/{database}"
app.config['SQLALCHEMY_DATABASE_URI'] = database_uri

# Create object to control SQLAlchemy from the Flask app
db = SQLAlchemy(app)

# Define the SQLAlchemy model
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

@app.route('/api/create', methods=['POST'])
def create_entry():
    """
    Endpoint to create an entry in the 'results' table.

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
            distance = data.get('distance')
            rasterBand = data.get('rasterBand')

            # Validate that all required fields are present
            if None in [startDate, endDate, coordinates, areaName, distance, rasterBand]:
                raise ValueError("Missing required fields")

            coordinates_str = json.dumps(coordinates)
            
            # Execute subprocess
            subprocess.run(["python", "__main__.py", "-s", startDate, "-e", endDate, "-c", coordinates_str, "-n", areaName, "-d", distance, "-b", rasterBand])
            
            return jsonify({'message': 'Script executed successfully'}), 201
        except ValueError as ve:
            raise InvalidDataError(str(ve))
        except SQLAlchemyError as sqle: # Example for database problems
            raise DatabaseError("Error encountered while processing database query")  
        except Exception as e: 
            traceback.print_exc()
            raise APIError('Internal server error. Contact the administrator.', 500)
    else:
        raise APIError('Method not allowed', 405)
    

import os
import logging

# Configure logging
logging.basicConfig(filename='flask.log', level=logging.INFO)

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


@app.errorhandler(APIError)
def handle_api_error(error):
    response = jsonify({'error': error.message})
    response.status_code = error.status_code
    return response

if __name__ == '__main__':
    app.run(debug=True)

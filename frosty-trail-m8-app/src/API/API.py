"""
This script defines a Flask application to handle requests related to querying results and creating entries.
"""

import traceback
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import subprocess
import json
#from geoalchemy2 import Geometry

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
             'total_points': result.total_points} for result in resultftm8]
    return jsonify(data)

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
            return jsonify({'error': str(ve)}), 400  # Bad request due to missing fields
        except Exception as e:
            traceback.print_exc()
            return jsonify({'error': 'Internal server error occurred. Please contact the administrator for assistance.'}), 500
    else:
        return jsonify({'error': 'Method not allowed'}), 405

if __name__ == '__main__':
    app.run(debug=True)

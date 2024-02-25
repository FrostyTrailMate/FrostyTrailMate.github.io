from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import subprocess

DB_CONFIG = {
    "database": "FTM8",
    "username": "editor_sebas",
    "password": "12345678",
    "host": "DESKTOP-UIUIA2A",
    "port": "5432"}

# Create a flask application
app = Flask(__name__)
# Enable CORS for all routes
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
class userpolygons(db.Model):
    
    # Table is implicitly called by the name of the class
    id = db.Column(db.Integer, primary_key=True)
    area_name = db.Column(db.String())
    datetime = db.Column(db.Date)
    geom = db.Column(db.Geometry(geometry_type='POLYGON', srid=4326))
    dem_path = db.Column(db.String())
    dem_processed = db.Column(db.String())
    sar_path = db.Column(db.String())
    sar_processed = db.Column(db.String())
    arg_s = db.Column(db.String())
    arg_e = db.Column(db.String())
    arg_b = db.Column(db.String())
    arg_d = db.Column(db.String())
    arg_p = db.Column(db.String())

    

# Route to fetch data
# This function will be called when a request is made to the '/api/results' endpoint
# Route to fetch sorted data by altitude

@app.route('/api/create', methods=['POST'])   
def create_poly():
    # Extract arguments from the request
    args = {
        '-s': request.json.get('start_date'),
        '-e': request.json.get('end_date'),
        '-n': request.json.get('area_name'),
        '-c': request.json.get('bounding_box'),
        '-d': request.json.get('distance'),
        '-b': request.json.get('raster_band')
    }
    
    # Pass arguments to the __main__.py script
    command = ['python', '__main__.py']
    for arg, value in args.items():
        if value:
            command.extend([arg, value])
    
    # Execute the script
    subprocess.run(command)
    
    return jsonify({'message': 'Script executed successfully'})

if __name__ == '__main__':
    app.run(debug=True)

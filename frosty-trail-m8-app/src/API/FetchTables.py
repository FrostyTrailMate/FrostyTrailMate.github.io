from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

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
class results(db.Model):
    
    # Table is implicitly called by the name of the class
    id_res = db.Column(db.Integer, primary_key=True)
    area_name = db.Column(db.String(30))
    elevation =  db.Column(db.String(30))
    coverage_percentage = db.Column(db.Float)
    datetime = db.Column(db.Date)
    detected_points = db.Column(db.Integer)
    total_points = db.Column(db.Integer)
    

# Route to fetch data
# This function will be called when a request is made to the '/api/results' endpoint
# Route to fetch sorted data by altitude

@app.route('/api/results')   
def get_results():
    
    resultftm8 = results.query.order_by(results.id_res).all()
    
    data = [{'id_res': result.id_res,
             'area_name': result.area_name, 
             'elevation': result.elevation,
             'coverage_percentage': result.coverage_percentage,
             'ddatetime': result.datetime, 
             'detected_points': result.detected_points, 
             'total_points': result.total_points} for result in resultftm8]
    
    return jsonify(data)
    
if __name__ == '__main__':
    app.run(debug=True)



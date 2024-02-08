from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, jsonify, request

DB_CONFIG = {
    "database": "FTM8",
    "username": "editor_sebas",
    "password": "12345678",
    "host": "DESKTOP-UIUIA2A",
    "port": "5432"}

# Create a flask application
app = Flask(__name__)

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

class resultstestapi(db.Model):
    
    # Table is implicitly called by the name of the class
    
    id_res = db.Column(db.Integer, primary_key=True)
    altitude = db.Column(db.Float)
    snowcover = db.Column(db.Integer)
    darea = db.Column(db.String(30))

# Route to fetch data
# This function will be called when a request is made to the '/api/results' endpoint
@app.route('/api/results', methods=['GET'])
def get_results():
    if request.method == 'GET':
        results = resultstestapi.query.all()
        data = [{'altitude': result.altitude, 'snowcover': result.snowcover, 'darea': result.darea} for result in results]
        return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
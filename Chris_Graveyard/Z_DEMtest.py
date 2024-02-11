#!/usr/bin/python
import requests

# The user credentials that will be used to authenticate access to the data
username = "iuag3fu3"
password = "V9wYMuRu3JBKAeX."
  
# The url of the file we wish to retrieve
url = "http://e4ftl01.cr.usgs.gov/MOLA/MYD17A3H.006/2009.01.01/MYD17A3H.A2009001.h12v05.006.2015198130546.hdf.xml"

try:
    # Create a session
    session = requests.Session()
    
    # Attach the user credentials to the session
    session.auth = (username, password)
    
    # Submit the request
    response = session.get(url)
    
    # Raise an exception in case of http errors
    response.raise_for_status()
    
    # Print out the result (not a good idea with binary data!)
    print(response.content)
    
except requests.exceptions.HTTPError as e:
    # Handle HTTP errors
    print(e)
except requests.exceptions.RequestException as e:
    # Handle other request errors
    print(e)

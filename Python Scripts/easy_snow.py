"""
This file contains the easiest way to dected snow trough backscatter intensity. 

In my search I used 0.8 just to have a value, but a common starting point for snow detection in SAR imagery 
is to use a threshold value in the range of -10 dB (decibels) to -15 dB for backscatter intensity. 
However, this value can vary widely depending on the aforementioned factors and may require adjustment through empirical 
testing and validation.

### MY SEARCH 
I'm aiming to detect the presence of snow in SAR images, with backsatter intensity above 0.8, 
without having explicit labels indicating whether snow is present or not.

Assuming the SAR images are obtained from the sRaster field of the sar_raw table from a PostgreSQL database.

Help me create a python algorithm that does everything automatically, using whatever you think is best.
"""

import psycopg2
import numpy as np
import cv2

# Connect to the PostgreSQL database
conn = psycopg2.connect(
    dbname="FTM8",
    user="postgres",
    password="admin",
    host="DESKTOP-UIUIA2A",
    port="5432"
)
cur = conn.cursor()

# Retrieve SAR images from the database ##### Need to check if the image has been processed already or not
cur.execute("SELECT sRaster FROM sar_raw")
sar_images = cur.fetchall()

# Define a function to process each SAR image
def process_sar_image(sar_image):
    # Convert SAR image from bytes to numpy array
    sar_array = np.frombuffer(sar_image[0], dtype=np.uint8)
    sar_img = cv2.imdecode(sar_array, flags=cv2.IMREAD_GRAYSCALE)
    
    # Calculate backscatter intensity
    backscatter_intensity = sar_img.astype(float) / 255.0
    
    # Threshold backscatter intensity to identify regions with intensity above 0.8
    ## NEED TO CHANGE THE VALUE TO WHAT WE WANT
    snow_mask = backscatter_intensity > 0.8
    
    # Analyze the identified regions to determine if snow is present
    if np.any(snow_mask):
        snow_present = True
    else:
        snow_present = False
    
    return snow_present

# Iterate over all SAR images and detect snow presence ### It should iterate only through one image at each of the sample points created in systematic_sampling.py
for sar_image in sar_images:
    snow_present = process_sar_image(sar_image)
    print("Snow present:", snow_present)

# Close the database connection
cur.close()
conn.close()

"""
steps explained:
Connect to the PostgreSQL database:

The psycopg2 library is used to establish a connection to the PostgreSQL database.
You provide your database credentials such as database name, username, password, host, and port to connect to the database.
Retrieve SAR images from the database:

A SQL query is executed to fetch SAR images from the database.
These images are stored as binary data (bytea) in the database.
Define a function to process each SAR image:

The process_sar_image function is defined to handle each SAR image.
It decodes the binary data into a NumPy array using OpenCV (cv2.imdecode) and converts it to grayscale.
Calculates the backscatter intensity by dividing the pixel values by 255.0 to normalize them between 0 and 1.
Thresholds the backscatter intensity to identify regions with intensity above 0.8, potentially indicating the presence of snow.
Determines if snow is present by checking if there are any True values in the snow mask.
Iterate over all SAR images and detect snow presence:

The main loop iterates over all the fetched SAR images.
For each SAR image, the process_sar_image function is called to detect the presence of snow.
The results indicating whether snow is present or not are printed.
Close the database connection:

Once all SAR images are processed, the database connection is closed to release resources.

"""

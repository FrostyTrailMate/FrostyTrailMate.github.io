"""
I'm aiming to detect the presence of snow in SAR images, with backsatter intensity in the range of -10 dB (decibels) to -15 dB, without having explicit labels indicating whether snow is present or no, trough a python code.

The first step of the code should be to check if a new image has been written by checking the the ‘processed’ field of the 'sar_raw' table from a PostgreSQL database.

If it has not been processed, it should go get the images from a folder called 'images', by checking the path to it in the field 'path' of the 'sar_raw' table.
After this, the process of detecting the presence of snow will begin: starting by checking the generated points in the ‘samples’ table, and then iterating through each of those those sample points and get a backscatter value for them.

It then writes the processed vector to the 'sar_processed' table and records the act in the ‘sar_raw’ table using the same key. 

It then writes the results in the ’results’ table, that is also in the PostgreSQL database, as a percentage of coverage at 100m intervals 

Help me create a python algorithm that does everything automatically, using whatever you think is best.

"""
import psycopg2
import os
import numpy as np
from skimage import io  # Assuming you're using skimage to read images
from snow_detection_algorithm import detect_snow  # Your snow detection algorithm function

# Connect to your PostgreSQL database
conn = psycopg2.connect(
    dbname="FTM8",
    user="postgres",
    password="admin",
    host="DESKTOP-UIUIA2A",
    port="5432"
)
cur = conn.cursor()

def check_new_images():
    cur.execute("SELECT id, path FROM sar_raw WHERE processed = false")
    rows = cur.fetchall()
    for row in rows:
        image_id, image_path = row
        process_image(image_id, image_path)

def process_image(image_id, image_path):
    # Load image from the specified path
    image = io.imread(image_path)

    # Assuming your snow detection algorithm returns a binary mask
    snow_mask = detect_snow(image)

    # Calculate snow coverage percentage at 100m intervals
    # You need to implement this part based on the resolution of your images

    # Update sar_processed table with the processed vector
    # Insert the snow coverage results into the results table

    # Update 'sar_raw' table to mark the image as processed
    cur.execute("UPDATE sar_raw SET processed = true WHERE id = %s", (image_id,))
    conn.commit()

if __name__ == "__main__":
    check_new_images()

# Close database connection
cur.close()
conn.close()


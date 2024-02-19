"""
I'm aiming to detect the presence of snow in SAR images, with backsatter intensity in the range of -10 dB (decibels) to -15 dB, without having explicit labels indicating whether snow is present or no, trough a python code.

The first step of the code should be to check if a new image has been written by checking the the ‘processed’ field of the 'sar_raw' table from a PostgreSQL database.

If it has not been processed, it should go get the images from a folder called 'images'.
After this, the process of detecting the presence of snow will begin: starting by checking the generated points in the ‘samples’ table, and then iterating through each of those those sample points and get a backscatter value for them.

It then writes the processed vector to the 'sar_processed' table and records the act in the ‘sar_raw’ table using the same key. 

It then writes the results in the ’results’ table, that is also in the PostgreSQL database, as a percentage of coverage at 100m intervals 

Help me create a python algorithm that does everything automatically, using whatever you think is best.
"""
pip install psycopg2

import os
import psycopg2
import numpy as np
from osgeo import gdal

# Function to check if a new image has been written
## This function connects to the PostgreSQL database and retrieves the IDs and filenames of images in the sar_raw table that have not been processed yet (processed = FALSE).
def check_for_new_image():
    conn = psycopg2.connect(database="your_db_name", user="your_username", password="your_password", host="your_host", port="your_port")
    cur = conn.cursor()
    cur.execute("SELECT id, filename FROM sar_raw WHERE processed = FALSE")
    rows = cur.fetchall()
    conn.close()
    return rows

# Function to process the SAR image and detect snow presence
## This function takes the path of a SAR image as input, loads the image using GDAL, applies a simple snow detection logic (checking if the pixel values fall within a certain range indicative of snow), and calculates the percentage of snow coverage in the image.
def detect_snow_presence(image_path):
    # Load SAR image
    sar_ds = gdal.Open(image_path)
    sar_array = sar_ds.GetRasterBand(1).ReadAsArray()

    # Example snow detection logic
    snow_mask = np.logical_and(sar_array >= -15, sar_array <= -10)
    snow_coverage_percentage = np.count_nonzero(snow_mask) / sar_array.size * 100

    return snow_coverage_percentage

# Function to update database tables
## It marks the processed status of the image in the sar_raw table as TRUE.
## It inserts the processed data (image ID and snow coverage percentage) into the sar_processed table.
def update_database(image_id, snow_coverage_percentage):
    conn = psycopg2.connect(database="your_db_name", user="your_username", password="your_password", host="your_host", port="your_port")
    cur = conn.cursor()
    
    # Update sar_raw table
    cur.execute("UPDATE sar_raw SET processed = TRUE WHERE id = %s", (image_id,))
    
    # Insert processed data into sar_processed table
    cur.execute("INSERT INTO sar_processed (image_id, snow_coverage_percentage) VALUES (%s, %s)", (image_id, snow_coverage_percentage))
    
    # Commit changes
    conn.commit()
    conn.close()

# Main function
## It runs an infinite loop to continuously check for new images in the sar_raw table.
## If no new images are found, it breaks out of the loop. For each new image, it:
### Calls detect_snow_presence() to calculate the snow coverage percentage.
### Calls update_database() to update the database with the processed data.
### Prints a message indicating the completion of processing for each image.
### Once all new images are processed, it prints a message indicating the completion of the process.
def main():
    while True:
        new_images = check_for_new_image()
        if not new_images:
            print("No new images found.")
            break

        for image_id, filename in new_images:
            image_path = os.path.join('images', filename)
            snow_coverage_percentage = detect_snow_presence(image_path)
            update_database(image_id, snow_coverage_percentage)
            print(f"Image {filename} processed. Snow coverage: {snow_coverage_percentage}%")
        print("All new images processed.")

## ensures that the main() function is executed when the script is run directly.
if __name__ == "__main__":
    main()

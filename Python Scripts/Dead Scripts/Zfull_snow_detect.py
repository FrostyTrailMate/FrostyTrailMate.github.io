"""
Backscatter Intensity Analysis Method

Backsatter: the reflection of radar signals back to the radar antenna from the Earth's surface or other targets.

• Snow-covered areas tend to exhibit higher backscatter intensity compared to other surfaces due to their relatively smooth and uniform texture.
• Analyzing the backscatter intensity can help identify regions with higher reflectivity, which may indicate the presence of snow.
• Quick and computationally efficient method for an initial assessment.
• Easier to implement in a machine learning model.
    o	Utilizing machine learning algorithms, such as supervised or unsupervised classification, can help automatically identify snow-covered areas based on training datasets.
    o	Algorithms examples: Random Forest, Support Vector Machines, or Convolutional Neural Networks (CNNs) for this purpose.

• A common starting point for snow detection in SAR imagery is to use a threshold value in the range of -10 dB (decibels) to -15 dB for backscatter intensity. 
However, this value can vary widely depending on the aforementioned factors and may require adjustment through empirical 
testing and validation.

Sentinel-1 operates in C-Band and provides images in both Vertical-Vertical (VV) and Vertical-Horizontal (VH) polarizations.

- VV Polarization is commonly used for snow detection in SAR imagery. 
Snow-covered areas typically exhibit increased backscatter intensity in VV polarization compared to bare ground or other land cover types.

- VH Polarization can also be useful for snow detection, particularly in discriminating between snow and other surface types. 
Snow-covered areas may exhibit different backscatter characteristics compared to non-snow-covered areas in VH polarization.

By analyzing the images in both VV and VH polarizations, it can provide complementary information and enhance the accuracy of snow detection, especially when explicit labels indicating snow presence are not available. 
By doing this, we can effectively detect the presence of snow within the specified backscatter intensity range (-10 dB to -15 dB). 

"""

""" 
MY SEARCH

I'm aiming to detect the presence of snow in SAR images, with backsatter intensity in the range of -10 dB (decibels) to -15 dB, without having explicit labels indicating whether snow is present or no, trough a python code.

Assuming the SAR images are obtained from the 'sar_raw' table from a PostgreSQL database.

The first step of the code should be to check if a new image has been written by checking the the ‘processed’ field of the 'sar_raw' table.

If it has not been processed, it should go get the images from the 'sRaster' field of the 'sar_raw' table.
After this, the process of detecting the presence of snow will begin: starting by checking the generated points in the ‘samples’ table, and then iterating through each of those those sample points and get a backscatter value for them.

It then writes the processed vector to the 'sar_processed' table and records the act in the ‘sar_raw’ table using the same key. 

It then writes the results in the ’results’ table as a percentage of coverage at 100m intervals 

Help me create a python algorithm that does everything automatically, using whatever you think is best.

-----------------------------
"""

import psycopg2
import numpy as np

# Connect to PostgreSQL
conn = psycopg2.connect(
    dbname="FTM8",
    user="postgres",
    password="admin",
    host="DESKTOP-UIUIA2A",
    port="5432"
)
cur = conn.cursor()

# Function to detect snow presence based on backscatter intensity
## This function takes the backscatter intensity as input and returns True if it falls within the range [-15 dB, -10 dB], indicating the presence of snow.

def detect_snow(backscatter_intensity):
    return (-15 <= backscatter_intensity <= -10)

# Check for new images in sar_raw table
## This SQL query selects all records from the sar_raw table where the processed field is false, indicating that the image has not been processed yet.

cur.execute("SELECT path FROM sar_raw WHERE processed is null")
new_images = cur.fetchall()

for image in new_images:
# For each image, it retrieves the image ID and SAR image data from the database.
    image_id = image[0]
    sar_image = image[1]  # Assuming the SAR image is stored as a numpy array in sRaster field

    # Process SAR image to detect snow presence
    ## It iterates through sample points within the image, checks the backscatter intensity, and if it indicates snow presence, adds the point to `snow_points`.
    snow_points = []
    for sample_point in image[2]:  # Assuming sample points are stored in the 'samples' field
        backscatter_intensity = sar_image[sample_point[0]][sample_point[1]]  # Assuming sample_point is (x, y) coordinate
        if detect_snow(backscatter_intensity):
            snow_points.append(sample_point)

# Calculate snow coverage percentage at 100m intervals by counting the snow points falling within each interval.
    coverage_percentage = {}
    for point in snow_points:
        interval = (point[0] // 100) * 100  # Assuming points are in meters
        if interval not in coverage_percentage:
            coverage_percentage[interval] = 1
        else:
            coverage_percentage[interval] += 1

    total_points = len(snow_points)
    for interval in coverage_percentage:
        coverage_percentage[interval] = (coverage_percentage[interval] / total_points) * 100

    # Update sar_processed table table with the detected snow points for the image.
    cur.execute("INSERT INTO sar_processed (image_id, snow_points) VALUES (%s, %s)", (image_id, snow_points))
    conn.commit()

    # Update results table with the snow coverage percentages at 100m intervals.
    for interval, percentage in coverage_percentage.items():
        cur.execute("INSERT INTO results (image_id, interval, coverage_percentage) VALUES (%s, %s, %s)",
                    (image_id, interval, percentage))
    conn.commit()

    # Mark image as processed in sar_raw table
    cur.execute("UPDATE sar_raw SET processed = true WHERE id = %s", (image_id,))
    conn.commit()

# Close database connection
cur.close()
conn.close()


### Steps for detecting snow in Synthetic Aperture Radar (SAR) images using machine learning: 

# 1.	Data collection: Obtain a dataset of SAR images labeled with the presence or absence of snow. Ensure that the dataset is diverse and representative of different conditions.

# 2.	Data preprocessing: SAR images often require specific preprocessing due to their nature. Preprocess the images to remove noise, normalize intensities, and handle speckle. Consider using SAR-specific libraries like pyroSAR or snappy for preprocessing.
#  a.	This example assumes that your SAR image is in a zip archive. Adjust the paths, filenames, and parameters according to your specific case.
import pyroSAR
from pyroSAR import identify
from pyroSAR.ancillary import groupby_helper

def preprocess_sar_image(input_path, output_path):
    # Identify the SAR product
    product = identify(input_path)

    # Apply radiometric calibration (if needed - If the SAR image is not already in gamma nought (γ0) format, it is often necessary to perform radiometric calibration.)
    if 'gamma0' not in product.polarizations:
        product = product.resample(30).calibrate(1)

    # Apply speckle filtering (SAR images are often affected by speckle noise, which can be reduced using speckle filtering techniques. In this example, a Lee filter is applied.)
    product = product.filter(1, 'Lee')

    # Extract metadata for geocoding (Geocoding involves projecting the SAR image onto a geographical coordinate system. This step requires additional data, such as a Digital Elevation Model (DEM). The example uses SRTM data for geocoding.)
    metadata = groupby_helper(product, 'outname', 'orbitnumber', 'date', 'platform', 'center_lon', 'center_lat', 'acquisition_mode', 'polarizations', 'looks')

    # Geocode the image (requires SRTM data, adjust the path accordingly)
    product.geocode(target=output_path, trgtsize=0.0001, overwrite=True, removeS1border=True, externalDEMFile='path/to/SRTM1/DEM/SRTM1.vrt', extern_mask=True, rtc=True)

# Example usage
input_sar_image = 'path/to/your/sar/image.zip'
output_preprocessed_image = 'path/to/your/preprocessed/image.tif'

preprocess_sar_image(input_sar_image, output_preprocessed_image)

# 3.	Feature extraction: Extract relevant features from the SAR images. These features might include texture, intensity, and statistical measures. You can use libraries like scikit-image or rasterio for feature extraction.
#  a.	Backsatter intensity feature extraction: These statistical features can be used as input features for machine learning models or combined with other features for more comprehensive analysis. Adjust the calculations or include additional features based on your specific requirements and the characteristics of your SAR images.
import numpy as np
import matplotlib.pyplot as plt
from skimage import io, color

def backscatter_feature_extraction(image_path):
    # Read the SAR image
    sar_image = io.imread(image_path)

    # Convert to grayscale
    sar_gray = color.rgb2gray(sar_image)

    # Calculate statistical features from the backscatter intensity (Compute statistical features from the backscatter intensity, such as mean, standard deviation, maximum, and minimum intensity values.)
    mean_intensity = np.mean(sar_gray)
    std_intensity = np.std(sar_gray)
    max_intensity = np.max(sar_gray)
    min_intensity = np.min(sar_gray)

    # Display the original SAR image
    plt.subplot(121)
    plt.imshow(sar_image, cmap='gray')
    plt.title('Original SAR Image')

    # Display the backscatter intensity distribution
    plt.subplot(122)
    plt.hist(sar_gray.flatten(), bins=256, range=[0, 1], density=True, cumulative=False, color='gray', alpha=0.75)
    plt.title('Backscatter Intensity Distribution')
    plt.xlabel('Pixel Intensity')
    plt.ylabel('Frequency')
    plt.show()

    print(f"Mean Intensity: {mean_intensity}")
    print(f"Standard Deviation Intensity: {std_intensity}")
    print(f"Maximum Intensity: {max_intensity}")
    print(f"Minimum Intensity: {min_intensity}")

# Example usage
image_path = 'path/to/your/preprocessed/image.tif'
backscatter_feature_extraction(image_path)

#  b.	Texture analysis feature extraction: Adjust the parameters (distance, angles, levels) based on your specific requirements and characteristics of the SAR images. Texture analysis can be combined with other feature extraction methods to improve the performance of your machine learning model for snow detection.
import numpy as np
import matplotlib.pyplot as plt
from skimage import io, color, img_as_ubyte
from skimage.feature import greycomatrix
from skimage import exposure

def texture_analysis(image_path, distance=1, angles=[0, np.pi/4, np.pi/2, 3*np.pi/4], levels=256):
    # Read the SAR image 
    sar_image = io.imread(image_path)

    # Convert to grayscale
    sar_gray = color.rgb2gray(sar_image)

    # Convert to unsigned byte for GLCM computation (Compute the Gray-Level Co-occurrence Matrix (GLCM) using the greycomatrix function from skimage.feature. This matrix describes the distribution of pixel pairs with certain intensity values and spatial relationships.)
    sar_gray = img_as_ubyte(sar_gray)

    # Apply texture analysis using GLCM
    glcm = greycomatrix(sar_gray, distances=[distance], angles=angles, levels=levels,
                        symmetric=True, normed=True)

    # Calculate texture features (contrast, dissimilarity, homogeneity, energy) (Extract texture features such as contrast, dissimilarity, homogeneity, and energy from the GLCM.)
    contrast = np.mean((glcm[:, :, 0, 0] * (np.arange(levels) - np.arange(levels).mean())**2))
    dissimilarity = np.mean(glcm[:, :, 0, 1])
    homogeneity = np.mean(glcm[:, :, 0, 2])
    energy = np.mean(glcm[:, :, 0, 3])

    # Display the original image
    plt.subplot(121)
    plt.imshow(sar_image)
    plt.title('Original SAR Image')

    # Display the GLCM
    plt.subplot(122)
    plt.imshow(np.log1p(glcm[:, :, 0, 0]), cmap=plt.cm.gray, interpolation='nearest')
    plt.title('GLCM (Contrast)')
    plt.show()

    print(f"Contrast: {contrast}")
    print(f"Dissimilarity: {dissimilarity}")
    print(f"Homogeneity: {homogeneity}")
    print(f"Energy: {energy}")

# Example usage
image_path = 'path/to/your/preprocessed/image.tif'
texture_analysis(image_path)

# 4.	Labeling: Ensure that your dataset is labeled with the presence or absence of snow. This is crucial for supervised learning.
#  a.	Automatically labeling SAR images for the presence or absence of snow can be done using Thresholding on Intensity: SAR images of snow-covered areas often have distinct intensity characteristics. You can set a threshold on the pixel intensity to differentiate between snow and non-snow regions. This threshold can be determined manually or through histogram analysis. 
# Adjust the threshold value according to the characteristics of your SAR images. You may need to experiment and fine-tune these methods based on the specific features of your dataset. Keep in mind that automatic labeling methods might not be perfect, and it's essential to validate and refine the labels through manual inspection or additional feedback loops to improve accuracy.
import cv2
import numpy as np

def label_snow_by_intensity(image_path, threshold=100):
    # Read the SAR image
    sar_image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

    # Apply thresholding
    snow_mask = (sar_image > threshold).astype(np.uint8)

    return snow_mask

# Example usage
image_path = 'path/to/your/sar/image.png'
snow_mask = label_snow_by_intensity(image_path, threshold=120)

# 'snow_mask' now contains binary labels where 1 represents snow-covered areas

# 5.	Splitting the data set: Split your dataset into training and testing sets. The training set is used to train your machine learning model, and the testing set is used to evaluate its performance on unseen data. This ensures that you can evaluate the model's performance on unseen data.
#  a.	Make sure to replace the placeholder values for X and y with your actual feature and label data. 
# The test_size parameter controls the percentage of the data that will be allocated for testing (here, 20%). Adjust this parameter based on your specific needs.
# After splitting the data, you can proceed with training your machine learning model using the X_train and y_train datasets. The X_test and y_test datasets are reserved for evaluating the model's performance.

from sklearn.model_selection import train_test_split

# Assuming X contains your features and y contains your labels (0 or 1 for no snow and snow, respectively)
# Adjust X and y based on your actual dataset structure

# Example features (replace this with your actual feature data)
X = [[feature1_value, feature2_value, ...], [feature1_value, feature2_value, ...], ...]

# Example labels (replace this with your actual label data)
y = [0, 1, 0, 1, ...]

# Split the dataset into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 'test_size' determines the proportion of the dataset used for testing (here, 20%)
# 'random_state' ensures reproducibility, using the same seed will yield the same split each time

# Print the sizes of the training and testing sets
print(f"Training set size: {len(X_train)} samples")
print(f"Testing set size: {len(X_test)} samples")

# 6.	Selecting a machine learning model: Choose a suitable machine learning algorithm for your task. Common choices for image classification include Support Vector Machines (SVM), Random Forests, or Convolutional Neural Networks (CNNs).
#  a.	One of the simplest and widely used machine learning algorithms is the Support Vector Machine (SVM). 
#  b.	If you have a large dataset or complex relationships, you might also consider exploring more advanced algorithms such as Random Forests.

# 7.	Model training: Train your chosen model using the training dataset. Feed the extracted features into the model along with their corresponding labels.
#  a.	Example for the SVM: Replace the placeholder values for X_train, y_train, X_test, and y_test with your actual training and testing data. In this example, we use a linear kernel for the SVM (kernel='linear'), which is a good starting point for many classification problems. Depending on your dataset, you might need to explore other kernel options and tune hyperparameters for better performance.
from sklearn import svm
from sklearn.metrics import accuracy_score

# Assuming X_train contains your training features and y_train contains your training labels
# Assuming X_test contains your testing features and y_test contains your testing labels

# Example training features (replace this with your actual training feature data)
X_train = [[feature1_value, feature2_value, ...], [feature1_value, feature2_value, ...], ...]

# Example training labels (replace this with your actual training label data)
y_train = [0, 1, 0, 1, ...]

# Example testing features (replace this with your actual testing feature data)
X_test = [[feature1_value, feature2_value, ...], [feature1_value, feature2_value, ...], ...]

# Example testing labels (replace this with your actual testing label data)
y_test = [0, 1, 0, 1, ...]

# Create an SVM classifier
svm_classifier = svm.SVC(kernel='linear')

# Train the classifier
svm_classifier.fit(X_train, y_train)

# Make predictions on the test set
predictions = svm_classifier.predict(X_test)

# Evaluate the model
accuracy = accuracy_score(y_test, predictions)
print(f'Accuracy: {accuracy}')

# 8.	Model evaluation: Evaluate the model's performance on the testing dataset. Common evaluation metrics for binary classification tasks include accuracy, precision, recall, and F1 score.
#  a.	Replace the placeholder values for predictions and y_test with your actual predicted labels and true labels, respectively.
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# Assuming predictions contain the predicted labels and y_test contains the true labels

# Example predictions (replace this with your actual predictions)
predictions = [0, 1, 0, 1, ...]

# Example true labels (replace this with your actual true labels)
y_test = [0, 1, 0, 1, ...]

# Calculate and print accuracy (Accuracy: The ratio of correctly predicted instances to the total instances.)
accuracy = accuracy_score(y_test, predictions)
print(f'Accuracy: {accuracy}')

# Display confusion matrix (A table showing the number of true positives, true negatives, false positives, and false negatives.)
conf_matrix = confusion_matrix(y_test, predictions)
print('Confusion Matrix:')
print(conf_matrix)

# Display classification report (Provides precision, recall, and F1-score for each class. Precision is the ratio of correctly predicted positive observations to the total predicted positives, recall is the ratio of correctly predicted positive observations to the all observations in the actual class, and F1-score is the weighted average of precision and recall.)
class_report = classification_report(y_test, predictions)
print('Classification Report:')
print(class_report)

# 9.	Tuning and optimization: Fine-tune your model parameters to improve its performance. Consider techniques like cross-validation and hyperparameter tuning.
#  a.	Grid search example: is a common technique used to search through a predefined set of hyperparameter values and find the combination that yields the best performance. 
# Adjust the param_grid values based on your specific requirements and the characteristics of your dataset. Grid search helps you find the optimal hyperparameters for your model, improving its overall performance.
#  b.	The param_grid dictionary defines the hyperparameters and their potential values that the grid search will explore.
#  c.	The GridSearchCV object performs a cross-validated grid search, trying out all possible combinations of hyperparameters.
from sklearn import svm, datasets
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.metrics import accuracy_score

# Load a sample dataset for demonstration purposes (replace this with your actual dataset)
iris = datasets.load_iris()
X, y = iris.data, iris.target

# Split the dataset into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Define the SVM classifier
svm_classifier = svm.SVC()

# Define the hyperparameter grid to search
param_grid = {'C': [0.1, 1, 10], 'kernel': ['linear', 'rbf', 'poly'], 'gamma': ['scale', 'auto']}

# Create a grid search object with the SVM classifier and hyperparameter grid
grid_search = GridSearchCV(svm_classifier, param_grid, cv=5, scoring='accuracy')

# Perform grid search on the training data
grid_search.fit(X_train, y_train)

# Print the best hyperparameters found by the grid search (The best hyperparameters found by the grid search are printed, and the best model is used to make predictions on the test set.)
best_params = grid_search.best_params_
print(f'Best Hyperparameters: {best_params}')

# Make predictions on the test set using the best model
best_model = grid_search.best_estimator_
predictions = best_model.predict(X_test)

# Evaluate the model
accuracy = accuracy_score(y_test, predictions)
print(f'Accuracy on Test Set: {accuracy}')

# 10.	Deployment: Once satisfied with the model's performance, deploy it for snow detection in new SAR images. Involves using your trained machine learning model to make predictions on new, unseen data.
#  a.	Example on how to save the trained Support Vector Machine (SVM) model and later use it for making predictions on new data: Replace the training and testing data with your actual dataset and adapt the code according to the specific requirements of your deployment environment.
We train an SVM classifier on a sample dataset (Iris dataset in this case)  We save the trained model to a file using joblib.dump -> Later, we load the saved model using joblib.load -> We make predictions on new data using the loaded model.

from sklearn import svm
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib

# Load a sample dataset for demonstration purposes (replace this with your actual dataset)
iris = load_iris()
X, y = iris.data, iris.target

# Split the dataset into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train an SVM classifier (you can replace this with your own training code)
svm_classifier = svm.SVC(kernel='linear')
svm_classifier.fit(X_train, y_train)

# Save the trained model to a file using joblib
model_filename = 'svm_model.joblib'
joblib.dump(svm_classifier, model_filename)

# Later, when you want to make predictions on new data:

# Load the saved model
loaded_model = joblib.load(model_filename)

# Assuming you have new data in the variable 'new_data'
new_data = [[4.8, 3.0, 1.4, 0.3]]  # Replace this with your actual new data

# Make predictions using the loaded model
predictions = loaded_model.predict(new_data)

# Display the predictions
print(f'Predictions for new data: {predictions}')
 

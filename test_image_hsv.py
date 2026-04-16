import cv2
import numpy as np
import matplotlib.pyplot as plt

path_to_repo = '.'
path_to_images = '/packages/test_image_publisher/sample_images/image'

# Load the images
image_paths = [
    path_to_repo + path_to_images + '0.jpg',
    path_to_repo + path_to_images + '1.jpg',
    path_to_repo + path_to_images + '2.jpg',
    path_to_repo + path_to_images + '3.jpg',
    path_to_repo + path_to_images + '4.jpg'
]

# Load images and convert to HSV
images = [cv2.imread(path) for path in image_paths]
hsv_images = [cv2.cvtColor(image, cv2.COLOR_BGR2HSV) for image in images]

# Create a subplot grid (2 rows, 5 columns)
fig, axes = plt.subplots(2, len(image_paths), figsize=(15, 6))

# Loop through each image and display both original and HSV versions
for i, (image, hsv_image) in enumerate(zip(images, hsv_images)):
    # Convert BGR to RGB for original image display
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Convert HSV to RGB for hsv_image display
    hsv_image_rgb = cv2.cvtColor(hsv_image, cv2.COLOR_HSV2RGB)
    
    # Display original image in first row
    axes[0, i].imshow(image_rgb)
    axes[0, i].axis('off')  # Hide axis
    axes[0, i].set_title(f'Original Image {i}')
    
    # Display HSV image in second row
    axes[1, i].imshow(hsv_image)
    axes[1, i].axis('off')  # Hide axis
    axes[1, i].set_title(f'HSV Image {i} plotted as RGB')

# Adjust layout
plt.tight_layout()
plt.show()
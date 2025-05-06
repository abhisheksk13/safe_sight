import os
import cv2
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

# Set paths
data_dir = 'path_to_scvd_dataset'  # Change this to the directory where your dataset is stored
labels_file = os.path.join(data_dir, 'labels.csv')  # Assuming the labels are in a CSV file
output_size = (224, 224)  # Resize all frames to 224x224 for the model

# Load the labels CSV (Assuming labels.csv contains 'video' and 'label' columns)
labels_df = pd.read_csv(labels_file)

# Function to load and preprocess the frames from the videos
def load_data(data_dir, labels_df, output_size):
    images = []
    labels = []
    
    # Loop through each row in the dataframe
    for _, row in labels_df.iterrows():
        video_path = os.path.join(data_dir, row['video'])  # Video file path
        label = row['label']  # Corresponding label for the video (threat/violence/etc.)
        
        # Initialize video capture
        video_capture = cv2.VideoCapture(video_path)
        frame_count = 0
        
        # Loop through the video to extract frames
        while True:
            ret, frame = video_capture.read()
            if not ret:
                break  # End of video
            
            # Process the frame every nth frame (e.g., every 30th frame)
            if frame_count % 30 == 0:
                # Resize the frame to match the input size for the CNN (224x224)
                resized_frame = cv2.resize(frame, output_size)
                images.append(resized_frame)
                labels.append(label)
            frame_count += 1
        
        # Release video capture
        video_capture.release()
    
    images = np.array(images)
    labels = np.array(labels)
    
    # Normalize images to [0, 1]
    images = images / 255.0
    
    return images, labels

# Load the data
X, y = load_data(data_dir, labels_df, output_size)

# Check data dimensions
print(f"Data shape: {X.shape}, Labels shape: {y.shape}")

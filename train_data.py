import os
import cv2
import numpy as np
from sklearn.model_selection import train_test_split
import tensorflow as tf
from tensorflow.keras import layers, models
import matplotlib.pyplot as plt

# Set dataset path
data_dir = 'C:/Users/kotya/OneDrive/Desktop/safesight_webapp/SCVD'
output_size = (224, 224)

# Label mapping (adjust if your folders are named differently)
label_map = {'violence': 1, 'normal': 0}

# Function to load data
def load_data(data_dir, output_size):
    images = []
    labels = []

    for label_name in os.listdir(data_dir):
        label_folder = os.path.join(data_dir, label_name)
        if not os.path.isdir(label_folder):
            continue

        for video_file in os.listdir(label_folder):
            video_path = os.path.join(label_folder, video_file)
            cap = cv2.VideoCapture(video_path)
            frame_count = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                if frame_count % 30 == 0:  # Take every 30th frame
                    resized = cv2.resize(frame, output_size)
                    images.append(resized)
                    labels.append(label_map[label_name.lower()])
                frame_count += 1
            cap.release()

    images = np.array(images) / 255.0
    labels = np.array(labels)
    return images, labels

# Load dataset
X, y = load_data(data_dir, output_size)

# Split dataset
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Define CNN model
def create_model():
    model = models.Sequential([
        layers.Conv2D(32, (3, 3), activation='relu', input_shape=(224, 224, 3)),
        layers.MaxPooling2D((2, 2)),
        layers.Conv2D(64, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        layers.Conv2D(128, (3, 3), activation='relu'),
        layers.Flatten(),
        layers.Dense(128, activation='relu'),
        layers.Dense(1, activation='sigmoid')
    ])
    return model

# Compile model
model = create_model()
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

# Train model
history = model.fit(X_train, y_train, epochs=10, batch_size=32, validation_data=(X_test, y_test))

# Evaluate model
test_loss, test_acc = model.evaluate(X_test, y_test, verbose=2)
print(f"Test accuracy: {test_acc}")

# Save model
model.save('violence_threat_detection_model.h5')
print("Model saved as 'violence_threat_detection_model.h5'")

# Plot accuracy
plt.plot(history.history['accuracy'], label='Train Accuracy')
plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
plt.xlabel('Epochs')
plt.ylabel('Accuracy')
plt.legend()
plt.show()

# Plot loss
plt.plot(history.history['loss'], label='Train Loss')
plt.plot(history.history['val_loss'], label='Validation Loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()
plt.show()

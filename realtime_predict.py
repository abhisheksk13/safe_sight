import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TensorFlow logs

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import firebase_admin
from firebase_admin import credentials, firestore
import tensorflow as tf
import cv2
import numpy as np

# Initialize Firebase Admin SDK
cred = credentials.Certificate("firebase-key.json")
firebase_admin.initialize_app(cred)

# Initialize Firestore
db = firestore.client()

# Load the trained model
model = tf.keras.models.load_model('violence_threat_detection_model.h5')

# Function to send prediction to Firebase
def send_to_firebase(label):
    alert_data = {
        'description': f'{label} detected',
        'status': 'New Alert',
        'timestamp': firestore.SERVER_TIMESTAMP,
    }

    # Add to Firestore collection
    db.collection("emergencies").add(alert_data)
    print(f"✅ Alert sent to Firebase: {alert_data['description']}")

# Function to process video or webcam input
def process_video(video_path):
    video_capture = cv2.VideoCapture(video_path)

    # Error check
    if not video_capture.isOpened():
        print(f"❌ Error: Unable to open video source: {video_path}")
        return

    frame_count = 0
    print("🎥 Processing started. Press Ctrl+C to stop.")

    while True:
        ret, frame = video_capture.read()
        if not ret:
            print("✅ Video ended or cannot read frame.")
            break

        if frame_count % 30 == 0:  # Every ~1 second for 30fps
            frame_resized = cv2.resize(frame, (224, 224))
            frame_input = np.expand_dims(frame_resized, axis=0) / 255.0

            prediction = model.predict(frame_input)
            score = prediction[0][0]
            label = "Violence" if score > 0.5 else "Normal"

            print(f"Frame {frame_count}: {label} ({score:.4f})")
            if label == "Violence":
        

                send_to_firebase(label)
                break

        frame_count += 1

    video_capture.release()
    cv2.destroyAllWindows()

# Choose video source
if __name__ == "__main__":
    # Use 0 for webcam, or provide video file path
    # Example: video_path = r"C:\path\to\video.mp4"
    video_path = 0  # Change this to a file path if needed
    process_video(video_path)

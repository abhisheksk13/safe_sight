import os
import cv2
import time
import threading
import numpy as np
from flask import Flask, render_template, Response, stream_with_context
from queue import Queue

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import tensorflow as tf
import firebase_admin
from firebase_admin import credentials, firestore

# Firebase setup
cred = credentials.Certificate("firebase-key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Load violence detection model
model = tf.keras.models.load_model("violence_detector.h5")

# Flask app
app = Flask(__name__)
status_queue = Queue()
latest_status = "Detecting..."

# Firebase alert
def send_to_firebase(label):
    alert_data = {
        'description': f'{label} detected',
        'status': 'New Alert',
        'timestamp': firestore.SERVER_TIMESTAMP,
    }
    db.collection("emergencies").add(alert_data)
    print(f"✅ Alert sent: {alert_data['description']}")

# Process 10 frames for prediction
def predict_violence(frames):
    if len(frames) < 10:
        return "Normal", 0.0
    clip = np.array(frames[:10])
    clip = clip / 255.0
    clip = np.expand_dims(clip, axis=0)
    pred = model.predict(clip)[0][0]
    label = "Violent" if pred > 0.5 else "Normal"
    return label, pred

# Webcam feed generator
def gen_frames():
    global latest_status
    cap = cv2.VideoCapture(0)
    frame_buffer = []
    frame_count = 0
    last_alert_time = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_buffer.append(cv2.resize(frame, (64, 64)))
        if len(frame_buffer) > 10:
            frame_buffer.pop(0)

        if frame_count % 30 == 0:
            label, score = predict_violence(frame_buffer)
            print(f"Frame {frame_count}: {label} ({score:.4f})")

            if label == "Violent":
                latest_status = "🚨 Violence detected"
                if time.time() - last_alert_time > 5:
                    send_to_firebase(label)
                    last_alert_time = time.time()
            else:
                latest_status = "✅ Normal"

            if status_queue.qsize() < 5:
                status_queue.put(latest_status)

        # Encode frame for streaming
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

        frame_count += 1

    cap.release()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/detection_status')
def detection_status():
    def event_stream():
        while True:
            if not status_queue.empty():
                status = status_queue.get()
                yield f"data: {status}\n\n"
            time.sleep(1)
    return Response(stream_with_context(event_stream()),
                    mimetype="text/event-stream")

if __name__ == '__main__':
    app.run(debug=True)

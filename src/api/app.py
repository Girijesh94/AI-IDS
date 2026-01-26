#!/usr/bin/env python3
"""
Flask API for the Hybrid AI-IDS
"""

from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
import joblib
import pandas as pd
from pathlib import Path

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

# --- Load Model ---
MODEL_PATH = Path('../../models/random_forest_optimized_model.joblib')
model = None

def load_model():
    """Load the trained model."""
    global model
    if MODEL_PATH.exists():
        print(f"Loading model from {MODEL_PATH}...")
        model = joblib.load(MODEL_PATH)
        print("Model loaded successfully.")
    else:
        print(f"Error: Model not found at {MODEL_PATH}")

@app.route('/predict', methods=['POST'])
def predict():
    """Receive log data, make a prediction, and emit an alert if necessary."""
    if model is None:
        return jsonify({'error': 'Model is not loaded'}), 500

    try:
        data = request.get_json()
        df = pd.DataFrame([data])
        
        prediction = model.predict(df)
        prediction_proba = model.predict_proba(df)

        result = {
            'prediction': int(prediction[0]),
            'confidence': max(prediction_proba[0])
        }

        # If an attack is detected, emit an alert to the dashboard
        if result['prediction'] != 0: # Assuming 0 is 'benign'
            alert_data = {**result, **data}
            socketio.emit('new_alert', alert_data)

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('stream_packet')
def handle_packet_stream(packet_data):
    """Receives packet data from the sniffer and broadcasts it to clients."""
    emit('new_packet', packet_data, broadcast=True)

if __name__ == '__main__':
    load_model()
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)

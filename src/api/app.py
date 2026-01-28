#!/usr/bin/env python3
"""
Flask API for the Hybrid AI-IDS
"""

from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
import joblib
import pandas as pd
from pathlib import Path
from collections import deque, defaultdict
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

API_VERSION = "dns-heuristics-v1"

# --- Load Model ---
MODEL_PATH = Path('models/random_forest_model.joblib')
model = None

# --- In-memory storage for alerts ---
# In a real application, you would use a database
alert_store = deque(maxlen=100) # Store the last 100 alerts
packet_count = 0
alert_count = 0

# Track destination ports per source over a short window for simple port-scan detection
recent_ports_by_src = defaultdict(lambda: deque(maxlen=2000))

def load_model():
    """Load the trained model."""
    global model
    if MODEL_PATH.exists():
        print(f"Loading model from {MODEL_PATH}...")
        model = joblib.load(MODEL_PATH)
        print("Model loaded successfully.")
    else:
        print(f"Error: Model not found at {MODEL_PATH}")

import datetime

# ... (keep existing imports)

@app.route('/predict', methods=['POST'])
def predict():
    """Receive log data, make a prediction, and emit an alert if necessary."""
    global alert_count
    if model is None:
        return jsonify({'error': 'Model is not loaded'}), 500

    try:
        data = request.get_json()
        
        # Create a DataFrame with all required columns, filling missing ones with 0
        # This is a temporary fix for the demo
        if hasattr(model, 'feature_names_in_'):
            full_data = {feature: 0 for feature in model.feature_names_in_}
        else:
            # Fallback if model has no feature_names_in_
            full_data = {f'feature_{i}': 0 for i in range(78)}
        
        full_data.update(data) # Overwrite with the features we received

        df = pd.DataFrame([full_data])
        
        # Ensure the DataFrame columns match the model's training data
        if hasattr(model, 'feature_names_in_'):
            df = df[model.feature_names_in_]

        prediction = model.predict(df)
        prediction_proba = model.predict_proba(df)

        result = {
            'prediction': int(prediction[0]),
            'confidence': max(prediction_proba[0])
        }

        # Debug output
        print(f"Prediction: {result['prediction']}, Confidence: {result['confidence']:.3f}")

        src_ip = data.get('src')
        dst_ip = data.get('dst')
        dst_port = data.get('destination_port', data.get('dst_port'))
        packet_id = data.get('packet_id')

        # Simple heuristic: many distinct destination ports in short time => suspicious
        suspicious_by_rule = False
        unique_ports = 0
        if src_ip is not None and dst_port is not None:
            now = time.time()
            q = recent_ports_by_src[src_ip]
            q.append((now, int(dst_port)))
            window_s = 10
            while q and (now - q[0][0]) > window_s:
                q.popleft()
            unique_ports = len({p for _, p in q})
            if unique_ports >= 30:  # Increased threshold from 10 to 30
                suspicious_by_rule = True

        # Determine severity from model output + heuristics
        confidence = float(result['confidence'])
        pred = int(result['prediction'])
        features = data
        # DNS Tunneling Detection
        is_dns_tunneling = bool(features.get('is_dns_tunneling', False))
        dns_tunneling_confidence = float(features.get('dns_tunneling_confidence', 0) or 0)
        dns_tunneling_score = float(features.get('dns_tunneling_score', 0) or 0)
        pred_out = pred
        
        # Determine status
        if pred != 0:
            status = "malicious"
            severity = "high"
        elif is_dns_tunneling and dns_tunneling_confidence >= 0.7:
            status = "malicious"
            severity = "high"
            pred_out = 6  # Custom DNS tunneling class
        elif suspicious_by_rule:
            status = "suspicious"
            severity = "medium"
        elif is_dns_tunneling and dns_tunneling_confidence >= 0.3:
            status = "suspicious"
            severity = "medium"
        else:
            status = "normal"
            severity = "low"

        # Emit classification event (always)
        socketio.emit('classification', {
            'packet_id': packet_id,
            'src': src_ip,
            'dst': dst_ip,
            'destination_port': dst_port,
            'prediction': pred_out,
            'confidence': confidence,
            'status': status,
            'rule_portscan': suspicious_by_rule,
            'unique_ports_10s': unique_ports,
            'dns_tunneling': is_dns_tunneling,
            'dns_tunneling_score': dns_tunneling_score,
            'dns_tunneling_confidence': dns_tunneling_confidence,
            'api_version': API_VERSION,
        })

        print(
            f"[DECISION] status={status} pred_out={pred_out} conf={confidence:.3f} "
            f"port={dst_port} portscan={suspicious_by_rule} unique_ports_10s={unique_ports} "
            f"dns_tunneling={is_dns_tunneling} dns_conf={dns_tunneling_confidence:.3f} dns_score={dns_tunneling_score}"
        )

        # Emit system log for prediction
        socketio.emit('system_log', {
            'timestamp': datetime.datetime.now().isoformat(),
            'level': 'INFO',
            'message': f"Prediction processed for port {dst_port if dst_port is not None else 'unknown'} - Result: {pred_out} ({status})"
        })

        # If suspicious or malicious is detected, emit an alert to the dashboard
        if status in ('suspicious', 'malicious'):
            alert_count += 1
            alert_data = {
                **result,
                **data,
                'id': alert_count,
                'status': status,
                'destination_port': dst_port,
                'prediction': pred_out,
                'rule_portscan': suspicious_by_rule,
                'unique_ports_10s': unique_ports,
                'dns_tunneling': is_dns_tunneling,
                'dns_tunneling_score': dns_tunneling_score,
                'dns_tunneling_confidence': dns_tunneling_confidence,
            }
            alert_store.append(alert_data)
            socketio.emit('new_alert', alert_data)
            
            # Emit system log for alert
            socketio.emit('system_log', {
                'timestamp': datetime.datetime.now().isoformat(),
                'level': 'WARNING',
                'message': f"Threat detected ({status}) from {src_ip if src_ip is not None else 'unknown'} to port {dst_port if dst_port is not None else 'unknown'}"
            })

        return jsonify({
            **result,
            'prediction': pred_out,
            'status': status,
            'rule_portscan': suspicious_by_rule,
            'unique_ports_10s': unique_ports,
            'dns_tunneling': is_dns_tunneling,
            'dns_tunneling_score': dns_tunneling_score,
            'dns_tunneling_confidence': dns_tunneling_confidence,
            'api_version': API_VERSION,
        })

    except Exception as e:
        # For debugging, print the actual error
        print(f"Prediction error: {e}")
        return jsonify({'error': str(e)}), 400

# ... (keep the rest of the file the same)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Provide general statistics for the dashboard."""
    return jsonify({
        'total_packets': packet_count,
        'total_alerts': alert_count,
    })

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Provide a list of recent alerts."""
    limit = request.args.get('limit', 20, type=int)
    return jsonify(list(alert_store)[-limit:])

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('stream_packet')
def handle_packet_stream(packet_data):
    """Receives packet data from the sniffer and broadcasts it to clients."""
    global packet_count
    packet_count += 1
    emit('new_packet', packet_data, broadcast=True)

if __name__ == '__main__':
    load_model()
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)

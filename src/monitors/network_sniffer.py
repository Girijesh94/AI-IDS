#!/usr/bin/env python3
"""
Real-time Network Sniffer for Hybrid AI-IDS
"""

import pyshark
import pyshark
import requests
import socketio
import time
import asyncio
import sys

API_URL = 'http://127.0.0.1:5000/predict'
SIO_URL = 'http://127.0.0.1:5000'

# --- Socket.IO Client ---
sio = socketio.Client()

@sio.event
def connect():
    print('Connected to server')

@sio.event
def disconnect():
    print('Disconnected from server')

def packet_to_features(packet):
    """Converts a pyshark packet to a feature dictionary and a summary."""
    try:
        # Simplified feature extraction for prediction
        features = {
            'dst_port': int(packet.tcp.dstport),
            'protocol': 6, # TCP
            # Add other features required by the model
        }

        # Summarized data for dashboard display
        summary = {
            'timestamp': packet.sniff_time.isoformat(),
            'src': packet.ip.src,
            'dst': packet.ip.dst,
            'protocol': packet.transport_layer,
            'length': int(packet.length),
        }
        return features, summary
    except AttributeError:
        return None, None

def main():
    """Capture packets, send for prediction, and stream to dashboard."""
    print("Starting real-time network sniffer...")

    # Set the asyncio event loop policy for Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        sio.connect(SIO_URL)
    except socketio.exceptions.ConnectionError as e:
        print(f"Could not connect to WebSocket server: {e}")
        return

    capture = pyshark.LiveCapture(interface='Ethernet')

    for packet in capture.sniff_continuously():
        features, summary = packet_to_features(packet)
        
        if summary:
            sio.emit('stream_packet', summary)

        if features:
            try:
                # Send to REST endpoint for prediction
                requests.post(API_URL, json=features)
            except requests.exceptions.RequestException as e:
                print(f"Could not connect to API: {e}")
                # Optional: attempt to reconnect or handle error
    
    sio.disconnect()

if __name__ == '__main__':
    main()

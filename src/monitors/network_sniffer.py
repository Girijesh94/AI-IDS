#!/usr/bin/env python3
"""
Network Sniffer for Hybrid AI-IDS
Captures network packets and extracts features for real intrusion detection
"""

import socketio
import requests
import time
import uuid
from scapy.all import sniff, IP, TCP, UDP
from feature_extractor import FlowFeatureExtractor

# Configuration
API_URL = "http://127.0.0.1:5000/predict"
SIO_URL = "http://127.0.0.1:5000"
INTERFACE = None  # Let scapy auto-detect the best interface

# Initialize components
sio = socketio.Client()
feature_extractor = FlowFeatureExtractor()

def process_packet(packet):
    """Process a packet and send for analysis"""
    try:
        print(f"[DEBUG] Packet captured: {len(packet)} bytes")
        
        # Extract features
        features = feature_extractor.extract_features(packet)
        
        if features:
            print(f"[DEBUG] Features extracted successfully")

            packet_id = uuid.uuid4().hex
            src_ip = packet[IP].src if IP in packet else None
            dst_ip = packet[IP].dst if IP in packet else None

            # Best-effort destination port extraction (matches model feature name)
            destination_port = None
            if TCP in packet:
                destination_port = int(packet[TCP].dport)
            elif UDP in packet:
                destination_port = int(packet[UDP].dport)

            # Attach correlation fields to features for the API
            features['packet_id'] = packet_id
            if src_ip is not None:
                features['src'] = src_ip
            if dst_ip is not None:
                features['dst'] = dst_ip
            if destination_port is not None:
                features['destination_port'] = destination_port
            
            # Create summary for dashboard
            summary = {
                'packet_id': packet_id,
                'timestamp': time.time(),
                'src': src_ip if src_ip is not None else 'Unknown',
                'dst': dst_ip if dst_ip is not None else 'Unknown',
                'protocol': 'TCP' if TCP in packet else 'UDP' if UDP in packet else 'Other',
                'length': len(packet),
                'destination_port': destination_port,
            }
            
            print(f"[DEBUG] Sending to dashboard: {summary['src']} -> {summary['dst']}")
            
            # Send to dashboard
            sio.emit('stream_packet', summary)
            
            # Send to API for prediction
            try:
                response = requests.post(API_URL, json=features, timeout=1)
                if response.status_code == 200:
                    result = response.json()
                    print(f"[DEBUG] API response: {result}")
                    if result.get('prediction') != 0:  # If not benign
                        print(f"⚠️  Threat detected: {result}")
                else:
                    print(f"[DEBUG] API error: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"[DEBUG] API connection error: {e}")
        else:
            print(f"[DEBUG] No features extracted")
        
        # Cleanup old flows periodically
        feature_extractor.cleanup_old_flows()
        
    except Exception as e:
        print(f"Error processing packet: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Start packet capture"""
    print(f"Starting Hybrid AI-IDS Network Sniffer on interface: {INTERFACE}")
    print("Press Ctrl+C to stop...")
    
    try:
        # Connect to WebSocket server
        sio.connect(SIO_URL)
        print("✓ Connected to WebSocket server")
        
        # Start packet capture
        sniff(iface=INTERFACE, prn=process_packet, store=0)
        
    except socketio.exceptions.ConnectionError as e:
        print(f"✗ Could not connect to WebSocket server: {e}")
        print("Make sure the API server is running on http://127.0.0.1:5000")
    except KeyboardInterrupt:
        print("\nStopping sniffer...")
    except PermissionError:
        print("✗ Permission denied. Try running with administrator privileges.")
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        sio.disconnect()

if __name__ == "__main__":
    main()
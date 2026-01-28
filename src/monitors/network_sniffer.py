#!/usr/bin/env python3
"""
Network Sniffer for Hybrid AI-IDS
Captures network packets and extracts features for real intrusion detection
"""

import socketio
import requests
import time
import uuid
from scapy.all import sniff, IP, TCP, UDP, DNS, DNSQR, conf
from feature_extractor import FlowFeatureExtractor

# Configuration
API_URL = "http://127.0.0.1:5000/predict"
SIO_URL = "http://127.0.0.1:5000"
INTERFACE = "\\Device\\NPF_Loopback"  # Explicitly use loopback for localhost traffic
INTERFACES = [INTERFACE]
try:
    if conf.iface and conf.iface not in INTERFACES:
        INTERFACES.append(conf.iface)
except Exception:
    pass

# Initialize components
sio = socketio.Client()
feature_extractor = FlowFeatureExtractor()

def process_packet(packet):
    """Process a packet and send for analysis"""
    try:
        print(f"[DEBUG] Packet captured: {len(packet)} bytes")

        if UDP in packet:
            try:
                print(f"[DEBUG] UDP ports sport={int(packet[UDP].sport)} dport={int(packet[UDP].dport)}")
            except Exception:
                pass

        if UDP in packet and int(packet[UDP].dport) == 53:
            if DNS in packet and DNSQR in packet:
                qname = packet[DNSQR].qname.decode('utf-8', errors='ignore')
                print(f"[DEBUG] DNS query captured qname={qname[:120]}")
            else:
                try:
                    parsed = DNS(bytes(packet[UDP].payload))
                    if parsed is not None and getattr(parsed, 'qd', None) is not None and getattr(parsed.qd, 'qname', None) is not None:
                        qname = parsed.qd.qname.decode('utf-8', errors='ignore')
                        print(f"[DEBUG] UDP/53 decoded via fallback qname={qname[:120]}")
                    else:
                        print("[DEBUG] UDP/53 captured but DNS layer not decoded")
                except Exception:
                    print("[DEBUG] UDP/53 captured but DNS layer not decoded")
        
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

            if 'dns_query_length' in features or destination_port == 53:
                print(
                    "[DEBUG] DNS features summary: "
                    f"destination_port={features.get('destination_port')} "
                    f"dns_query_length={features.get('dns_query_length')} "
                    f"domain_entropy={features.get('domain_entropy')} "
                    f"is_dns_tunneling={features.get('is_dns_tunneling')} "
                    f"dns_conf={features.get('dns_tunneling_confidence')}"
                )
            
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
                if features.get('is_dns_tunneling'):
                    print(
                        "[DEBUG] DNS tunneling features before API: "
                        f"is_dns_tunneling={features.get('is_dns_tunneling')} "
                        f"dns_score={features.get('dns_tunneling_score')} "
                        f"dns_conf={features.get('dns_tunneling_confidence')}"
                    )
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
    print(f"Starting Hybrid AI-IDS Network Sniffer on interface(s): {INTERFACES}")
    print("Press Ctrl+C to stop...")
    
    try:
        # Connect to WebSocket server
        sio.connect(SIO_URL)
        print("✓ Connected to WebSocket server")
        
        # Start packet capture
        sniff(iface=INTERFACES, prn=process_packet, store=0)
        
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
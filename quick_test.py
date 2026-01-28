#!/usr/bin/env python3
"""
Quick test to generate suspicious traffic for IDS
"""

import socket
import time

print("Generating suspicious traffic...")

# Generate multiple connection attempts (port scan behavior)
for port in range(20, 30):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.1)
        sock.connect_ex(("127.0.0.1", port))
        sock.close()
        print(f"Attempted connection to port {port}")
    except:
        pass
    time.sleep(0.1)

# Generate rapid connections (potential DoS)
print("\nGenerating rapid connections...")
for i in range(50):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.01)
        sock.connect_ex(("127.0.0.1", 80))
        sock.close()
    except:
        pass

print("\nDone! Check your IDS dashboard for alerts.")

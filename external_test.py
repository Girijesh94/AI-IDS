#!/usr/bin/env python3
"""
Generate traffic to external services - this will be captured
"""

import socket
import time

def generate_external_traffic():
    """Generate traffic to external services"""
    print("[*] Generating traffic to external services...")
    
    # Test 1: Google DNS (port 53)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(1)
        sock.sendto(b"test", ("8.8.8.8", 53))
        sock.close()
        print("[+] Sent UDP packet to Google DNS")
    except:
        pass
    
    # Test 2: HTTP connection to google.com
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(("google.com", 80))
        if result == 0:
            sock.send(b"GET / HTTP/1.1\r\nHost: google.com\r\n\r\n")
            print("[+] Connected to google.com:80")
        sock.close()
    except:
        pass
    
    # Test 3: Multiple connections to different ports
    external_targets = [
        ("google.com", 80),
        ("github.com", 443),
        ("stackoverflow.com", 80),
        ("microsoft.com", 443),
    ]
    
    for host, port in external_targets:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            if result == 0:
                print(f"[+] Connected to {host}:{port}")
            sock.close()
        except:
            pass
        time.sleep(0.2)

if __name__ == "__main__":
    print("=== External Traffic Test ===")
    print("Generating traffic to external services...")
    print("This traffic WILL be captured by the sniffer!")
    
    generate_external_traffic()
    
    print("\n[*] Test complete!")
    print("[*] Check the sniffer - it should show packets being captured")

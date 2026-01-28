#!/usr/bin/env python3
"""
Simple Attack Simulation - generates suspicious traffic patterns
"""

import socket
import time
import threading
import random

def generate_suspicious_traffic():
    """Generate various suspicious traffic patterns"""
    target = "127.0.0.1"
    
    print("[*] Generating suspicious traffic patterns...")
    print("[*] Watch IDS dashboard for alerts!")
    
    # Pattern 1: Port Scan Simulation
    print("\n[+] Port Scan Simulation")
    common_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995, 1433, 3306, 3389, 5432, 6379]
    
    for port in common_ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.1)
            result = sock.connect_ex((target, port))
            if result == 0:
                print(f"[!] Port {port} OPEN")
            sock.close()
        except:
            pass
        time.sleep(0.05)
    
    # Pattern 2: Rapid Connection Attempts
    print("\n[+] Rapid Connection Attempts (DoS-like)")
    for i in range(100):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.01)
            sock.connect_ex((target, 80))
            sock.close()
        except:
            pass
        time.sleep(0.01)
    
    # Pattern 3: Unusual Port Connections
    print("\n[+] Unusual Port Connections")
    unusual_ports = [1234, 31337, 4444, 6667, 8080, 9000, 12345, 54321]
    
    for port in unusual_ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.2)
            sock.connect_ex((target, port))
            sock.close()
            print(f"[!] Connected to unusual port {port}")
        except:
            pass
        time.sleep(0.1)
    
    # Pattern 4: UDP Flood Simulation
    print("\n[+] UDP Traffic Simulation")
    for i in range(50):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(b"test_data", (target, 53))
            sock.close()
        except:
            pass
        time.sleep(0.02)
    
    print("\n[*] Attack simulation complete!")
    print("[*] Check IDS dashboard for detected threats")

def continuous_traffic():
    """Generate continuous suspicious traffic"""
    target = "127.0.0.1"
    
    while True:
        # Random suspicious activity
        activity = random.choice([
            lambda: socket.create_connection((target, 80), timeout=0.1),
            lambda: socket.create_connection((target, 443), timeout=0.1),
            lambda: socket.create_connection((target, 22), timeout=0.1),
        ])
        
        try:
            activity()
            print(f"[*] Suspicious connection at {time.strftime('%H:%M:%S')}")
        except:
            pass
        
        time.sleep(random.uniform(0.1, 0.5))

def main():
    print("=== Simple Attack Simulation ===")
    print("Generates suspicious traffic patterns for IDS testing")
    
    while True:
        print("\nOptions:")
        print("1. One-time attack simulation")
        print("2. Continuous suspicious traffic")
        print("3. Exit")
        
        choice = input("\nEnter choice (1-3): ")
        
        if choice == "1":
            generate_suspicious_traffic()
        elif choice == "2":
            print("\n[*] Starting continuous traffic generation...")
            print("[*] Press Ctrl+C to stop")
            try:
                continuous_traffic()
            except KeyboardInterrupt:
                print("\n[*] Stopped")
        elif choice == "3":
            break
        else:
            print("Invalid choice")

if __name__ == "__main__":
    main()

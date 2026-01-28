#!/usr/bin/env python3
"""
Port Scan Test - generates traffic that should be captured
"""

import socket
import time
import threading

def generate_port_scan():
    """Generate port scan behavior that will trigger suspicious detection"""
    target = "127.0.0.1"
    ports_to_scan = list(range(8000, 8050))  # 50 ports
    
    print(f"[*] Starting port scan simulation to {target}")
    print(f"[*] Scanning {len(ports_to_scan)} ports...")
    
    for i, port in enumerate(ports_to_scan):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.1)
            result = sock.connect_ex((target, port))
            sock.close()
            print(f"[*] Scanned port {port} - {'Open' if result == 0 else 'Closed'}")
        except:
            pass
        
        # Small delay to simulate real scan
        time.sleep(0.05)
        
        # Every 10 ports, show progress
        if (i + 1) % 10 == 0:
            print(f"[*] Progress: {i + 1}/{len(ports_to_scan)} ports scanned")
    
    print("[*] Port scan simulation complete!")
    print("[*] This should trigger the port-scan detection rule")

def generate_rapid_connections():
    """Generate rapid connections to same port (different pattern)"""
    target = "127.0.0.1"
    port = 9999
    
    # Start a simple server
    def simple_server():
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(("127.0.0.1", port))
            server.listen(100)
            print(f"[*] Test server listening on port {port}")
            
            while True:
                try:
                    conn, addr = server.accept()
                    print(f"[+] Connection from {addr}")
                    conn.close()
                except:
                    break
        except:
            pass
    
    server_thread = threading.Thread(target=simple_server)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(1)
    
    print(f"[*] Generating 100 rapid connections to port {port}...")
    for i in range(100):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.1)
            sock.connect_ex((target, port))
            sock.close()
        except:
            pass
        time.sleep(0.01)
    
    print("[*] Rapid connections complete!")

if __name__ == "__main__":
    print("=== Port Scan Detection Test ===")
    print("This test generates traffic patterns that should be detected as suspicious")
    print()
    
    while True:
        print("Select test:")
        print("1. Port Scan (50 ports) - SHOULD trigger suspicious detection")
        print("2. Rapid Connections (100 to same port)")
        print("3. Both tests")
        print("4. Exit")
        
        choice = input("\nEnter choice (1-4): ")
        
        if choice == "1":
            generate_port_scan()
        elif choice == "2":
            generate_rapid_connections()
        elif choice == "3":
            generate_port_scan()
            time.sleep(2)
            generate_rapid_connections()
        elif choice == "4":
            break
        else:
            print("Invalid choice")
        
        print("\n[*] Check your IDS dashboard for suspicious activity!")
        time.sleep(2)

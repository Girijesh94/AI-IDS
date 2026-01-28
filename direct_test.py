#!/usr/bin/env python3
"""
Direct test to generate traffic that will be captured
"""

import socket
import time
import threading

def generate_http_traffic():
    """Generate HTTP traffic to localhost"""
    try:
        # Connect to a common local service (if running)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        
        # Try connecting to common local ports
        ports = [80, 443, 3000, 5000, 8080]
        
        for port in ports:
            try:
                result = sock.connect_ex(("127.0.0.1", port))
                if result == 0:
                    print(f"[*] Connected to port {port}")
                    # Send some data
                    sock.send(b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n")
                    time.sleep(0.1)
                sock.close()
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
            except:
                pass
                
    except Exception as e:
        print(f"Error: {e}")

def generate_tcp_connections():
    """Generate TCP connections that will be captured"""
    target = "127.0.0.1"
    
    # Create a simple server to ensure traffic
    def simple_server():
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(("127.0.0.1", 9999))
            server.listen(5)
            print("[*] Test server listening on port 9999")
            
            while True:
                try:
                    conn, addr = server.accept()
                    print(f"[+] Connection from {addr}")
                    conn.close()
                except:
                    break
        except:
            pass
    
    # Start server in background
    server_thread = threading.Thread(target=simple_server)
    server_thread.daemon = True
    server_thread.start()
    
    time.sleep(1)  # Let server start
    
    # Generate connections to our test server
    print("[*] Generating connections to test server...")
    for i in range(20):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            sock.connect_ex(("127.0.0.1", 9999))
            sock.close()
            print(f"[*] Connection {i+1}/20")
            time.sleep(0.1)
        except:
            pass

if __name__ == "__main__":
    print("=== Direct Traffic Test ===")
    print("Generating traffic that should be captured by the sniffer...")
    
    # Generate different types of traffic
    generate_http_traffic()
    generate_tcp_connections()
    
    print("\n[*] Test complete!")
    print("[*] Check the sniffer and dashboard for activity")

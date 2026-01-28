#!/usr/bin/env python3
"""
Test DNS Tunneling Detection Directly
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'monitors'))

from dns_analyzer import DNSAnalyzer
from scapy.all import DNS, DNSQR, IP, UDP

def test_dns_tunneling_detection():
    print("=== DNS Tunneling Detection Test ===")
    
    analyzer = DNSAnalyzer()
    
    # Test 1: Normal DNS query
    print("\n1. Testing normal DNS query...")
    normal_packet = IP(dst="8.8.8.8")/UDP(dport=53)/DNS(rd=1, qd=DNSQR(qname="google.com"))
    normal_features = analyzer.extract_dns_features(normal_packet)
    normal_result = analyzer.is_dns_tunneling(normal_features)
    
    print(f"   Domain: google.com")
    print(f"   Features: {len(normal_features)} DNS features extracted")
    print(f"   Tunneling result: {normal_result}")
    print(f"   Expected: Normal (is_tunneling=False)")
    
    # Test 2: High entropy DNS query (simulated tunneling)
    print("\n2. Testing high entropy DNS query...")
    high_entropy_domain = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6.evil.com"
    tunneling_packet = IP(dst="8.8.8.8")/UDP(dport=53)/DNS(rd=1, qd=DNSQR(qname=high_entropy_domain))
    tunneling_features = analyzer.extract_dns_features(tunneling_packet)
    tunneling_result = analyzer.is_dns_tunneling(tunneling_features)
    
    print(f"   Domain: {high_entropy_domain[:50]}...")
    print(f"   Features: {len(tunneling_features)} DNS features extracted")
    print(f"   Tunneling result: {tunneling_result}")
    print(f"   Expected: Tunneling (is_tunneling=True)")
    
    # Test 3: Base64 encoded query
    print("\n3. Testing Base64 encoded DNS query...")
    base64_data = "SGVsbG9Xb3JsZEFkbWluUGFzc3dvcmQxMjM="
    base64_domain = f"{base64_data}.tunnel.evil.com"
    base64_packet = IP(dst="8.8.8.8")/UDP(dport=53)/DNS(rd=1, qd=DNSQR(qname=base64_domain))
    base64_features = analyzer.extract_dns_features(base64_packet)
    base64_result = analyzer.is_dns_tunneling(base64_features)
    
    print(f"   Domain: {base64_domain[:50]}...")
    print(f"   Features: {len(base64_features)} DNS features extracted")
    print(f"   Tunneling result: {base64_result}")
    print(f"   Expected: Tunneling (is_tunneling=True)")
    
    # Summary
    print("\n=== Test Summary ===")
    print(f"Normal query detected as tunneling: {normal_result['is_tunneling']}")
    print(f"High entropy query detected as tunneling: {tunneling_result['is_tunneling']}")
    print(f"Base64 query detected as tunneling: {base64_result['is_tunneling']}")
    
    if not normal_result['is_tunneling'] and tunneling_result['is_tunneling'] and base64_result['is_tunneling']:
        print("✅ DNS Tunneling Detection is working correctly!")
        return True
    else:
        print("❌ DNS Tunneling Detection has issues!")
        return False

if __name__ == "__main__":
    test_dns_tunneling_detection()

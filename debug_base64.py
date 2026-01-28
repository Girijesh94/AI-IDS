#!/usr/bin/env python3
"""
Debug Base64 Detection
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'monitors'))

from dns_analyzer import DNSAnalyzer

def debug_base64_detection():
    print("=== Debug Base64 Detection ===")
    
    analyzer = DNSAnalyzer()
    
    # Test the base64 detection directly
    base64_data = "SGVsbG9Xb3JsZEFkbWluUGFzc3dvcmQxMjM="
    print(f"Testing base64 string: {base64_data}")
    print(f"Length: {len(base64_data)}")
    print(f"Length % 4: {len(base64_data) % 4}")
    
    # Test if it's valid base64
    import base64
    try:
        decoded = base64.b64decode(base64_data + '==')
        print(f"Decoded: {decoded}")
        print("✅ Valid base64")
    except Exception as e:
        print(f"❌ Invalid base64: {e}")
    
    # Test the domain splitting
    base64_domain = f"{base64_data}.tunnel.evil.com"
    subdomains = base64_domain.split('.')
    print(f"Subdomains: {subdomains}")
    
    # Test the detection logic
    base64_count = 0
    for subdomain in subdomains:
        if len(subdomain) > 4 and len(subdomain) % 4 == 0:
            try:
                base64.b64decode(subdomain + '==')
                base64_count += 1
                print(f"✅ Found base64 subdomain: {subdomain}")
            except:
                print(f"❌ Not base64: {subdomain}")
    
    print(f"Base64 count: {base64_count}")
    print(f"Total subdomains: {len(subdomains)}")
    print(f"Ratio: {base64_count / len(subdomains) if subdomains else 0}")

if __name__ == "__main__":
    debug_base64_detection()

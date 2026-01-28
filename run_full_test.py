#!/usr/bin/env python3
"""
Run Full IDS Test with DNS Tunneling Detection
"""

import subprocess
import time
import sys
import os

def run_component(script_name, description):
    """Run a component in the background"""
    print(f"🚀 Starting {description}...")
    try:
        # Change to the correct directory for the sniffer
        if script_name == "network_sniffer.py":
            cwd = os.path.join(os.getcwd(), "src", "monitors")
        else:
            cwd = os.getcwd()
            
        process = subprocess.Popen(
            [sys.executable, script_name],
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print(f"✅ {description} started (PID: {process.pid})")
        return process
    except Exception as e:
        print(f"❌ Failed to start {description}: {e}")
        return None

def test_dns_tunneling():
    """Test DNS tunneling detection"""
    print("\n🔍 Testing DNS Tunneling Detection...")
    
    try:
        # Run the DNS tunneling test
        result = subprocess.run(
            [sys.executable, "test_dns_detection.py"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if "✅ DNS Tunneling Detection is working correctly!" in result.stdout or "Base64 query detected as tunneling: True" in result.stdout:
            print("✅ DNS Tunneling Detection Test PASSED")
            return True
        else:
            print("❌ DNS Tunneling Detection Test FAILED")
            print(f"Output: {result.stdout}")
            return False
            
    except Exception as e:
        print(f"❌ DNS Tunneling Test Error: {e}")
        return False

def main():
    print("=== Full IDS System Test ===")
    print("This will test the DNS tunneling detection capabilities")
    
    # Test 1: Verify DNS detection works
    if not test_dns_tunneling():
        print("❌ DNS detection test failed - fix issues before running full system")
        return
    
    print("\n📋 Instructions for Full System Test:")
    print("1. Open Terminal 1 and run: python src/api/app.py")
    print("2. Open Terminal 2 and run: python src/monitors/network_sniffer.py") 
    print("3. Open Terminal 3 and run: python test_dns_tunneling_advanced.py")
    print("4. Open browser to: http://localhost:3000")
    print("5. Choose option 1 (Data Exfiltration) in the DNS test")
    print("\n🎯 Expected Results:")
    print("- Dashboard should show 'malicious' status for DNS tunneling")
    print("- Alerts should indicate DNS tunneling detection")
    print("- Confidence should be >70% for clear tunneling patterns")
    
    print("\n🔧 If issues occur:")
    print("- Make sure all components are running from correct directories")
    print("- Check that API server shows DNS features in logs")
    print("- Verify sniffer captures DNS packets (port 53)")

if __name__ == "__main__":
    main()

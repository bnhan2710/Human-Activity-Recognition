"""
Test DNS resolution for Firebase
"""
import socket
import sys

def test_dns():
    hostname = "imu-detection-app-default-rtdb.asia-southeast1.firebasedatabase.app"
    
    print("="*80)
    print("Testing DNS Resolution for Firebase")
    print("="*80)
    print(f"Hostname: {hostname}")
    print()
    
    try:
        print("Attempting to resolve hostname...")
        ip_addresses = socket.getaddrinfo(hostname, 443, socket.AF_INET)
        
        print(f"✅ SUCCESS! Resolved to:")
        for info in ip_addresses:
            print(f"   - {info[4][0]}")
        
        print()
        print("DNS resolution is working correctly.")
        print("The Firebase connection error must be due to another reason.")
        
    except socket.gaierror as e:
        print(f"❌ FAILED to resolve hostname")
        print(f"Error: {e}")
        print()
        print("Possible causes:")
        print("  1. No internet connection")
        print("  2. DNS server not configured correctly")
        print("  3. Firewall blocking DNS requests")
        print("  4. VPN or proxy issues")
        print()
        print("Troubleshooting steps:")
        print("  1. Check internet connection: ping google.com")
        print("  2. Check DNS: nslookup imu-detection-app-default-rtdb.asia-southeast1.firebasedatabase.app")
        print("  3. Try using Google DNS: 8.8.8.8")
        print("  4. Disable VPN/proxy temporarily")
        print("  5. Check firewall settings")
        
        sys.exit(1)
    
    print()
    print("="*80)

if __name__ == "__main__":
    test_dns()

import os
import sys
from utils.http_client import HTTPClient

def test_setup():
    print("[*] Starting Prometheus Diagnostic Check...", flush=True)
    
    url = os.getenv("TARGET_URL", "http://localhost/")
    user = os.getenv("TARGET_USER", "admin")
    password = os.getenv("TARGET_PASS", "password")
    security = os.getenv("TARGET_SECURITY", "medium")
    
    client = HTTPClient(base_url=url)
    
    print(f"[*] Target: {url}")
    print(f"[*] Security Level: {security.upper()}")
    
    if client.setup_dvwa(username=user, password=password, security_level=security):
        print("[+] Session established successfully.")
        
        # Test a basic logic payload based on the security level settings we implemented
        test_payload = "1 OR 1=1"
        print(f"[*] Sending diagnostic payload: {test_payload}")
        
        res = client.send_request(test_payload)
        
        print(f"[+] Response Status: {res['status']}")
        print(f"[+] Response Length: {len(res['text'])} bytes")
        
        if "Unknown column" in res['text']:
            print("[!] Alert: 'Unknown column' error detected. Engine will auto-patch this during attack.")
        elif "syntax error" in res['text'].lower():
            print("[!] Alert: SQL Syntax error detected. Context might be mismatched.")
        elif res['status'] == 200:
            print("[+] Target responded correctly. Connection is solid.")
        else:
            print(f"[!] Unexpected status code: {res['status']}")
            
    else:
        print("[!] Failed to establish session. Check credentials and target URL.")

if __name__ == "__main__":
    test_setup()

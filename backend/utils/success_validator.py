import random
import re
import difflib

class SuccessValidator:
    def __init__(self):
        # Signatures that indicate reflected data (Union/Error outputs)
        self.basic_signatures = ["First name:", "Surname:", "ID:", "admin", "gordonb", "1337"]
        self.hash_pattern = r"[a-f0-9]{32}"
        self.schema_signatures = [
            r"table_name", r"column_name", r"information_schema", r"schema_name",
            r"datname", r"user_tables", r"all_tab_columns", r"sysobjects"
        ]
        
        # sqlmap-inspired Error Signatures (Exhaustive list)
        self.db_errors = {
            "MySQL": [
                r"SQL syntax.*MySQL", r"Warning.*mysql_.*", r"valid MySQL result",
                r"MySqlClient\.", r"com\.mysql\.jdbc\.exceptions", r"Unknown column '[^']+' in 'where clause'"
            ],
            "PostgreSQL": [
                r"PostgreSQL.*ERROR", r"Warning.*\Wpg_.*", r"valid PostgreSQL result",
                r"Npgsql\.", r"PG::Error", r"ERROR:\s+column\s+\"[^\"]+\"\s+does\s+not\s+exist"
            ],
            "Microsoft SQL Server": [
                r"Driver.*SQL[\-\_\s]*Server", r"OLE DB.* SQL Server", r"\bSQL Server[^;]*Driver",
                r"Warning.*mssql_.*", r"SqlException", r"System\.Data\.SqlClient\."
            ],
            "Oracle": [
                r"\bORA-\d{5}", r"Oracle error", r"Oracle.*Driver", r"Warning.*\Woci_.*",
                r"Warning.*\Wora_.*"
            ]
        }

    def get_sql_error(self, response_text):
        """sqlmap-style error extraction: finds the specific error string."""
        for db, patterns in self.db_errors.items():
            for pattern in patterns:
                match = re.search(rf".*?({pattern}.*?)(?:\n|<br|<\/pre|<\/div|$)", response_text, re.IGNORECASE | re.DOTALL)
                if match:
                    error_msg = re.sub(r'<[^>]+>', '', match.group(1)).strip()
                    return f"[{db}] {error_msg}"
        return None

    def _calculate_ratio(self, text1, text2):
        """Returns similarity ratio between two strings (0.0 to 1.0)"""
        if not text1 or not text2: return 0.0
        return difflib.SequenceMatcher(None, text1, text2).quick_ratio()

    def validate(self, response_text, status_code, payload=None, latency=0, baseline=None):
        """
        Synthesized sqlmap-style validation core.
        Hierarchy: 1. Full Exfiltration -> 2. Error detection -> 3. Boolean/Structural Inference -> 4. WAF Block
        """
        if not response_text:
            return 0.0, "CONNECTION_ERROR"
            
        low_body = response_text.lower()
        payload_upper = payload.upper() if payload else ""

        # 1. WAF CLUE: Early exit if explicitly blocked (WAFs often return specific codes)
        # Using sqlmap logic: 403, 406, 501 are usually WAF/IPS fingerprints
        waf_signatures = [r"incident id:", r"support id:", r"rejected by", r"forbidden", r"captcha"]
        if status_code in [403, 406, 501, 999] or any(re.search(s, low_body) for s in waf_signatures):
            return 0.1, "WAF_BLOCKED"

        # 2. DATA REFLECTION (UNION/ERROR-BASED)
        # Check for MD5-like hashes (exfiltrated data)
        if re.search(self.hash_pattern, response_text):
            return 1.0, "EXFILTRATION_SUCCESS"
            
        # Check for DB Schema markers
        if any(re.search(sig, low_body) for sig in self.schema_signatures):
            return 0.95, "DATA_LEAK_CONFIRMED"

        # 3. ERROR REFLECTION
        error_msg = self.get_sql_error(response_text)
        if error_msg:
            # If we see an error but it contains "admin" or sensitive data, it's a partial leak
            if any(sig.lower() in error_msg.lower() for sig in self.basic_signatures):
                return 0.6, "ERROR_LEAK_PARTIAL"
            return 0.25, "SQL_ERROR_DETECTED"

        # 4. BOOLEAN-BASED BLIND (The sqlmap "Ratio" method)
        if baseline and status_code == 200:
            current_ratio = self._calculate_ratio(response_text, baseline.get('text', ''))
            
            # If latency is significantly high (e.g. SLEEP executed)
            if latency > (baseline.get('latency', 0) + 4000):
                return 0.85, "TIME_BASED_INJECTION"

            # Dynamic ratio analysis: significant content change (mimics --string/--not-string)
            if current_ratio < 0.95:
                # If payloads like '1 OR 1=1' generate a different ratio than baseline, it's boolean-true
                if "1=1" in payload_upper or "TRUE" in payload_upper or "OR 1" in payload_upper:
                    return 0.75, "BOOLEAN_INFERENCE_TRUE"
                return 0.5, "STRUCTURAL_CHANGE"

        # 5. CONTENT INFERENCE (Fallthrough)
        if any(sig in response_text for sig in self.basic_signatures):
            if "UNION" in payload_upper:
                return 0.9, "UNION_SUCCESS"
            return 0.7, "LOGIC_BYPASS_VERIFIED"

        return 0.2, "INCONCLUSIVE"

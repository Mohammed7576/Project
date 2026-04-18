import random
import re
import difflib
import time

class SuccessValidator:
    def __init__(self):
        # Signatures that indicate reflected data (Union/Error outputs)
        self.basic_signatures = ["First name:", "Surname:", "ID:", "admin", "gordonb", "1337"]
        self.password_signatures = [
            r"password", r"passwd", r"key", r"secret", r"hash", r"token", 
            r"credential", r"login_password", r"user_password"
        ]
        self.hash_pattern = r"[a-f0-9]{32}"
        self.schema_signatures = [
            r"table_name", r"column_name", r"information_schema", r"schema_name",
            r"datname", r"user_tables", r"all_tab_columns", r"sysobjects",
            r"Current User:", r"Database:"
        ]
        
        # sqlmap (official data/xml/errors.xml) exhaustive signatures for MySQL ONLY
        self.db_errors = {
            "MySQL": [
                r"SQL syntax.*MySQL", 
                r"Warning.*mysql_.*", 
                r"valid MySQL result",
                r"MySqlClient\.", 
                r"com\.mysql\.jdbc\.exceptions", 
                r"MySQL Error",
                r"Unknown column '[^']+' in 'where clause'",
                r"Table '[^']+' doesn't exist", 
                r"Column count doesn't match value count at row \d+",
                r"The used SELECT statements have a different number of columns",
                r"Incorrect column name '[^']+'",
                r"Can't find file: '[^']+'",
                r"Access denied for user '[^']+'@'[^']+'",
                r"Error: 1064 SQLSTATE: 42000",
                r"Incorrect parameter count in the call to native function '[^']+'",
                r"Illegal mix of collations",
                r"found in our database",
                r"Unknown table '[^']+' in field list",
                r"Duplicate entry '[^']+' for key \d+",
                r"Record at line \d+ error:"
            ]
        }
        
        # sqlmap's default ratio threshold
        self.ratio_threshold = 0.88 # Based on lib/core/settings.py: URI_INJECTION_RATIO

    def get_sql_error(self, response_text):
        """sqlmap-style error extraction: finds the specific error string from exhaustive set."""
        if not response_text: return None
        for db, patterns in self.db_errors.items():
            for pattern in patterns:
                match = re.search(rf".*?({pattern}.*?)(?:\n|<br|<\/pre|<\/div|$)", response_text, re.IGNORECASE | re.DOTALL)
                if match:
                    # Clean up HTML tags
                    error_msg = re.sub(r'<[^>]+>', '', match.group(1)).strip()
                    return f"[{db}] {error_msg}"
        return None

    def _calculate_ratio(self, text1, text2):
        """sqlmap logic (lib/core/comparison.py): Returns exact similarity ratio."""
        if not text1 or not text2: return 0.0
        # sqlmap uses a more complex system filtering out dynamic parts, 
        # but SequenceMatcher is the core engine for its 'comparison' function.
        return difflib.SequenceMatcher(None, text1, text2).quick_ratio()

    def validate(self, response_text, status_code, payload=None, latency=0, baseline=None):
        """
        Synthesized sqlmap-style validation core (lib/core/check.py).
        Assessment order:
        -1. BASELINE COMPARISON (Preventing Fails from 1 XOR 1=2 types)
        0. PASSWORDS & HASHES (Critical Objective)
        1. MASS DUMP DETECTION (Highest Priority for '1 OR true')
        ...
        """
        if not response_text:
            return 0.0, "CONNECTION_ERROR"
            
        low_body = response_text.lower()
        payload_upper = payload.upper() if payload else ""

        # -1. BASELINE COMPARISON (Critical fix for the user's observation)
        # If the response is nearly identical to the normal (non-attack) page, 
        # then the payload didn't actually "bypass" or "leak" anything new.
        if baseline and status_code == 200:
            ratio = self._calculate_ratio(response_text, baseline.get('text', ''))
            # Over 98% similarity means it's essentially the same page
            if ratio > 0.98:
                return 0.2, "NO_DATA_VARIATION"

        # 0. SENSITIVE DATA DETECTION (Focus on Passwords and NEW reflecting data)
        # We only care if these signatures appear and WERE NOT already in the baseline
        baseline_text = baseline.get('text', '').lower() if baseline else ""
        
        found_sensitive = False
        if re.search(self.hash_pattern, response_text):
            found_sensitive = True
        else:
            for sig in self.password_signatures:
                # Check if it exists in response but NOT in baseline (or count increased)
                if re.search(sig, low_body):
                    if not re.search(sig, baseline_text) or response_text.lower().count(sig.lower()) > baseline_text.count(sig.lower()):
                        found_sensitive = True
                        break
        
        if found_sensitive:
            return 1.0, "EXFILTRATION_SENSITIVE"

        # 0.1 UNION REFLECTION DETECTION (Context-Aware Bridgehead)
        if payload and "UNION" in payload_upper and "SELECT" in payload_upper:
            # Safely extract numbers (e.g., 1, 2 from UNION SELECT 1,2)
            # Using \b to avoid variable-width lookbehind issues
            scouts = re.findall(r"\b(\d+)\b", payload)
            scouts = [s for s in scouts if len(s) < 3] # Only focus on small scout numbers
            
            if scouts:
                matches = 0
                for s in scouts[:3]: # Check the first 3 columns
                    # Comprehensive Check: Number must appear after a label or inside specific tags (pre, td, div, span)
                    patterns = [
                        rf"(?:[:=|>])\s*{s}\s*(?:<|$)",  # After :, =, or > and followed by < or end
                        rf"<(pre|td|span|div)[^>]*>\s*{s}\s*</\1>", # Inside specific tags
                        rf"\b{s}\b(?=\s*<br)",           # Specifically for <br /> trailing reflection
                        rf">\s*{s}\s*<"                  # Pure tag content reflection
                    ]
                    if any(re.search(p, response_text, re.IGNORECASE) for p in patterns):
                        matches += 1
                
                if matches >= 1:
                    # If we see at least one reflected column in a safe context
                    return 0.98, "UNION_REFLECTION_VERIFIED"

        # 1. MASS DUMP DETECTION (Highest Priority for '1 OR true')
        # If we see many occurrences of data signatures, it's a successful dump
        sig_matches = sum(1 for sig in self.basic_signatures if response_text.count(sig) > 2)
        if sig_matches >= 2 or response_text.count("ID:") > 5:
            return 1.0, "SUCCESS_MASS_DATA_DUMP"

        # 2. WAF/IPS Detection (sqlmap logic)
        waf_signatures = [
            r"incident id:", r"support id:", r"rejected by", 
            r"captcha", r"blocked by administrative rules", r"safedog", r"webknight"
        ]
        
        if (status_code in [403, 406, 501, 999] or any(re.search(s, low_body) for s in waf_signatures)):
            # Special case: check if we bypassed it but it still returned 200 with data
            return 0.1, "WAF_BLOCKED"

        # 3. ERROR-BASED (The 'admin--' scenario - Treated as a diagnostic failure)
        error_msg = self.get_sql_error(response_text)
        if error_msg:
            # Check if actual data is leaked inside the error
            if any(re.search(sig, response_text, re.IGNORECASE) for sig in self.schema_signatures):
                return 0.95, "ERROR_SUCCESS_DATA_LEAK"
            
            # Simple SQL error without data exfiltration is a failure/scout info
            return 0.2, "SQL_SYNTAX_ERROR" # Lowered significantly from 0.8

        # 4. CONTENT-BASED (UNION/DATA LEAK)
        if re.search(self.hash_pattern, response_text):
            return 1.0, "EXFILTRATION_FULL"
            
        if any(re.search(sig, response_text, re.IGNORECASE) for sig in self.schema_signatures):
            if "UNION" in payload_upper:
                return 0.95, "UNION_EXFILTRATION"
            return 0.8, "DATA_REFLECTION_DETECTED"

        # 4. BOOLEAN-BASED (Comparison-ratio)
        if baseline and status_code == 200:
            # Baseline is usually the 'original' or 'False' condition
            ratio = self._calculate_ratio(response_text, baseline.get('text', ''))
            
            # sqlmap logic: If ratio is significantly different from 1.0, 
            # and the payload is a 'True' condition (OR 1=1), it's a positive match.
            if ratio < self.ratio_threshold:
                if any(kw in payload_upper for kw in ["OR 1=1", "TRUE", "NOT 0", "OR 1"]):
                    return 0.75, "BOOLEAN_INFERENCE_POSITIVE"
                return 0.4, "STRUCTURAL_VARIANCE"

        # 5. TIME-BASED (Statistical Delay)
        if baseline:
            # sqlmap uses a threshold based on average latency + std-dev. 
            # Here we use a fixed 4s + baseline as a simplified but effective check.
            if latency > (baseline.get('latency', 0) + 4000):
                return 0.85, "TIME_BASED_POSITIVE"

        # 6. HEURISTIC SIGNATURES
        if any(sig in response_text for sig in self.basic_signatures):
            return 0.65, "LOGIC_BYPASS_GENERIC"

        return 0.2, "INCONCLUSIVE"

import random
import re

class SuccessValidator:
    def __init__(self):
        self.basic_signatures = ["First name:", "Surname:", "ID:", "admin", "gordonb", "1337"]
        self.hash_pattern = r"[a-f0-9]{32}"
        self.schema_signatures = ["table_name", "column_name", "information_schema", "users", "guest"]

    def get_sql_error(self, response_text):
        """Detects and extracts the full SQL error message for better feedback."""
        # Common SQL error prefixes
        error_indicators = [
            r"you have an error in your sql syntax",
            r"mysql_fetch_array\(\)",
            r"native client",
            r"unclosed quotation mark",
            r"postgresql query failed",
            r"the used select statements have a different number of columns",
            r"column count doesn't match",
            r"invalid column name",
            r"unknown column",
            r"sqlstate"
        ]
        
        for indicator in error_indicators:
            # Search for the indicator and capture everything until a common terminator
            # (newline, <br>, or closing tag)
            pattern = rf".*?({indicator}.*?)(?:\n|<br|<\/pre|<\/div|$)"
            match = re.search(pattern, response_text, re.IGNORECASE | re.DOTALL)
            if match:
                # Clean up HTML tags if any
                error_msg = re.sub(r'<[^>]+>', '', match.group(1)).strip()
                return error_msg
        return None

    def validate(self, response_text, status_code, payload=None, latency=0, baseline=None):
        """
        Behavioral Analysis: Detects success/failure not just by content, 
        but by structural changes and timing.
        """
        if not response_text:
            return 0.0, "CONNECTION_ERROR"
            
        low_body = response_text.lower()
        payload_upper = payload.upper() if payload else ""

        # 1. SQL Error Awareness (CHECK THIS FIRST to avoid false positives)
        error_msg = self.get_sql_error(response_text)
        
        # 2. Real Data Extraction (The Ultimate Goal)
        if re.search(self.hash_pattern, response_text):
            return 1.0, "CRITICAL_DATA_LEAKED"
            
        # 3. WAF Detection (Behavioral) - If blocked, nothing else matters
        # Fix: Removed generic 'security' and 'blocked' to avoid false positives in DVWA
        waf_signatures = [
            r"incident id:", r"support id:", r"rejected by", r"forbidden by administrative rules",
            r"access denied", r"cloudflare", r"fortinet", r"barracuda", r"sucuri", 
            r"modsecurity", r"akami", r"imperva", r"incapsula", r"captcha"
        ]
        
        is_blocked = False
        if status_code in [403, 406, 501, 999]:
            is_blocked = True
        else:
            # Only block on 200 if we see a very high confidence WAF signature
            for sig in waf_signatures:
                if re.search(sig, low_body, re.IGNORECASE):
                    is_blocked = True
                    break
        
        if is_blocked:
            return 0.1, "WAF_BLOCKED"

        # If there is a SQL error, we penalize the score unless it's error-based exfiltration (not yet implemented)
        # We process signatures AFTER checking for errors to ensure data is actually being returned, not just reflected in error
        clean_text = response_text
        if error_msg:
            # Remove the error message from the text to see if signatures exist OUTSIDE the error
            clean_text = response_text.replace(error_msg, "")
            
        clean_low = clean_text.lower()

        # 4. Success Signatures (Only if not purely an error)
        if any(sig in clean_low for sig in self.schema_signatures) and "UNION" in payload_upper:
            return 0.95, "SCHEMA_EXFILTRATED"

        if any(sig in clean_text for sig in self.basic_signatures):
            # Give a higher score if it actually uses UNION, otherwise cap it at 0.7 
            if "UNION" in payload_upper or "SELECT" in payload_upper:
                return 0.85, "SQL_EXECUTION_VERIFIED"
            else:
                return 0.65, "WAF_BYPASSED_PARTIAL"

        # If it was an error and no signatures were found outside it, return the error score
        if error_msg:
            return 0.25, "SQL_ERROR_DETECTED"

        # 5. Behavioral Analysis (Comparison with Baseline)
        if baseline:
            # Time-Based Analysis (Detection of Time-Based Blind SQLi)
            if latency > (baseline.get('latency', 0) + 4000): # 4s delay
                return 0.80, "TIME_BASED_SUCCESS"
            
            # Structural Analysis (Detection of Boolean-Based Blind SQLi)
            size_diff = abs(len(response_text) - baseline.get('size', 0))
            if size_diff > 50 and status_code == 200:
                return 0.5, "STRUCTURAL_BEHAVIOR_CHANGE"

        if status_code == 200 and len(response_text) > 500:
            return 0.3, "POTENTIAL_BYPASS"
            
        return 0.2, "INCONCLUSIVE_RESPONSE"

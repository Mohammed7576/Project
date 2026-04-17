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
        
        # 1. Real Data Extraction (The Ultimate Goal)
        if re.search(self.hash_pattern, response_text):
            return 1.0, "CRITICAL_DATA_LEAKED"
            
        if any(sig in low_body for sig in self.schema_signatures) and "UNION" in payload_upper:
            return 0.95, "SCHEMA_EXFILTRATED"
            
        # 2. Logic Bypasses (Cap the score to avoid Genetic Drift)
        # We don't want the AI to get obsessed with just '1=1'. We cap its score so it doesn't max out.
        if any(sig in response_text for sig in self.basic_signatures):
            # Give a higher score if it actually uses UNION, otherwise cap it at 0.7 
            # to force the AI to keep trying exfiltration techniques.
            if "UNION" in payload_upper or "SELECT" in payload_upper:
                return 0.85, "SQL_EXECUTION_VERIFIED"
            else:
                return 0.65, "WAF_BYPASSED_PARTIAL"

        # 3. Behavioral Analysis (Comparison with Baseline)
        if baseline:
            # Time-Based Analysis (Detection of Time-Based Blind SQLi)
            if latency > (baseline.get('latency', 0) + 4000): # 4s delay
                return 0.80, "TIME_BASED_SUCCESS"
            
            # Structural Analysis (Detection of Boolean-Based Blind SQLi)
            size_diff = abs(len(response_text) - baseline.get('size', 0))
            if size_diff > 50 and status_code == 200:
                return 0.5, "STRUCTURAL_BEHAVIOR_CHANGE"

        # 4. WAF Detection (Behavioral)
        waf_indicators = ["forbidden", "access denied", "waf", "security", "blocked", "captcha", "cloudflare"]
        if status_code in [403, 406, 501] or any(ind in low_body for ind in waf_indicators):
            return 0.1, "WAF_BLOCKED"

        # 5. SQL Error Awareness
        error_msg = self.get_sql_error(response_text)
        if error_msg:
            return 0.25, "SQL_ERROR_DETECTED"

        if status_code == 200 and len(response_text) > 500:
            return 0.3, "POTENTIAL_BYPASS"
            
        return 0.2, "INCONCLUSIVE_RESPONSE"

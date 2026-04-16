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

    def validate(self, response_text, status_code, latency=0, baseline=None):
        """
        Behavioral Analysis: Detects success/failure not just by content, 
        but by structural changes and timing.
        """
        if not response_text:
            return 0.0, "CONNECTION_ERROR"
            
        low_body = response_text.lower()
        
        # 1. Critical Data Detection
        if re.search(self.hash_pattern, response_text):
            return 1.0, "CRITICAL_DATA_LEAKED"
        if any(sig in low_body for sig in self.schema_signatures) and "UNION" in response_text.upper():
            return 0.95, "SCHEMA_EXFILTRATED"
        if any(sig in response_text for sig in self.basic_signatures):
            return 0.9, "WAF_BYPASSED_PARTIAL"

        # 2. Behavioral Analysis (Comparison with Baseline)
        if baseline:
            # Time-Based Analysis (Detection of Time-Based Blind SQLi)
            if latency > (baseline.get('latency', 0) + 4000): # 4s delay
                return 0.85, "TIME_BASED_SUCCESS"
            
            # Structural Analysis (Detection of Boolean-Based Blind SQLi)
            # If the response size or structure changed significantly from baseline
            size_diff = abs(len(response_text) - baseline.get('size', 0))
            if size_diff > 50 and status_code == 200:
                return 0.6, "STRUCTURAL_BEHAVIOR_CHANGE"

        # 3. WAF Detection (Behavioral)
        waf_indicators = ["forbidden", "access denied", "waf", "security", "blocked", "captcha", "cloudflare"]
        if status_code in [403, 406, 501] or any(ind in low_body for ind in waf_indicators):
            return 0.1, "WAF_BLOCKED"

        if status_code == 200 and len(response_text) > 500:
            return 0.4, "POTENTIAL_BYPASS"
            
        return 0.2, "INCONCLUSIVE_RESPONSE"

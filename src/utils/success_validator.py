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

    def validate(self, response_text, status_code, size=0, word_count=0, baseline=None):
        if not response_text:
            return 0.0, "CONNECTION_ERROR"
        
        low_body = response_text.lower()
        
        # 1. High Confidence: Data Leakage
        if re.search(self.hash_pattern, response_text):
            return 1.0, "CRITICAL_DATA_LEAKED"
        if any(sig in low_body for sig in self.schema_signatures) and "UNION" in response_text.upper():
            return 0.95, "SCHEMA_EXFILTRATED"
        if any(sig in response_text for sig in self.basic_signatures):
            return 0.9, "WAF_BYPASSED_PARTIAL"

        # 2. Response Shape Fingerprinting (Idea #3)
        if baseline:
            size_diff = abs(size - baseline.get("size", 0))
            word_diff = abs(word_count - baseline.get("word_count", 0))
            
            # If size or word count changed significantly without a 403/406
            if status_code == 200:
                if size_diff > 50 or word_diff > 5:
                    print(f"  [Fingerprint] Shape change detected: Size Diff {size_diff}, Word Diff {word_diff}", flush=True)
                    return 0.6, "BLIND_SUCCESS_POTENTIAL"

        # 3. Fallbacks
        if status_code == 200 and len(response_text) > 1000:
            return 0.5, "POTENTIAL_BYPASS"
        
        if status_code in [403, 406] or "waf" in low_body or "forbidden" in low_body:
            return 0.1, "WAF_BLOCKED"
            
        return 0.2, "UNKNOWN_RESPONSE"

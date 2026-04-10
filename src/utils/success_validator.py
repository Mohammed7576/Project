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

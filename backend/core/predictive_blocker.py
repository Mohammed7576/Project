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
            
            # Prune broad rules once at startup
            bad_rules = [r"\bSELECT\b", r"\bOR\b", r"\bAND\b", r"\bUNION\b", r"\bXOR\b", r"\d+\s*=\s*\d+", r"/\*.*\*/"]
            for bad in bad_rules:
                cursor.execute('DELETE FROM blocking_rules WHERE pattern = ?', (bad,))
            conn.commit()
        except Exception as e:
            print(f"[!] Blocker: Error in _init_db: {e}")

    def _load_patterns(self):
        """Loads known blocking patterns from the database."""
        try:
            conn = self.conn
            cursor = conn.cursor()
            cursor.execute('SELECT pattern FROM blocking_rules WHERE confidence > 0.4')
            self.blocked_patterns = {row[0] for row in cursor.fetchall()}
        except Exception as e:
            print(f"[!] Blocker: Error loading patterns: {e}")

    def should_block(self, payload):
        """Checks if the payload matches any known blocking pattern."""
        for pattern in self.blocked_patterns:
            try:
                if re.search(pattern, payload, re.IGNORECASE):
                    return True, pattern
            except: pass
        return False, None

    def learn_from_block(self, payload):
        """Analyzes a blocked payload and extracts WAF rules to avoid."""
        tokens = self.mutator._tokenize(payload)
        rule_updates = []
        
        # We look for dangerous pairings (e.g., KEYWORD + KEYWORD or KEYWORD + SYMBOL)
        for i in range(len(tokens) - 1):
            tok1 = tokens[i]
            
            # 1. Structural Function Calls: Block the specific function structure
            if tok1['type'] in ['KEYWORD', 'IDENTIFIER'] and tokens[i+1]['value'] == '(':
                # Block the exact keyword + parenthesis format specifically
                pattern = f"\\b{re.escape(tok1['value']).upper()}\\s*\\("
                rule_updates.append((pattern, 0.15))
                
            # 2. Syntax-Specific Injection: Find Operator + Keyword blocks
            if tok1['type'] == 'KEYWORD':
                # Walk ahead to find the next meaningful token (skip spaces and minor comments)
                for j in range(i+1, min(len(tokens), i+4)):
                    tok2 = tokens[j]
                    if tok2['type'] in ['KEYWORD', 'OPERATOR', 'SYS_VAR']:
                        pattern = f"\\b{re.escape(tok1['value']).upper()}\\b.*?\\b{re.escape(tok2['value']).upper()}\\b"
                        rule_updates.append((pattern, 0.1))
                        break

            # 3. Direct Encoding / Evasion Signatures
            if tok1['type'] == 'HEX_BIT':
                rule_updates.append((r"0[xX][0-9a-fA-F]+", 0.1))

            if tok1['type'] == 'EXEC_COMMENT':
                ver_match = re.search(r"/\*!(\d{5})", tok1['value'])
                if ver_match:
                    rule_updates.append((rf"/\*!{ver_match.group(1)}", 0.1))

        # 4. Fallback: If AST tokenization missed it, mark the raw payload to reflect reality
        if not rule_updates and len(payload) > 5:
            pattern = re.escape(payload)
            rule_updates.append((pattern, 0.05))

        for pattern, boost in rule_updates:
            self._update_rule(pattern, boost)
        
        # Reload once after all individual pattern updates
        if rule_updates:
            self._load_patterns()

    def report_success(self, payload):
        """Reduces confidence in rules that were present in a successful payload."""
        to_reduce = []
        for pattern in self.blocked_patterns:
            if re.search(pattern, payload, re.IGNORECASE):
                to_reduce.append(pattern)
        
        if not to_reduce:
            return

        try:
            conn = self.conn
            cursor = conn.cursor()
            for pattern in to_reduce:
                cursor.execute('UPDATE blocking_rules SET confidence = confidence - 0.2 WHERE pattern = ?', (pattern,))
            
            cursor.execute('DELETE FROM blocking_rules WHERE confidence < 0.3')
            conn.commit()
        except Exception as e:
            print(f"[!] Blocker: Error reducing confidence: {e}")
        
        self._load_patterns() # Refresh local set

    def _update_rule(self, pattern, confidence_boost):
        # We'll stick to direct updates for now as batching across different patterns 
        # that might already exist needs more complex logic, 
        # but we'll at least reduce overhead by not reloading patterns.
        import time
        max_retries = 3 # Reduced retries to avoid hanging
        for attempt in range(max_retries):
            try:
                conn = self.conn
                cursor = conn.cursor()
                cursor.execute('SELECT confidence FROM blocking_rules WHERE pattern = ?', (pattern,))
                row = cursor.fetchone()
                if row:
                    new_conf = min(1.0, row[0] + confidence_boost)
                    cursor.execute('UPDATE blocking_rules SET confidence = ? WHERE pattern = ?', (new_conf, pattern))
                else:
                    initial_conf = 0.6 + confidence_boost
                    cursor.execute('INSERT INTO blocking_rules (pattern, confidence) VALUES (?, ?)', (pattern, initial_conf))
                
                conn.commit()
                return
            except sqlite3.OperationalError as e:
                if "locked" in str(e).lower():
                    time.sleep(0.1 * (attempt + 1))
                    continue
                break
            except Exception:
                break

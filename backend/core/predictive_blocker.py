import re
import sqlite3
import sys
import os
sys.path.append(os.path.abspath("/app/applet/backend"))
from core.mutator_ast import ASTMutator  # Import to use Lexer

class PredictiveBlocker:
    _conn = None

    def __init__(self, db_path="memory.db"):
        self.db_path = db_path
        self.blocked_patterns = set()
        self.mutator = ASTMutator() # Just for tokenization
        self.load_patterns()

    def _get_conn(self):
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30)
        return self._conn

    def load_patterns(self):
        """Loads known blocking patterns from the database into memory."""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute('CREATE TABLE IF NOT EXISTS blocking_rules (pattern TEXT PRIMARY KEY, confidence REAL)')
            
            # Prune overly broad rules that kill evolution
            bad_rules = [r"\bSELECT\b", r"\bOR\b", r"\bAND\b", r"\bUNION\b", r"\bXOR\b", r"\d+\s*=\s*\d+", r"/\*.*\*/"]
            for bad in bad_rules:
                cursor.execute('DELETE FROM blocking_rules WHERE pattern = ?', (bad,))
            if cursor.rowcount > 0:
                conn.commit()

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
        """Analyzes a blocked payload using Token sequencing to extract specific WAF rules."""
        tokens = self.mutator._tokenize(payload)
        
        # We look for dangerous pairings (e.g., KEYWORD + KEYWORD or KEYWORD + SYMBOL)
        # Instead of blocking the whole string, we block the semantic pattern that caused the WAF to trigger.
        
        for i in range(len(tokens) - 1):
            tok1 = tokens[i]
            
            # 1. Structural Function Calls: Block the specific function structure
            if tok1['type'] in ['KEYWORD', 'IDENTIFIER'] and tokens[i+1]['value'] == '(':
                # Block the exact keyword + parenthesis format specifically
                pattern = f"\\b{re.escape(tok1['value']).upper()}\\s*\\("
                self._update_rule(pattern, 0.15)
                
            # 2. Syntax-Specific Injection: Find Operator + Keyword blocks
            if tok1['type'] == 'KEYWORD':
                # Walk ahead to find the next meaningful token (skip spaces and minor comments)
                for j in range(i+1, min(len(tokens), i+4)):
                    tok2 = tokens[j]
                    if tok2['type'] in ['KEYWORD', 'OPERATOR', 'SYS_VAR']:
                        # The WAF likely triggered on the logical jump (e.g. UNION followed by SELECT)
                        pattern = f"\\b{re.escape(tok1['value']).upper()}\\b.*?\\b{re.escape(tok2['value']).upper()}\\b"
                        self._update_rule(pattern, 0.1)
                        break

            # 3. Direct Encoding / Evasion Signatures
            if tok1['type'] == 'HEX_BIT':
                self._update_rule(r"0[xX][0-9a-fA-F]+", 0.1)

            if tok1['type'] == 'EXEC_COMMENT':
                # The WAF might be blocking MySQL executable comments
                ver_match = re.search(r"/\*!(\d{5})", tok1['value'])
                if ver_match:
                    self._update_rule(rf"/\*!{ver_match.group(1)}", 0.1)

    def report_success(self, payload):
        """Reduces confidence in rules that were present in a successful payload."""
        for pattern in self.blocked_patterns:
            if re.search(pattern, payload, re.IGNORECASE):
                # Reduce confidence
                try:
                    conn = self._get_conn()
                    cursor = conn.cursor()
                    cursor.execute('UPDATE blocking_rules SET confidence = confidence - 0.2 WHERE pattern = ?', (pattern,))
                    cursor.execute('DELETE FROM blocking_rules WHERE confidence < 0.3')
                    if cursor.rowcount > 0:
                        print(f"[*] Blocker: Rule '{pattern}' confidence reduced/removed due to success.", flush=True)
                    conn.commit()
                except Exception as e:
                    print(f"[!] Blocker: Error reducing confidence: {e}")
        self.load_patterns() # Refresh local set

    def _update_rule(self, pattern, confidence_boost):
        try:
            conn = self._get_conn()
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
            self.load_patterns()
        except Exception as e:
            print(f"[!] Blocker: Error updating rule: {e}")

import re
import sqlite3

class PredictiveBlocker:
    def __init__(self, db_path="memory.db"):
        self.db_path = db_path
        self.blocked_patterns = set()
        self._load_patterns()

    def _load_patterns(self):
        """Loads known blocking patterns from the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('CREATE TABLE IF NOT EXISTS blocking_rules (pattern TEXT PRIMARY KEY, confidence REAL)')
            # Lowered the threshold to 0.4 so patterns show up faster and the AI adapts quicker
            cursor.execute('SELECT pattern FROM blocking_rules WHERE confidence > 0.4')
            self.blocked_patterns = {row[0] for row in cursor.fetchall()}
            conn.close()
        except Exception as e:
            print(f"[!] Blocker: Error loading patterns: {e}")

    def should_block(self, payload):
        """Checks if the payload matches any known blocking pattern."""
        for pattern in self.blocked_patterns:
            if re.search(pattern, payload, re.IGNORECASE):
                return True, pattern
        return False, None

    def learn_from_block(self, payload):
        """Analyzes a blocked payload to extract potential blocking rules."""
        # Detect more specific and dynamic patterns that caused the block
        
        # 1. Broaden Keyword Detection
        keywords = ["UNION", "SELECT", "INFORMATION_SCHEMA", "SLEEP", "BENCHMARK", "GROUP_CONCAT", "OR", "AND", "XOR", "ORDER BY", "CAST", "CONVERT"]
        for kw in keywords:
            if re.search(rf'\b{kw}\b', payload, re.IGNORECASE):
                # We found a matching keyword, increase confidence that it's blocked
                self._update_rule(f"\\b{kw}\\b", 0.05)
                
                # Check for common keyword combinations that triggered the block
                if " " in payload and kw in payload:
                    parts = re.split(rf'\s+{kw}\s+', payload, maxsplit=1, flags=re.IGNORECASE)
                    if len(parts) == 2 and parts[1]:
                       # Record the immediate context after the keyword
                       context = parts[1].split()[0][:10]
                       if len(context) > 2 and context.isalnum():
                          self._update_rule(f"\\b{kw}\\s+{context}", 0.1)

        # 2. Heuristics for Structural Patterns
        # Detect encoded characters that might be blocked
        if "%" in payload:
            encoded_patterns = set(re.findall(r"%[0-9a-fA-F]{2}", payload))
            if encoded_patterns:
                self._update_rule(r"\%[0-9A-Fa-f]{2}", 0.05 * len(encoded_patterns))

        # Detect specific function calls
        functions = set(re.findall(r"\b([a-zA-Z_]+)\s*\(", payload))
        for func in functions:
            if func.upper() in ["CHAR", "ASCII", "SUBSTRING", "MID", "SLEEP"]:
                self._update_rule(f"{func}\\(", 0.1)

        # 3. Detect existing known suspicious patterns
        suspicious = [
            (r"/\*.*\*/", 0.1),             # Inline comments
            (r"0x[0-9a-fA-F]+", 0.1),       # Hex encoding
            (r"\'\s*=\s*\'", 0.1),          # Trivial tautology ('=')
            (r"\d+\s*=\s*\d+", 0.1),        # Trivial numeric tautology (1=1)
            (r"\|\|", 0.1),                 # Logical OR alternative
            (r"\&\&", 0.1)                  # Logical AND alternative
        ]
        
        for pattern, base_boost in suspicious:
            if re.search(pattern, payload, re.IGNORECASE):
                self._update_rule(pattern, base_boost)

    def report_success(self, payload):
        """Reduces confidence in rules that were present in a successful payload."""
        to_remove = []
        for pattern in self.blocked_patterns:
            if re.search(pattern, payload, re.IGNORECASE):
                # Reduce confidence
                try:
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.execute('UPDATE blocking_rules SET confidence = confidence - 0.2 WHERE pattern = ?', (pattern,))
                    cursor.execute('DELETE FROM blocking_rules WHERE confidence < 0.3')
                    if cursor.rowcount > 0:
                        print(f"[*] Blocker: Rule '{pattern}' confidence reduced/removed due to success.", flush=True)
                    conn.commit()
                    conn.close()
                    # We'll reload patterns next time or just remove from set
                except Exception as e:
                    print(f"[!] Blocker: Error reducing confidence: {e}")
        self._load_patterns() # Refresh local set

    def _update_rule(self, pattern, confidence_boost):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # Check if exists
            cursor.execute('SELECT confidence FROM blocking_rules WHERE pattern = ?', (pattern,))
            row = cursor.fetchone()
            if row:
                new_conf = min(1.0, row[0] + confidence_boost)
                cursor.execute('UPDATE blocking_rules SET confidence = ? WHERE pattern = ?', (new_conf, pattern))
            else:
                # New rule starts with a base confidence
                cursor.execute('INSERT INTO blocking_rules (pattern, confidence) VALUES (?, ?)', (pattern, 0.5 + confidence_boost))
            
            conn.commit()
            conn.close()
            if pattern not in self.blocked_patterns:
                print(f"[*] Blocker: New blocking pattern learned: {pattern}", flush=True)
            self._load_patterns() # Refresh
        except Exception as e:
            print(f"[!] Blocker: Error updating rule: {e}")

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
            cursor.execute('SELECT pattern FROM blocking_rules WHERE confidence > 0.7')
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
        # Simple heuristic: if a payload is blocked, its keywords are suspicious
        keywords = ["UNION", "SELECT", "INFORMATION_SCHEMA", "SLEEP", "BENCHMARK", "GROUP_CONCAT"]
        found_bad = []
        
        for kw in keywords:
            if kw in payload.upper():
                found_bad.append(kw)
        
        if found_bad:
            # If we found known dangerous keywords, increase their 'bad' confidence
            self._update_rule(f"\\b{found_bad[0]}\\b", 0.1) # Increment confidence
            
        # Also look for suspicious character combinations
        suspicious = [r"/\*.*\*/", r"0x[0-9a-f]+", r"char\("]
        for pattern in suspicious:
            if re.search(pattern, payload, re.IGNORECASE):
                self._update_rule(pattern, 0.1)

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

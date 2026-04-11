import sqlite3
import os

class ExperienceManager:
    def __init__(self, db_path="memory.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS experience (
                    payload TEXT PRIMARY KEY,
                    score REAL,
                    status TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[!] Error initializing database: {e}")

    def save_attempt(self, payload, score, status):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO experience (payload, score, status)
                VALUES (?, ?, ?)
            ''', (payload, score, status))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[!] Database Error (Save): {e}")

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

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

    def get_score(self, payload):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT score FROM experience WHERE payload = ?', (payload,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else None
        except Exception as e:
            print(f"[!] Database Error (Get): {e}")
            return None

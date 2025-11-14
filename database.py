# database.py
import sqlite3
import re
from typing import Tuple

DB_NAME = "users.db"

def init_db():
    """Create users table if not exists."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def is_strong_password(password: str) -> Tuple[bool, str]:
    """
    Validate password:
    - At least 8 chars
    - At least one uppercase
    - At least one lowercase
    - At least one digit
    - At least one special char from set [#@$!%*?&]
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number."
    if not re.search(r"[#@\$!%*?&]", password):
        return False, "Password must contain at least one special symbol (# @ $ ! % * ? &)."
    return True, "OK"

def register_user(username: str, hashed_password: str) -> bool:
    """Insert new user. Returns True on success, False if username exists."""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        # username already exists
        return False
    except Exception:
        return False

def get_user(username: str):
    """Return user row or None."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, username, password FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    return row

# Initialize DB on import (safe to call multiple times)
init_db()

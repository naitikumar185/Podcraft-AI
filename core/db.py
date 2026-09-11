"""
core/db.py
----------
Single place that owns the SQLite connection and the schema.

Why SQLite: no separate server to install/run, the whole database is one
file (podcast.db), and it's trivial to open in a DB browser during your
viva to show the tables.

Streamlit re-runs the whole script on every interaction, so instead of
keeping one long-lived connection we open a short-lived connection per
call (get_conn()). SQLite handles this fine for a project of this size.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "podcast.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets us access columns by name, e.g. row["email"]
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Creates all tables if they don't exist yet. Safe to call on every app start."""
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',       -- 'user' | 'admin'
            plan TEXT NOT NULL DEFAULT 'free',        -- 'free' | 'premium'
            credits INTEGER NOT NULL DEFAULT 5,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS scripts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT,
            topic TEXT,
            content TEXT,
            category TEXT,
            duration INTEGER,
            num_speakers INTEGER,
            speaker_names TEXT,
            language TEXT,
            tone TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_scripts_user_id ON scripts(user_id)")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            plan TEXT NOT NULL,
            amount REAL NOT NULL,
            razorpay_order_id TEXT,
            razorpay_payment_id TEXT,
            status TEXT NOT NULL DEFAULT 'pending',   -- 'pending' | 'successful' | 'failed'
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id)")

    conn.commit()
    conn.close()

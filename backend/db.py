import os
import sqlite3
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# SQLite Local DB Setup
if os.path.exists("/app/data"):
    DB_FILE = "/app/data/trades.db"
else:
    DB_FILE = os.path.join(os.path.dirname(__file__), "trades.db")

def init_local_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        model_name TEXT NOT NULL,
        strategy_tag TEXT NOT NULL,
        asset_class TEXT NOT NULL,
        symbol TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'open',
        direction TEXT NOT NULL DEFAULT 'long',
        quantity REAL NOT NULL,
        entry_price REAL NOT NULL,
        entry_time TEXT NOT NULL,
        exit_price REAL,
        exit_time TEXT,
        unrealized_pnl REAL DEFAULT 0,
        realized_pnl REAL DEFAULT 0,
        simulated_fees REAL DEFAULT 0,
        pnl_pct REAL,
        reasoning_text TEXT NOT NULL,
        confidence REAL NOT NULL
    )
    """)
    conn.commit()
    conn.close()

init_local_db()

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def get_supabase() -> Optional[Client]:
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            return create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception:
            return None
    return None

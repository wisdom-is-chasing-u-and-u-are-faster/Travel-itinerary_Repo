"""
Database Initialization Module for Travel Itinerary Generator Platform.
Ensures tables exist and sample data is seeded into SQLite database.
"""

import os
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = os.environ.get("DATABASE_PATH", "travel_platform.db")

def init_db(db_path: str = None) -> None:
    target_path = db_path or os.environ.get("DATABASE_PATH", DEFAULT_DB_PATH)
    base_dir = Path(__file__).resolve().parent.parent.parent
    schema_path = base_dir / "db" / "schema.sql"
    seed_path = base_dir / "db" / "seed.sql"

    conn = sqlite3.connect(target_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        if schema_path.exists():
            conn.executescript(schema_path.read_text(encoding="utf-8"))
        if seed_path.exists():
            conn.executescript(seed_path.read_text(encoding="utf-8"))
        conn.commit()
    finally:
        conn.close()

def get_db_connection(db_path: str = None) -> sqlite3.Connection:
    target_path = db_path or os.environ.get("DATABASE_PATH", DEFAULT_DB_PATH)
    
    # Auto-initialize if database file doesn't exist or is empty
    if not Path(target_path).exists() or Path(target_path).stat().st_size == 0:
        init_db(target_path)
        
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at:", DEFAULT_DB_PATH)

"""
Database Schema & Migrations Integrity Test Suite (ARCH-7851).
Verifies DDL schema, foreign key constraints, indexes, and seed records.
"""

import sqlite3
import pytest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def test_schema_syntax_and_tables():
    """Verifies DDL creates all 10 required relational tables."""
    schema_path = BASE_DIR / "db" / "schema.sql"
    assert schema_path.exists(), "db/schema.sql must exist"

    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(schema_path.read_text(encoding="utf-8"))

    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = {r[0] for r in cursor.fetchall()}

    expected_tables = {
        "users", "itineraries", "itinerary_days", "activities",
        "collaborators", "expenses", "expense_splits", "bookings",
        "affiliates", "admin_metrics"
    }
    for t in expected_tables:
        assert t in tables, f"Expected table '{t}' was not found in schema"

def test_seed_data_execution_and_constraints():
    """Verifies seed data populates without violating foreign key constraints."""
    schema_path = BASE_DIR / "db" / "schema.sql"
    seed_path = BASE_DIR / "db" / "seed.sql"

    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(schema_path.read_text(encoding="utf-8"))
    conn.executescript(seed_path.read_text(encoding="utf-8"))

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    assert cursor.fetchone()[0] >= 3

    cursor.execute("SELECT COUNT(*) FROM itineraries")
    assert cursor.fetchone()[0] >= 2

    cursor.execute("SELECT COUNT(*) FROM activities")
    assert cursor.fetchone()[0] >= 5

    cursor.execute("SELECT COUNT(*) FROM expenses")
    assert cursor.fetchone()[0] >= 3

def test_foreign_key_enforcement():
    """Verifies that inserting an activity with an invalid day_id raises IntegrityError."""
    schema_path = BASE_DIR / "db" / "schema.sql"
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(schema_path.read_text(encoding="utf-8"))

    cursor = conn.cursor()
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            """
            INSERT INTO activities (itinerary_id, day_id, time, title, location)
            VALUES (999, 999, '10:00 AM', 'Orphan Activity', 'Nowhere')
            """
        )

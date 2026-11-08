"""SQLite WAL database storage and query layer for keyboard press events."""

from pathlib import Path
import sqlite3
import threading
from typing import Any


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS key_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    iso_time TEXT NOT NULL,
    date_str TEXT NOT NULL,
    hour INTEGER NOT NULL,
    vk_code INTEGER NOT NULL,
    key_code TEXT NOT NULL,
    key_label TEXT NOT NULL,
    modifiers TEXT NOT NULL,
    combo_label TEXT NOT NULL,
    is_printable INTEGER NOT NULL,
    app_name TEXT NOT NULL,
    window_title TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_key_events_date ON key_events(date_str);
CREATE INDEX IF NOT EXISTS idx_key_events_date_key ON key_events(date_str, key_code);
CREATE INDEX IF NOT EXISTS idx_key_events_date_app ON key_events(date_str, app_name);
CREATE INDEX IF NOT EXISTS idx_key_events_timestamp ON key_events(timestamp DESC);
"""


class Database:
    """Thread-safe SQLite database manager using WAL journal mode."""

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)
        self._lock = threading.Lock()

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def init_db(self) -> None:
        """Create the key_events table and indexes if they do not exist."""
        with self._lock:
            with self._connect() as conn:
                conn.executescript(SCHEMA_SQL)

    def insert_events_batch(self, events: list[dict[str, Any]]) -> int:
        """Insert a batch of key event dictionaries in a single transaction."""
        if not events:
            return 0
        query = """
            INSERT INTO key_events (
                timestamp, iso_time, date_str, hour, vk_code,
                key_code, key_label, modifiers, combo_label,
                is_printable, app_name, window_title
            ) VALUES (
                :timestamp, :iso_time, :date_str, :hour, :vk_code,
                :key_code, :key_label, :modifiers, :combo_label,
                :is_printable, :app_name, :window_title
            )
        """
        with self._lock:
            with self._connect() as conn:
                conn.executemany(query, events)
                conn.commit()
        return len(events)

    def get_available_dates(self) -> list[str]:
        """Return distinct date strings ordered newest first."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT DISTINCT date_str FROM key_events ORDER BY date_str DESC"
            ).fetchall()
        return [row["date_str"] for row in rows]

    def get_events_for_date(self, date_str: str) -> list[dict[str, Any]]:
        """Return all sequential events for a given date ordered chronologically."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM key_events WHERE date_str = ? ORDER BY timestamp ASC, id ASC",
                (date_str,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_events_in_range(self, start_date: str, end_date: str) -> list[dict[str, Any]]:
        """Return all sequential events between start_date and end_date (inclusive)."""
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM key_events
                WHERE date_str >= ? AND date_str <= ?
                ORDER BY timestamp ASC, id ASC
                """,
                (start_date, end_date),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_paginated_events(
        self,
        date_str: str,
        limit: int = 100,
        offset: int = 0,
        key_filter: str = "",
        app_filter: str = "",
        search_query: str = "",
    ) -> dict[str, Any]:
        """Return newest-first paginated raw key events for a date with optional filters."""
        clauses = ["date_str = ?"]
        params: list[Any] = [date_str]

        if key_filter:
            clauses.append("(key_code = ? OR key_label = ? OR combo_label = ?)")
            params.extend([key_filter, key_filter, key_filter])
        if app_filter:
            clauses.append("app_name = ?")
            params.append(app_filter)
        if search_query:
            like_val = f"%{search_query}%"
            clauses.append(
                "(key_label LIKE ? OR key_code LIKE ? OR combo_label LIKE ? "
                "OR app_name LIKE ? OR window_title LIKE ?)"
            )
            params.extend([like_val] * 5)

        where_sql = " AND ".join(clauses)
        with self._connect() as conn:
            total = conn.execute(
                f"SELECT COUNT(*) AS cnt FROM key_events WHERE {where_sql}",
                params,
            ).fetchone()["cnt"]

            rows = conn.execute(
                f"""
                SELECT * FROM key_events
                WHERE {where_sql}
                ORDER BY timestamp DESC, id DESC
                LIMIT ? OFFSET ?
                """,
                [*params, limit, offset],
            ).fetchall()

        return {
            "total": int(total),
            "limit": limit,
            "offset": offset,
            "items": [dict(row) for row in rows],
        }

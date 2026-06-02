from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import DATA_DIR

DB_PATH = DATA_DIR / "history.db"


def _conn() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db() -> None:
    with _conn() as c:
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                title TEXT,
                kind TEXT,
                file_path TEXT,
                created_at TEXT NOT NULL
            )
            """
        )


def add_entry(url: str, title: str, kind: str, file_path: str) -> int:
    init_db()
    ts = datetime.now(timezone.utc).isoformat()
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO downloads (url, title, kind, file_path, created_at) VALUES (?,?,?,?,?)",
            (url, title, kind, file_path, ts),
        )
        return int(cur.lastrowid)


def list_entries(limit: int = 50) -> list[dict[str, Any]]:
    init_db()
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM downloads ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]

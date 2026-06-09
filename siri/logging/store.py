"""SQLite interaction logger."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class InteractionLogger:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT
                )
                """
            )
            conn.commit()

    def log(self, role: str, content: str, metadata: dict[str, Any] | None = None) -> None:
        ts = datetime.now(timezone.utc).isoformat()
        meta = json.dumps(metadata or {})
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO interactions (timestamp, role, content, metadata) VALUES (?, ?, ?, ?)",
                (ts, role, content, meta),
            )
            conn.commit()

    def recent(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM interactions ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in reversed(rows)]

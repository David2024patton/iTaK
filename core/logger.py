"""
iTaK Structured Logger — 14 event types, dual storage (JSONL + SQLite), 24hr rotation.
Secret masking ensures API keys never appear in logs.
"""

import json
import sqlite3
import time
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class EventType(str, Enum):
    """14 structured event types for iTaK logging."""
    USER_MESSAGE = "user_message"
    AGENT_RESPONSE = "agent_response"
    AGENT_THOUGHTS = "agent_thoughts"
    TOOL_EXECUTION = "tool_execution"
    TOOL_RESULT = "tool_result"
    MEMORY_ACCESS = "memory_access"
    MEMORY_SAVE = "memory_save"
    ERROR = "error"
    CRITICAL_ERROR = "critical_error"
    WARNING = "warning"
    INTERVENTION = "intervention"
    EXTENSION_FIRED = "extension_fired"
    AGENT_COMPLETE = "agent_complete"
    SYSTEM = "system"


class Logger:
    """Dual-write logger: JSONL files + SQLite database.

    Features:
    - 14 structured event types
    - 24-hour log rotation (new file at midnight UTC)
    - Secret masking (API keys, tokens never appear)
    - SQLite for fast querying / cost tracking
    - JSONL for human-readable append-only logs
    """

    def __init__(self, config: dict):
        self.config = config
        self.level = config.get("level", "INFO")
        self.mask_secrets = config.get("mask_secrets", True)

        # Paths
        self.jsonl_dir = Path(config.get("jsonl_dir", "data/logs"))
        self.sqlite_path = Path(config.get("sqlite_path", "data/db/logs.db"))

        # Ensure directories exist
        self.jsonl_dir.mkdir(parents=True, exist_ok=True)
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)

        # Secrets to mask (populated by security module)
        self._secrets: list[str] = []

        # Current log file
        self._current_date: str = ""
        self._current_file = None

        # Initialize SQLite
        self._init_sqlite()

    def _init_sqlite(self):
        """Create the logs table if it doesn't exist."""
        try:
            conn = sqlite3.connect(str(self.sqlite_path))
            conn.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    datetime TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    room_id TEXT DEFAULT 'default',
                    adapter TEXT DEFAULT 'cli',
                    data TEXT,
                    tokens_used INTEGER DEFAULT 0,
                    cost_usd REAL DEFAULT 0.0
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_logs_event_type
                ON logs(event_type)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_logs_timestamp
                ON logs(timestamp)
            """)
            # FTS5 for full-text search on log data
            try:
                conn.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS logs_fts
                    USING fts5(data, content=logs, content_rowid=id)
                """)
            except sqlite3.OperationalError:
                pass  # FTS5 may not be available
            conn.commit()
            conn.close()
        except Exception:
            pass  # Don't crash if SQLite fails

    def register_secret(self, secret: str):
        """Register a secret value to be masked in all logs."""
        if secret and len(secret) > 3:
            self._secrets.append(secret)

    def _mask(self, text: str) -> str:
        """Mask all registered secrets in text."""
        if not self.mask_secrets:
            return text
        for secret in self._secrets:
            if secret in text:
                masked = secret[:3] + "***" + secret[-2:] if len(secret) > 5 else "***"
                text = text.replace(secret, masked)
        return text

    def _get_jsonl_path(self) -> Path:
        """Get the current JSONL log file path (24hr rotation)."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if today != self._current_date:
            self._current_date = today
            if self._current_file:
                self._current_file.close()
            self._current_file = None
        return self.jsonl_dir / f"{today}.jsonl"

    def log(
        self,
        event_type: EventType,
        data: Any = None,
        room_id: str = "default",
        adapter: str = "cli",
        tokens_used: int = 0,
        cost_usd: float = 0.0,
    ):
        """Write a structured log entry to both JSONL and SQLite."""
        now = time.time()
        dt = datetime.fromtimestamp(now, tz=timezone.utc).isoformat()

        # Serialize data
        if isinstance(data, str):
            data_str = self._mask(data)
        elif isinstance(data, dict):
            data_str = self._mask(json.dumps(data, default=str))
        else:
            data_str = self._mask(str(data)) if data else ""

        entry = {
            "timestamp": now,
            "datetime": dt,
            "event_type": event_type.value if isinstance(event_type, EventType) else event_type,
            "room_id": room_id,
            "adapter": adapter,
            "data": data_str,
            "tokens_used": tokens_used,
            "cost_usd": cost_usd,
        }

        # Write to JSONL
        self._write_jsonl(entry)

        # Write to SQLite
        self._write_sqlite(entry)

    def _write_jsonl(self, entry: dict):
        """Append entry to the current JSONL log file."""
        try:
            log_path = self._get_jsonl_path()
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, default=str) + "\n")
        except Exception:
            pass

    def _write_sqlite(self, entry: dict):
        """Insert entry into the SQLite logs table."""
        try:
            conn = sqlite3.connect(str(self.sqlite_path))
            conn.execute(
                """INSERT INTO logs
                   (timestamp, datetime, event_type, room_id, adapter, data, tokens_used, cost_usd)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    entry["timestamp"],
                    entry["datetime"],
                    entry["event_type"],
                    entry["room_id"],
                    entry["adapter"],
                    entry["data"],
                    entry["tokens_used"],
                    entry["cost_usd"],
                ),
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

    def query(
        self,
        event_type: Optional[str] = None,
        room_id: Optional[str] = None,
        limit: int = 50,
        search: Optional[str] = None,
    ) -> list[dict]:
        """Query logs from SQLite."""
        try:
            conn = sqlite3.connect(str(self.sqlite_path))
            conn.row_factory = sqlite3.Row

            conditions = []
            params = []

            if event_type:
                conditions.append("event_type = ?")
                params.append(event_type)
            if room_id:
                conditions.append("room_id = ?")
                params.append(room_id)
            if search:
                conditions.append("data LIKE ?")
                params.append(f"%{search}%")

            where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            query = f"SELECT * FROM logs {where} ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, params).fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except Exception:
            return []

    def get_cost_summary(self, days: int = 7) -> dict:
        """Get token usage and cost summary for the last N days."""
        try:
            cutoff = time.time() - (days * 86400)
            conn = sqlite3.connect(str(self.sqlite_path))
            row = conn.execute(
                """SELECT
                    SUM(tokens_used) as total_tokens,
                    SUM(cost_usd) as total_cost,
                    COUNT(*) as total_events
                   FROM logs WHERE timestamp > ?""",
                (cutoff,),
            ).fetchone()
            conn.close()
            return {
                "total_tokens": row[0] or 0,
                "total_cost": round(row[1] or 0, 4),
                "total_events": row[2] or 0,
                "period_days": days,
            }
        except Exception:
            return {"total_tokens": 0, "total_cost": 0, "total_events": 0, "period_days": days}

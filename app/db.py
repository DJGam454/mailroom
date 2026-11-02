"""SQLite helpers.

The whole app is local, so a small set of explicit SQL helpers is easier to
audit than an ORM. Every connection uses WAL and foreign keys.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from app import config

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def connect(path: Path | None = None) -> sqlite3.Connection:
    config.ensure_data_dirs()
    conn = sqlite3.connect(str(path or config.DB_PATH), timeout=15, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 15000")
    return conn


@contextmanager
def transaction(path: Path | None = None) -> Iterator[sqlite3.Connection]:
    conn = connect(path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(path: Path | None = None) -> None:
    config.ensure_data_dirs()
    conn = connect(path)
    try:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        columns = {row[1] for row in conn.execute("PRAGMA table_info(sheet_sync_state)")}
        if "content_hash" not in columns:
            conn.execute("ALTER TABLE sheet_sync_state ADD COLUMN content_hash TEXT")
        # Auto-send is not implemented. Keep every campaign on manual approval
        # so an old row can never imply a bypass of the human step.
        conn.execute("UPDATE campaigns SET approval_mode = 'manual' WHERE approval_mode != 'manual'")
        conn.execute("DELETE FROM settings WHERE key = 'transport_mode'")
        defaults = {
            "require_dns_pass": "0",
            "sending_paused": "0",
            "agent_webhook": "",
            "sender_name": "Alex Morgan",
            "sender_title": "Founder",
            "sender_company": "Dynamisers",
            "default_timezone": "Asia/Kolkata",
            "default_offer": "a short video and website audit",
            "warmup_enabled": "1",
            "warmup_daily_limit": "10",
            "warmup_domain_daily_limit": "50",
            "warmup_pair_cooldown_days": "7",
            "warmup_reply_rate": "0.30",
            "warmup_open_rate": "0.80",
            "warmup_important_rate": "0.30",
            "warmup_min_gap_seconds": "5",
            "warmup_max_gap_seconds": "30",
            "warmup_window_start": "00:00",
            "warmup_window_end": "23:59",
            "warmup_weekdays_only": "0",
            "warmup_max_sends_per_tick": "10",
            "warmup_ramp": "2,2,2,4,4,4,4,6,6,6,6,6,6,6,10,10,10,10,10,10,10,15,15,15,15,15,15,15,15,15",
            "google_sheets_spreadsheet_id": "",
            "google_sheets_credentials_enc": "",
            "google_sheets_conflict_policy": "merge",
            "google_sheets_last_sync_at": "",
        }
        for key, value in defaults.items():
            conn.execute(
                "INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)",
                (key, value),
            )
        conn.execute(
            "INSERT OR IGNORE INTO warmup_profiles(mailbox_id, enabled, status, daily_limit) "
            "SELECT id, 0, 'off', 10 FROM mailboxes"
        )
        conn.commit()
    finally:
        conn.close()


def rows(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    return [dict(row) for row in conn.execute(sql, params).fetchall()]


def one(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    row = conn.execute(sql, params).fetchone()
    return dict(row) if row else None


def setting(conn: sqlite3.Connection, key: str, default: str = "") -> str:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return str(row["value"]) if row else default


def set_setting(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO settings(key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )


def settings_dict(conn: sqlite3.Connection) -> dict[str, str]:
    return {row["key"]: row["value"] for row in conn.execute("SELECT key, value FROM settings")}


def audit(
    conn: sqlite3.Connection,
    kind: str,
    entity_type: str = "",
    entity_id: str | int = "",
    detail: str | dict[str, Any] = "",
) -> None:
    if not isinstance(detail, str):
        detail = json.dumps(detail, separators=(",", ":"))
    conn.execute(
        "INSERT INTO activity(kind, entity_type, entity_id, detail, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (kind, entity_type, str(entity_id), detail, now_iso()),
    )

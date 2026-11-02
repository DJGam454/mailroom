"""Runtime configuration for Mailroom."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("MAILROOM_DATA_DIR", ROOT / "data"))
DB_PATH = Path(os.getenv("MAILROOM_DB", DATA_DIR / "mailroom.db"))
OUTBOX_DIR = DATA_DIR / "outbox"
WARMUP_OUTBOX_DIR = DATA_DIR / "warmup_outbox"
SECRET_KEY_FILE = DATA_DIR / "secret.key"

HOST = os.getenv("MAILROOM_HOST", "127.0.0.1")
PORT = int(os.getenv("MAILROOM_PORT", "4600"))
WORKER_ENABLED = os.getenv("MAILROOM_WORKER", "1").lower() not in {"0", "false", "no"}
WORKER_INTERVAL = float(os.getenv("MAILROOM_WORKER_INTERVAL", "2"))
WARMUP_WORKER_ENABLED = os.getenv("MAILROOM_WARMUP_WORKER", "1").lower() not in {"0", "false", "no"}
WARMUP_WORKER_INTERVAL = float(os.getenv("MAILROOM_WARMUP_INTERVAL", "5"))
APP_VERSION = "0.3.2"


def ensure_data_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
    WARMUP_OUTBOX_DIR.mkdir(parents=True, exist_ok=True)

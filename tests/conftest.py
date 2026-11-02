from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("MAILROOM_WORKER", "0")
os.environ.setdefault("MAILROOM_AUTO_SEED", "0")

from app import config, db  # noqa: E402
from app.seed import seed_demo  # noqa: E402


@pytest.fixture()
def app_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "mailroom.db")
    monkeypatch.setattr(config, "OUTBOX_DIR", tmp_path / "outbox")
    monkeypatch.setattr(config, "SECRET_KEY_FILE", tmp_path / "secret.key")
    db.init_db()
    return tmp_path


@pytest.fixture()
def conn(app_paths):
    connection = db.connect()
    try:
        yield connection
    finally:
        connection.close()


@pytest.fixture()
def seeded(app_paths):
    seed_demo()
    connection = db.connect()
    try:
        yield connection
    finally:
        connection.close()

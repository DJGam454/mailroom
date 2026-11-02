"""Local credential encryption.

The key never leaves the machine. It is created with mode 0600 under data/.
Set MAILROOM_SECRET_KEY to provide a key from a password manager instead.
"""

from __future__ import annotations

import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from app import config


def _load_key() -> bytes:
    env_key = os.getenv("MAILROOM_SECRET_KEY", "").strip()
    if env_key:
        return env_key.encode("utf-8")

    path: Path = config.SECRET_KEY_FILE
    if path.exists():
        return path.read_bytes().strip()

    config.ensure_data_dirs()
    key = Fernet.generate_key()
    path.write_bytes(key)
    path.chmod(0o600)
    return key


def encrypt(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    return Fernet(_load_key()).encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    try:
        return Fernet(_load_key()).decrypt(value.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Could not decrypt a stored credential. Check MAILROOM_SECRET_KEY.") from exc

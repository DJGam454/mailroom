"""Suppression list routes."""

from __future__ import annotations

import re
from typing import Any

from fastapi import APIRouter, HTTPException

from app.deps import Conn
from app.schemas import SuppressionCreate
from app import db

router = APIRouter(prefix="/api/suppression", tags=["suppression"])
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@router.get("")
def list_suppression(conn=Conn) -> dict[str, Any]:
    items = db.rows(conn, "SELECT * FROM suppression ORDER BY created_at DESC, email")
    return {"items": items}


@router.post("")
def add_suppression(payload: SuppressionCreate, conn=Conn) -> dict[str, Any]:
    email = payload.email.strip().lower()
    if not EMAIL_RE.match(email):
        raise HTTPException(status_code=400, detail="Enter a valid email address.")
    with conn:
        conn.execute(
            "INSERT INTO suppression(email, reason, created_at) VALUES (?, ?, ?) "
            "ON CONFLICT(email) DO UPDATE SET reason = excluded.reason",
            (email, payload.reason.strip() or "Added by operator", db.now_iso()),
        )
        db.audit(conn, "suppression_added", "suppression", email, {"reason": payload.reason.strip()})
    return {"ok": True, "item": db.one(conn, "SELECT * FROM suppression WHERE email = ?", (email,))}


@router.delete("/{email}")
def remove_suppression(email: str, conn=Conn) -> dict[str, Any]:
    with conn:
        deleted = conn.execute("DELETE FROM suppression WHERE email = ?", (email.strip().lower(),)).rowcount
        db.audit(conn, "suppression_removed", "suppression", email, {"deleted": deleted})
    return {"ok": True, "deleted": deleted}

"""Suppression list routes."""

from __future__ import annotations

import re
from typing import Any

from fastapi import APIRouter, HTTPException

from app import db
from app.deps import Conn
from app.schemas import SuppressionCreate
from app.services import suppression

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
        result = suppression.add(conn, email, payload.reason)
    return {"ok": True, "item": db.one(conn, "SELECT * FROM suppression WHERE email = ?", (email,)), **result}


@router.delete("/{email}")
def remove_suppression(email: str, conn=Conn) -> dict[str, Any]:
    with conn:
        deleted = conn.execute("DELETE FROM suppression WHERE email = ?", (email.strip().lower(),)).rowcount
        db.audit(conn, "suppression_removed", "suppression", email, {"deleted": deleted})
    return {"ok": True, "deleted": deleted}

"""App settings routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app import db
from app.deps import Conn
from app.schemas import SettingsUpdate

router = APIRouter(prefix="/api", tags=["settings"])

ALLOWED = {
    "transport_mode",
    "require_dns_pass",
    "sending_paused",
    "agent_webhook",
    "sender_name",
    "sender_title",
    "sender_company",
    "default_timezone",
    "default_offer",
}


@router.get("/settings")
def get_settings(conn=Conn) -> dict[str, Any]:
    return {"values": db.settings_dict(conn)}


@router.patch("/settings")
def update_settings(payload: SettingsUpdate, conn=Conn) -> dict[str, Any]:
    unknown = set(payload.values) - ALLOWED
    if unknown:
        raise HTTPException(status_code=400, detail=f"Unknown settings: {sorted(unknown)}")
    with conn:
        for key, value in payload.values.items():
            db.set_setting(conn, key, str(value))
        db.audit(conn, "settings_updated", "settings", "", payload.values)
    return {"ok": True, "values": db.settings_dict(conn)}

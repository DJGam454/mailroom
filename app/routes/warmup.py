"""Warmup control routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.deps import Conn
from app.schemas import WarmupAction, WarmupSettingsUpdate, WarmupStart
from app.services import warmup

router = APIRouter(prefix="/api", tags=["warmup"])


@router.get("/warmup")
def warmup_status(conn=Conn) -> dict[str, Any]:
    with conn:
        return warmup.status(conn)


@router.post("/warmup/start")
def start(payload: WarmupStart, conn=Conn) -> dict[str, Any]:
    with conn:
        result = warmup.start(conn, payload.mailbox_ids, payload.daily_limit)
    tick = warmup.tick()
    return {"ok": True, **result, "tick": tick}


@router.post("/warmup/pause")
def pause(payload: WarmupAction, conn=Conn) -> dict[str, Any]:
    with conn:
        result = warmup.set_status(conn, "paused", payload.mailbox_ids)
    return result


@router.post("/warmup/resume")
def resume(payload: WarmupAction, conn=Conn) -> dict[str, Any]:
    with conn:
        result = warmup.set_status(conn, "ramping", payload.mailbox_ids)
    return result


@router.post("/warmup/stop")
def stop(payload: WarmupAction, conn=Conn) -> dict[str, Any]:
    with conn:
        result = warmup.set_status(conn, "off", payload.mailbox_ids)
    return result


@router.patch("/warmup/settings")
def settings(payload: WarmupSettingsUpdate, conn=Conn) -> dict[str, Any]:
    with conn:
        warmup.update_settings(conn, payload.values)
    return {"ok": True, "settings": warmup._settings(conn)}  # noqa: SLF001


@router.post("/warmup/tick")
def tick() -> dict[str, Any]:
    return warmup.tick()

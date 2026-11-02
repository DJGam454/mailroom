"""Google Sheets sync routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.deps import Conn
from app.schemas import SheetsConfigure, SheetsSyncRequest
from app.services import sheets

router = APIRouter(prefix="/api/sheets", tags=["sheets"])


@router.get("/status")
def sheet_status(conn=Conn) -> dict[str, Any]:
    return sheets.status(conn)


@router.post("/configure")
def configure(payload: SheetsConfigure, conn=Conn) -> dict[str, Any]:
    try:
        with conn:
            result = sheets.configure(conn, payload.spreadsheet_id, payload.credentials_json, payload.conflict_policy)
    except sheets.SheetsError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, **result}


@router.post("/test")
def test(conn=Conn) -> dict[str, Any]:
    try:
        with conn:
            result = sheets.test(conn)
    except sheets.SheetsError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result


@router.post("/sync")
def sync(payload: SheetsSyncRequest, conn=Conn) -> dict[str, Any]:
    try:
        with conn:
            result = sheets.sync(conn, payload.direction, payload.dry_run)
    except sheets.SheetsError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result

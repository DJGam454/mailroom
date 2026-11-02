"""Activity log routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from app import db
from app.deps import Conn

router = APIRouter(prefix="/api", tags=["activity"])


@router.get("/activity")
def activity(
    conn=Conn,
    kind: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> dict[str, Any]:
    if kind:
        items = db.rows(
            conn,
            "SELECT * FROM activity WHERE kind = ? ORDER BY id DESC LIMIT ?",
            (kind, limit),
        )
    else:
        items = db.rows(conn, "SELECT * FROM activity ORDER BY id DESC LIMIT ?", (limit,))
    return {"items": items}

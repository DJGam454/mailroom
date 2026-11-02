"""Send queue routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app import db
from app.deps import Conn
from app.services import worker

router = APIRouter(prefix="/api", tags=["queue"])


@router.get("/queue")
def list_queue(
    conn=Conn,
    campaign_id: int | None = None,
    status: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> dict[str, Any]:
    clauses = []
    params: list[Any] = []
    if campaign_id:
        clauses.append("q.campaign_id = ?")
        params.append(campaign_id)
    if status:
        clauses.append("q.status = ?")
        params.append(status)
    else:
        clauses.append("q.status IN ('queued', 'leased', 'failed')")
    where = "WHERE " + " AND ".join(clauses)
    order = "DESC" if status == "sent" else "ASC"
    items = db.rows(
        conn,
        f"""
        SELECT q.*, d.subject, d.body, d.status AS draft_status,
               l.name, l.email, l.company, l.role, l.industry,
               m.email AS mailbox_email, c.name AS campaign_name
        FROM send_queue q
        JOIN drafts d ON d.id = q.draft_id
        JOIN leads l ON l.id = q.lead_id
        JOIN mailboxes m ON m.id = q.mailbox_id
        JOIN campaigns c ON c.id = q.campaign_id
        {where}
        ORDER BY q.scheduled_at {order}, q.id {order}
        LIMIT ?
        """,
        (*params, limit),
    )
    count_where = "WHERE campaign_id = ?" if campaign_id else ""
    count_params = (campaign_id,) if campaign_id else ()
    counts = db.one(
        conn,
        f"""
        SELECT
          SUM(CASE WHEN status = 'queued' THEN 1 ELSE 0 END) AS queued,
          SUM(CASE WHEN status = 'leased' THEN 1 ELSE 0 END) AS leased,
          SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) AS sent,
          SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed
        FROM send_queue
        {count_where}
        """,
        count_params,
    )
    return {"items": items, "counts": counts or {}}


@router.post("/queue/{queue_id}/send-now")
def send_now(queue_id: int) -> dict[str, Any]:
    result = worker.send_now(queue_id)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error") or "Could not send")
    return result


@router.post("/queue/{queue_id}/cancel")
def cancel(queue_id: int) -> dict[str, Any]:
    result = worker.cancel(queue_id)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error") or "Could not cancel")
    return result


@router.post("/queue/tick")
def tick() -> dict[str, Any]:
    return worker.tick()

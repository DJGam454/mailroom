"""Approval queue routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app import db
from app.deps import Conn
from app.schemas import ApproveRequest, BulkRequest, DenyRequest, DraftUpdate
from app.services import approvals as approval_service
from app.services import drafting, rotation

router = APIRouter(prefix="/api", tags=["approvals"])


@router.get("/approvals")
def pending_approvals(
    conn=Conn,
    campaign_id: int | None = None,
    q: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
) -> dict[str, Any]:
    where = "WHERE d.status = 'pending'"
    params: list[Any] = []
    if campaign_id:
        where += " AND d.campaign_id = ?"
        params.append(campaign_id)
    if q and q.strip():
        escaped = q.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        like = f"%{escaped}%"
        where += (
            " AND (l.name LIKE ? ESCAPE '\\' OR l.email LIKE ? ESCAPE '\\' "
            "OR l.company LIKE ? ESCAPE '\\' OR l.role LIKE ? ESCAPE '\\')"
        )
        params.extend([like, like, like, like])
    total_row = db.one(
        conn,
        f"SELECT COUNT(*) AS count FROM drafts d JOIN leads l ON l.id = d.lead_id {where}",
        tuple(params),
    )
    total = int(total_row["count"]) if total_row else 0
    offset = (page - 1) * page_size
    items = db.rows(
        conn,
        f"""
        SELECT d.id AS draft_id, d.subject, d.body, d.step_no, d.created_at AS draft_created_at,
               l.id AS lead_id, l.name, l.email, l.role, l.company, l.industry, l.city,
               l.website, l.notes, l.offer, l.email_grade, l.verification, l.source,
               c.id AS campaign_id, c.name AS campaign_name, c.approval_mode
        FROM drafts d
        JOIN leads l ON l.id = d.lead_id
        JOIN campaigns c ON c.id = d.campaign_id
        {where}
        ORDER BY d.id DESC
        LIMIT ? OFFSET ?
        """,
        (*params, page_size, offset),
    )
    pools: dict[int, dict[str, Any]] = {}
    for item in items:
        cid = item["campaign_id"]
        if cid in pools:
            continue
        campaign = db.one(conn, "SELECT * FROM campaigns WHERE id = ?", (cid,))
        if not campaign:
            pools[cid] = {"count": 0, "suggested": None}
            continue
        eligible = rotation.eligible_mailboxes(conn, campaign)
        suggested = rotation.pick_mailbox(conn, campaign)
        pools[cid] = {
            "count": len(eligible),
            "suggested": suggested["email"] if suggested else None,
        }
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max(1, (total + page_size - 1) // page_size),
        "pools": pools,
    }


@router.post("/approvals/{draft_id}/approve")
def approve(draft_id: int, payload: ApproveRequest, conn=Conn) -> dict[str, Any]:
    try:
        with conn:
            result = approval_service.approve_draft(conn, draft_id, payload.mailbox_id)
    except approval_service.ApprovalError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, **result}


@router.post("/approvals/{draft_id}/deny")
def deny(draft_id: int, payload: DenyRequest, conn=Conn) -> dict[str, Any]:
    try:
        with conn:
            result = approval_service.deny_draft(conn, draft_id, payload.reason, payload.suppress)
    except approval_service.ApprovalError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, **result}


@router.post("/approvals/bulk")
def bulk(payload: BulkRequest, conn=Conn) -> dict[str, Any]:
    try:
        with conn:
            result = approval_service.bulk_action(
                conn,
                payload.draft_ids,
                payload.action,
                payload.reason,
                payload.suppress,
            )
    except approval_service.ApprovalError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, **result}


@router.post("/drafts/{draft_id}/agent")
def agent_draft(draft_id: int, conn=Conn) -> dict[str, Any]:
    with conn:
        draft, error = drafting.agent_redraft(conn, draft_id)
    if error:
        status_code = 404 if error == "Draft not found" else 400
        raise HTTPException(status_code=status_code, detail=error)
    return {"ok": True, "draft": draft}


@router.patch("/drafts/{draft_id}")
def edit_draft(draft_id: int, payload: DraftUpdate, conn=Conn) -> dict[str, Any]:
    try:
        with conn:
            draft = approval_service.edit_draft(conn, draft_id, payload.subject, payload.body)
    except approval_service.ApprovalError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "draft": draft}

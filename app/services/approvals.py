"""Approval state transitions."""

from __future__ import annotations

from typing import Any

from app import db
from app.services import rotation, suppression


class ApprovalError(Exception):
    pass


def approve_draft(
    conn,
    draft_id: int,
    mailbox_id: int | None = None,
) -> dict[str, Any]:
    draft = db.one(conn, "SELECT * FROM drafts WHERE id = ?", (draft_id,))
    if not draft:
        raise ApprovalError("Draft not found")
    if draft["status"] != "pending":
        raise ApprovalError(f"Draft is already {draft['status']}")

    lead = db.one(conn, "SELECT * FROM leads WHERE id = ?", (draft["lead_id"],))
    if not lead:
        raise ApprovalError("Lead not found")
    if lead["status"] in {"denied", "suppressed", "sent", "replied", "bounced"}:
        raise ApprovalError(f"Lead is {lead['status']} and cannot be approved")

    try:
        result = rotation.schedule_draft(conn, draft_id, mailbox_id)
    except rotation.NoMailboxAvailable as exc:
        raise ApprovalError(str(exc)) from exc

    db.audit(
        conn,
        "draft_approved",
        "draft",
        draft_id,
        {
            "lead_id": lead["id"],
            "lead_email": lead["email"],
            "mailbox": result["mailbox"]["email"],
            "scheduled_at": result["queue"]["scheduled_at"],
        },
    )
    return result


def deny_draft(
    conn,
    draft_id: int,
    reason: str = "",
    suppress: bool = False,
) -> dict[str, Any]:
    draft = db.one(conn, "SELECT * FROM drafts WHERE id = ?", (draft_id,))
    if not draft:
        raise ApprovalError("Draft not found")
    if draft["status"] not in {"pending", "denied"}:
        raise ApprovalError(f"Draft is already {draft['status']}")

    lead = db.one(conn, "SELECT * FROM leads WHERE id = ?", (draft["lead_id"],))
    if not lead:
        raise ApprovalError("Lead not found")

    now = db.now_iso()
    if suppress:
        suppression.add(conn, lead["email"], reason.strip() or "operator denied")
    conn.execute(
        "UPDATE drafts SET status = 'denied', denied_at = ?, deny_reason = ?, updated_at = ? WHERE id = ?",
        (now, reason.strip(), now, draft_id),
    )
    conn.execute(
        "UPDATE leads SET status = ?, updated_at = ? WHERE id = ?",
        ("suppressed" if suppress else "denied", now, lead["id"]),
    )
    db.audit(
        conn,
        "draft_denied",
        "draft",
        draft_id,
        {
            "lead_id": lead["id"],
            "reason": reason.strip(),
            "suppressed": suppress,
        },
    )
    return {
        "draft": db.one(conn, "SELECT * FROM drafts WHERE id = ?", (draft_id,)),
        "lead": db.one(conn, "SELECT * FROM leads WHERE id = ?", (lead["id"],)),
    }


def edit_draft(conn, draft_id: int, subject: str, body: str) -> dict[str, Any]:
    draft = db.one(conn, "SELECT * FROM drafts WHERE id = ?", (draft_id,))
    if not draft:
        raise ApprovalError("Draft not found")
    if draft["status"] != "pending":
        raise ApprovalError("Only pending drafts can be edited. A denied draft is terminal.")
    subject = subject.strip()
    body = body.strip()
    if not subject or not body:
        raise ApprovalError("Subject and body cannot be empty")
    now = db.now_iso()
    conn.execute(
        "UPDATE drafts SET subject = ?, body = ?, status = 'pending', denied_at = NULL, "
        "deny_reason = NULL, updated_at = ? WHERE id = ?",
        (subject, body, now, draft_id),
    )
    conn.execute(
        "UPDATE leads SET status = 'pending_approval', updated_at = ? WHERE id = ?",
        (now, draft["lead_id"]),
    )
    db.audit(conn, "draft_edited", "draft", draft_id, {"lead_id": draft["lead_id"]})
    return db.one(conn, "SELECT * FROM drafts WHERE id = ?", (draft_id,))


def bulk_action(
    conn,
    draft_ids: list[int],
    action: str,
    reason: str = "",
    suppress: bool = False,
) -> dict[str, Any]:
    approved: list[dict[str, Any]] = []
    denied: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for draft_id in draft_ids:
        try:
            if action == "approve":
                approved.append(approve_draft(conn, draft_id))
            elif action == "deny":
                denied.append(deny_draft(conn, draft_id, reason, suppress))
            else:
                raise ApprovalError("Unknown action")
        except ApprovalError as exc:
            errors.append({"id": draft_id, "error": str(exc)})
    return {"approved": approved, "denied": denied, "errors": errors}

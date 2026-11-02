"""Suppression list and the automatic stop of pending work.

Adding an address is a safety action, not just a list edit. It must deny any
pending draft, cancel queued sends and mark the affected leads suppressed so a
stale approval cannot go out later.
"""

from __future__ import annotations

from typing import Any

from app import db


def add(conn, email: str, reason: str) -> dict[str, Any]:
    email = email.strip().lower()
    reason = reason.strip() or "Added by operator"
    now = db.now_iso()
    conn.execute(
        "INSERT INTO suppression(email, reason, created_at) VALUES (?, ?, ?) "
        "ON CONFLICT(email) DO UPDATE SET reason = excluded.reason",
        (email, reason, now),
    )
    leads = db.rows(
        conn,
        "SELECT id FROM leads WHERE lower(email) = ? "
        "AND status NOT IN ('sent', 'replied', 'bounced', 'denied')",
        (email,),
    )
    lead_ids = [row["id"] for row in leads]
    drafts_denied = 0
    queue_cancelled = 0
    if lead_ids:
        placeholders = ",".join("?" for _ in lead_ids)
        queue_cancelled = conn.execute(
            f"UPDATE send_queue SET status = 'cancelled', last_error = ?, updated_at = ? "
            f"WHERE lead_id IN ({placeholders}) AND status IN ('queued', 'leased')",
            (f"Suppressed: {reason}", now, *lead_ids),
        ).rowcount
        drafts_denied = conn.execute(
            f"UPDATE drafts SET status = 'denied', denied_at = ?, deny_reason = ?, updated_at = ? "
            f"WHERE lead_id IN ({placeholders}) AND status IN ('pending', 'approved', 'queued')",
            (now, f"Suppressed: {reason}", now, *lead_ids),
        ).rowcount
        conn.execute(
            f"UPDATE leads SET status = 'suppressed', updated_at = ? WHERE id IN ({placeholders})",
            (now, *lead_ids),
        )
    result = {
        "email": email,
        "reason": reason,
        "drafts_denied": drafts_denied,
        "queue_cancelled": queue_cancelled,
        "leads_suppressed": len(lead_ids),
    }
    db.audit(conn, "suppression_added", "suppression", email, result)
    return result

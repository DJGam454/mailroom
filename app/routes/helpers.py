"""Small serialization helpers shared by routers."""

from __future__ import annotations

import json
from typing import Any

from app import db


def campaign_with_counts(conn, campaign_id: int) -> dict[str, Any] | None:
    return db.one(
        conn,
        """
        SELECT c.*,
               (SELECT COUNT(*) FROM leads l WHERE l.campaign_id = c.id) AS lead_count,
               (SELECT COUNT(*) FROM drafts d WHERE d.campaign_id = c.id AND d.status = 'pending') AS pending_count,
               (SELECT COUNT(*) FROM drafts d WHERE d.campaign_id = c.id AND d.status = 'sent') AS sent_count,
               (SELECT COUNT(*) FROM send_queue q WHERE q.campaign_id = c.id AND q.status IN ('queued', 'leased')) AS queued_count,
               (SELECT COUNT(DISTINCT cm.mailbox_id) FROM campaign_mailboxes cm WHERE cm.campaign_id = c.id AND cm.enabled = 1) AS mailbox_count,
               (SELECT COUNT(*) FROM messages msg
                 WHERE msg.campaign_id = c.id
                   AND date(msg.sent_at, 'localtime') = date('now', 'localtime')) AS sent_today
        FROM campaigns c
        WHERE c.id = ?
        """,
        (campaign_id,),
    )


def mailbox_public(row: dict[str, Any]) -> dict[str, Any]:
    data = dict(row)
    data["has_smtp_password"] = bool(data.pop("smtp_password_enc", None))
    data["has_imap_password"] = bool(data.pop("imap_password_enc", None))
    data["has_gas_secret"] = bool(data.pop("gas_secret_enc", None))
    return data


def json_list(value: str | None, fallback: list[int] | None = None) -> list[int]:
    try:
        parsed = json.loads(value or "[]")
        return [int(item) for item in parsed]
    except (ValueError, TypeError, json.JSONDecodeError):
        return fallback or []

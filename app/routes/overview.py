"""Dashboard overview."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app import db
from app.deps import Conn
from app.routes.helpers import campaign_with_counts

router = APIRouter(prefix="/api", tags=["overview"])


@router.get("/overview")
def overview(conn=Conn) -> dict[str, Any]:
    stats = db.one(
        conn,
        """
        SELECT
          (SELECT COUNT(*) FROM leads) AS lead_count,
          (SELECT COUNT(*) FROM drafts WHERE status = 'pending') AS pending_count,
          (SELECT COUNT(*) FROM send_queue WHERE status IN ('queued', 'leased')) AS queued_count,
          (SELECT COUNT(*) FROM messages WHERE status = 'sent' AND date(sent_at) = date('now')) AS sent_today,
          (SELECT COUNT(*) FROM messages WHERE status = 'sent') AS sent_total,
          (SELECT COUNT(*) FROM campaigns WHERE status = 'active') AS active_campaigns,
          (SELECT COUNT(*) FROM mailboxes WHERE status = 'active') AS active_mailboxes,
          (SELECT COUNT(*) FROM domains WHERE status = 'active') AS active_domains,
          (SELECT COUNT(*) FROM suppression) AS suppressed,
          (SELECT COUNT(*) FROM send_queue WHERE status = 'failed') AS failed_queue,
          (SELECT COUNT(*) FROM warmup_profiles WHERE enabled = 1 AND status IN ('ramping', 'active')) AS warmup_active,
          (SELECT COUNT(*) FROM warmup_messages WHERE kind = 'initial' AND date(sent_at) = date('now')) AS warmup_sent_today,
          (SELECT COUNT(*) FROM warmup_messages WHERE kind = 'reply' AND date(sent_at) = date('now')) AS warmup_replies_today
        """,
    ) or {}

    campaign_ids = db.rows(conn, "SELECT id FROM campaigns ORDER BY id DESC")
    campaigns = [campaign_with_counts(conn, row["id"]) for row in campaign_ids]

    mailbox_health = db.rows(
        conn,
        """
        SELECT m.id, m.email, m.display_name, m.daily_limit, m.hourly_limit, m.status, m.transport,
               d.name AS domain_name, COALESCE(u.sent, 0) AS sent_today,
               (SELECT COUNT(*) FROM messages msg
                 WHERE msg.mailbox_id = m.id AND msg.sent_at >= datetime('now', '-1 hour')) AS sent_hour
        FROM mailboxes m
        JOIN domains d ON d.id = m.domain_id
        LEFT JOIN mailbox_usage_daily u ON u.mailbox_id = m.id AND u.date = date('now')
        ORDER BY u.sent DESC, m.id
        LIMIT 8
        """,
    )

    queue_preview = db.rows(
        conn,
        """
        SELECT q.id, q.scheduled_at, q.status, m.email AS mailbox_email,
               l.name, l.company, l.email, c.name AS campaign_name
        FROM send_queue q
        JOIN mailboxes m ON m.id = q.mailbox_id
        JOIN leads l ON l.id = q.lead_id
        JOIN campaigns c ON c.id = q.campaign_id
        WHERE q.status IN ('queued', 'leased')
        ORDER BY q.scheduled_at ASC
        LIMIT 8
        """,
    )

    activity = db.rows(conn, "SELECT * FROM activity ORDER BY id DESC LIMIT 10")

    daily = db.rows(
        conn,
        """
        SELECT date, SUM(sent) AS sent, SUM(failed) AS failed
        FROM mailbox_usage_daily
        WHERE date >= date('now', '-6 days')
        GROUP BY date
        ORDER BY date
        """,
    )

    transport = db.one(
        conn,
        """
        SELECT
          SUM(CASE WHEN transport = 'mock' THEN 1 ELSE 0 END) AS mock,
          SUM(CASE WHEN transport = 'smtp' THEN 1 ELSE 0 END) AS smtp,
          SUM(CASE WHEN transport = 'gas' THEN 1 ELSE 0 END) AS gas
        FROM mailboxes
        """,
    ) or {"mock": 0, "smtp": 0, "gas": 0}

    return {
        "stats": stats,
        "campaigns": campaigns,
        "mailbox_health": mailbox_health,
        "queue_preview": queue_preview,
        "activity": activity,
        "daily": daily,
        "transport": transport,
        "mock_only": int(transport.get("smtp") or 0) == 0 and int(transport.get("gas") or 0) == 0,
    }

"""Deliverability counters and DNS state."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app import db
from app.deps import Conn

router = APIRouter(prefix="/api", tags=["deliverability"])


@router.get("/deliverability")
def deliverability(conn=Conn) -> dict[str, Any]:
    domains = db.rows(
        conn,
        """
        SELECT d.*, COUNT(m.id) AS mailbox_count,
               COALESCE(SUM(u.sent), 0) AS sent_today,
               (SELECT COUNT(*) FROM warmup_messages wm
                 JOIN mailboxes wm_m ON wm_m.id = wm.mailbox_id
                WHERE wm_m.domain_id = d.id AND wm.kind = 'initial'
                  AND date(wm.sent_at, 'localtime') = date('now', 'localtime')) AS warmup_sent_today,
               COALESCE(SUM(m.daily_limit), 0) AS daily_capacity
        FROM domains d
        LEFT JOIN mailboxes m ON m.domain_id = d.id
        LEFT JOIN mailbox_usage_daily u ON u.mailbox_id = m.id AND u.date = date('now', 'localtime')
        GROUP BY d.id
        ORDER BY d.name
        """,
    )
    mailboxes = db.rows(
        conn,
        """
        SELECT m.id, m.email, m.display_name, m.daily_limit, m.hourly_limit, m.status, m.transport,
               d.name AS domain_name,
               COALESCE(u.sent, 0) AS sent_today,
               (SELECT COUNT(*) FROM warmup_messages wm
                 WHERE wm.mailbox_id = m.id AND wm.kind = 'initial'
                   AND date(wm.sent_at, 'localtime') = date('now', 'localtime')) AS warmup_sent_today,
               COALESCE(u.failed, 0) AS failed_today,
               COALESCE(u.bounces, 0) AS bounces_today,
               (SELECT COUNT(*) FROM messages msg
                 WHERE msg.mailbox_id = m.id AND msg.sent_at >= datetime('now', '-1 hour')) AS sent_hour
        FROM mailboxes m
        JOIN domains d ON d.id = m.domain_id
        LEFT JOIN mailbox_usage_daily u ON u.mailbox_id = m.id AND u.date = date('now', 'localtime')
        ORDER BY d.name, m.email
        """,
    )
    campaigns = db.rows(
        conn,
        """
        SELECT c.id, c.name, c.daily_limit, c.per_domain_limit, c.status,
               (SELECT COUNT(*) FROM messages msg
                 WHERE msg.campaign_id = c.id AND date(msg.sent_at, 'localtime') = date('now', 'localtime')) AS sent_today,
               (SELECT COUNT(*) FROM leads l WHERE l.campaign_id = c.id AND l.status = 'sent') AS total_sent,
               (SELECT COUNT(*) FROM leads l WHERE l.campaign_id = c.id) AS total_leads
        FROM campaigns c
        ORDER BY c.id DESC
        """,
    )
    daily = db.rows(
        conn,
        """
        SELECT date, SUM(sent) AS sent, SUM(failed) AS failed, SUM(bounces) AS bounces
        FROM mailbox_usage_daily
        WHERE date >= date('now', '-6 days', 'localtime')
        GROUP BY date
        ORDER BY date
        """,
    )
    return {
        "domains": domains,
        "mailboxes": mailboxes,
        "campaigns": campaigns,
        "daily": daily,
    }

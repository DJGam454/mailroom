"""Domain and mailbox connection routes."""

from __future__ import annotations

import re
import sqlite3
from typing import Any

from fastapi import APIRouter, HTTPException

from app import crypto, db
from app.deps import Conn
from app.routes.helpers import mailbox_public
from app.schemas import DomainCreate, DomainUpdate, MailboxCreate, MailboxUpdate
from app.services import dnscheck, sender

router = APIRouter(prefix="/api", tags=["mailboxes"])

DOMAIN_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _mailbox_rows(conn) -> list[dict[str, Any]]:
    rows = db.rows(
        conn,
        """
        SELECT m.*, d.name AS domain_name, d.status AS domain_status,
               COALESCE(u.sent, 0) AS sent_today,
               (SELECT COUNT(*) FROM warmup_messages wm
                 WHERE wm.mailbox_id = m.id AND wm.kind IN ('initial', 'reply')
                   AND date(wm.sent_at, 'localtime') = date('now', 'localtime')) AS warmup_sent_today,
               (SELECT COUNT(*) FROM messages msg
                 WHERE msg.mailbox_id = m.id AND msg.sent_at >= datetime('now', '-1 hour')) AS sent_hour,
               (SELECT group_concat(c.name, ', ')
                  FROM campaign_mailboxes cm
                  JOIN campaigns c ON c.id = cm.campaign_id
                 WHERE cm.mailbox_id = m.id AND cm.enabled = 1) AS campaigns,
               (SELECT group_concat(c.id)
                  FROM campaign_mailboxes cm
                  JOIN campaigns c ON c.id = cm.campaign_id
                 WHERE cm.mailbox_id = m.id AND cm.enabled = 1) AS campaign_ids_csv
        FROM mailboxes m
        JOIN domains d ON d.id = m.domain_id
        LEFT JOIN mailbox_usage_daily u ON u.mailbox_id = m.id AND u.date = date('now', 'localtime')
        ORDER BY m.id
        """,
    )
    items = []
    for row in rows:
        item = mailbox_public(row)
        raw_ids = str(item.pop("campaign_ids_csv", "") or "")
        item["campaign_ids"] = sorted(int(value) for value in raw_ids.split(",") if value.strip().isdigit())
        item["combined_sent_today"] = int(item.get("sent_today") or 0) + int(item.get("warmup_sent_today") or 0)
        items.append(item)
    return items


@router.get("/mailboxes")
def list_mailboxes(conn=Conn) -> dict[str, Any]:
    return {"items": _mailbox_rows(conn)}


@router.post("/mailboxes")
def create_mailbox(payload: MailboxCreate, conn=Conn) -> dict[str, Any]:
    domain = db.one(conn, "SELECT * FROM domains WHERE id = ?", (payload.domain_id,))
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    email = payload.email.strip().lower()
    if not EMAIL_RE.match(email):
        raise HTTPException(status_code=400, detail="Enter a valid mailbox email address")
    if not email.endswith("@" + domain["name"]):
        raise HTTPException(status_code=400, detail=f"Email must end with @{domain['name']}")
    try:
        with conn:
            cursor = conn.execute(
                "INSERT INTO mailboxes(domain_id, email, display_name, transport, smtp_host, smtp_port, "
                "smtp_username, smtp_password_enc, imap_host, imap_port, imap_username, imap_password_enc, "
                "gas_url, gas_secret_enc, daily_limit, hourly_limit, min_gap_seconds, max_gap_seconds, "
                "timezone, status, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    payload.domain_id,
                    email,
                    payload.display_name.strip(),
                    payload.transport,
                    payload.smtp_host,
                    payload.smtp_port,
                    payload.smtp_username,
                    crypto.encrypt(payload.smtp_password),
                    payload.imap_host,
                    payload.imap_port,
                    payload.imap_username,
                    crypto.encrypt(payload.imap_password),
                    payload.gas_url,
                    crypto.encrypt(payload.gas_secret),
                    payload.daily_limit,
                    payload.hourly_limit,
                    payload.min_gap_seconds,
                    payload.max_gap_seconds,
                    payload.timezone,
                    payload.status,
                    db.now_iso(),
                    db.now_iso(),
                ),
            )
            mailbox_id = int(cursor.lastrowid)
            if payload.campaign_ids:
                for campaign_id in payload.campaign_ids:
                    conn.execute(
                        "INSERT OR IGNORE INTO campaign_mailboxes(campaign_id, mailbox_id) VALUES (?, ?)",
                        (campaign_id, mailbox_id),
                    )
            db.audit(conn, "mailbox_created", "mailbox", mailbox_id, {"email": email, "transport": payload.transport})
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="That mailbox already exists") from exc
    return {"ok": True, "item": next(row for row in _mailbox_rows(conn) if row["id"] == mailbox_id)}


@router.patch("/mailboxes/{mailbox_id}")
def update_mailbox(mailbox_id: int, payload: MailboxUpdate, conn=Conn) -> dict[str, Any]:
    mailbox = db.one(conn, "SELECT * FROM mailboxes WHERE id = ?", (mailbox_id,))
    if not mailbox:
        raise HTTPException(status_code=404, detail="Mailbox not found")
    data = payload.model_dump(exclude_unset=True)
    campaign_ids = data.pop("campaign_ids", None)
    if "smtp_password" in data:
        data["smtp_password_enc"] = crypto.encrypt(data.pop("smtp_password"))
    if "imap_password" in data:
        data["imap_password_enc"] = crypto.encrypt(data.pop("imap_password"))
    if "gas_secret" in data:
        data["gas_secret_enc"] = crypto.encrypt(data.pop("gas_secret"))
    allowed = {
        "display_name",
        "transport",
        "smtp_host",
        "smtp_port",
        "smtp_username",
        "smtp_password_enc",
        "imap_host",
        "imap_port",
        "imap_username",
        "imap_password_enc",
        "gas_url",
        "gas_secret_enc",
        "daily_limit",
        "hourly_limit",
        "min_gap_seconds",
        "max_gap_seconds",
        "timezone",
        "status",
    }
    updates = {key: value for key, value in data.items() if key in allowed and value is not None}
    with conn:
        if updates:
            assignments = ", ".join(f"{key} = ?" for key in updates)
            conn.execute(
                f"UPDATE mailboxes SET {assignments}, updated_at = ? WHERE id = ?",
                (*updates.values(), db.now_iso(), mailbox_id),
            )
        if campaign_ids is not None:
            conn.execute("DELETE FROM campaign_mailboxes WHERE mailbox_id = ?", (mailbox_id,))
            for campaign_id in campaign_ids:
                conn.execute(
                    "INSERT OR IGNORE INTO campaign_mailboxes(campaign_id, mailbox_id) VALUES (?, ?)",
                    (campaign_id, mailbox_id),
                )
        db.audit(conn, "mailbox_updated", "mailbox", mailbox_id, updates or {"campaigns": campaign_ids})
    return {"ok": True, "item": next(row for row in _mailbox_rows(conn) if row["id"] == mailbox_id)}


@router.post("/mailboxes/{mailbox_id}/test")
def test_mailbox(mailbox_id: int, conn=Conn) -> dict[str, Any]:
    mailbox = db.one(conn, "SELECT * FROM mailboxes WHERE id = ?", (mailbox_id,))
    if not mailbox:
        raise HTTPException(status_code=404, detail="Mailbox not found")
    result = sender.test_mailbox_connection(mailbox)
    with conn:
        db.audit(conn, "mailbox_tested", "mailbox", mailbox_id, result)
    return result


@router.post("/mailboxes/{mailbox_id}/pause")
def pause_mailbox(mailbox_id: int, conn=Conn) -> dict[str, Any]:
    with conn:
        conn.execute("UPDATE mailboxes SET status = 'paused', updated_at = ? WHERE id = ?", (db.now_iso(), mailbox_id))
        db.audit(conn, "mailbox_paused", "mailbox", mailbox_id, "")
    return {"ok": True}


@router.post("/mailboxes/{mailbox_id}/resume")
def resume_mailbox(mailbox_id: int, conn=Conn) -> dict[str, Any]:
    with conn:
        conn.execute("UPDATE mailboxes SET status = 'active', updated_at = ? WHERE id = ?", (db.now_iso(), mailbox_id))
        db.audit(conn, "mailbox_resumed", "mailbox", mailbox_id, "")
    return {"ok": True}


@router.get("/domains")
def list_domains(conn=Conn) -> dict[str, Any]:
    items = db.rows(
        conn,
        """
        SELECT d.*, COUNT(m.id) AS mailbox_count,
               COALESCE(SUM(u.sent), 0) AS sent_today
        FROM domains d
        LEFT JOIN mailboxes m ON m.domain_id = d.id
        LEFT JOIN mailbox_usage_daily u ON u.mailbox_id = m.id AND u.date = date('now', 'localtime')
        GROUP BY d.id
        ORDER BY d.name
        """,
    )
    return {"items": items}


@router.post("/domains")
def create_domain(payload: DomainCreate, conn=Conn) -> dict[str, Any]:
    name = payload.name.strip().lower().removeprefix("https://").removeprefix("http://").strip("/")
    if not DOMAIN_RE.match(name):
        raise HTTPException(status_code=400, detail="Enter a domain without a path, for example outreach.example.com")
    try:
        with conn:
            cursor = conn.execute(
                "INSERT INTO domains(name, provider, dkim_selector, status) VALUES (?, ?, ?, ?)",
                (name, payload.provider, payload.dkim_selector, payload.status),
            )
            domain_id = int(cursor.lastrowid)
            db.audit(conn, "domain_created", "domain", domain_id, {"name": name})
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="That domain already exists") from exc
    return {"ok": True, "item": db.one(conn, "SELECT * FROM domains WHERE id = ?", (domain_id,))}


@router.patch("/domains/{domain_id}")
def update_domain(domain_id: int, payload: DomainUpdate, conn=Conn) -> dict[str, Any]:
    if not db.one(conn, "SELECT id FROM domains WHERE id = ?", (domain_id,)):
        raise HTTPException(status_code=404, detail="Domain not found")
    data = payload.model_dump(exclude_unset=True)
    allowed = {"provider", "dkim_selector", "status"}
    updates = {key: value for key, value in data.items() if key in allowed and value is not None}
    with conn:
        if updates:
            assignments = ", ".join(f"{key} = ?" for key in updates)
            conn.execute(f"UPDATE domains SET {assignments} WHERE id = ?", (*updates.values(), domain_id))
        db.audit(conn, "domain_updated", "domain", domain_id, updates)
    return {"ok": True, "item": db.one(conn, "SELECT * FROM domains WHERE id = ?", (domain_id,))}


@router.post("/domains/{domain_id}/check")
def check_domain(domain_id: int, conn=Conn) -> dict[str, Any]:
    domain = db.one(conn, "SELECT * FROM domains WHERE id = ?", (domain_id,))
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    with conn:
        result = dnscheck.check_domain(conn, domain_id)
    return result

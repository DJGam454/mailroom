"""Mailbox eligibility, rotation and slot reservation."""

from __future__ import annotations

import json
import random
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from app import db


class NoMailboxAvailable(Exception):
    pass


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def campaign_tz(campaign: dict[str, Any]) -> ZoneInfo:
    try:
        return ZoneInfo(campaign.get("timezone") or "UTC")
    except Exception:
        return ZoneInfo("UTC")


def local_date(campaign: dict[str, Any]) -> str:
    return datetime.now(campaign_tz(campaign)).date().isoformat()


def working_days(campaign: dict[str, Any]) -> set[int]:
    try:
        values = json.loads(campaign.get("working_days") or "[1,2,3,4,5]")
        return {int(value) for value in values}
    except (ValueError, TypeError, json.JSONDecodeError):
        return {1, 2, 3, 4, 5}


def _time_parts(value: str, fallback: tuple[int, int]) -> tuple[int, int]:
    try:
        hour, minute = value.split(":", 1)
        return int(hour), int(minute)
    except (ValueError, AttributeError):
        return fallback


def window_is_all_day(start_value: str | None, end_value: str | None) -> bool:
    start_h, start_m = _time_parts(start_value or "00:00", (0, 0))
    end_h, end_m = _time_parts(end_value or "23:59", (23, 59))
    return (start_h, start_m) == (0, 0) and (end_h, end_m) >= (23, 59)


def window_state(campaign: dict[str, Any], at: datetime | None = None) -> dict[str, Any]:
    tz = campaign_tz(campaign)
    current = (at or now_utc()).astimezone(tz)
    start_h, start_m = _time_parts(campaign.get("window_start", "09:30"), (9, 30))
    end_h, end_m = _time_parts(campaign.get("window_end", "17:30"), (17, 30))
    start = current.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
    end = current.replace(hour=end_h, minute=end_m, second=0, microsecond=0)
    days = working_days(campaign)
    all_day = window_is_all_day(campaign.get("window_start"), campaign.get("window_end"))
    inside = current.isoweekday() in days and (all_day or start <= current <= end)
    return {
        "inside": inside,
        "local_now": current,
        "start": start,
        "end": end,
        "window_start": campaign.get("window_start", "09:30"),
        "window_end": campaign.get("window_end", "17:30"),
        "working_days": sorted(days),
    }


def campaign_day_bounds(campaign: dict[str, Any], at: datetime | None = None) -> tuple[str, str]:
    tz = campaign_tz(campaign)
    current = (at or now_utc()).astimezone(tz)
    start = current.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return iso(start.astimezone(timezone.utc)), iso(end.astimezone(timezone.utc))


def campaign_sent_today(conn, campaign: dict[str, Any], at: datetime | None = None) -> int:
    start, end = campaign_day_bounds(campaign, at)
    row = db.one(
        conn,
        "SELECT COUNT(*) AS count FROM messages "
        "WHERE campaign_id = ? AND status = 'sent' AND sent_at >= ? AND sent_at < ?",
        (campaign["id"], start, end),
    )
    return int(row["count"]) if row else 0


def next_window_start(campaign: dict[str, Any], at: datetime | None = None) -> datetime:
    tz = campaign_tz(campaign)
    current = (at or now_utc()).astimezone(tz)
    start_h, start_m = _time_parts(campaign.get("window_start", "09:30"), (9, 30))
    end_h, end_m = _time_parts(campaign.get("window_end", "17:30"), (17, 30))
    days = working_days(campaign)
    all_day = window_is_all_day(campaign.get("window_start"), campaign.get("window_end"))

    if current.isoweekday() in days:
        start = current.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
        end = current.replace(hour=end_h, minute=end_m, second=0, microsecond=0)
        if all_day or start <= current <= end:
            return current.astimezone(timezone.utc)
        if current < start:
            return start.astimezone(timezone.utc)

    for offset in range(1, 8):
        candidate_date = current.date() + timedelta(days=offset)
        if candidate_date.isoweekday() in days:
            candidate = datetime.combine(
                candidate_date,
                datetime.min.time(),
                tzinfo=tz,
            ).replace(hour=start_h, minute=start_m)
            return candidate.astimezone(timezone.utc)

    # Fallback: next day at the start time.
    return (
        current.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
        + timedelta(days=1)
    ).astimezone(timezone.utc)


def _usage(conn, campaign: dict[str, Any], now: datetime | None = None) -> list[dict[str, Any]]:
    date = local_date(campaign)
    hour_ago = iso((now or now_utc()) - timedelta(hours=1))
    return db.rows(
        conn,
        """
        SELECT m.*, cm.weight AS weight, d.name AS domain_name,
               COALESCE(u.sent, 0) AS sent_today,
               (
                   SELECT COUNT(*) FROM messages msg
                   WHERE msg.mailbox_id = m.id AND msg.sent_at >= ?
               ) AS sent_hour,
               (
                   SELECT COALESCE(SUM(u2.sent), 0)
                   FROM mailbox_usage_daily u2
                   JOIN mailboxes m2 ON m2.id = u2.mailbox_id
                   WHERE m2.domain_id = m.domain_id AND u2.date = ?
               ) AS domain_sent_today
        FROM mailboxes m
        JOIN domains d ON d.id = m.domain_id
        JOIN campaign_mailboxes cm ON cm.mailbox_id = m.id
        LEFT JOIN mailbox_usage_daily u ON u.mailbox_id = m.id AND u.date = ?
        WHERE cm.campaign_id = ?
          AND cm.enabled = 1
          AND m.status = 'active'
          AND d.status = 'active'
        """,
        (hour_ago, date, date, campaign["id"]),
    )


def eligible_mailboxes(conn, campaign: dict[str, Any], at: datetime | None = None) -> list[dict[str, Any]]:
    state = window_state(campaign, at)
    if not state["inside"]:
        return []
    if campaign_sent_today(conn, campaign, at) >= int(campaign.get("daily_limit") or 0):
        return []
    candidates = _usage(conn, campaign, at)
    eligible = []
    for mailbox in candidates:
        if int(mailbox["sent_today"]) >= int(mailbox["daily_limit"]):
            continue
        if int(mailbox["sent_hour"]) >= int(mailbox["hourly_limit"]):
            continue
        if int(mailbox["domain_sent_today"]) >= int(campaign.get("per_domain_limit", 50)):
            continue
        eligible.append(mailbox)
    return eligible


def pick_mailbox(conn, campaign: dict[str, Any], at: datetime | None = None) -> dict[str, Any] | None:
    candidates = eligible_mailboxes(conn, campaign, at)
    if not candidates:
        return None

    strategy = campaign.get("rotation_strategy") or "least_used"
    if strategy == "round_robin":
        return sorted(
            candidates,
            key=lambda item: (item.get("last_sent_at") or "", item["id"]),
        )[0]
    if strategy == "weighted":
        weights = [max(1, int(item.get("weight") or 1)) for item in candidates]
        return random.choices(candidates, weights=weights, k=1)[0]

    return sorted(
        candidates,
        key=lambda item: (
            int(item["sent_today"]),
            item.get("next_available_at") or "",
            item.get("last_sent_at") or "",
            item["id"],
        ),
    )[0]


def reserve_slot(conn, campaign: dict[str, Any], mailbox: dict[str, Any], at: datetime | None = None) -> str:
    base = at or now_utc()
    next_available = parse_dt(mailbox.get("next_available_at")) or base
    scheduled = max(base, next_available, next_window_start(campaign, base))
    # If the mailbox's cooldown lands after the window, move to the next window.
    state = window_state(campaign, scheduled)
    if not state["inside"]:
        scheduled = next_window_start(campaign, scheduled)

    gap_min = max(
        1,
        int(campaign.get("min_gap_seconds") or 90),
        int(mailbox.get("min_gap_seconds") or 1),
    )
    campaign_max = max(gap_min, int(campaign.get("max_gap_seconds") or gap_min))
    mailbox_max = int(mailbox.get("max_gap_seconds") or 0)
    gap_max = max(gap_min, min(campaign_max, mailbox_max)) if mailbox_max else campaign_max
    gap = random.randint(gap_min, gap_max)
    conn.execute(
        "UPDATE mailboxes SET next_available_at = ?, updated_at = ? WHERE id = ?",
        (iso(scheduled + timedelta(seconds=gap)), db.now_iso(), mailbox["id"]),
    )
    return iso(scheduled)


def is_suppressed(conn, email: str) -> dict[str, Any] | None:
    return db.one(
        conn,
        "SELECT * FROM suppression WHERE email = ?",
        ((email or "").strip().lower(),),
    )


def schedule_draft(conn, draft_id: int, mailbox_id: int | None = None) -> dict[str, Any]:
    draft = db.one(conn, "SELECT * FROM drafts WHERE id = ?", (draft_id,))
    if not draft:
        raise NoMailboxAvailable("Draft not found")
    if draft["status"] == "queued":
        queue = db.one(conn, "SELECT * FROM send_queue WHERE draft_id = ?", (draft_id,))
        mailbox = db.one(conn, "SELECT * FROM mailboxes WHERE id = ?", (queue["mailbox_id"],))
        return {"queue": queue, "mailbox": mailbox}
    if draft["status"] not in {"pending", "approved"}:
        raise NoMailboxAvailable(f"Draft is {draft['status']}, not pending")

    lead = db.one(conn, "SELECT * FROM leads WHERE id = ?", (draft["lead_id"],))
    campaign = db.one(conn, "SELECT * FROM campaigns WHERE id = ?", (draft["campaign_id"],))
    if not lead or not campaign:
        raise NoMailboxAvailable("Lead or campaign not found")
    if is_suppressed(conn, lead["email"]):
        raise NoMailboxAvailable("Recipient is on the suppression list")
    prior_send = db.one(
        conn,
        """
        SELECT msg.id, msg.sent_at, c.name AS campaign_name
        FROM messages msg
        JOIN campaigns c ON c.id = msg.campaign_id
        WHERE lower(msg.to_email) = lower(?)
          AND msg.direction = 'outbound'
          AND msg.status = 'sent'
        ORDER BY msg.id DESC
        LIMIT 1
        """,
        (lead["email"],),
    )
    if prior_send:
        raise NoMailboxAvailable(
            f"This contact was already emailed in {prior_send['campaign_name']}. "
            "Mailroom blocks repeat sends to the same address."
        )
    queued_send = db.one(
        conn,
        """
        SELECT q.id, c.name AS campaign_name
        FROM send_queue q
        JOIN leads l ON l.id = q.lead_id
        JOIN campaigns c ON c.id = q.campaign_id
        WHERE lower(l.email) = lower(?)
          AND q.status IN ('queued', 'leased')
          AND q.draft_id != ?
        LIMIT 1
        """,
        (lead["email"], draft_id),
    )
    if queued_send:
        raise NoMailboxAvailable(
            f"This contact already has a queued send in {queued_send['campaign_name']}. "
            "Cancel it before queueing another."
        )
    if campaign["status"] != "active":
        raise NoMailboxAvailable("Campaign is not active")
    if db.settings_dict(conn).get("sending_paused") == "1":
        raise NoMailboxAvailable("Sending is paused globally in Settings")

    mailbox = None
    if mailbox_id:
        mailbox = db.one(conn, "SELECT * FROM mailboxes WHERE id = ? AND status = 'active'", (mailbox_id,))
        assigned = db.one(
            conn,
            "SELECT 1 FROM campaign_mailboxes WHERE campaign_id = ? AND mailbox_id = ? AND enabled = 1",
            (campaign["id"], mailbox_id),
        )
        if mailbox and not assigned:
            mailbox = None
    if not mailbox:
        mailbox = pick_mailbox(conn, campaign)
    if not mailbox:
        raise NoMailboxAvailable("No eligible mailbox right now. Check caps, status and the send window.")

    scheduled_at = reserve_slot(conn, campaign, mailbox)
    now = db.now_iso()
    cursor = conn.execute(
        "INSERT INTO send_queue(draft_id, lead_id, campaign_id, mailbox_id, scheduled_at, status, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, 'queued', ?, ?)",
        (draft_id, lead["id"], campaign["id"], mailbox["id"], scheduled_at, now, now),
    )
    conn.execute(
        "UPDATE drafts SET status = 'queued', approved_at = COALESCE(approved_at, ?), updated_at = ? WHERE id = ?",
        (now, now, draft_id),
    )
    conn.execute(
        "UPDATE leads SET status = 'queued', updated_at = ? WHERE id = ?",
        (now, lead["id"]),
    )
    db.audit(
        conn,
        "draft_queued",
        "draft",
        draft_id,
        {"lead_id": lead["id"], "mailbox": mailbox["email"], "scheduled_at": scheduled_at},
    )
    queue = db.one(conn, "SELECT * FROM send_queue WHERE id = ?", (cursor.lastrowid,))
    return {"queue": queue, "mailbox": mailbox}

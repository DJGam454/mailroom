"""Closed-pool email warmup.

The engine is deliberately conservative:

- cross-domain pairs only
- pair cooldown
- per-mailbox and per-domain daily caps
- a slow ramp
- varied plain-text conversations
- opens, replies and best-effort IMAP read flags
- warmup traffic is separate from campaign traffic

This is a closed pool by default. It is useful for mechanics and baseline
signals, but adding external seed inboxes (Gmail, Outlook, another provider)
gives providers a more realistic network. The UI says this explicitly.
"""

from __future__ import annotations

import logging
import random
import threading
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import formataddr, format_datetime, make_msgid
from typing import Any
from zoneinfo import ZoneInfo

from app import config, db
from app.services import rotation, sender

log = logging.getLogger("mailroom.warmup")
_lock = threading.Lock()

CONTENT = [
    ("Quick check-in", "Hi {name},\n\nHope your week is going well. I saw your note and wanted to say hello.\n\n{sender}"),
    ("That article", "Hi {name},\n\nI finally read the piece you mentioned. The section on small teams was the part that stayed with me.\n\n{sender}"),
    ("Coffee next week?", "Hi {name},\n\nAre you free for a short coffee next week? Tuesday or Thursday afternoon works on my side.\n\n{sender}"),
    ("Following up", "Hi {name},\n\nFollowing up on our last exchange. No rush at all, just keeping it on the radar.\n\n{sender}"),
    ("A small update", "Hi {name},\n\nSmall update from my side: the project is moving and the next review is on Friday.\n\n{sender}"),
    ("Re: planning", "Hi {name},\n\nI moved the planning notes into one place so we stop losing the small decisions.\n\n{sender}"),
    ("That intro", "Hi {name},\n\nThanks for the introduction. I had a good conversation and will keep you posted.\n\n{sender}"),
    ("Lunch?", "Hi {name},\n\nI am near your office on Wednesday. If you are around, lunch would be good.\n\n{sender}"),
    ("The draft", "Hi {name},\n\nI took a first pass at the draft. It is shorter now and the main point is easier to find.\n\n{sender}"),
    ("One question", "Hi {name},\n\nOne question before I close this out: do you want the summary in the doc or in the thread?\n\n{sender}"),
    ("Weekend", "Hi {name},\n\nHope you get a quiet weekend. I am going to stay off the laptop for at least one day.\n\n{sender}"),
    ("The notes", "Hi {name},\n\nThe notes are ready. I kept the open questions separate so they are easier to scan.\n\n{sender}"),
    ("Quick thought", "Hi {name},\n\nQuick thought after our call: the smaller version is probably the right place to start.\n\n{sender}"),
    ("Checking in", "Hi {name},\n\nChecking in after a busy week. How did the review go?\n\n{sender}"),
    ("Next step", "Hi {name},\n\nFor the next step, I suggest we keep the scope tight and revisit the rest later.\n\n{sender}"),
]

REPLIES = [
    "Thanks, that helps.",
    "Sounds good to me.",
    "I will take a look this afternoon.",
    "Yes, next week works.",
    "Appreciate the note.",
    "That makes sense.",
    "Let's do it.",
    "Good timing. I was about to ask the same.",
    "Noted, thank you.",
    "I will keep you posted.",
]


def _settings(conn) -> dict[str, Any]:
    raw = db.settings_dict(conn)
    ramp = []
    try:
        ramp = [max(1, int(value.strip())) for value in raw.get("warmup_ramp", "").split(",") if value.strip()]
    except ValueError:
        ramp = []
    if not ramp:
        ramp = [2, 2, 2, 4, 4, 4, 4, 6, 6, 6, 6, 6, 6, 6, 10, 10, 10, 10, 10, 10, 10, 15, 15, 15, 15, 15, 15, 15, 15, 15]
    return {
        "enabled": raw.get("warmup_enabled", "1") == "1",
        "daily_limit": max(1, int(raw.get("warmup_daily_limit", "10"))),
        "domain_daily_limit": max(1, int(raw.get("warmup_domain_daily_limit", "50"))),
        "pair_cooldown_days": max(1, int(raw.get("warmup_pair_cooldown_days", "7"))),
        "reply_rate": min(1.0, max(0.0, float(raw.get("warmup_reply_rate", "0.30")))),
        "open_rate": min(1.0, max(0.0, float(raw.get("warmup_open_rate", "0.80")))),
        "important_rate": min(1.0, max(0.0, float(raw.get("warmup_important_rate", "0.30")))),
        "min_gap": max(1, int(raw.get("warmup_min_gap_seconds", "5"))),
        "max_gap": max(1, int(raw.get("warmup_max_gap_seconds", "30"))),
        "window_start": raw.get("warmup_window_start", "00:00"),
        "window_end": raw.get("warmup_window_end", "23:59"),
        "weekdays_only": raw.get("warmup_weekdays_only", "0") == "1",
        "max_per_tick": max(1, int(raw.get("warmup_max_sends_per_tick", "10"))),
        "ramp": ramp,
    }


def ramp_target(day: int, daily_limit: int, ramp: list[int]) -> int:
    index = min(max(0, day - 1), len(ramp) - 1)
    return max(1, min(daily_limit, int(ramp[index])))


def profile_day(started_at: str | None) -> int:
    start = rotation.parse_dt(started_at)
    if not start:
        return 1
    return max(1, (datetime.now(timezone.utc).date() - start.date()).days + 1)


def _local_window(mailbox: dict[str, Any], settings: dict[str, Any]) -> bool:
    try:
        now = datetime.now(ZoneInfo(mailbox.get("timezone") or "UTC"))
    except Exception:
        now = datetime.now(timezone.utc)
    if settings["weekdays_only"] and now.isoweekday() > 5:
        return False
    try:
        start_h, start_m = [int(part) for part in settings["window_start"].split(":")]
        end_h, end_m = [int(part) for part in settings["window_end"].split(":")]
    except ValueError:
        return True
    start = now.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
    end = now.replace(hour=end_h, minute=end_m, second=0, microsecond=0)
    return start <= now <= end


def ensure_profiles(conn) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO warmup_profiles(mailbox_id, enabled, status, daily_limit) "
        "SELECT id, 0, 'off', 10 FROM mailboxes"
    )


def _count(conn, sql: str, params: tuple[Any, ...]) -> int:
    row = db.one(conn, sql, params)
    return int(row["count"]) if row else 0


def sent_today(conn, mailbox_id: int) -> int:
    return _count(
        conn,
        "SELECT COUNT(*) AS count FROM warmup_messages WHERE mailbox_id = ? AND kind = 'initial' AND date(sent_at) = date('now')",
        (mailbox_id,),
    )


def received_today(conn, email: str) -> int:
    return _count(
        conn,
        "SELECT COUNT(*) AS count FROM warmup_messages WHERE to_email = ? AND kind = 'initial' AND date(sent_at) = date('now')",
        (email,),
    )


def replies_today(conn, mailbox_id: int) -> int:
    return _count(
        conn,
        "SELECT COUNT(*) AS count FROM warmup_messages WHERE mailbox_id = ? AND kind = 'reply' AND date(sent_at) = date('now')",
        (mailbox_id,),
    )


def threads_today(conn, mailbox_id: int) -> int:
    return _count(
        conn,
        "SELECT COUNT(*) AS count FROM warmup_threads WHERE source_mailbox_id = ? AND date(created_at) = date('now')",
        (mailbox_id,),
    )


def domain_sent_today(conn, domain_id: int) -> int:
    return _count(
        conn,
        """
        SELECT COUNT(*) AS count FROM warmup_messages wm
        JOIN mailboxes m ON m.id = wm.mailbox_id
        WHERE m.domain_id = ? AND wm.kind = 'initial' AND date(wm.sent_at) = date('now')
        """,
        (domain_id,),
    )


def health_for(conn, mailbox: dict[str, Any]) -> int:
    row = db.one(
        conn,
        """
        SELECT
          (SELECT COUNT(*) FROM warmup_messages WHERE mailbox_id = ? AND kind = 'initial' AND date(sent_at) >= date('now', '-6 days')) AS sent7,
          (SELECT COUNT(*) FROM warmup_messages WHERE mailbox_id = ? AND kind = 'reply' AND date(sent_at) >= date('now', '-6 days')) AS replies7,
          (SELECT COUNT(*) FROM warmup_messages WHERE mailbox_id = ? AND kind = 'initial' AND read_at IS NOT NULL AND date(sent_at) >= date('now', '-6 days')) AS opened7,
          (SELECT COUNT(*) FROM warmup_messages WHERE to_email = ? AND kind = 'initial' AND date(sent_at) >= date('now', '-6 days')) AS received7
        """,
        (mailbox["id"], mailbox["id"], mailbox["id"], mailbox["email"]),
    ) or {}
    sent7 = int(row.get("sent7") or 0)
    replies7 = int(row.get("replies7") or 0)
    opened7 = int(row.get("opened7") or 0)
    received7 = int(row.get("received7") or 0)
    reply_rate = replies7 / sent7 if sent7 else 0
    open_rate = opened7 / sent7 if sent7 else 0
    score = 20 + min(30, sent7 * 1.5) + min(25, reply_rate * 25) + min(15, open_rate * 15) + min(10, received7 * 0.5)
    return int(round(min(100, score)))


def profile_rows(conn) -> list[dict[str, Any]]:
    ensure_profiles(conn)
    settings = _settings(conn)
    rows = db.rows(
        conn,
        """
        SELECT m.id, m.email, m.display_name, m.timezone, m.status AS mailbox_status,
               d.name AS domain_name, d.id AS domain_id,
               p.enabled, p.status, p.started_at, p.daily_limit, p.reply_rate, p.open_rate,
               p.important_rate, p.last_run_at
        FROM warmup_profiles p
        JOIN mailboxes m ON m.id = p.mailbox_id
        JOIN domains d ON d.id = m.domain_id
        ORDER BY m.email
        """,
    )
    for row in rows:
        day = profile_day(row.get("started_at"))
        row["day"] = day
        row["daily_target"] = ramp_target(day, int(row["daily_limit"]), settings["ramp"]) if row["status"] in {"ramping", "active"} else 0
        row["sent_today"] = sent_today(conn, row["id"])
        row["received_today"] = received_today(conn, row["email"])
        row["replies_today"] = replies_today(conn, row["id"])
        row["health"] = health_for(conn, row)
        last = db.one(
            conn,
            "SELECT MAX(sent_at) AS at FROM warmup_messages WHERE mailbox_id = ? OR to_email = ?",
            (row["id"], row["email"]),
        )
        row["last_activity_at"] = last.get("at") if last else None
    return rows


def choose_target(conn, source: dict[str, Any], settings: dict[str, Any] | None = None) -> dict[str, Any] | None:
    settings = settings or _settings(conn)
    cooldown = rotation.iso(rotation.now_utc() - timedelta(days=settings["pair_cooldown_days"]))
    candidates = db.rows(
        conn,
        """
        SELECT m.*, d.name AS domain_name,
               p.daily_limit AS warmup_limit,
               (SELECT COUNT(*) FROM warmup_messages wm
                 WHERE wm.to_email = m.email AND wm.kind = 'initial' AND date(wm.sent_at) = date('now')) AS received_today,
               (SELECT COUNT(*) FROM warmup_threads wt
                 WHERE wt.source_mailbox_id = ? AND wt.target_mailbox_id = m.id) AS pair_count
        FROM mailboxes m
        JOIN domains d ON d.id = m.domain_id
        JOIN warmup_profiles p ON p.mailbox_id = m.id
        WHERE m.id != ?
          AND m.domain_id != ?
          AND m.status = 'active'
          AND d.status = 'active'
          AND p.enabled = 1
          AND p.status IN ('ramping', 'active')
          AND m.id NOT IN (
              SELECT CASE WHEN wt.source_mailbox_id = ? THEN wt.target_mailbox_id ELSE wt.source_mailbox_id END
              FROM warmup_threads wt
              WHERE (wt.source_mailbox_id = ? OR wt.target_mailbox_id = ?)
                AND wt.created_at >= ?
          )
        """,
        (source["id"], source["id"], source["domain_id"], source["id"], source["id"], source["id"], cooldown),
    )
    candidates = [
        candidate
        for candidate in candidates
        if int(candidate["received_today"]) < max(2, int(candidate["warmup_limit"]))
    ]
    if not candidates:
        return None
    weights = [1.0 / (1 + int(candidate["pair_count"])) for candidate in candidates]
    return random.choices(candidates, weights=weights, k=1)[0]


def _create_thread(conn, source: dict[str, Any], target: dict[str, Any], settings: dict[str, Any]) -> int:
    subject, body_template = random.choice(CONTENT)
    body = body_template.format(
        name=(target.get("display_name") or target["email"].split("@")[0]),
        sender=(source.get("display_name") or source["email"].split("@")[0]),
    )
    now = db.now_iso()
    cursor = conn.execute(
        "INSERT INTO warmup_threads(source_mailbox_id, target_mailbox_id, subject, body, status, created_at, last_activity_at) "
        "VALUES (?, ?, ?, ?, 'open', ?, ?)",
        (source["id"], target["id"], subject, body, now, now),
    )
    thread_id = int(cursor.lastrowid)
    last = db.one(
        conn,
        "SELECT MAX(scheduled_at) AS at FROM warmup_queue "
        "WHERE mailbox_id = ? AND kind = 'send' AND status IN ('queued', 'leased')",
        (source["id"],),
    )
    base = rotation.parse_dt(last.get("at")) if last and last.get("at") else rotation.now_utc()
    base = max(base, rotation.now_utc())
    delay = random.randint(settings["min_gap"], max(settings["min_gap"], settings["max_gap"]))
    scheduled = rotation.iso(base + timedelta(seconds=delay))
    conn.execute(
        "INSERT INTO warmup_queue(thread_id, mailbox_id, kind, scheduled_at, status, created_at, updated_at) "
        "VALUES (?, ?, 'send', ?, 'queued', ?, ?)",
        (thread_id, source["id"], scheduled, now, now),
    )
    db.audit(
        conn,
        "warmup_thread_created",
        "warmup_thread",
        thread_id,
        {"from": source["email"], "to": target["email"], "scheduled_at": scheduled},
    )
    return thread_id


def _profile_for(conn, mailbox_id: int) -> dict[str, Any] | None:
    return db.one(conn, "SELECT * FROM warmup_profiles WHERE mailbox_id = ?", (mailbox_id,))


def _message_id_for(conn, thread_id: int) -> str | None:
    row = db.one(
        conn,
        "SELECT message_id FROM warmup_messages WHERE thread_id = ? AND kind = 'initial' ORDER BY id DESC LIMIT 1",
        (thread_id,),
    )
    return row["message_id"] if row else None


def _mark_queue(conn, queue_id: int, status: str, error: str | None = None) -> None:
    conn.execute(
        "UPDATE warmup_queue SET status = ?, last_error = ?, lease_until = NULL, updated_at = ? WHERE id = ?",
        (status, error, db.now_iso(), queue_id),
    )


def _requeue(conn, queue_id: int, error: str, delay: int = 120) -> None:
    queue = db.one(conn, "SELECT * FROM warmup_queue WHERE id = ?", (queue_id,))
    if not queue:
        return
    attempts = int(queue["attempts"]) + 1
    status = "failed" if attempts >= 3 else "queued"
    conn.execute(
        "UPDATE warmup_queue SET status = ?, attempts = ?, lease_until = NULL, last_error = ?, "
        "scheduled_at = ?, updated_at = ? WHERE id = ?",
        (
            status,
            attempts,
            error[:800],
            rotation.iso(rotation.now_utc() + timedelta(seconds=delay)),
            db.now_iso(),
            queue_id,
        ),
    )
    db.audit(
        conn,
        "warmup_task_retry" if status == "queued" else "warmup_task_failed",
        "warmup_queue",
        queue_id,
        {"reason": error[:800], "attempts": attempts},
    )


def _process(queue_id: int) -> dict[str, Any]:
    conn = db.connect()
    try:
        conn.execute("BEGIN IMMEDIATE")
        queue = db.one(
            conn,
            "SELECT * FROM warmup_queue WHERE id = ? AND status = 'queued'",
            (queue_id,),
        )
        if not queue:
            conn.rollback()
            return {"ok": False, "skipped": True}
        conn.execute(
            "UPDATE warmup_queue SET status = 'leased', lease_until = ?, updated_at = ? WHERE id = ?",
            (rotation.iso(rotation.now_utc() + timedelta(seconds=120)), db.now_iso(), queue_id),
        )
        conn.commit()

        thread = db.one(conn, "SELECT * FROM warmup_threads WHERE id = ?", (queue["thread_id"],))
        mailbox = db.one(conn, "SELECT * FROM mailboxes WHERE id = ?", (queue["mailbox_id"],))
        if not thread or not mailbox:
            conn.execute("BEGIN IMMEDIATE")
            _mark_queue(conn, queue_id, "failed", "Thread or mailbox missing")
            conn.commit()
            return {"ok": False, "error": "Thread or mailbox missing"}

        source = db.one(conn, "SELECT * FROM mailboxes WHERE id = ?", (thread["source_mailbox_id"],))
        target = db.one(conn, "SELECT * FROM mailboxes WHERE id = ?", (thread["target_mailbox_id"],))
        if not source or not target:
            conn.execute("BEGIN IMMEDIATE")
            _mark_queue(conn, queue_id, "failed", "Source or target mailbox missing")
            conn.commit()
            return {"ok": False, "error": "Source or target mailbox missing"}

        settings = _settings(conn)
        now = db.now_iso()
        conn.execute("BEGIN IMMEDIATE")

        if queue["kind"] == "send":
            source_profile = _profile_for(conn, source["id"])
            if not source_profile or not source_profile["enabled"] or source_profile["status"] not in {"ramping", "active"}:
                _mark_queue(conn, queue_id, "cancelled", "Source warmup is off")
                conn.commit()
                return {"ok": False, "cancelled": True}
            if not _local_window(source, settings):
                _mark_queue(conn, queue_id, "queued", "Outside warmup window")
                conn.execute(
                    "UPDATE warmup_queue SET scheduled_at = ? WHERE id = ?",
                    (rotation.iso(rotation.now_utc() + timedelta(minutes=30)), queue_id),
                )
                conn.commit()
                return {"ok": False, "retry": True, "reason": "Outside warmup window"}

            message = EmailMessage()
            message["Subject"] = thread["subject"]
            message["From"] = formataddr((source.get("display_name") or "", source["email"]))
            message["To"] = formataddr((target.get("display_name") or "", target["email"]))
            message["Date"] = format_datetime(datetime.now(timezone.utc))
            message["Message-ID"] = make_msgid(domain=source["email"].split("@", 1)[1])
            message.set_content(thread["body"])
            message_id = sender.dispatch_message(message, source, config.WARMUP_OUTBOX_DIR)
            cursor = conn.execute(
                "INSERT INTO warmup_messages(thread_id, mailbox_id, kind, direction, from_email, to_email, subject, body, "
                "message_id, status, sent_at, created_at) VALUES (?, ?, 'initial', 'outbound', ?, ?, ?, ?, ?, 'sent', ?, ?)",
                (thread["id"], source["id"], source["email"], target["email"], thread["subject"], thread["body"], message_id, now, now),
            )
            conn.execute("UPDATE warmup_threads SET last_activity_at = ? WHERE id = ?", (now, thread["id"]))
            _mark_queue(conn, queue_id, "sent")
            # Engagement tasks. The open and reply are separate so a failed
            # reply never blocks the read signal.
            open_at = rotation.iso(rotation.now_utc() + timedelta(seconds=random.randint(30, 600)))
            conn.execute(
                "INSERT INTO warmup_queue(thread_id, mailbox_id, kind, scheduled_at, status, created_at, updated_at) "
                "VALUES (?, ?, 'open', ?, 'queued', ?, ?)",
                (thread["id"], target["id"], open_at, now, now),
            )
            if random.random() <= settings["reply_rate"]:
                reply_at = rotation.iso(rotation.now_utc() + timedelta(seconds=random.randint(120, 900)))
                conn.execute(
                    "INSERT INTO warmup_queue(thread_id, mailbox_id, kind, scheduled_at, status, created_at, updated_at) "
                    "VALUES (?, ?, 'reply', ?, 'queued', ?, ?)",
                    (thread["id"], target["id"], reply_at, now, now),
                )
            db.audit(conn, "warmup_message_sent", "warmup_thread", thread["id"], {"from": source["email"], "to": target["email"], "message_id": message_id})
            conn.commit()
            return {"ok": True, "kind": "send", "message_id": message_id}

        if queue["kind"] == "open":
            initial = db.one(
                conn,
                "SELECT * FROM warmup_messages WHERE thread_id = ? AND kind = 'initial' ORDER BY id DESC LIMIT 1",
                (thread["id"],),
            )
            if not initial:
                _mark_queue(conn, queue_id, "failed", "No initial message")
                conn.commit()
                return {"ok": False, "error": "No initial message"}
            if random.random() <= settings["open_rate"]:
                conn.execute("UPDATE warmup_messages SET read_at = ? WHERE id = ?", (now, initial["id"]))
                sender.mark_read_imap(target, initial["message_id"] or "")
                db.audit(conn, "warmup_opened", "warmup_thread", thread["id"], {"mailbox": target["email"]})
            conn.execute("UPDATE warmup_threads SET last_activity_at = ? WHERE id = ?", (now, thread["id"]))
            _mark_queue(conn, queue_id, "sent")
            conn.commit()
            return {"ok": True, "kind": "open"}

        if queue["kind"] == "reply":
            target_profile = _profile_for(conn, target["id"])
            if not target_profile or not target_profile["enabled"] or target_profile["status"] not in {"ramping", "active"}:
                _mark_queue(conn, queue_id, "cancelled", "Reply mailbox warmup is off")
                conn.commit()
                return {"ok": False, "cancelled": True}
            initial = db.one(
                conn,
                "SELECT * FROM warmup_messages WHERE thread_id = ? AND kind = 'initial' ORDER BY id DESC LIMIT 1",
                (thread["id"],),
            )
            if not initial:
                _mark_queue(conn, queue_id, "failed", "No initial message to reply to")
                conn.commit()
                return {"ok": False, "error": "No initial message"}
            reply_body = random.choice(REPLIES)
            message = EmailMessage()
            message["Subject"] = f"Re: {initial['subject']}"
            message["From"] = formataddr((target.get("display_name") or "", target["email"]))
            message["To"] = formataddr((source.get("display_name") or "", source["email"]))
            message["Date"] = format_datetime(datetime.now(timezone.utc))
            message["Message-ID"] = make_msgid(domain=target["email"].split("@", 1)[1])
            if initial.get("message_id"):
                message["In-Reply-To"] = initial["message_id"]
                message["References"] = initial["message_id"]
            message.set_content(reply_body)
            message_id = sender.dispatch_message(message, target, config.WARMUP_OUTBOX_DIR)
            conn.execute(
                "INSERT INTO warmup_messages(thread_id, mailbox_id, kind, direction, from_email, to_email, subject, body, "
                "message_id, status, sent_at, created_at) VALUES (?, ?, 'reply', 'outbound', ?, ?, ?, ?, ?, 'sent', ?, ?)",
                (thread["id"], target["id"], target["email"], source["email"], message["Subject"], reply_body, message_id, now, now),
            )
            conn.execute("UPDATE warmup_messages SET replied_at = ? WHERE id = ?", (now, initial["id"]))
            conn.execute("UPDATE warmup_threads SET status = 'replied', last_activity_at = ? WHERE id = ?", (now, thread["id"]))
            _mark_queue(conn, queue_id, "sent")
            db.audit(conn, "warmup_replied", "warmup_thread", thread["id"], {"from": target["email"], "to": source["email"]})
            conn.commit()
            return {"ok": True, "kind": "reply", "message_id": message_id}

        _mark_queue(conn, queue_id, "failed", f"Unknown warmup task: {queue['kind']}")
        conn.commit()
        return {"ok": False, "error": "Unknown task"}
    except Exception as exc:  # noqa: BLE001
        log.exception("Warmup task %s failed", queue_id)
        conn.rollback()
        try:
            conn.execute("BEGIN IMMEDIATE")
            _requeue(conn, queue_id, str(exc), 120)
            conn.commit()
        except Exception:
            conn.rollback()
        return {"ok": False, "error": str(exc)}
    finally:
        conn.close()


def tick() -> dict[str, Any]:
    if not _lock.acquire(blocking=False):
        return {"ok": True, "skipped": "warmup tick already running"}
    try:
        conn = db.connect()
        try:
            ensure_profiles(conn)
            conn.commit()
            settings = _settings(conn)
            if not settings["enabled"]:
                return {"ok": True, "enabled": False, "generated": 0, "sent": 0}
            now = db.now_iso()
            conn.execute(
                "UPDATE warmup_queue SET status = 'queued', lease_until = NULL "
                "WHERE status = 'leased' AND lease_until IS NOT NULL AND lease_until < ?",
                (now,),
            )
            conn.commit()
            due = db.rows(
                conn,
                "SELECT id FROM warmup_queue WHERE status = 'queued' AND scheduled_at <= ? "
                "ORDER BY scheduled_at LIMIT ?",
                (now, settings["max_per_tick"]),
            )
        finally:
            conn.close()

        results = [_process(row["id"]) for row in due]
        generated = 0
        with db.transaction() as conn:
            profiles = db.rows(
                conn,
                """
                SELECT m.*, d.name AS domain_name, p.status AS warmup_status, p.started_at, p.daily_limit
                FROM warmup_profiles p
                JOIN mailboxes m ON m.id = p.mailbox_id
                JOIN domains d ON d.id = m.domain_id
                WHERE p.enabled = 1 AND p.status IN ('ramping', 'active')
                  AND m.status = 'active' AND d.status = 'active'
                ORDER BY p.last_run_at IS NULL DESC, p.last_run_at ASC
                """,
            )
            settings = _settings(conn)
            pending = db.one(
                conn,
                "SELECT COUNT(*) AS count FROM warmup_queue WHERE status IN ('queued', 'leased') AND kind = 'send'",
            )
            if pending and int(pending["count"]) >= 200:
                profiles = []
            for profile in profiles:
                if generated >= settings["max_per_tick"]:
                    break
                if not _local_window(profile, settings):
                    continue
                day = profile_day(profile.get("started_at"))
                target_count = ramp_target(day, int(profile["daily_limit"]), settings["ramp"])
                # Count reservations as well as sends: threads created today
                # are already committed volume even if their send is still queued.
                current = max(sent_today(conn, profile["id"]), threads_today(conn, profile["id"]))
                if current >= target_count:
                    continue
                if domain_sent_today(conn, profile["domain_id"]) >= settings["domain_daily_limit"]:
                    continue
                remaining = min(target_count - current, settings["max_per_tick"] - generated)
                for _ in range(max(0, remaining)):
                    target = choose_target(conn, profile, settings)
                    if not target:
                        break
                    _create_thread(conn, profile, target, settings)
                    generated += 1
                    if generated >= settings["max_per_tick"]:
                        break
                conn.execute(
                    "UPDATE warmup_profiles SET last_run_at = ?, updated_at = ? WHERE mailbox_id = ?",
                    (db.now_iso(), db.now_iso(), profile["id"]),
                )
        return {
            "ok": True,
            "generated": generated,
            "processed": len(results),
            "sent": sum(1 for item in results if item.get("ok") and item.get("kind") == "send"),
            "replied": sum(1 for item in results if item.get("ok") and item.get("kind") == "reply"),
            "opened": sum(1 for item in results if item.get("ok") and item.get("kind") == "open"),
            "results": results,
        }
    finally:
        _lock.release()


def start(conn, mailbox_ids: list[int] | None = None, daily_limit: int | None = None) -> dict[str, Any]:
    ensure_profiles(conn)
    settings = _settings(conn)
    now = db.now_iso()
    limit = daily_limit or settings["daily_limit"]
    if mailbox_ids:
        placeholders = ",".join("?" for _ in mailbox_ids)
        rows = db.rows(conn, f"SELECT id FROM mailboxes WHERE id IN ({placeholders}) AND status = 'active'", tuple(mailbox_ids))
    else:
        rows = db.rows(conn, "SELECT id FROM mailboxes WHERE status = 'active'")
    for row in rows:
        conn.execute(
            "UPDATE warmup_profiles SET enabled = 1, status = 'ramping', "
            "started_at = COALESCE(started_at, ?), daily_limit = ?, updated_at = ? "
            "WHERE mailbox_id = ?",
            (now, limit, now, row["id"]),
        )
    db.audit(conn, "warmup_started", "warmup", "", {"mailboxes": len(rows), "daily_limit": daily_limit or settings["daily_limit"]})
    return {"ok": True, "started": len(rows)}


def set_status(conn, status: str, mailbox_ids: list[int] | None = None) -> dict[str, Any]:
    ensure_profiles(conn)
    if mailbox_ids:
        placeholders = ",".join("?" for _ in mailbox_ids)
        params: tuple[Any, ...] = (*mailbox_ids, db.now_iso(), status)
        conn.execute(
            f"UPDATE warmup_profiles SET status = ?, enabled = ?, updated_at = ? "
            f"WHERE mailbox_id IN ({placeholders})",
            (status, 0 if status == "off" else 1, db.now_iso(), *mailbox_ids),
        )
    else:
        conn.execute(
            "UPDATE warmup_profiles SET status = ?, enabled = ?, updated_at = ?",
            (status, 0 if status == "off" else 1, db.now_iso()),
        )
    db.audit(conn, f"warmup_{status}", "warmup", "", {"mailboxes": len(mailbox_ids or [])})
    return {"ok": True, "status": status}


def update_settings(conn, values: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "warmup_enabled",
        "warmup_daily_limit",
        "warmup_domain_daily_limit",
        "warmup_pair_cooldown_days",
        "warmup_reply_rate",
        "warmup_open_rate",
        "warmup_important_rate",
        "warmup_min_gap_seconds",
        "warmup_max_gap_seconds",
        "warmup_window_start",
        "warmup_window_end",
        "warmup_weekdays_only",
        "warmup_max_sends_per_tick",
    }
    clean = {}
    for key, value in values.items():
        if key not in allowed:
            continue
        clean[key] = str(value)
    for key, value in clean.items():
        db.set_setting(conn, key, value)
    if "warmup_daily_limit" in clean:
        try:
            limit = max(1, int(clean["warmup_daily_limit"]))
            conn.execute("UPDATE warmup_profiles SET daily_limit = ?", (limit,))
        except ValueError:
            pass
    db.audit(conn, "warmup_settings_updated", "warmup", "", clean)
    return _settings(conn)


def status(conn) -> dict[str, Any]:
    ensure_profiles(conn)
    conn.commit()
    settings = _settings(conn)
    profiles = profile_rows(conn)
    active = [profile for profile in profiles if profile["enabled"] and profile["status"] in {"ramping", "active"}]
    pair_preview = []
    for profile in active[:8]:
        target = choose_target(conn, profile, settings)
        pair_preview.append(
            {
                "from": profile["email"],
                "from_domain": profile["domain_name"],
                "to": target["email"] if target else None,
                "to_domain": target["domain_name"] if target else None,
            }
        )
    queue = db.rows(
        conn,
        """
        SELECT q.*, t.subject, t.source_mailbox_id, t.target_mailbox_id,
               sm.email AS from_email, tm.email AS to_email
        FROM warmup_queue q
        JOIN warmup_threads t ON t.id = q.thread_id
        JOIN mailboxes sm ON sm.id = t.source_mailbox_id
        JOIN mailboxes tm ON tm.id = t.target_mailbox_id
        WHERE q.status IN ('queued', 'leased')
        ORDER BY q.scheduled_at LIMIT 12
        """,
    )
    recent = db.rows(
        conn,
        """
        SELECT wm.*, sm.email AS from_email, tm.email AS to_email, t.subject AS thread_subject
        FROM warmup_messages wm
        JOIN warmup_threads t ON t.id = wm.thread_id
        JOIN mailboxes sm ON sm.id = t.source_mailbox_id
        JOIN mailboxes tm ON tm.id = t.target_mailbox_id
        ORDER BY wm.id DESC LIMIT 12
        """,
    )
    counts = db.one(
        conn,
        """
        SELECT
          (SELECT COUNT(*) FROM warmup_queue WHERE status = 'queued') AS queued,
          (SELECT COUNT(*) FROM warmup_queue WHERE status = 'failed') AS failed,
          (SELECT COUNT(*) FROM warmup_threads WHERE date(created_at) = date('now')) AS threads_today,
          (SELECT COUNT(*) FROM warmup_messages WHERE kind = 'initial' AND date(sent_at) = date('now')) AS sent_today,
          (SELECT COUNT(*) FROM warmup_messages WHERE kind = 'reply' AND date(sent_at) = date('now')) AS replies_today,
          (SELECT COUNT(*) FROM warmup_messages WHERE kind = 'initial' AND read_at IS NOT NULL AND date(sent_at) = date('now')) AS opened_today
        """,
    ) or {}
    average_health = round(sum(profile["health"] for profile in active) / len(active)) if active else 0
    return {
        "settings": settings,
        "profiles": profiles,
        "summary": {
            "active": len(active),
            "total": len(profiles),
            "sent_today": int(counts.get("sent_today") or 0),
            "replies_today": int(counts.get("replies_today") or 0),
            "opened_today": int(counts.get("opened_today") or 0),
            "threads_today": int(counts.get("threads_today") or 0),
            "queued": int(counts.get("queued") or 0),
            "failed": int(counts.get("failed") or 0),
            "average_health": average_health,
        },
        "pair_preview": pair_preview,
        "queue": queue,
        "recent": recent,
        "algorithm": {
            "cross_domain": True,
            "pair_cooldown_days": settings["pair_cooldown_days"],
            "reply_rate": settings["reply_rate"],
            "open_rate": settings["open_rate"],
            "ramp": settings["ramp"],
            "daily_limit": settings["daily_limit"],
            "domain_daily_limit": settings["domain_daily_limit"],
            "window": f"{settings['window_start']}-{settings['window_end']}",
        },
    }

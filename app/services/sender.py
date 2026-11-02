"""Transport dispatch and message recording."""

from __future__ import annotations

import imaplib
import json
import smtplib
import ssl
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import formataddr, format_datetime, make_msgid
from pathlib import Path
from typing import Any

from app import config, crypto, db
from app.services import rotation


class RetrySend(Exception):
    """A temporary condition: window closed, cap reached, mailbox paused."""


class SendError(Exception):
    """A permanent or attempt-limited failure."""


def usage_date(campaign: dict[str, Any]) -> str:
    return rotation.local_date(campaign)


def mailbox_usage(conn, mailbox_id: int, campaign: dict[str, Any]) -> dict[str, Any]:
    date = usage_date(campaign)
    row = db.one(
        conn,
        "SELECT * FROM mailbox_usage_daily WHERE mailbox_id = ? AND date = ?",
        (mailbox_id, date),
    )
    return row or {"mailbox_id": mailbox_id, "date": date, "sent": 0, "failed": 0, "bounces": 0}


def _build_message(draft: dict[str, Any], lead: dict[str, Any], mailbox: dict[str, Any], domain: str) -> EmailMessage:
    message = EmailMessage()
    message["Subject"] = draft["subject"]
    message["From"] = formataddr((mailbox.get("display_name") or "", mailbox["email"]))
    message["To"] = formataddr((lead.get("name") or "", lead["email"]))
    message["Reply-To"] = mailbox["email"]
    message["Date"] = format_datetime(datetime.now(timezone.utc))
    message["Message-ID"] = make_msgid(domain=domain)
    message["X-Mailroom-Campaign"] = str(draft.get("campaign_id", ""))
    message["X-Mailroom-Lead"] = str(lead["id"])
    message["List-Unsubscribe"] = f"<mailto:unsubscribe@{domain}?subject=unsubscribe>"
    message.set_content(draft["body"])
    return message


def _dispatch_mock(message: EmailMessage, mailbox: dict[str, Any], outbox_dir: Path | None = None) -> str:
    config.ensure_data_dirs()
    message_id = str(message["Message-ID"])
    safe_id = message_id.strip("<>").replace("@", "_at_").replace(".", "_")
    directory = outbox_dir or config.OUTBOX_DIR
    directory.mkdir(parents=True, exist_ok=True)
    path: Path = directory / f"{safe_id}.eml"
    path.write_bytes(message.as_bytes())
    return message_id


def _dispatch_smtp(message: EmailMessage, mailbox: dict[str, Any]) -> str:
    password = crypto.decrypt(mailbox.get("smtp_password_enc"))
    if not mailbox.get("smtp_host") or not mailbox.get("smtp_port"):
        raise SendError("SMTP host and port are required")
    port = int(mailbox["smtp_port"])
    if port == 465:
        client = smtplib.SMTP_SSL(
            mailbox["smtp_host"],
            port,
            timeout=30,
            context=ssl.create_default_context(),
        )
    else:
        client = smtplib.SMTP(mailbox["smtp_host"], port, timeout=30)
    try:
        client.ehlo()
        if port != 465:
            try:
                client.starttls(context=ssl.create_default_context())
                client.ehlo()
            except smtplib.SMTPNotSupportedError:
                pass
        if mailbox.get("smtp_username"):
            client.login(mailbox["smtp_username"], password or "")
        refused = client.send_message(message)
        if refused:
            raise SendError(f"SMTP refused recipients: {refused}")
    finally:
        try:
            client.quit()
        except Exception:
            pass
    return str(message["Message-ID"])


def _dispatch_gas(message: EmailMessage, mailbox: dict[str, Any]) -> str:
    if not mailbox.get("gas_url"):
        raise SendError("Apps Script URL is missing")
    secret = crypto.decrypt(mailbox.get("gas_secret_enc")) or ""
    payload = json.dumps(
        {
            "action": "send",
            "secret": secret,
            "from": mailbox["email"],
            "to": str(message["To"]),
            "subject": str(message["Subject"]),
            "body": message.get_content(),
            "messageId": str(message["Message-ID"]),
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        mailbox["gas_url"],
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise SendError(f"Apps Script send failed: {exc}") from exc
    if not data.get("ok"):
        raise SendError(f"Apps Script refused the send: {data.get('error', data)}")
    return str(data.get("messageId") or message["Message-ID"])


def dispatch_message(
    message: EmailMessage,
    mailbox: dict[str, Any],
    outbox_dir: Path | None = None,
) -> str:
    transport = mailbox.get("transport") or "mock"
    if transport == "mock":
        return _dispatch_mock(message, mailbox, outbox_dir)
    if transport == "smtp":
        return _dispatch_smtp(message, mailbox)
    if transport == "gas":
        return _dispatch_gas(message, mailbox)
    raise SendError(f"Unknown transport: {transport}")


def _dispatch(message: EmailMessage, mailbox: dict[str, Any]) -> str:
    return dispatch_message(message, mailbox)


def mark_read_imap(mailbox: dict[str, Any], message_id: str, important: bool = True) -> bool:
    """Best-effort IMAP read/flag for warmup engagement.

    Mock mailboxes and missing IMAP settings return False. The caller treats
    this as an optional provider-level signal, not a delivery requirement.
    """
    host = mailbox.get("imap_host")
    if not host or not mailbox.get("imap_username"):
        return False
    password = crypto.decrypt(mailbox.get("imap_password_enc"))
    if not password:
        return False
    try:
        client = imaplib.IMAP4_SSL(host, int(mailbox.get("imap_port") or 993), timeout=10)
        try:
            client.login(mailbox["imap_username"], password)
            client.select("INBOX")
            search_id = message_id if message_id.startswith("<") else f"<{message_id}>"
            status, data = client.search(None, "HEADER", "Message-ID", search_id)
            if status != "OK" or not data or not data[0]:
                return False
            flags = r"(\Seen \Flagged)" if important else r"(\Seen)"
            for uid in data[0].split():
                client.store(uid, "+FLAGS", flags)
            return True
        finally:
            try:
                client.logout()
            except Exception:
                pass
    except (OSError, imaplib.IMAP4.error):
        return False


def _check_eligible(conn, queue: dict[str, Any], draft: dict[str, Any], lead: dict[str, Any], mailbox: dict[str, Any], campaign: dict[str, Any], domain: dict[str, Any]) -> None:
    if queue["status"] not in {"queued", "leased"}:
        raise SendError(f"Queue item is {queue['status']}")
    if draft["status"] not in {"queued", "approved"}:
        raise SendError(f"Draft is {draft['status']}")
    if lead["status"] in {"denied", "suppressed", "sent", "replied"}:
        raise SendError(f"Lead is {lead['status']}")
    if campaign["status"] != "active":
        raise RetrySend("Campaign is not active")
    if mailbox["status"] != "active":
        raise RetrySend("Mailbox is paused")
    if domain["status"] != "active":
        raise RetrySend("Domain is paused")
    if rotation.is_suppressed(conn, lead["email"]):
        raise SendError("Recipient is suppressed")
    prior_send = db.one(
        conn,
        "SELECT id FROM messages WHERE lower(to_email) = lower(?) "
        "AND direction = 'outbound' AND status = 'sent' LIMIT 1",
        (lead["email"],),
    )
    if prior_send:
        raise SendError("Recipient already received a message from Mailroom")

    settings = db.settings_dict(conn)
    if settings.get("sending_paused") == "1":
        raise RetrySend("Sending is paused globally in Settings")
    if settings.get("require_dns_pass") == "1" and (mailbox.get("transport") or "mock") != "mock":
        if not all(domain.get(field) == "pass" for field in ("mx_status", "spf_status", "dkim_status", "dmarc_status")):
            raise RetrySend("DNS is not fully verified for this domain")

    state = rotation.window_state(campaign)
    if not state["inside"]:
        raise RetrySend("Outside the campaign send window")

    usage = mailbox_usage(conn, mailbox["id"], campaign)
    if int(usage["sent"]) >= int(mailbox["daily_limit"]):
        raise RetrySend("Mailbox daily limit reached")
    hour_ago = rotation.iso(rotation.now_utc().replace(microsecond=0) - timedelta(hours=1))
    hour_row = db.one(
        conn,
        "SELECT COUNT(*) AS count FROM messages WHERE mailbox_id = ? AND sent_at >= ?",
        (mailbox["id"], hour_ago),
    )
    if int(hour_row["count"]) >= int(mailbox["hourly_limit"]):
        raise RetrySend("Mailbox hourly limit reached")

    domain_usage = db.one(
        conn,
        """
        SELECT COALESCE(SUM(u.sent), 0) AS sent
        FROM mailbox_usage_daily u
        JOIN mailboxes m ON m.id = u.mailbox_id
        WHERE m.domain_id = ? AND u.date = ?
        """,
        (domain["id"], usage["date"]),
    )
    if int(domain_usage["sent"]) >= int(campaign["per_domain_limit"]):
        raise RetrySend("Domain daily limit reached")


def send_queue_item(conn, queue_id: int) -> dict[str, Any]:
    queue = db.one(conn, "SELECT * FROM send_queue WHERE id = ?", (queue_id,))
    if not queue:
        raise SendError("Queue item not found")
    draft = db.one(conn, "SELECT * FROM drafts WHERE id = ?", (queue["draft_id"],))
    lead = db.one(conn, "SELECT * FROM leads WHERE id = ?", (queue["lead_id"],))
    mailbox = db.one(conn, "SELECT * FROM mailboxes WHERE id = ?", (queue["mailbox_id"],))
    campaign = db.one(conn, "SELECT * FROM campaigns WHERE id = ?", (queue["campaign_id"],))
    domain = db.one(conn, "SELECT * FROM domains WHERE id = ?", (mailbox["domain_id"],)) if mailbox else None
    if not all([draft, lead, mailbox, campaign, domain]):
        raise SendError("Queue item points to missing data")

    _check_eligible(conn, queue, draft, lead, mailbox, campaign, domain)

    message = _build_message(draft, lead, mailbox, domain["name"])
    message_id = _dispatch(message, mailbox)
    sent_at = db.now_iso()
    transport = mailbox.get("transport") or "mock"

    conn.execute(
        "INSERT INTO messages(draft_id, lead_id, campaign_id, mailbox_id, direction, from_email, to_email, "
        "subject, body, message_id, transport, status, sent_at, created_at) "
        "VALUES (?, ?, ?, ?, 'outbound', ?, ?, ?, ?, ?, ?, 'sent', ?, ?)",
        (
            draft["id"],
            lead["id"],
            campaign["id"],
            mailbox["id"],
            mailbox["email"],
            lead["email"],
            draft["subject"],
            draft["body"],
            message_id,
            transport,
            sent_at,
            sent_at,
        ),
    )
    conn.execute(
        "UPDATE send_queue SET status = 'sent', last_error = NULL, updated_at = ? WHERE id = ?",
        (sent_at, queue_id),
    )
    conn.execute(
        "UPDATE drafts SET status = 'sent', updated_at = ? WHERE id = ?",
        (sent_at, draft["id"]),
    )
    conn.execute(
        "UPDATE leads SET status = 'sent', updated_at = ? WHERE id = ?",
        (sent_at, lead["id"]),
    )
    conn.execute(
        "UPDATE mailboxes SET last_sent_at = ?, updated_at = ? WHERE id = ?",
        (sent_at, sent_at, mailbox["id"]),
    )
    date = usage_date(campaign)
    conn.execute(
        "INSERT INTO mailbox_usage_daily(mailbox_id, date, sent) VALUES (?, ?, 1) "
        "ON CONFLICT(mailbox_id, date) DO UPDATE SET sent = sent + 1",
        (mailbox["id"], date),
    )
    db.audit(
        conn,
        "message_sent",
        "draft",
        draft["id"],
        {
            "lead_id": lead["id"],
            "email": lead["email"],
            "mailbox": mailbox["email"],
            "transport": transport,
            "message_id": message_id,
        },
    )
    return {
        "ok": True,
        "queue_id": queue_id,
        "message_id": message_id,
        "mailbox": mailbox["email"],
        "transport": transport,
    }


def test_mailbox_connection(mailbox: dict[str, Any]) -> dict[str, Any]:
    transport = mailbox.get("transport") or "mock"
    if transport == "mock":
        return {"ok": True, "message": "Mock transport is ready. No email will leave this Mac."}
    if transport == "smtp":
        password = crypto.decrypt(mailbox.get("smtp_password_enc"))
        if not mailbox.get("smtp_host") or not mailbox.get("smtp_port"):
            return {"ok": False, "message": "SMTP host and port are required."}
        port = int(mailbox["smtp_port"])
        try:
            if port == 465:
                client = smtplib.SMTP_SSL(
                    mailbox["smtp_host"],
                    port,
                    timeout=15,
                    context=ssl.create_default_context(),
                )
            else:
                client = smtplib.SMTP(mailbox["smtp_host"], port, timeout=15)
            try:
                client.ehlo()
                if port != 465:
                    try:
                        client.starttls(context=ssl.create_default_context())
                        client.ehlo()
                    except smtplib.SMTPNotSupportedError:
                        pass
                if mailbox.get("smtp_username"):
                    client.login(mailbox["smtp_username"], password or "")
                return {"ok": True, "message": "SMTP login succeeded. No test email was sent."}
            finally:
                try:
                    client.quit()
                except Exception:
                    pass
        except Exception as exc:
            return {"ok": False, "message": f"SMTP connection failed: {exc}"}
    if transport == "gas":
        if not mailbox.get("gas_url"):
            return {"ok": False, "message": "Apps Script URL is missing."}
        secret = crypto.decrypt(mailbox.get("gas_secret_enc")) or ""
        payload = json.dumps({"action": "ping", "secret": secret}).encode("utf-8")
        request = urllib.request.Request(
            mailbox["gas_url"],
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                data = json.loads(response.read().decode("utf-8"))
            if data.get("ok"):
                return {"ok": True, "message": "Apps Script webhook responded."}
            return {"ok": False, "message": str(data.get("error") or "Webhook refused the ping.")}
        except Exception as exc:
            return {"ok": False, "message": f"Webhook failed: {exc}"}
    return {"ok": False, "message": f"Unknown transport: {transport}"}

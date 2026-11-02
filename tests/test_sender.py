from __future__ import annotations

from app import config, db
from app.services import approvals, sender, worker


def test_message_headers_are_sanitized():
    message = sender._build_message(
        {"subject": "Hello\r\nBcc: evil@example.test", "body": "Body", "campaign_id": 1},
        {"id": 1, "name": "Ada\r\nBcc: evil@example.test", "email": "ada@example.test"},
        {"email": "sender@example.test", "display_name": "Sender\r\nBcc: evil@example.test"},
        "example.test",
    )
    assert message["Bcc"] is None
    assert "\r" not in str(message["Subject"])
    assert "\n" not in str(message["Subject"])
    assert "\r" not in str(message["To"])
    assert sender.clean_header("a\r\nb") == "a b"


def test_mock_send_marks_message_sent(seeded):
    draft = db.one(seeded, "SELECT * FROM drafts WHERE status = 'pending' ORDER BY id LIMIT 1")
    assert draft
    with db.transaction() as conn:
        result = approvals.approve_draft(conn, draft["id"])
    queue_id = result["queue"]["id"]
    with db.transaction() as conn:
        conn.execute(
            "UPDATE send_queue SET scheduled_at = ? WHERE id = ?",
            (db.now_iso(), queue_id),
        )
    result = worker.tick()
    assert result["sent"] == 1
    message = db.one(seeded, "SELECT * FROM messages WHERE draft_id = ?", (draft["id"],))
    assert message
    assert message["transport"] == "mock"
    assert message["status"] == "sent"
    assert db.one(seeded, "SELECT status FROM drafts WHERE id = ?", (draft["id"],))["status"] == "sent"
    assert db.one(seeded, "SELECT status FROM leads WHERE id = ?", (draft["lead_id"],))["status"] == "sent"
    files = list(config.OUTBOX_DIR.glob("*.eml"))
    assert files


def test_campaign_daily_limit_blocks_a_burst(seeded):
    campaign = db.one(
        seeded,
        """
        SELECT c.* FROM campaigns c
        WHERE (SELECT COUNT(*) FROM drafts d WHERE d.campaign_id = c.id AND d.status = 'pending') >= 2
          AND (SELECT COUNT(*) FROM messages m WHERE m.campaign_id = c.id AND m.status = 'sent'
               AND date(m.sent_at, 'localtime') = date('now', 'localtime')) = 0
        ORDER BY c.id LIMIT 1
        """,
    )
    assert campaign
    drafts = db.rows(
        seeded,
        "SELECT * FROM drafts WHERE campaign_id = ? AND status = 'pending' ORDER BY id LIMIT 2",
        (campaign["id"],),
    )
    assert len(drafts) == 2
    with db.transaction() as conn:
        conn.execute("UPDATE campaigns SET daily_limit = 1 WHERE id = ?", (campaign["id"],))
    queue_ids = []
    for draft in drafts:
        with db.transaction() as conn:
            result = approvals.approve_draft(conn, draft["id"])
        queue_ids.append(result["queue"]["id"])
    with db.transaction() as conn:
        conn.executemany(
            "UPDATE send_queue SET scheduled_at = ? WHERE id = ?",
            [(db.now_iso(), queue_id) for queue_id in queue_ids],
        )
    sent = worker.tick()
    assert sent["sent"] == 1
    messages = db.one(
        seeded,
        "SELECT COUNT(*) AS count FROM messages WHERE campaign_id = ? AND status = 'sent'",
        (campaign["id"],),
    )
    assert messages["count"] == 1
    blocked = db.one(seeded, "SELECT status, last_error FROM send_queue WHERE id = ?", (queue_ids[1],))
    assert blocked["status"] == "queued"
    assert "Campaign daily limit reached" in (blocked["last_error"] or "")


def test_global_pause_blocks_the_worker(seeded):
    draft = db.one(seeded, "SELECT * FROM drafts WHERE status = 'pending' ORDER BY id LIMIT 1")
    with db.transaction() as conn:
        result = approvals.approve_draft(conn, draft["id"])
    with db.transaction() as conn:
        conn.execute("UPDATE send_queue SET scheduled_at = ? WHERE id = ?", (db.now_iso(), result["queue"]["id"]))
        db.set_setting(conn, "sending_paused", "1")
    tick = worker.tick()
    assert tick["sent"] == 0
    queue = db.one(seeded, "SELECT status, last_error FROM send_queue WHERE id = ?", (result["queue"]["id"],))
    assert queue["status"] == "queued"
    assert "paused" in (queue["last_error"] or "").lower()


def test_duplicate_send_is_not_created(seeded):
    draft = db.one(seeded, "SELECT * FROM drafts WHERE status = 'pending' ORDER BY id LIMIT 1")
    with db.transaction() as conn:
        result = approvals.approve_draft(conn, draft["id"])
    queue_id = result["queue"]["id"]
    with db.transaction() as conn:
        conn.execute("UPDATE send_queue SET scheduled_at = ? WHERE id = ?", (db.now_iso(), queue_id))
    worker.tick()
    worker.tick()
    count = db.one(seeded, "SELECT COUNT(*) AS c FROM messages WHERE draft_id = ?", (draft["id"],))
    assert count["c"] == 1

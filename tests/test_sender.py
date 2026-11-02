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

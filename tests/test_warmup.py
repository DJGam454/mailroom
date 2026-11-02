from __future__ import annotations

import random

from app import config, db
from app.services import warmup


def test_ramp_target() -> None:
    ramp = [2, 2, 2, 4, 4, 4, 4, 6]
    assert warmup.ramp_target(1, 10, ramp) == 2
    assert warmup.ramp_target(4, 10, ramp) == 4
    assert warmup.ramp_target(8, 10, ramp) == 6
    assert warmup.ramp_target(99, 10, ramp) == 6
    assert warmup.ramp_target(1, 1, ramp) == 1


def test_warmup_closed_pool_cycle(seeded):
    random.seed(3)
    with db.transaction() as conn:
        warmup.update_settings(
            conn,
            {
                "warmup_reply_rate": "1",
                "warmup_open_rate": "1",
                "warmup_min_gap_seconds": "1",
                "warmup_max_gap_seconds": "1",
            },
        )
        mailbox_ids = [row["id"] for row in db.rows(conn, "SELECT id FROM mailboxes ORDER BY id LIMIT 5")]
        warmup.start(conn, mailbox_ids, daily_limit=2)
    first = warmup.tick()
    assert first["generated"] > 0
    threads = db.rows(seeded, "SELECT * FROM warmup_threads")
    assert threads
    # Every pair must cross a domain boundary.
    for thread in threads:
        source = db.one(seeded, "SELECT * FROM mailboxes WHERE id = ?", (thread["source_mailbox_id"],))
        target = db.one(seeded, "SELECT * FROM mailboxes WHERE id = ?", (thread["target_mailbox_id"],))
        assert source["domain_id"] != target["domain_id"]
        assert source["id"] != target["id"]

    with db.transaction() as conn:
        conn.execute("UPDATE warmup_queue SET scheduled_at = ? WHERE kind = 'send'", (db.now_iso(),))
    sent = warmup.tick()
    assert sent["sent"] > 0
    messages = db.rows(seeded, "SELECT * FROM warmup_messages WHERE kind = 'initial'")
    assert messages
    assert all(message["message_id"] for message in messages)
    assert list(config.WARMUP_OUTBOX_DIR.glob("*.eml"))

    with db.transaction() as conn:
        conn.execute("UPDATE warmup_queue SET scheduled_at = ? WHERE kind IN ('open', 'reply')", (db.now_iso(),))
    engagement = warmup.tick()
    assert engagement["opened"] > 0
    assert engagement["replied"] > 0
    opened = db.one(seeded, "SELECT COUNT(*) AS c FROM warmup_messages WHERE kind = 'initial' AND read_at IS NOT NULL")
    replies = db.one(seeded, "SELECT COUNT(*) AS c FROM warmup_messages WHERE kind = 'reply'")
    assert opened["c"] > 0
    assert replies["c"] > 0
    status = warmup.status(seeded)
    assert status["summary"]["active"] == 5
    assert status["summary"]["sent_today"] > 0
    assert status["algorithm"]["cross_domain"] is True


def test_warmup_respects_daily_target(seeded):
    random.seed(4)
    with db.transaction() as conn:
        mailbox_ids = [row["id"] for row in db.rows(conn, "SELECT id FROM mailboxes ORDER BY id LIMIT 3")]
        warmup.start(conn, mailbox_ids, daily_limit=1)
    warmup.tick()
    warmup.tick()
    warmup.tick()
    for mailbox_id in mailbox_ids:
        count = db.one(
            seeded,
            "SELECT COUNT(*) AS c FROM warmup_threads WHERE source_mailbox_id = ?",
            (mailbox_id,),
        )
        assert count["c"] <= 1

from __future__ import annotations

import pytest

from app import db
from app.services import approvals, rotation


def first_pending(conn) -> dict:
    draft = db.one(conn, "SELECT * FROM drafts WHERE status = 'pending' ORDER BY id LIMIT 1")
    assert draft
    return draft


def test_seed_has_a_full_rotation_pool(seeded):
    campaign = db.one(seeded, "SELECT * FROM campaigns WHERE name LIKE 'Demo - NCR SME%'")
    assert campaign
    candidates = rotation.eligible_mailboxes(seeded, campaign)
    assert len(candidates) == 25
    picked = rotation.pick_mailbox(seeded, campaign)
    assert picked
    assert picked["email"].endswith("@atlas-outreach.test") or "@" in picked["email"]


def test_approval_reserves_a_mailbox_and_queue_slot(seeded):
    draft = first_pending(seeded)
    with db.transaction() as conn:
        result = approvals.approve_draft(conn, draft["id"])
    assert result["queue"]["status"] == "queued"
    assert result["mailbox"]["email"]
    assert result["queue"]["scheduled_at"]
    updated = db.one(seeded, "SELECT status FROM drafts WHERE id = ?", (draft["id"],))
    assert updated["status"] == "queued"


def test_rotation_spreads_across_more_than_one_mailbox(seeded):
    drafts = db.rows(seeded, "SELECT id FROM drafts WHERE status = 'pending' ORDER BY id LIMIT 5")
    used = []
    with db.transaction() as conn:
        for row in drafts:
            result = approvals.approve_draft(conn, row["id"])
            used.append(result["mailbox"]["id"])
    assert len(set(used)) > 1


def test_deny_is_terminal_and_can_suppress(seeded):
    draft = first_pending(seeded)
    with db.transaction() as conn:
        result = approvals.deny_draft(conn, draft["id"], "Not a fit", suppress=True)
    assert result["draft"]["status"] == "denied"
    assert result["lead"]["status"] == "suppressed"
    suppression = db.one(
        seeded,
        "SELECT * FROM suppression WHERE email = ?",
        (result["lead"]["email"],),
    )
    assert suppression
    with pytest.raises(approvals.ApprovalError):
        with db.transaction() as conn:
            approvals.approve_draft(conn, draft["id"])


def test_suppressed_contact_cannot_be_queued(seeded):
    draft = first_pending(seeded)
    lead = db.one(seeded, "SELECT * FROM leads WHERE id = ?", (draft["lead_id"],))
    with db.transaction() as conn:
        conn.execute(
            "INSERT INTO suppression(email, reason) VALUES (?, ?)",
            (lead["email"].lower(), "test suppression"),
        )
    with pytest.raises(approvals.ApprovalError):
        with db.transaction() as conn:
            approvals.approve_draft(conn, draft["id"])

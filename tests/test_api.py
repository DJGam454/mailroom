from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_health_and_overview(seeded):
    with TestClient(app) as client:
        health = client.get("/api/health")
        assert health.status_code == 200
        assert health.json()["ok"] is True
        overview = client.get("/api/overview")
        assert overview.status_code == 200
        assert overview.json()["stats"]["lead_count"] > 0
        assert "warmup_active" in overview.json()["stats"]
        assert client.get("/api/warmup").status_code == 200


def test_approval_api(seeded):
    with TestClient(app) as client:
        pending = client.get("/api/approvals?page_size=1").json()
        assert pending["total"] > 0
        draft_id = pending["items"][0]["draft_id"]
        response = client.post(f"/api/approvals/{draft_id}/approve", json={})
        assert response.status_code == 200
        assert response.json()["queue"]["status"] == "queued"
        queue = client.get("/api/queue").json()
        assert queue["items"]
        queue_id = next(item["id"] for item in queue["items"] if item["draft_id"] == draft_id)
        sent = client.post(f"/api/queue/{queue_id}/send-now")
        assert sent.status_code == 200
        recent = client.get("/api/queue?status=sent&limit=1").json()
        assert recent["items"][0]["id"] == queue_id
        detail = client.get(f"/api/leads/{pending['items'][0]['lead_id']}").json()
        assert detail["message"]["status"] == "sent"
        assert detail["queue"]["mailbox_email"]


def test_repeat_send_blocked_across_campaigns(seeded):
    from app import db

    sent = db.one(
        seeded,
        "SELECT to_email, campaign_id FROM messages WHERE direction = 'outbound' AND status = 'sent' LIMIT 1",
    )
    assert sent
    other = db.one(
        seeded,
        "SELECT id FROM campaigns WHERE id != ? AND status = 'active' LIMIT 1",
        (sent["campaign_id"],),
    )
    assert other
    now = db.now_iso()
    lead_id = seeded.execute(
        "INSERT INTO leads(campaign_id, name, email, status, created_at, updated_at) "
        "VALUES (?, 'Repeat Contact', ?, 'pending_approval', ?, ?)",
        (other["id"], sent["to_email"], now, now),
    ).lastrowid
    draft_id = seeded.execute(
        "INSERT INTO drafts(lead_id, campaign_id, subject, body, status, created_at, updated_at) "
        "VALUES (?, ?, 'Hello again', 'This should be blocked.', 'pending', ?, ?)",
        (lead_id, other["id"], now, now),
    ).lastrowid
    seeded.commit()
    with TestClient(app) as client:
        response = client.post(f"/api/approvals/{draft_id}/approve", json={})
        assert response.status_code == 400
        assert "already emailed" in response.json()["detail"]

        mailbox = db.one(
            seeded,
            "SELECT mailbox_id FROM messages WHERE direction = 'outbound' AND status = 'sent' LIMIT 1",
        )
        seeded.execute("UPDATE drafts SET status = 'queued' WHERE id = ?", (draft_id,))
        queue_id = seeded.execute(
            "INSERT INTO send_queue(draft_id, lead_id, campaign_id, mailbox_id, scheduled_at, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, 'queued', ?, ?)",
            (draft_id, lead_id, other["id"], mailbox["mailbox_id"], now, now, now),
        ).lastrowid
        seeded.commit()
        sent = client.post(f"/api/queue/{queue_id}/send-now")
        assert sent.status_code == 400
        assert "already received" in sent.json()["detail"]


def test_queue_filters_by_campaign(seeded):
    with TestClient(app) as client:
        pending = client.get("/api/approvals?page_size=1").json()["items"][0]
        approved = client.post(f"/api/approvals/{pending['draft_id']}/approve", json={})
        assert approved.status_code == 200
        queue = client.get(f"/api/queue?campaign_id={pending['campaign_id']}").json()
        assert queue["items"]
        assert all(item["campaign_id"] == pending["campaign_id"] for item in queue["items"])
        assert queue["counts"]["queued"] >= 1
        assert queue["sending_paused"] is False


def test_send_now_retries_failed_item(seeded):
    from app import db

    with TestClient(app) as client:
        pending = client.get("/api/approvals?page_size=1").json()["items"][0]
        approved = client.post(f"/api/approvals/{pending['draft_id']}/approve", json={})
        assert approved.status_code == 200
        queue_id = approved.json()["queue"]["id"]
        now = db.now_iso()
        seeded.execute("UPDATE send_queue SET status = 'failed', attempts = 3 WHERE id = ?", (queue_id,))
        seeded.execute("UPDATE drafts SET status = 'failed' WHERE id = ?", (pending["draft_id"],))
        seeded.execute("UPDATE leads SET status = 'failed' WHERE id = ?", (pending["lead_id"],))
        seeded.commit()
        retried = client.post(f"/api/queue/{queue_id}/send-now")
        assert retried.status_code == 200
        assert retried.json()["ok"] is True
        row = db.one(seeded, "SELECT status, attempts FROM send_queue WHERE id = ?", (queue_id,))
        assert row["status"] == "sent"
        assert row["attempts"] == 0


def test_duplicate_queued_send_blocked(seeded):
    from app import db

    with TestClient(app) as client:
        pending = client.get("/api/approvals?page_size=1").json()["items"][0]
        approved = client.post(f"/api/approvals/{pending['draft_id']}/approve", json={})
        assert approved.status_code == 200
        other = db.one(
            seeded,
            "SELECT id FROM campaigns WHERE id != ? AND status = 'active' LIMIT 1",
            (pending["campaign_id"],),
        )
        now = db.now_iso()
        lead_id = seeded.execute(
            "INSERT INTO leads(campaign_id, name, email, status, created_at, updated_at) "
            "VALUES (?, ?, ?, 'pending_approval', ?, ?)",
            (other["id"], pending["name"], pending["email"], now, now),
        ).lastrowid
        draft_id = seeded.execute(
            "INSERT INTO drafts(lead_id, campaign_id, subject, body, status, created_at, updated_at) "
            "VALUES (?, ?, 'Duplicate', 'This should be blocked.', 'pending', ?, ?)",
            (lead_id, other["id"], now, now),
        ).lastrowid
        seeded.commit()
        duplicate = client.post(f"/api/approvals/{draft_id}/approve", json={})
        assert duplicate.status_code == 400
        assert "queued send" in duplicate.json()["detail"]


def test_auto_approval_is_rejected(seeded):
    with TestClient(app) as client:
        response = client.post("/api/campaigns", json={"name": "Auto campaign", "approval_mode": "auto"})
        assert response.status_code == 422


def test_suppression_cancels_pending_work(seeded):
    from app import db

    with TestClient(app) as client:
        pending = client.get("/api/approvals?page_size=1").json()["items"][0]
        approved = client.post(f"/api/approvals/{pending['draft_id']}/approve", json={})
        assert approved.status_code == 200
        queue_id = approved.json()["queue"]["id"]
        suppressed = client.post(
            "/api/suppression",
            json={"email": pending["email"], "reason": "asked to stop"},
        )
        assert suppressed.status_code == 200
        assert suppressed.json()["drafts_denied"] == 1
        assert suppressed.json()["queue_cancelled"] == 1
        lead = db.one(seeded, "SELECT status FROM leads WHERE id = ?", (pending["lead_id"],))
        draft = db.one(seeded, "SELECT status FROM drafts WHERE id = ?", (pending["draft_id"],))
        queue = db.one(seeded, "SELECT status FROM send_queue WHERE id = ?", (queue_id,))
        assert lead["status"] == "suppressed"
        assert draft["status"] == "denied"
        assert queue["status"] == "cancelled"


def test_deny_with_suppress(seeded):
    from app import db

    with TestClient(app) as client:
        pending = client.get("/api/approvals?page_size=1").json()["items"][0]
        denied = client.post(
            f"/api/approvals/{pending['draft_id']}/deny",
            json={"reason": "asked to stop", "suppress": True},
        )
        assert denied.status_code == 200
        assert client.get("/api/suppression").json()["items"]
        lead = db.one(seeded, "SELECT status FROM leads WHERE id = ?", (pending["lead_id"],))
        assert lead["status"] == "suppressed"


def test_bounced_lead_cannot_be_approved(seeded):
    with TestClient(app) as client:
        pending = client.get("/api/approvals?page_size=1").json()["items"][0]
        seeded.execute("UPDATE leads SET status = 'bounced' WHERE id = ?", (pending["lead_id"],))
        seeded.commit()
        response = client.post(f"/api/approvals/{pending['draft_id']}/approve", json={})
        assert response.status_code == 400
        assert "cannot be approved" in response.json()["detail"]


def test_denied_draft_is_terminal(seeded):
    with TestClient(app) as client:
        pending = client.get("/api/approvals?page_size=1").json()["items"][0]
        denied = client.post(f"/api/approvals/{pending['draft_id']}/deny", json={"reason": "not a fit"})
        assert denied.status_code == 200
        edited = client.patch(
            f"/api/drafts/{pending['draft_id']}",
            json={"subject": "Try again", "body": "This should fail."},
        )
        assert edited.status_code == 400
        assert "terminal" in edited.json()["detail"]
        regenerated = client.post(f"/api/drafts/{pending['draft_id']}/regenerate")
        assert regenerated.status_code == 400


def test_approval_search(seeded):
    with TestClient(app) as client:
        from urllib.parse import quote

        first = client.get("/api/approvals?page_size=1").json()["items"][0]
        found = client.get(f"/api/approvals?q={quote(first['email'])}").json()
        assert found["total"] >= 1
        assert any(item["email"] == first["email"] for item in found["items"])
        missing = client.get("/api/approvals?q=no-such-person-xyz").json()
        assert missing["total"] == 0


def test_export_can_be_reimported(seeded):
    with TestClient(app) as client:
        campaigns = client.get("/api/campaigns").json()["items"]
        source, target = campaigns[0], campaigns[1]
        exported = client.get(f"/api/leads/export.csv?campaign_id={source['id']}")
        assert exported.status_code == 200
        response = client.post(
            "/api/leads/import",
            data={"campaign_id": str(target["id"])},
            files={"file": ("mailroom-export.csv", exported.content, "text/csv")},
        )
        assert response.status_code == 200
        assert response.json()["imported"] > 0
        assert response.json()["skipped"] == 0


def test_global_pause_blocks_approval(seeded):
    with TestClient(app) as client:
        saved = client.patch("/api/settings", json={"values": {"sending_paused": "1"}})
        assert saved.status_code == 200
        assert saved.json()["values"]["sending_paused"] == "1"
        assert not any(key.endswith("_enc") for key in saved.json()["values"])
        assert client.get("/api/overview").json()["stats"]["sending_paused"] is True
        pending = client.get("/api/approvals?page_size=1").json()
        response = client.post(f"/api/approvals/{pending['items'][0]['draft_id']}/approve", json={})
        assert response.status_code == 400
        assert "paused globally" in response.json()["detail"]


def test_campaign_patch_api(seeded):
    with TestClient(app) as client:
        campaign = client.get("/api/campaigns").json()["items"][0]
        response = client.patch(
            f"/api/campaigns/{campaign['id']}",
            json={"daily_limit": 99, "window_start": "08:00", "window_end": "18:00"},
        )
        assert response.status_code == 200
        assert response.json()["daily_limit"] == 99
        assert response.json()["window_start"] == "08:00"


def test_campaign_and_leads_api(seeded):
    with TestClient(app) as client:
        campaigns = client.get("/api/campaigns").json()
        assert len(campaigns["items"]) >= 2
        leads = client.get("/api/leads?page_size=5").json()
        assert leads["total"] >= 1
        assert leads["items"][0]["campaign_name"]
        mailbox = client.get("/api/mailboxes").json()["items"][0]
        assert "warmup_sent_today" in mailbox
        assert mailbox["combined_sent_today"] == mailbox["sent_today"] + mailbox["warmup_sent_today"]
        assert client.get("/api/domains").status_code == 200
        deliverability = client.get("/api/deliverability").json()
        assert "warmup_sent_today" in deliverability["mailboxes"][0]
        assert "warmup_sent_today" in deliverability["domains"][0]
        assert client.get("/api/activity").status_code == 200
        assert client.get("/api/queue").status_code == 200
        assert client.get("/api/sheets/status").status_code == 200
        settings = client.get("/api/settings").json()["values"]
        assert settings["sender_name"]
        assert not any(key.endswith("_enc") for key in settings)


def test_suppression_api(seeded):
    with TestClient(app) as client:
        created = client.post("/api/suppression", json={"email": "stop@example.test", "reason": "manual"})
        assert created.status_code == 200
        assert client.get("/api/suppression").json()["items"]
        removed = client.delete("/api/suppression/stop%40example.test")
        assert removed.status_code == 200
        assert removed.json()["deleted"] == 1


def test_warmup_start_api(seeded):
    with TestClient(app) as client:
        first = client.get("/api/warmup").json()
        assert first["summary"]["total"] == 25
        started = client.post("/api/warmup/start", json={"daily_limit": 1})
        assert started.status_code == 200
        assert started.json()["started"] == 25
        status = client.get("/api/warmup").json()
        assert status["summary"]["active"] == 25


def test_csv_import_upload(seeded):
    with TestClient(app) as client:
        campaign_id = seeded.execute("SELECT id FROM campaigns ORDER BY id LIMIT 1").fetchone()[0]
        csv_body = (
            "Lead ID,Doctor Name,Contact Name,Email,Industry,Service Assigned,Notes,Website\n"
            "1,Upload Dental,,upload@example.test,Dental clinic,Website Development,"
            "\"140 reviews, 4.8* | Email grade: B\",https://example.test\n"
        )
        response = client.post(
            "/api/leads/import",
            data={"campaign_id": str(campaign_id)},
            files={"file": ("upload.csv", csv_body, "text/csv")},
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["imported"] == 1
        assert body["drafts"] == 1

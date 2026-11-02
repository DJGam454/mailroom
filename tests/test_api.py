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
        assert client.get("/api/mailboxes").status_code == 200
        assert client.get("/api/domains").status_code == 200
        assert client.get("/api/deliverability").status_code == 200
        assert client.get("/api/activity").status_code == 200
        assert client.get("/api/queue").status_code == 200
        assert client.get("/api/sheets/status").status_code == 200
        settings = client.get("/api/settings").json()["values"]
        assert settings["sender_name"]


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

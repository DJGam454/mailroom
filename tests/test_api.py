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


def test_campaign_and_leads_api(seeded):
    with TestClient(app) as client:
        campaigns = client.get("/api/campaigns").json()
        assert len(campaigns["items"]) >= 2
        leads = client.get("/api/leads?page_size=5").json()
        assert leads["total"] >= 1
        assert leads["items"][0]["campaign_name"]

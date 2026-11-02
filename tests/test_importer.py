from __future__ import annotations

import json

from app import db
from app.services import importer


def test_json_import_maps_and_drafts(conn, tmp_path):
    source = tmp_path / "leads.json"
    source.write_text(
        json.dumps(
            [
                {
                    "business_name": "Acme Design",
                    "contact_name": "Aarti Mehta",
                    "contact_title": "Founder",
                    "email": "aarti@acmedesign.test",
                    "industry": "Design studio",
                    "city": "Delhi",
                    "website": "https://acmedesign.test",
                    "observation": "12-person studio with a strong portfolio.",
                    "recommended_offer": "Reels + social video",
                    "email_grade": "A",
                    "verification": "Deliverable",
                },
                {
                    "business_name": "Acme Design",
                    "contact_name": "Aarti Mehta",
                    "contact_title": "Founder",
                    "email": "aarti@acmedesign.test",
                    "industry": "Design studio",
                    "city": "Delhi",
                    "email_grade": "A",
                },
            ]
        ),
        encoding="utf-8",
    )
    with db.transaction() as tx:
        result = importer.import_json(tx, source, "Test campaign")
    assert result["imported"] == 1
    assert result["skipped"] == 1
    assert result["drafts"] == 1
    lead = db.one(conn, "SELECT * FROM leads WHERE email = ?", ("aarti@acmedesign.test",))
    assert lead["company"] == "Acme Design"
    assert lead["role"] == "Founder"
    assert lead["status"] == "pending_approval"
    draft = db.one(conn, "SELECT * FROM drafts WHERE lead_id = ?", (lead["id"],))
    assert draft
    assert "Aarti" in draft["body"]


def test_import_is_idempotent(conn, tmp_path):
    source = tmp_path / "leads.json"
    source.write_text(
        json.dumps(
            [
                {
                    "business_name": "Beta Studio",
                    "contact_name": "Rohan Kapoor",
                    "email": "rohan@betastudio.test",
                    "industry": "Design studio",
                    "email_grade": "B",
                }
            ]
        ),
        encoding="utf-8",
    )
    with db.transaction() as tx:
        first = importer.import_json(tx, source, "Idempotent campaign")
    with db.transaction() as tx:
        second = importer.import_json(tx, source, "Idempotent campaign")
    assert first["imported"] == 1
    assert second["imported"] == 0
    assert second["skipped"] == 1

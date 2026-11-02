from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app import db
from app.services import sheets


class FakeWorksheet:
    def __init__(self, title="Fake"):
        self.title = title
        self.values = []
        self.col_count = 4

    def get_all_values(self):
        return self.values

    def resize(self, rows=None, cols=None):
        self.col_count = cols or self.col_count

    def clear(self):
        self.values = []

    def update(self, values, range_name=None, value_input_option=None):
        self.values = [list(row) for row in values]
        self.col_count = max(self.col_count, max(len(row) for row in values))


class FakeSpreadsheet:
    def __init__(self):
        self.title = "Fake workbook"
        self.worksheets = {}

    def worksheet(self, title):
        if title not in self.worksheets:
            import gspread

            raise gspread.exceptions.WorksheetNotFound(title)
        return self.worksheets[title]

    def add_worksheet(self, title, rows=1000, cols=10):
        worksheet = FakeWorksheet(title)
        self.worksheets[title] = worksheet
        return worksheet


def test_write_read_round_trip():
    worksheet = FakeWorksheet()
    headers = sheets.HEADERS["suppression"]
    sheets.write_tab(worksheet, headers, [["a@example.test", "reason", "2026-11-02T00:00:00Z"]])
    rows = sheets.read_tab(worksheet, headers)
    assert rows[0]["Email"] == "a@example.test"
    assert rows[0]["Reason"] == "reason"


def test_parse_sheet_time_iso_and_serial():
    assert sheets.parse_sheet_time("2026-11-02T10:00:00Z") is not None
    assert sheets.parse_sheet_time("2026-11-02T10:00:00+00:00") is not None
    serial = 46300.5
    parsed = sheets.parse_sheet_time(serial)
    assert parsed is not None
    assert parsed.year >= 2026


def test_build_rows(seeded):
    lead_rows = sheets.build_lead_rows(seeded)
    campaign_rows = sheets.build_campaign_rows(seeded)
    suppression_rows = sheets.build_suppression_rows(seeded)
    warmup_rows = sheets.build_warmup_rows(seeded)
    assert len(lead_rows[0]) == len(sheets.HEADERS["leads"])
    assert len(campaign_rows[0]) == len(sheets.HEADERS["campaigns"])
    assert suppression_rows == []
    assert len(warmup_rows) == 25
    assert len(warmup_rows[0]) == len(sheets.HEADERS["warmup"])


def test_remote_lead_update_and_conflict(seeded):
    lead = db.one(seeded, "SELECT * FROM leads ORDER BY id LIMIT 1")
    remote = {
        "ID": str(lead["id"]),
        "Campaign ID": str(lead["campaign_id"]),
        "Campaign": lead["campaign_id"],
        "Name": "Updated from Sheet",
        "Email": lead["email"],
        "Role": lead["role"],
        "Company": lead["company"],
        "Industry": lead["industry"],
        "City": lead["city"],
        "Website": lead["website"],
        "Status": lead["status"],
        "Verification": lead["verification"],
        "Grade": lead["email_grade"],
        "Notes": "Edited in Google Sheets",
        "Offer": lead["offer"],
        "Source": lead["source"],
        "Updated At": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
    }
    result = sheets.apply_remote_leads(seeded, [remote], policy="merge")
    seeded.commit()
    assert result["updated"] == 1
    updated = db.one(seeded, "SELECT * FROM leads WHERE id = ?", (lead["id"],))
    assert updated["name"] == "Updated from Sheet"

    # Force both sides to have changed after the last sync.
    state = db.one(seeded, "SELECT * FROM sheet_sync_state WHERE sheet_name = 'leads' AND entity_key = ?", (str(lead["id"]),))
    assert state
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    future_local = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    future_remote = (datetime.now(timezone.utc) + timedelta(hours=3)).isoformat()
    with db.transaction() as conn:
        conn.execute("UPDATE sheet_sync_state SET last_synced_at = ? WHERE sheet_name = 'leads' AND entity_key = ?", (past, str(lead["id"])))
        conn.execute("UPDATE leads SET updated_at = ? WHERE id = ?", (future_local, lead["id"]))
    remote["Name"] = "Conflicting Sheet Name"
    remote["Updated At"] = future_remote
    conflict = sheets.apply_remote_leads(seeded, [remote], policy="merge")
    assert conflict["conflicts"]
    still = db.one(seeded, "SELECT name FROM leads WHERE id = ?", (lead["id"],))
    assert still["name"] == "Updated from Sheet"


def test_full_sync_against_fake_worksheet(seeded, monkeypatch):
    fake = FakeSpreadsheet()
    monkeypatch.setattr(sheets, "_client", lambda conn: (fake, "svc@example.test"))
    with db.transaction() as conn:
        pushed = sheets.sync(conn, "push")
    assert pushed["ok"] is True
    assert set(fake.worksheets) == set(sheets.SHEET_TABS.values())
    lead_ws = fake.worksheets["Mailroom Leads"]
    assert len(lead_ws.values) > 20
    lead_header = lead_ws.values[0]
    lead_row = lead_ws.values[1]
    lead_id = lead_row[lead_header.index("ID")]
    lead_name_index = lead_header.index("Name")
    lead_updated_index = lead_header.index("Updated At")
    lead_row[lead_name_index] = "Pulled from fake sheet"
    # Deliberately leave Updated At unchanged: the content hash should catch it.
    with db.transaction() as conn:
        pulled = sheets.sync(conn, "pull")
    assert pulled["ok"] is True
    assert not pulled["conflicts"]
    updated = db.one(seeded, "SELECT name FROM leads WHERE id = ?", (lead_id,))
    assert updated["name"] == "Pulled from fake sheet"


def test_suppression_pull(seeded):
    result = sheets.apply_remote_suppression(
        seeded,
        [{"Email": "blocked@example.test", "Reason": "sheet unsub", "Created At": "2026-11-02T00:00:00Z"}],
    )
    assert result["inserted"] == 1
    row = db.one(seeded, "SELECT * FROM suppression WHERE email = ?", ("blocked@example.test",))
    assert row
    assert sheets.apply_remote_suppression(seeded, [{"Email": "blocked@example.test"}])["inserted"] == 0

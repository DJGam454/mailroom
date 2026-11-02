from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from app import db
from app.services import sheets


def _a1_rowcol(value: str) -> tuple[int, int]:
    match = re.match(r"^([A-Z]+)(\d+)$", value or "A1")
    if not match:
        return 0, 0
    column = 0
    for letter in match.group(1):
        column = column * 26 + (ord(letter) - ord("A") + 1)
    return int(match.group(2)) - 1, column - 1


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
        start_row, start_col = _a1_rowcol((range_name or "A1").split(":", 1)[0])
        width = max(len(row) for row in values) if values else 0
        while len(self.values) < start_row + len(values):
            self.values.append([])
        for row in self.values:
            row.extend([""] * max(0, start_col + width - len(row)))
        for offset, row in enumerate(values):
            for index, value in enumerate(row):
                self.values[start_row + offset][start_col + index] = str(value)
        self.col_count = max(self.col_count, width)


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


def test_write_tab_preserves_helper_columns():
    worksheet = FakeWorksheet()
    headers = sheets.HEADERS["suppression"]
    sheets.write_tab(worksheet, headers, [["a@example.test", "reason", "2026-11-02T00:00:00Z"]])
    worksheet.values[0].append("My note")
    worksheet.values[1].append("keep me")
    sheet_header = worksheet.values[0]
    assert sheet_header[-1] == "My note"
    sheets.write_tab(worksheet, headers, [["a@example.test", "updated", "2026-11-02T00:00:00Z"]])
    assert worksheet.values[0][-1] == "My note"
    assert worksheet.values[1][-1] == "keep me"
    assert worksheet.values[1][1] == "updated"


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


def test_invalid_sheet_edits_are_reported(seeded):
    campaign = db.one(
        seeded,
        "SELECT campaign_id FROM leads GROUP BY campaign_id HAVING COUNT(*) > 1 LIMIT 1",
    )
    leads = db.rows(
        seeded,
        "SELECT * FROM leads WHERE campaign_id = ? ORDER BY id LIMIT 2",
        (campaign["campaign_id"],),
    )
    future = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    duplicate = {
        "ID": str(leads[1]["id"]),
        "Campaign ID": str(campaign["campaign_id"]),
        "Name": leads[1]["name"],
        "Email": leads[0]["email"],
        "Updated At": future,
    }
    result = sheets.apply_remote_leads(seeded, [duplicate], policy="merge")
    assert result["errors"]
    assert result["updated"] == 0

    campaign_row = db.one(seeded, "SELECT * FROM campaigns WHERE id = ?", (campaign["campaign_id"],))
    bad_campaign = {
        "ID": str(campaign_row["id"]),
        "Name": campaign_row["name"],
        "Status": campaign_row["status"],
        "Daily Limit": "not-a-number",
        "Per-Domain Limit": "5",
        "Updated At": future,
    }
    result = sheets.apply_remote_campaigns(seeded, [bad_campaign], policy="merge")
    assert result["errors"]
    assert result["updated"] == 0


def test_suppression_pull(seeded):
    result = sheets.apply_remote_suppression(
        seeded,
        [{"Email": "blocked@example.test", "Reason": "sheet unsub", "Created At": "2026-11-02T00:00:00Z"}],
    )
    assert result["inserted"] == 1
    row = db.one(seeded, "SELECT * FROM suppression WHERE email = ?", ("blocked@example.test",))
    assert row
    assert sheets.apply_remote_suppression(seeded, [{"Email": "blocked@example.test"}])["inserted"] == 0

"""Google Sheets two-way sync.

Tabs:
  Mailroom Leads
  Mailroom Campaigns
  Mailroom Suppression
  Mailroom Warmup

Leads and campaigns are two-way. Suppression is unioned. Warmup is read-only.
The sync uses a service account and stores the JSON encrypted at rest.

Conflict model:
  - sheet_sync_state keeps the last local/remote timestamps per row.
  - if only remote changed, apply it;
  - if only local changed, leave it for the push;
  - if both changed, report a conflict;
  - merge policy never overwrites a conflict; local/remote are explicit
    operator choices.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any

from app import crypto, db
from app.services import drafting, warmup

SHEET_TABS = {
    "leads": "Mailroom Leads",
    "campaigns": "Mailroom Campaigns",
    "suppression": "Mailroom Suppression",
    "warmup": "Mailroom Warmup",
}

HEADERS = {
    "leads": [
        "ID",
        "Campaign ID",
        "Campaign",
        "Name",
        "Email",
        "Role",
        "Company",
        "Industry",
        "City",
        "Website",
        "Status",
        "Verification",
        "Grade",
        "Notes",
        "Offer",
        "Source",
        "Updated At",
    ],
    "campaigns": [
        "ID",
        "Name",
        "Status",
        "Approval Mode",
        "Daily Limit",
        "Per-Domain Limit",
        "Timezone",
        "Window Start",
        "Window End",
        "Working Days",
        "Rotation",
        "Updated At",
    ],
    "suppression": ["Email", "Reason", "Created At"],
    "warmup": [
        "Mailbox",
        "Domain",
        "Status",
        "Day",
        "Daily Target",
        "Sent Today",
        "Received Today",
        "Replies Today",
        "Health",
        "Updated At",
    ],
}


class SheetsError(Exception):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def parse_sheet_time(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = str(value).strip()
    if not text:
        return None
    # Google Sheets serial date, epoch 1899-12-30.
    try:
        number = float(text)
        if 0 < number < 100000:
            return (datetime(1899, 12, 30, tzinfo=timezone.utc) + timedelta(days=number))
    except ValueError:
        pass
    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        pass
    for fmt in ("%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _same_time(a: datetime | None, b: datetime | None) -> bool:
    if a is None or b is None:
        return False
    return abs((a - b).total_seconds()) <= 1


def _state(conn, sheet: str, key: str) -> dict[str, Any] | None:
    return db.one(
        conn,
        "SELECT * FROM sheet_sync_state WHERE sheet_name = ? AND entity_key = ?",
        (sheet, key),
    )


def _save_state(
    conn,
    sheet: str,
    key: str,
    local_updated: str | None,
    remote_updated: str | None,
    synced_at: str | None = None,
    content_hash: str | None = None,
) -> None:
    conn.execute(
        "INSERT INTO sheet_sync_state(sheet_name, entity_key, local_updated_at, remote_updated_at, last_synced_at, content_hash) "
        "VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(sheet_name, entity_key) DO UPDATE SET "
        "local_updated_at = excluded.local_updated_at, remote_updated_at = excluded.remote_updated_at, "
        "last_synced_at = excluded.last_synced_at, content_hash = excluded.content_hash",
        (sheet, key, local_updated, remote_updated, synced_at or _now(), content_hash),
    )


def _hash_row(row: dict[str, Any]) -> str:
    payload = {key: str(value) for key, value in sorted(row.items()) if key != "Updated At"}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def _client(conn):
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError as exc:
        raise SheetsError("Google Sheets support is not installed. Run pip install -r requirements.txt.") from exc

    raw = db.settings_dict(conn)
    spreadsheet_id = _normalize_spreadsheet_id(raw.get("google_sheets_spreadsheet_id") or "")
    encrypted = raw.get("google_sheets_credentials_enc") or ""
    if not spreadsheet_id or not encrypted:
        raise SheetsError("Google Sheets is not configured. Add a spreadsheet ID and service account JSON first.")
    try:
        info = json.loads(crypto.decrypt(encrypted) or "{}")
    except (ValueError, json.JSONDecodeError) as exc:
        raise SheetsError("The service account JSON could not be decrypted. Re-save it.") from exc
    try:
        credentials = Credentials.from_service_account_info(
            info,
            scopes=["https://www.googleapis.com/auth/spreadsheets"],
        )
        client = gspread.authorize(credentials)
        spreadsheet = client.open_by_key(spreadsheet_id)
    except Exception as exc:  # noqa: BLE001
        raise SheetsError(f"Could not open the Google Sheet: {exc}") from exc
    return spreadsheet, info.get("client_email", "")


def ensure_tabs(spreadsheet) -> dict[str, Any]:
    try:
        import gspread
    except ImportError as exc:
        raise SheetsError("gspread is not installed.") from exc

    worksheets = {}
    for key, title in SHEET_TABS.items():
        headers = HEADERS[key]
        try:
            worksheet = spreadsheet.worksheet(title)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=title, rows=1000, cols=len(headers))
            worksheet.update(values=[headers], range_name="A1", value_input_option="RAW")
        except Exception as exc:  # noqa: BLE001
            raise SheetsError(f"Could not open tab {title}: {exc}") from exc
        values = worksheet.get_all_values()
        if not values:
            worksheet.update(values=[headers], range_name="A1", value_input_option="RAW")
        else:
            existing = [str(item).strip() for item in values[0]]
            if existing[: len(headers)] != headers:
                raise SheetsError(
                    f"Tab '{title}' has different headers. Use a clean Mailroom tab or restore this header row."
                )
        worksheets[key] = worksheet
    return worksheets


def read_tab(worksheet, headers: list[str]) -> list[dict[str, str]]:
    values = worksheet.get_all_values()
    if len(values) < 2:
        return []
    header = [str(item).strip() for item in values[0]]
    if header[: len(headers)] != headers:
        raise SheetsError("The sheet header changed while reading. Run Test and check the tab headers.")
    rows = []
    for raw in values[1:]:
        if not any(str(item).strip() for item in raw):
            continue
        padded = list(raw) + [""] * max(0, len(headers) - len(raw))
        rows.append({key: padded[index] for index, key in enumerate(headers)})
    return rows


def write_tab(worksheet, headers: list[str], rows: list[list[Any]]) -> None:
    values = [headers] + [[str(value) if value is not None else "" for value in row] for row in rows]
    worksheet.resize(rows=max(1000, len(values)), cols=max(len(headers), worksheet.col_count))
    worksheet.clear()
    worksheet.update(values=values, range_name="A1", value_input_option="RAW")


def build_lead_rows(conn) -> list[list[Any]]:
    rows = db.rows(
        conn,
        """
        SELECT l.*, c.name AS campaign_name
        FROM leads l JOIN campaigns c ON c.id = l.campaign_id
        ORDER BY l.id
        """,
    )
    return [
        [
            row["id"],
            row["campaign_id"],
            row["campaign_name"],
            row["name"],
            row["email"],
            row["role"],
            row["company"],
            row["industry"],
            row["city"],
            row["website"],
            row["status"],
            row["verification"],
            row["email_grade"],
            row["notes"],
            row["offer"],
            row["source"],
            row["updated_at"],
        ]
        for row in rows
    ]


def build_campaign_rows(conn) -> list[list[Any]]:
    rows = db.rows(conn, "SELECT * FROM campaigns ORDER BY id")
    return [
        [
            row["id"],
            row["name"],
            row["status"],
            row["approval_mode"],
            row["daily_limit"],
            row["per_domain_limit"],
            row["timezone"],
            row["window_start"],
            row["window_end"],
            row["working_days"],
            row["rotation_strategy"],
            row["updated_at"],
        ]
        for row in rows
    ]


def build_suppression_rows(conn) -> list[list[Any]]:
    rows = db.rows(conn, "SELECT * FROM suppression ORDER BY email")
    return [[row["email"], row["reason"], row["created_at"]] for row in rows]


def build_warmup_rows(conn) -> list[list[Any]]:
    now = _now()
    rows = warmup.profile_rows(conn)
    return [
        [
            row["email"],
            row["domain_name"],
            row["status"],
            row["day"],
            row["daily_target"],
            row["sent_today"],
            row["received_today"],
            row["replies_today"],
            row["health"],
            now,
        ]
        for row in rows
    ]


def _normalize_remote_time(value: Any) -> datetime:
    return parse_sheet_time(value) or datetime.now(timezone.utc)


def _apply_lead_fields(conn, lead: dict[str, Any], remote: dict[str, Any]) -> None:
    email = (remote.get("Email") or lead["email"]).strip().lower()
    if not email or "@" not in email:
        return
    company = (remote.get("Company") or lead["company"] or "").strip()
    values = {
        "name": (remote.get("Name") or lead["name"] or "").strip(),
        "email": email,
        "role": (remote.get("Role") or lead["role"] or "").strip(),
        "company": company,
        "industry": (remote.get("Industry") or lead["industry"] or "").strip(),
        "company_domain": email.split("@", 1)[1] if "@" in email else lead["company_domain"],
        "city": (remote.get("City") or lead["city"] or "").strip(),
        "website": (remote.get("Website") or lead["website"] or "").strip(),
        "notes": (remote.get("Notes") or lead["notes"] or "").strip(),
        "offer": (remote.get("Offer") or lead["offer"] or "").strip(),
        "verification": (remote.get("Verification") or lead["verification"] or "Unknown").strip(),
        "email_grade": (remote.get("Grade") or lead["email_grade"] or "").strip(),
        "updated_at": _now(),
    }
    conn.execute(
        "UPDATE leads SET name=?, email=?, role=?, company=?, industry=?, company_domain=?, city=?, "
        "website=?, notes=?, offer=?, verification=?, email_grade=?, updated_at=? WHERE id=?",
        (
            values["name"],
            values["email"],
            values["role"],
            values["company"],
            values["industry"],
            values["company_domain"],
            values["city"],
            values["website"],
            values["notes"],
            values["offer"],
            values["verification"],
            values["email_grade"],
            values["updated_at"],
            lead["id"],
        ),
    )


def _find_campaign(conn, row: dict[str, Any]) -> dict[str, Any] | None:
    campaign_id = (row.get("Campaign ID") or "").strip()
    if campaign_id:
        found = db.one(conn, "SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
        if found:
            return found
    name = (row.get("Campaign") or "").strip()
    if name:
        return db.one(conn, "SELECT * FROM campaigns WHERE name = ?", (name,))
    return None


def apply_remote_leads(
    conn,
    remote_rows: list[dict[str, str]],
    policy: str = "merge",
    dry_run: bool = False,
) -> dict[str, Any]:
    created = 0
    updated = 0
    conflicts: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    drafts_for: set[int] = set()
    for remote in remote_rows:
        remote_id = (remote.get("ID") or "").strip()
        campaign = _find_campaign(conn, remote)
        local = None
        if remote_id:
            local = db.one(conn, "SELECT * FROM leads WHERE id = ?", (remote_id,))
        if not local and campaign:
            email = (remote.get("Email") or "").strip().lower()
            if email:
                local = db.one(
                    conn,
                    "SELECT * FROM leads WHERE campaign_id = ? AND email = ?",
                    (campaign["id"], email),
                )
        if not local:
            if not campaign:
                errors.append({"row": remote_id or remote.get("Email"), "error": "Campaign not found"})
                continue
            email = (remote.get("Email") or "").strip().lower()
            if not email or "@" not in email:
                errors.append({"row": remote_id or remote.get("Email"), "error": "Valid email is required"})
                continue
            if not dry_run:
                try:
                    cursor = conn.execute(
                        "INSERT INTO leads(campaign_id, external_id, name, email, role, company, industry, company_domain, "
                        "website, city, notes, offer, email_grade, verification, source, status, created_at, updated_at) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Google Sheet', 'new', ?, ?)",
                        (
                            campaign["id"],
                            remote_id or None,
                            (remote.get("Name") or email).strip(),
                            email,
                            (remote.get("Role") or "").strip(),
                            (remote.get("Company") or "").strip(),
                            (remote.get("Industry") or "").strip(),
                            email.split("@", 1)[1],
                            (remote.get("Website") or "").strip(),
                            (remote.get("City") or "").strip(),
                            (remote.get("Notes") or "").strip(),
                            (remote.get("Offer") or "").strip(),
                            (remote.get("Grade") or "").strip(),
                            (remote.get("Verification") or "Unknown").strip(),
                            _now(),
                            _now(),
                        ),
                    )
                    lead_id = int(cursor.lastrowid)
                    _save_state(
                        conn,
                        "leads",
                        str(lead_id),
                        _now(),
                        _normalized_remote_time(remote.get("Updated At")),
                        content_hash=_hash_row(remote),
                    )
                    drafts_for.add(campaign["id"])
                    created += 1
                except Exception as exc:  # noqa: BLE001
                    errors.append({"row": remote_id or email, "error": str(exc)})
            continue

        remote_updated = _normalize_remote_time(remote.get("Updated At"))
        remote_hash = _hash_row(remote)
        local_updated = parse_sheet_time(local.get("updated_at"))
        state = _state(conn, "leads", str(local["id"]))
        last_synced = parse_sheet_time(state.get("last_synced_at")) if state else None
        local_changed = bool(state and local_updated and last_synced and local_updated > last_synced)
        remote_changed = bool(
            state
            and (
                (last_synced and remote_updated > last_synced)
                or (state.get("content_hash") and state["content_hash"] != remote_hash)
            )
        )
        if state is None:
            local_changed = bool(local_updated and remote_updated and local_updated > remote_updated + timedelta(seconds=1))
            remote_changed = bool(local_updated and remote_updated and remote_updated > local_updated + timedelta(seconds=1))
        if local_changed and remote_changed and not _same_time(local_updated, remote_updated):
            conflict = {
                "sheet": "leads",
                "id": local["id"],
                "email": local["email"],
                "local_updated": local.get("updated_at"),
                "remote_updated": remote.get("Updated At"),
            }
            conflicts.append(conflict)
            if policy == "remote" and not dry_run:
                _apply_lead_fields(conn, local, remote)
                _save_state(conn, "leads", str(local["id"]), _now(), _iso(remote_updated), content_hash=remote_hash)
                updated += 1
            continue
        if remote_changed:
            if not dry_run:
                _apply_lead_fields(conn, local, remote)
                _save_state(conn, "leads", str(local["id"]), _now(), _iso(remote_updated), content_hash=remote_hash)
            updated += 1
        elif state is None and not dry_run:
            _save_state(conn, "leads", str(local["id"]), local.get("updated_at"), _iso(remote_updated), content_hash=remote_hash)
    if drafts_for and not dry_run:
        for campaign_id in drafts_for:
            drafting.generate_drafts(conn, campaign_id)
    return {"created": created, "updated": updated, "conflicts": conflicts, "errors": errors}


def apply_remote_campaigns(
    conn,
    remote_rows: list[dict[str, str]],
    policy: str = "merge",
    dry_run: bool = False,
) -> dict[str, Any]:
    updated = 0
    conflicts: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for remote in remote_rows:
        remote_id = (remote.get("ID") or "").strip()
        local = db.one(conn, "SELECT * FROM campaigns WHERE id = ?", (remote_id,)) if remote_id else None
        if not local:
            errors.append({"row": remote_id or remote.get("Name"), "error": "Campaign ID not found"})
            continue
        remote_updated = _normalize_remote_time(remote.get("Updated At"))
        remote_hash = _hash_row(remote)
        local_updated = parse_sheet_time(local.get("updated_at"))
        state = _state(conn, "campaigns", str(local["id"]))
        last_synced = parse_sheet_time(state.get("last_synced_at")) if state else None
        local_changed = bool(state and local_updated and last_synced and local_updated > last_synced)
        remote_changed = bool(
            state
            and (
                (last_synced and remote_updated > last_synced)
                or (state.get("content_hash") and state["content_hash"] != remote_hash)
            )
        )
        if state is None:
            local_changed = bool(local_updated and remote_updated and local_updated > remote_updated + timedelta(seconds=1))
            remote_changed = bool(local_updated and remote_updated and remote_updated > local_updated + timedelta(seconds=1))
        if local_changed and remote_changed and not _same_time(local_updated, remote_updated):
            conflicts.append(
                {
                    "sheet": "campaigns",
                    "id": local["id"],
                    "name": local["name"],
                    "local_updated": local.get("updated_at"),
                    "remote_updated": remote.get("Updated At"),
                }
            )
            if policy != "remote" or dry_run:
                continue
        if remote_changed or (state is None and policy == "remote"):
            fields = {
                "name": (remote.get("Name") or local["name"]).strip(),
                "status": (remote.get("Status") or local["status"]).strip().lower(),
                # Auto-send is intentionally not implemented. A sheet edit can
                # never bypass the human approval step.
                "approval_mode": "manual",
                "daily_limit": int(remote.get("Daily Limit") or local["daily_limit"]),
                "per_domain_limit": int(remote.get("Per-Domain Limit") or local["per_domain_limit"]),
                "timezone": (remote.get("Timezone") or local["timezone"]).strip(),
                "window_start": (remote.get("Window Start") or local["window_start"]).strip(),
                "window_end": (remote.get("Window End") or local["window_end"]).strip(),
                "working_days": (remote.get("Working Days") or local["working_days"]).strip(),
                "rotation_strategy": (remote.get("Rotation") or local["rotation_strategy"]).strip().lower(),
            }
            if fields["status"] not in {"draft", "active", "paused", "archived"}:
                errors.append({"row": local["id"], "error": "Invalid campaign status"})
                continue
            if not dry_run:
                try:
                    conn.execute(
                        "UPDATE campaigns SET name=?, status=?, approval_mode=?, daily_limit=?, per_domain_limit=?, "
                        "timezone=?, window_start=?, window_end=?, working_days=?, rotation_strategy=?, updated_at=? WHERE id=?",
                        (
                            fields["name"],
                            fields["status"],
                            fields["approval_mode"],
                            fields["daily_limit"],
                            fields["per_domain_limit"],
                            fields["timezone"],
                            fields["window_start"],
                            fields["window_end"],
                            fields["working_days"],
                            fields["rotation_strategy"],
                            _now(),
                            local["id"],
                        ),
                    )
                    _save_state(conn, "campaigns", str(local["id"]), _now(), _iso(remote_updated), content_hash=remote_hash)
                except Exception as exc:  # noqa: BLE001
                    errors.append({"row": local["id"], "error": str(exc)})
            updated += 1
    return {"updated": updated, "conflicts": conflicts, "errors": errors}


def apply_remote_suppression(conn, remote_rows: list[dict[str, str]], dry_run: bool = False) -> dict[str, Any]:
    inserted = 0
    for remote in remote_rows:
        email = (remote.get("Email") or "").strip().lower()
        if not email or "@" not in email:
            continue
        existing = db.one(conn, "SELECT * FROM suppression WHERE email = ?", (email,))
        if existing:
            continue
        inserted += 1
        if not dry_run:
            conn.execute(
                "INSERT OR IGNORE INTO suppression(email, reason, created_at) VALUES (?, ?, ?)",
                (email, (remote.get("Reason") or "Google Sheet").strip(), (remote.get("Created At") or _now()).strip()),
            )
    return {"inserted": inserted}


def status(conn) -> dict[str, Any]:
    raw = db.settings_dict(conn)
    credentials_present = bool(raw.get("google_sheets_credentials_enc"))
    email = None
    if credentials_present:
        try:
            info = json.loads(crypto.decrypt(raw.get("google_sheets_credentials_enc")) or "{}")
            email = info.get("client_email")
        except Exception:
            email = None
    counts = db.one(
        conn,
        """
        SELECT
          (SELECT COUNT(*) FROM leads) AS leads,
          (SELECT COUNT(*) FROM campaigns) AS campaigns,
          (SELECT COUNT(*) FROM suppression) AS suppression,
          (SELECT COUNT(*) FROM warmup_profiles) AS warmup
        """,
    ) or {}
    return {
        "configured": bool((raw.get("google_sheets_spreadsheet_id") or "").strip() and credentials_present),
        "spreadsheet_id": raw.get("google_sheets_spreadsheet_id", ""),
        "service_account_email": email,
        "credentials_present": credentials_present,
        "conflict_policy": raw.get("google_sheets_conflict_policy", "merge"),
        "last_sync_at": raw.get("google_sheets_last_sync_at", ""),
        "tabs": SHEET_TABS,
        "local_counts": counts,
    }


def _normalize_spreadsheet_id(value: str) -> str:
    text = value.strip()
    marker = "/spreadsheets/d/"
    if marker in text:
        text = text.split(marker, 1)[1]
    text = text.split("/", 1)[0].split("?", 1)[0].split("#", 1)[0]
    return text.strip()


def configure(
    conn,
    spreadsheet_id: str,
    credentials_json: str | None,
    conflict_policy: str = "merge",
) -> dict[str, Any]:
    spreadsheet_id = _normalize_spreadsheet_id(spreadsheet_id)
    if not spreadsheet_id:
        raise SheetsError("Spreadsheet ID is required.")
    if conflict_policy not in {"merge", "local", "remote"}:
        raise SheetsError("conflict_policy must be merge, local or remote.")
    if credentials_json:
        try:
            info = json.loads(credentials_json)
        except json.JSONDecodeError as exc:
            raise SheetsError("The service account JSON is not valid JSON.") from exc
        if not info.get("client_email") or not info.get("private_key"):
            raise SheetsError("The service account JSON must contain client_email and private_key.")
        db.set_setting(conn, "google_sheets_credentials_enc", crypto.encrypt(credentials_json) or "")
    db.set_setting(conn, "google_sheets_spreadsheet_id", spreadsheet_id)
    db.set_setting(conn, "google_sheets_conflict_policy", conflict_policy)
    db.audit(conn, "google_sheets_configured", "sheets", "", {"spreadsheet_id": spreadsheet_id, "policy": conflict_policy})
    return status(conn)


def test(conn) -> dict[str, Any]:
    spreadsheet, email = _client(conn)
    worksheets = ensure_tabs(spreadsheet)
    return {
        "ok": True,
        "spreadsheet": spreadsheet.title,
        "service_account_email": email,
        "tabs": {key: worksheet.title for key, worksheet in worksheets.items()},
    }


def _push(conn, worksheets: dict[str, Any], dry_run: bool) -> dict[str, Any]:
    leads = build_lead_rows(conn)
    campaigns = build_campaign_rows(conn)
    suppression = build_suppression_rows(conn)
    warmup_rows = build_warmup_rows(conn)
    if not dry_run:
        write_tab(worksheets["leads"], HEADERS["leads"], leads)
        write_tab(worksheets["campaigns"], HEADERS["campaigns"], campaigns)
        write_tab(worksheets["suppression"], HEADERS["suppression"], suppression)
        write_tab(worksheets["warmup"], HEADERS["warmup"], warmup_rows)
        now = _now()
        lead_dicts = [dict(zip(HEADERS["leads"], row)) for row in leads]
        for record in lead_dicts:
            _save_state(
                conn,
                "leads",
                str(record["ID"]),
                record["Updated At"],
                now,
                now,
                content_hash=_hash_row(record),
            )
        campaign_dicts = [dict(zip(HEADERS["campaigns"], row)) for row in campaigns]
        for record in campaign_dicts:
            _save_state(
                conn,
                "campaigns",
                str(record["ID"]),
                record["Updated At"],
                now,
                now,
                content_hash=_hash_row(record),
            )
    return {
        "leads": len(leads),
        "campaigns": len(campaigns),
        "suppression": len(suppression),
        "warmup": len(warmup_rows),
    }


def sync(conn, direction: str = "both", dry_run: bool = False) -> dict[str, Any]:
    if direction not in {"pull", "push", "both"}:
        raise SheetsError("direction must be pull, push or both.")
    policy = db.settings_dict(conn).get("google_sheets_conflict_policy", "merge")
    spreadsheet, email = _client(conn)
    worksheets = ensure_tabs(spreadsheet)
    result: dict[str, Any] = {
        "ok": True,
        "direction": direction,
        "dry_run": dry_run,
        "spreadsheet": spreadsheet.title,
        "service_account_email": email,
        "conflict_policy": policy,
        "pulled": {"leads": {}, "campaigns": {}, "suppression": {}},
        "pushed": {},
        "conflicts": [],
        "errors": [],
    }
    if direction in {"pull", "both"}:
        remote_leads = read_tab(worksheets["leads"], HEADERS["leads"])
        remote_campaigns = read_tab(worksheets["campaigns"], HEADERS["campaigns"])
        remote_suppression = read_tab(worksheets["suppression"], HEADERS["suppression"])
        lead_result = apply_remote_leads(conn, remote_leads, policy, dry_run)
        campaign_result = apply_remote_campaigns(conn, remote_campaigns, policy, dry_run)
        suppression_result = apply_remote_suppression(conn, remote_suppression, dry_run)
        result["pulled"] = {
            "leads": lead_result,
            "campaigns": campaign_result,
            "suppression": suppression_result,
        }
        result["conflicts"] = lead_result["conflicts"] + campaign_result["conflicts"]
        result["errors"] = lead_result["errors"] + campaign_result["errors"]
    if direction in {"push", "both"}:
        if result["conflicts"] and policy == "merge":
            result["ok"] = False
            result["aborted_push"] = "Resolve conflicts first, or set the policy to local or remote."
            return result
        result["pushed"] = _push(conn, worksheets, dry_run)
    if not dry_run:
        db.set_setting(conn, "google_sheets_last_sync_at", _now())
        result["last_sync_at"] = _now()
    return result

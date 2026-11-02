"""Import the ICP extractor pack into a campaign.

Real lead data stays in the local SQLite database and is never committed.
The public demo uses synthetic leads from app/seed.py.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

from app import db
from app.services import drafting

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _clean_email(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "")).lower()


DEFAULT_SUBJECT = "Quick idea for {{company}}"
DEFAULT_BODY = (
    "Hi {{first_name}},\n\n"
    "I came across {{company}} while looking at {{industry}} businesses in {{city}}.\n\n"
    "One thing that stood out: {{observation_line}}\n\n"
    "We help teams with {{offer}}.\n\n"
    "Would a 15-minute call be useful?\n\n"
    "{{sender_name}}\n"
    "{{sender_title}}, {{sender_company}}\n\n"
    'If this is not relevant, reply "no" and I will not follow up.'
)


def ensure_campaign(
    conn,
    name: str,
    all_day: bool = True,
    daily_limit: int = 250,
    per_domain_limit: int = 50,
) -> dict[str, Any]:
    campaign = db.one(conn, "SELECT * FROM campaigns WHERE name = ?", (name,))
    if campaign:
        return campaign
    window_start = "00:00" if all_day else "09:30"
    window_end = "23:59" if all_day else "17:30"
    working_days = "[1,2,3,4,5,6,7]" if all_day else "[1,2,3,4,5]"
    timezone = db.settings_dict(conn).get("default_timezone") or "Asia/Kolkata"
    now = db.now_iso()
    cursor = conn.execute(
        "INSERT INTO campaigns(name, status, approval_mode, daily_limit, per_domain_limit, timezone, "
        "window_start, window_end, working_days, rotation_strategy, min_gap_seconds, max_gap_seconds, "
        "created_at, updated_at) VALUES (?, 'active', 'manual', ?, ?, ?, ?, ?, ?, "
        "'least_used', 45, 240, ?, ?)",
        (name, daily_limit, per_domain_limit, timezone, window_start, window_end, working_days, now, now),
    )
    campaign_id = int(cursor.lastrowid)
    conn.execute(
        "INSERT OR IGNORE INTO campaign_mailboxes(campaign_id, mailbox_id) SELECT ?, id FROM mailboxes",
        (campaign_id,),
    )
    conn.execute(
        "INSERT INTO campaign_steps(campaign_id, step_no, delay_days, subject_template, body_template, enabled, created_at) "
        "VALUES (?, 1, 0, ?, ?, 1, ?)",
        (campaign_id, DEFAULT_SUBJECT, DEFAULT_BODY, now),
    )
    db.audit(conn, "campaign_created", "campaign", campaign_id, {"name": name, "import": True})
    return db.one(conn, "SELECT * FROM campaigns WHERE id = ?", (campaign_id,))


def _email_domain(email: str) -> str:
    return email.split("@", 1)[1].strip().lower() if "@" in email else ""


def _trim(value: Any, limit: int = 260) -> str:
    text = " ".join(str(value or "").split())
    return text[:limit]


def map_json_lead(item: dict[str, Any]) -> dict[str, Any]:
    email = _clean_email(item.get("email"))
    name = (item.get("contact_name") or item.get("business_name") or "").strip()
    company = (item.get("business_name") or item.get("company") or "").strip()
    observation = item.get("business_strength") or item.get("observation") or ""
    notes = _trim(observation)
    return {
        "external_id": (item.get("place_url") or email)[:500],
        "name": name[:200],
        "email": email,
        "role": _trim(item.get("contact_title") or "Business owner", 120),
        "company": company[:240],
        "industry": _trim(item.get("industry"), 160),
        "company_domain": _email_domain(email),
        "website": _trim(item.get("website"), 500),
        "city": _trim(item.get("city"), 120),
        "notes": notes,
        "offer": _trim(item.get("recommended_offer") or item.get("service_assigned"), 180),
        "email_grade": _trim(item.get("email_grade"), 4),
        "verification": _trim(item.get("verification") or "Unknown", 40),
        "source": "ICPExtractor",
    }


GRADE_RE = re.compile(r"email grade:\s*([ABC])", re.IGNORECASE)
REVIEW_RE = re.compile(r"([\d,]+)\s+reviews,\s*([\d.]+)\s*\*", re.IGNORECASE)


def _csv_strength(notes: str) -> str:
    match = REVIEW_RE.search(notes)
    if match:
        return f"your {match.group(1)} reviews at {match.group(2)} stars."
    return ""


def map_csv_lead(row: dict[str, str]) -> dict[str, Any]:
    values = {str(key).strip().lower(): value for key, value in row.items()}

    def pick(*names: str) -> str:
        for name in names:
            value = values.get(name.strip().lower())
            if value is not None and str(value).strip():
                return str(value).strip()
        return ""

    email = _clean_email(pick("Email"))
    company = pick("Doctor Name", "Business Name", "Company")
    contact = pick("Contact Name", "Name")
    role = pick("Role", "Contact Title")
    notes = _trim(pick("Notes"))
    grade_match = GRADE_RE.search(notes)
    grade = (
        pick("Email Grade", "email_grade", "Grade").upper()[:4]
        or (grade_match.group(1).upper() if grade_match else "")
        or ("C" if email.endswith(("@gmail.com", "@yahoo.com", "@outlook.com")) else "B")
    )
    source = pick("Source") or "ICPExtractor CSV"
    mailroom_export = "draft_status" in values or "campaign_id" in values
    return {
        "external_id": (pick("Lead ID", "ID") or email)[:500],
        "name": (contact or company or email)[:200],
        "email": email,
        "role": (role or ("Business owner" if contact else "Owner / team"))[:120],
        "company": company[:240],
        "industry": _trim(pick("Industry"), 160),
        "company_domain": _email_domain(email),
        "website": _trim(pick("Website"), 500),
        "city": _trim(pick("City"), 120),
        "notes": notes if mailroom_export else _csv_strength(notes),
        "offer": _trim(pick("Offer", "Service Assigned"), 180),
        "email_grade": grade,
        "verification": _trim(pick("Verification") or "Unknown", 40),
        "source": source,
    }


def _insert_leads(conn, campaign_id: int, records: list[dict[str, Any]]) -> tuple[int, int]:
    imported = 0
    skipped = 0
    now = db.now_iso()
    for record in records:
        if not EMAIL_RE.match(record["email"]):
            skipped += 1
            continue
        cursor = conn.execute(
            "INSERT OR IGNORE INTO leads(campaign_id, external_id, name, email, role, company, industry, "
            "company_domain, website, city, notes, offer, email_grade, verification, source, status, "
            "created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'new', ?, ?)",
            (
                campaign_id,
                record["external_id"],
                record["name"],
                record["email"],
                record["role"],
                record["company"],
                record["industry"],
                record["company_domain"],
                record["website"],
                record["city"],
                record["notes"],
                record["offer"],
                record["email_grade"],
                record["verification"],
                record["source"],
                now,
                now,
            ),
        )
        if cursor.rowcount:
            imported += 1
        else:
            skipped += 1
    return imported, skipped


def import_records(conn, campaign_id: int, records: list[dict[str, Any]]) -> dict[str, Any]:
    campaign = db.one(conn, "SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
    if not campaign:
        raise ValueError("Campaign not found")
    imported, skipped = _insert_leads(conn, campaign_id, records)
    drafts = drafting.generate_drafts(conn, campaign_id)
    db.audit(
        conn,
        "leads_imported",
        "campaign",
        campaign_id,
        {"source": "upload", "imported": imported, "skipped": skipped, "drafts": drafts},
    )
    return {
        "campaign": campaign,
        "imported": imported,
        "skipped": skipped,
        "drafts": drafts,
    }


def import_json(
    conn,
    path: str | Path,
    campaign_name: str,
    limit: int | None = None,
    grades: set[str] | None = None,
    all_day: bool = True,
) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Expected a JSON array of leads")
    records = [map_json_lead(item) for item in data]
    if grades:
        records = [item for item in records if item["email_grade"].upper() in grades]
    if limit:
        records = records[:limit]
    campaign = ensure_campaign(conn, campaign_name, all_day=all_day)
    imported, skipped = _insert_leads(conn, campaign["id"], records)
    drafts = drafting.generate_drafts(conn, campaign["id"])
    db.audit(
        conn,
        "leads_imported",
        "campaign",
        campaign["id"],
        {"source": str(path), "imported": imported, "skipped": skipped, "drafts": drafts},
    )
    return {
        "ok": True,
        "campaign": campaign,
        "imported": imported,
        "skipped": skipped,
        "drafts": drafts,
    }


def import_csv(
    conn,
    path: str | Path,
    campaign_name: str,
    limit: int | None = None,
    all_day: bool = True,
) -> dict[str, Any]:
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        records = [map_csv_lead(row) for row in csv.DictReader(handle)]
    if limit:
        records = records[:limit]
    campaign = ensure_campaign(conn, campaign_name, all_day=all_day)
    imported, skipped = _insert_leads(conn, campaign["id"], records)
    drafts = drafting.generate_drafts(conn, campaign["id"])
    db.audit(
        conn,
        "leads_imported",
        "campaign",
        campaign["id"],
        {"source": str(path), "imported": imported, "skipped": skipped, "drafts": drafts},
    )
    return {
        "ok": True,
        "campaign": campaign,
        "imported": imported,
        "skipped": skipped,
        "drafts": drafts,
    }


def import_file(
    conn,
    path: str | Path,
    campaign_name: str,
    limit: int | None = None,
    grades: set[str] | None = None,
    all_day: bool = True,
) -> dict[str, Any]:
    suffix = Path(path).suffix.lower()
    if suffix == ".json":
        return import_json(conn, path, campaign_name, limit, grades, all_day)
    if suffix == ".csv":
        return import_csv(conn, path, campaign_name, limit, all_day)
    raise ValueError("Only .json and .csv files are supported")

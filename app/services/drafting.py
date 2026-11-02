"""Draft rendering and the optional agent webhook hook."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import Any

from app import db

PLACEHOLDER = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")


def render(template: str, values: dict[str, Any]) -> str:
    def replace(match: re.Match[str]) -> str:
        return str(values.get(match.group(1), "") or "")

    return PLACEHOLDER.sub(replace, template or "").strip()


TITLES = {"dr", "dr.", "mr", "mr.", "mrs", "mrs.", "ms", "ms.", "prof", "prof.", "shri", "smt", "sri"}


def first_name(name: str) -> str:
    parts = (name or "").strip().split()
    while parts and parts[0].lower() in TITLES:
        parts.pop(0)
    return parts[0] if parts else "there"


def campaign_step(conn, campaign_id: int, step_no: int = 1) -> dict[str, Any] | None:
    return db.one(
        conn,
        "SELECT * FROM campaign_steps WHERE campaign_id = ? AND step_no = ? AND enabled = 1",
        (campaign_id, step_no),
    )


def context_for(
    conn,
    lead: dict[str, Any],
    campaign: dict[str, Any],
    step: dict[str, Any],
) -> dict[str, Any]:
    settings = db.settings_dict(conn)
    notes = (lead.get("notes") or "").strip()
    industry = (lead.get("industry") or "").strip()
    city = (lead.get("city") or "").strip() or "your area"
    company = (lead.get("company") or "").strip()
    person_name = (lead.get("name") or "").strip()
    greeting = first_name(person_name)
    if not person_name or person_name.lower() == company.lower() or greeting.lower() in {"owner", "team"}:
        greeting = "there"
    observation_line = notes
    if not observation_line:
        if industry:
            observation_line = f"your work in {industry} in {city}."
        else:
            observation_line = f"your local presence in {city}."

    return {
        "first_name": greeting,
        "name": lead.get("name") or "there",
        "email": lead.get("email") or "",
        "company": company or "your team",
        "role": lead.get("role") or "",
        "industry": industry or "your industry",
        "city": city,
        "website": lead.get("website") or "",
        "notes": notes,
        "observation_line": observation_line,
        "offer": lead.get("offer")
        or settings.get("default_offer")
        or "a short video and website audit",
        "sender_name": settings.get("sender_name", "Alex Morgan"),
        "sender_title": settings.get("sender_title", "Founder"),
        "sender_company": settings.get("sender_company", "Dynamisers"),
        "campaign_name": campaign.get("name", ""),
        "step_no": step.get("step_no", 1),
    }


def template_draft(conn, lead: dict[str, Any], campaign: dict[str, Any], step: dict[str, Any]) -> tuple[str, str]:
    values = context_for(conn, lead, campaign, step)
    return (
        render(step["subject_template"], values),
        render(step["body_template"], values),
    )


def agent_draft(
    lead: dict[str, Any],
    campaign: dict[str, Any],
    instruction: str,
    webhook: str,
    timeout: int = 30,
) -> tuple[str, str] | None:
    """Optional contract for an external agent.

    POST {
      "instruction": "...",
      "campaign": {...},
      "lead": {...}
    }
    Expect {"subject": "...", "body": "..."}.
    """
    if not webhook:
        return None
    payload = json.dumps(
        {
            "instruction": instruction,
            "campaign": campaign,
            "lead": lead,
            "output": "Return JSON with exactly two string fields: subject and body.",
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        webhook,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None
    subject = str(data.get("subject") or "").strip()
    body = str(data.get("body") or "").strip()
    return (subject, body) if subject and body else None


def generate_drafts(
    conn,
    campaign_id: int,
    lead_ids: list[int] | None = None,
    use_agent: bool = False,
) -> int:
    campaign = db.one(conn, "SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
    if not campaign:
        return 0
    step = campaign_step(conn, campaign_id)
    if not step:
        return 0

    settings = db.settings_dict(conn)
    agent_webhook = settings.get("agent_webhook", "")
    instruction = (
        "Write a short, honest cold email. Use only facts in the lead record. "
        "Do not invent customers, metrics or product claims. Keep it under 120 words. "
        "Return JSON with subject and body."
    )

    if lead_ids:
        placeholders = ",".join("?" for _ in lead_ids)
        candidates = db.rows(
            conn,
            f"SELECT * FROM leads WHERE campaign_id = ? AND id IN ({placeholders}) "
            "AND id NOT IN (SELECT lead_id FROM drafts)",
            (campaign_id, *lead_ids),
        )
    else:
        candidates = db.rows(
            conn,
            "SELECT * FROM leads WHERE campaign_id = ? "
            "AND id NOT IN (SELECT lead_id FROM drafts)",
            (campaign_id,),
        )

    created = 0
    for lead in candidates:
        subject, body = template_draft(conn, lead, campaign, step)
        if use_agent and agent_webhook:
            generated = agent_draft(lead, campaign, instruction, agent_webhook)
            if generated:
                subject, body = generated
        if not subject or not body:
            continue
        conn.execute(
            "INSERT INTO drafts(lead_id, campaign_id, step_no, subject, body, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)",
            (lead["id"], campaign_id, step["step_no"], subject, body, db.now_iso(), db.now_iso()),
        )
        conn.execute(
            "UPDATE leads SET status = 'pending_approval', updated_at = ? WHERE id = ?",
            (db.now_iso(), lead["id"]),
        )
        created += 1
    if created:
        db.audit(conn, "drafts_generated", "campaign", campaign_id, {"count": created})
    return created


def regenerate_draft(conn, draft_id: int) -> dict[str, Any] | None:
    draft = db.one(conn, "SELECT * FROM drafts WHERE id = ?", (draft_id,))
    if not draft:
        return None
    lead = db.one(conn, "SELECT * FROM leads WHERE id = ?", (draft["lead_id"],))
    campaign = db.one(conn, "SELECT * FROM campaigns WHERE id = ?", (draft["campaign_id"],))
    step = campaign_step(conn, draft["campaign_id"], draft.get("step_no", 1))
    if not lead or not campaign or not step:
        return None
    subject, body = template_draft(conn, lead, campaign, step)
    conn.execute(
        "UPDATE drafts SET subject = ?, body = ?, status = 'pending', approved_at = NULL, "
        "denied_at = NULL, deny_reason = NULL, updated_at = ? WHERE id = ?",
        (subject, body, db.now_iso(), draft_id),
    )
    conn.execute(
        "UPDATE leads SET status = 'pending_approval', updated_at = ? WHERE id = ?",
        (db.now_iso(), lead["id"]),
    )
    db.audit(conn, "draft_regenerated", "draft", draft_id, {"lead_id": lead["id"]})
    return db.one(conn, "SELECT * FROM drafts WHERE id = ?", (draft_id,))

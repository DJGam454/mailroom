"""Campaign routes."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from fastapi import APIRouter, HTTPException

from app import db
from app.deps import Conn
from app.schemas import CampaignCreate, CampaignUpdate
from app.services import importer
from app.routes.helpers import campaign_with_counts

router = APIRouter(prefix="/api", tags=["campaigns"])


@router.get("/campaigns")
def list_campaigns(conn=Conn) -> dict[str, Any]:
    rows = db.rows(conn, "SELECT id FROM campaigns ORDER BY id DESC")
    return {"items": [campaign_with_counts(conn, row["id"]) for row in rows]}


@router.post("/campaigns")
def create_campaign(payload: CampaignCreate, conn=Conn) -> dict[str, Any]:
    now = db.now_iso()
    try:
        with conn:
            cursor = conn.execute(
                "INSERT INTO campaigns(name, status, approval_mode, daily_limit, per_domain_limit, timezone, "
                "window_start, window_end, working_days, rotation_strategy, min_gap_seconds, max_gap_seconds, "
                "created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    payload.name.strip(),
                    payload.status,
                    payload.approval_mode,
                    payload.daily_limit,
                    payload.per_domain_limit,
                    payload.timezone,
                    payload.window_start,
                    payload.window_end,
                    json.dumps(payload.working_days),
                    payload.rotation_strategy,
                    payload.min_gap_seconds,
                    payload.max_gap_seconds,
                    now,
                    now,
                ),
            )
            campaign_id = int(cursor.lastrowid)
            if payload.mailbox_ids is None:
                conn.execute(
                    "INSERT OR IGNORE INTO campaign_mailboxes(campaign_id, mailbox_id) SELECT ?, id FROM mailboxes",
                    (campaign_id,),
                )
            else:
                for mailbox_id in payload.mailbox_ids:
                    conn.execute(
                        "INSERT OR IGNORE INTO campaign_mailboxes(campaign_id, mailbox_id) VALUES (?, ?)",
                        (campaign_id, mailbox_id),
                    )
            conn.execute(
                "INSERT INTO campaign_steps(campaign_id, step_no, delay_days, subject_template, body_template, enabled, created_at) "
                "VALUES (?, 1, 0, ?, ?, 1, ?)",
                (campaign_id, importer.DEFAULT_SUBJECT, importer.DEFAULT_BODY, now),
            )
            db.audit(conn, "campaign_created", "campaign", campaign_id, {"name": payload.name})
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="A campaign with that name already exists") from exc
    return campaign_with_counts(conn, campaign_id) or {}


@router.patch("/campaigns/{campaign_id}")
def update_campaign(campaign_id: int, payload: CampaignUpdate, conn=Conn) -> dict[str, Any]:
    campaign = db.one(conn, "SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    data = payload.model_dump(exclude_unset=True)
    mailbox_ids = data.pop("mailbox_ids", None)
    if "working_days" in data and data["working_days"] is not None:
        data["working_days"] = json.dumps(data["working_days"])
    allowed = {
        "name",
        "status",
        "approval_mode",
        "daily_limit",
        "per_domain_limit",
        "timezone",
        "window_start",
        "window_end",
        "working_days",
        "rotation_strategy",
        "min_gap_seconds",
        "max_gap_seconds",
    }
    updates = {key: value for key, value in data.items() if key in allowed and value is not None}
    try:
        with conn:
            if updates:
                assignments = ", ".join(f"{key} = ?" for key in updates)
                conn.execute(
                    f"UPDATE campaigns SET {assignments}, updated_at = ? WHERE id = ?",
                    (*updates.values(), db.now_iso(), campaign_id),
                )
            if mailbox_ids is not None:
                conn.execute("DELETE FROM campaign_mailboxes WHERE campaign_id = ?", (campaign_id,))
                for mailbox_id in mailbox_ids:
                    conn.execute(
                        "INSERT OR IGNORE INTO campaign_mailboxes(campaign_id, mailbox_id) VALUES (?, ?)",
                        (campaign_id, mailbox_id),
                    )
            db.audit(conn, "campaign_updated", "campaign", campaign_id, updates or {"mailboxes": mailbox_ids})
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="That campaign name is already in use") from exc
    return campaign_with_counts(conn, campaign_id) or {}

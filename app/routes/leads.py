"""Lead table, detail, CSV export and import."""

from __future__ import annotations

import csv
import io
import json
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import Response

from app import db
from app.deps import Conn
from app.services import drafting, importer

router = APIRouter(prefix="/api", tags=["leads"])

LEAD_SELECT = """
SELECT l.*, c.name AS campaign_name,
       d.id AS draft_id, d.status AS draft_status, d.subject AS draft_subject,
       q.id AS queue_id, q.status AS queue_status, q.scheduled_at,
       m.email AS mailbox_email
FROM leads l
JOIN campaigns c ON c.id = l.campaign_id
LEFT JOIN drafts d ON d.lead_id = l.id
LEFT JOIN send_queue q ON q.draft_id = d.id
LEFT JOIN mailboxes m ON m.id = q.mailbox_id
"""


def _where(campaign_id: int | None, status: str | None, q: str | None) -> tuple[str, list[Any]]:
    clauses = []
    params: list[Any] = []
    if campaign_id:
        clauses.append("l.campaign_id = ?")
        params.append(campaign_id)
    if status:
        clauses.append("l.status = ?")
        params.append(status)
    if q:
        clauses.append("(l.name LIKE ? OR l.email LIKE ? OR l.company LIKE ? OR l.industry LIKE ?)")
        like = f"%{q.strip()}%"
        params.extend([like, like, like, like])
    return ("WHERE " + " AND ".join(clauses)) if clauses else "", params


@router.get("/leads")
def list_leads(
    conn=Conn,
    campaign_id: int | None = None,
    status: str | None = None,
    q: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
) -> dict[str, Any]:
    where, params = _where(campaign_id, status, q)
    total_row = db.one(conn, f"SELECT COUNT(*) AS count FROM leads l {where}", tuple(params))
    total = int(total_row["count"]) if total_row else 0
    offset = (page - 1) * page_size
    items = db.rows(
        conn,
        f"{LEAD_SELECT} {where} ORDER BY l.id DESC LIMIT ? OFFSET ?",
        (*params, page_size, offset),
    )
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max(1, (total + page_size - 1) // page_size),
    }


@router.get("/leads/export.csv")
def export_leads(
    conn=Conn,
    campaign_id: int | None = None,
    status: str | None = None,
    q: str | None = None,
) -> Response:
    where, params = _where(campaign_id, status, q)
    items = db.rows(conn, f"{LEAD_SELECT} {where} ORDER BY l.id DESC", tuple(params))
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "id",
            "name",
            "email",
            "role",
            "company",
            "industry",
            "city",
            "website",
            "email_grade",
            "verification",
            "status",
            "campaign_id",
            "draft_status",
            "mailbox",
            "scheduled_at",
            "notes",
        ]
    )
    for item in items:
        writer.writerow(
            [
                item["id"],
                item["name"],
                item["email"],
                item["role"],
                item["company"],
                item["industry"],
                item["city"],
                item["website"],
                item["email_grade"],
                item["verification"],
                item["status"],
                item["campaign_id"],
                item.get("draft_status") or "",
                item.get("mailbox_email") or "",
                item.get("scheduled_at") or "",
                (item.get("notes") or "").replace("\n", " "),
            ]
        )
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="mailroom-leads.csv"'},
    )


@router.get("/leads/{lead_id}")
def get_lead(lead_id: int, conn=Conn) -> dict[str, Any]:
    lead = db.one(conn, "SELECT * FROM leads WHERE id = ?", (lead_id,))
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    draft = db.one(conn, "SELECT * FROM drafts WHERE lead_id = ?", (lead_id,))
    queue = db.one(
        conn,
        "SELECT * FROM send_queue WHERE lead_id = ? ORDER BY id DESC LIMIT 1",
        (lead_id,),
    )
    message = db.one(
        conn,
        "SELECT * FROM messages WHERE lead_id = ? ORDER BY id DESC LIMIT 1",
        (lead_id,),
    )
    activity = db.rows(
        conn,
        "SELECT * FROM activity WHERE entity_id = ? OR detail LIKE ? ORDER BY id DESC LIMIT 20",
        (str(lead_id), f'%"lead_id":{lead_id}%'),
    )
    return {"lead": lead, "draft": draft, "queue": queue, "message": message, "activity": activity}


@router.post("/leads/import")
async def import_leads(
    conn=Conn,
    campaign_id: int = Form(...),
    file: UploadFile = File(...),
) -> dict[str, Any]:
    campaign = db.one(conn, "SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    raw = await file.read()
    if len(raw) > 20 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File is larger than 20 MB")
    filename = (file.filename or "").lower()
    try:
        text = raw.decode("utf-8-sig")
        if filename.endswith(".json"):
            data = json.loads(text)
            if not isinstance(data, list):
                raise ValueError("JSON must be an array of leads")
            records = [importer.map_json_lead(item) for item in data]
        elif filename.endswith(".csv"):
            records = [importer.map_csv_lead(row) for row in csv.DictReader(io.StringIO(text))]
        else:
            raise ValueError("Only .csv and .json are supported")
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    try:
        with conn:
            result = importer.import_records(conn, campaign_id, records)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Import failed: {exc}") from exc
    return {"ok": True, **result}


@router.post("/drafts/{draft_id}/regenerate")
def regenerate(draft_id: int, conn=Conn) -> dict[str, Any]:
    with conn:
        draft = drafting.regenerate_draft(conn, draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return {"ok": True, "draft": draft}

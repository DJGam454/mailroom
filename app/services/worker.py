"""Background send worker with leases and retry backoff."""

from __future__ import annotations

import logging
import threading
import time
from datetime import timedelta

from app import db
from app.services import rotation, sender

log = logging.getLogger("mailroom.worker")
_lock = threading.Lock()
_stop = threading.Event()
_thread: threading.Thread | None = None
MAX_ATTEMPTS = 3


def _now_plus(seconds: int) -> str:
    return rotation.iso(rotation.now_utc() + timedelta(seconds=seconds))


def _finish_failure(conn, queue_id: int, reason: str, retry_delay: int, count_attempt: bool = True) -> None:
    queue = db.one(conn, "SELECT * FROM send_queue WHERE id = ?", (queue_id,))
    if not queue:
        return
    attempts = int(queue["attempts"]) + (1 if count_attempt else 0)
    now = db.now_iso()
    if attempts >= MAX_ATTEMPTS:
        conn.execute(
            "UPDATE send_queue SET status = 'failed', attempts = ?, lease_until = NULL, "
            "last_error = ?, updated_at = ? WHERE id = ?",
            (attempts, reason[:1000], now, queue_id),
        )
        conn.execute(
            "UPDATE drafts SET status = 'failed', updated_at = ? WHERE id = ?",
            (now, queue["draft_id"]),
        )
        conn.execute(
            "UPDATE leads SET status = 'failed', updated_at = ? WHERE id = ?",
            (now, queue["lead_id"]),
        )
        db.audit(conn, "send_failed", "draft", queue["draft_id"], {"reason": reason, "attempts": attempts})
        return

    conn.execute(
        "UPDATE send_queue SET status = 'queued', attempts = ?, scheduled_at = ?, "
        "lease_until = NULL, last_error = ?, updated_at = ? WHERE id = ?",
        (attempts, _now_plus(retry_delay), reason[:1000], now, queue_id),
    )
    db.audit(
        conn,
        "send_retry",
        "draft",
        queue["draft_id"],
        {"reason": reason, "attempts": attempts, "retry_in_seconds": retry_delay},
    )


def _process(queue_id: int) -> dict:
    conn = db.connect()
    try:
        conn.execute("BEGIN IMMEDIATE")
        queue = db.one(
            conn,
            "SELECT * FROM send_queue WHERE id = ? AND status = 'queued'",
            (queue_id,),
        )
        if not queue:
            conn.rollback()
            return {"ok": False, "skipped": True}
        lease_until = _now_plus(120)
        conn.execute(
            "UPDATE send_queue SET status = 'leased', lease_until = ?, updated_at = ? WHERE id = ?",
            (lease_until, db.now_iso(), queue_id),
        )
        conn.commit()

        conn.execute("BEGIN IMMEDIATE")
        result = sender.send_queue_item(conn, queue_id)
        conn.commit()
        return result
    except sender.RetrySend as exc:
        conn.rollback()
        conn.execute("BEGIN IMMEDIATE")
        _finish_failure(conn, queue_id, f"Retry: {exc}", 300, count_attempt=False)
        conn.commit()
        return {"ok": False, "retry": True, "reason": str(exc), "error": str(exc)}
    except sender.SendError as exc:
        conn.rollback()
        conn.execute("BEGIN IMMEDIATE")
        _finish_failure(conn, queue_id, str(exc), 60)
        conn.commit()
        return {"ok": False, "error": str(exc)}
    except Exception as exc:  # noqa: BLE001
        log.exception("Unexpected send failure for queue %s", queue_id)
        conn.rollback()
        conn.execute("BEGIN IMMEDIATE")
        _finish_failure(conn, queue_id, f"Unexpected error: {exc}", 300)
        conn.commit()
        return {"ok": False, "error": str(exc)}
    finally:
        conn.close()


def tick() -> dict:
    if not _lock.acquire(blocking=False):
        return {"ok": True, "skipped": "worker already running"}
    try:
        conn = db.connect()
        try:
            now = db.now_iso()
            conn.execute(
                "UPDATE send_queue SET status = 'queued', lease_until = NULL "
                "WHERE status = 'leased' AND lease_until IS NOT NULL AND lease_until < ?",
                (now,),
            )
            conn.commit()
            due = db.rows(
                conn,
                "SELECT id FROM send_queue WHERE status = 'queued' AND scheduled_at <= ? "
                "ORDER BY scheduled_at LIMIT 20",
                (now,),
            )
        finally:
            conn.close()

        results = []
        for row in due:
            results.append({"queue_id": row["id"], **_process(row["id"])})
        return {
            "ok": True,
            "processed": len(results),
            "sent": sum(1 for item in results if item.get("ok")),
            "results": results,
        }
    finally:
        _lock.release()


def run_forever(interval: float = 2.0) -> None:
    log.info("Send worker started with %.1fs interval", interval)
    while not _stop.is_set():
        try:
            result = tick()
            if result.get("sent"):
                log.info("Worker sent %s message(s)", result["sent"])
        except Exception:
            log.exception("Worker tick failed")
        _stop.wait(interval)
    log.info("Send worker stopped")


def start(interval: float = 2.0) -> None:
    global _thread
    if _thread and _thread.is_alive():
        return
    _stop.clear()
    _thread = threading.Thread(target=run_forever, args=(interval,), name="mailroom-worker", daemon=True)
    _thread.start()


def stop() -> None:
    _stop.set()


def send_now(queue_id: int) -> dict:
    with db.transaction() as conn:
        queue = db.one(conn, "SELECT * FROM send_queue WHERE id = ?", (queue_id,))
        if not queue:
            return {"ok": False, "error": "Queue item not found"}
        if queue["status"] not in {"queued", "failed"}:
            return {"ok": False, "error": f"Queue item is {queue['status']}"}
        now = db.now_iso()
        if queue["status"] == "failed":
            # A manual retry is an explicit operator override. Reset the
            # attempt count and the dependent states so the item can actually
            # pass the send-time eligibility checks.
            conn.execute(
                "UPDATE drafts SET status = 'queued', updated_at = ? WHERE id = ?",
                (now, queue["draft_id"]),
            )
            conn.execute(
                "UPDATE leads SET status = 'queued', updated_at = ? WHERE id = ?",
                (now, queue["lead_id"]),
            )
        conn.execute(
            "UPDATE send_queue SET status = 'queued', attempts = 0, last_error = NULL, "
            "scheduled_at = ?, updated_at = ? WHERE id = ?",
            (now, now, queue_id),
        )
        db.audit(
            conn,
            "queue_send_now",
            "draft",
            queue["draft_id"],
            {"queue_id": queue_id, "previous_status": queue["status"]},
        )
    result = tick()
    item = next((row for row in result.get("results", []) if row.get("queue_id") == queue_id), None)
    if item is None:
        return {"ok": False, "error": result.get("skipped") or "The queue item could not be processed."}
    return item


def cancel(queue_id: int, reason: str = "Cancelled by operator") -> dict:
    with db.transaction() as conn:
        queue = db.one(conn, "SELECT * FROM send_queue WHERE id = ?", (queue_id,))
        if not queue:
            return {"ok": False, "error": "Queue item not found"}
        if queue["status"] == "sent":
            return {"ok": False, "error": "Already sent"}
        if queue["status"] == "leased":
            return {"ok": False, "error": "Item is currently sending; wait for the result"}
        now = db.now_iso()
        conn.execute(
            "UPDATE send_queue SET status = 'cancelled', last_error = ?, updated_at = ? WHERE id = ?",
            (reason, now, queue_id),
        )
        conn.execute(
            "UPDATE drafts SET status = 'denied', denied_at = ?, deny_reason = ?, updated_at = ? WHERE id = ?",
            (now, reason, now, queue["draft_id"]),
        )
        conn.execute(
            "UPDATE leads SET status = 'denied', updated_at = ? WHERE id = ?",
            (now, queue["lead_id"]),
        )
        db.audit(conn, "queue_cancelled", "draft", queue["draft_id"], {"reason": reason})
    return {"ok": True}

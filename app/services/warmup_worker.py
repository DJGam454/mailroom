"""Background warmup loop."""

from __future__ import annotations

import logging
import threading

from app.services import warmup

log = logging.getLogger("mailroom.warmup_worker")
_stop = threading.Event()
_thread: threading.Thread | None = None


def run_forever(interval: float = 5.0) -> None:
    log.info("Warmup worker started with %.1fs interval", interval)
    while not _stop.is_set():
        try:
            result = warmup.tick()
            if result.get("generated") or result.get("sent") or result.get("replied"):
                log.info(
                    "Warmup generated=%s sent=%s replied=%s opened=%s",
                    result.get("generated", 0),
                    result.get("sent", 0),
                    result.get("replied", 0),
                    result.get("opened", 0),
                )
        except Exception:
            log.exception("Warmup tick failed")
        _stop.wait(interval)
    log.info("Warmup worker stopped")


def start(interval: float = 5.0) -> None:
    global _thread
    if _thread and _thread.is_alive():
        return
    _stop.clear()
    _thread = threading.Thread(target=run_forever, args=(interval,), name="mailroom-warmup", daemon=True)
    _thread.start()


def stop() -> None:
    _stop.set()

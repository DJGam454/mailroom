"""Mailroom FastAPI entrypoint."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import config, db
from app.routes import (
    activity,
    approvals,
    campaigns,
    deliverability,
    leads,
    mailboxes,
    overview,
    queue,
    settings,
)
from app.services import worker

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("mailroom")

STATIC_DIR = Path(__file__).with_name("static")


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.init_db()
    if os.getenv("MAILROOM_AUTO_SEED", "1").lower() not in {"0", "false", "no"}:
        from app.seed import seed_demo

        with db.connect() as conn:
            count = db.one(conn, "SELECT COUNT(*) AS count FROM campaigns")
        if not count or int(count["count"]) == 0:
            log.info("No campaigns found; seeding synthetic demo data")
            seed_demo()
    if config.WORKER_ENABLED:
        worker.start(config.WORKER_INTERVAL)
    yield
    worker.stop()


app = FastAPI(title="Mailroom", version=config.APP_VERSION, lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

for router in (
    overview.router,
    campaigns.router,
    leads.router,
    approvals.router,
    mailboxes.router,
    deliverability.router,
    queue.router,
    activity.router,
    settings.router,
):
    app.include_router(router)


@app.get("/api/health")
def health() -> dict:
    return {
        "ok": True,
        "version": config.APP_VERSION,
        "worker": config.WORKER_ENABLED,
        "db": str(config.DB_PATH),
    }


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=config.HOST,
        port=config.PORT,
        reload=False,
    )

"""MASDojo FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from sqlalchemy.orm import Session

from app.api import (
    admin,
    auth,
    downloads,
    instructor,
    lab,
    mentor,
    pathway,
    settings as settings_api,
    stats,
    submissions,
    tasks,
)
from app.core.config import settings
from app.core.logging import configure_logging
from app.db.session import get_db
from app.services import instance_config


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    configure_logging()
    # Fail closed on placeholder secrets before serving any request.
    settings.assert_secure()
    if settings.insecure_defaults():
        logger.warning(
            "running with INSECURE default secrets ({}) — dev only",
            ", ".join(settings.insecure_defaults()),
        )
    logger.info("MASDojo backend starting up")
    # Clean up any per-session lab containers orphaned by a previous run.
    try:
        from app.db.session import SessionLocal
        from app.services import lab_session

        with SessionLocal() as db:
            lab_session.reap_orphans(db)
    except Exception as exc:  # noqa: BLE001 - never block startup on cleanup
        logger.warning("lab orphan reap skipped: {}", exc)
    yield
    logger.info("MASDojo backend shutting down")


app = FastAPI(
    title="MASDojo API",
    version="0.1.0",
    description="Mobile App Security Dojo — adaptive Android pentest training, graded on a real emulator.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/config", tags=["meta"])
def public_config(db: Session = Depends(get_db)) -> dict[str, object]:
    """Public front-end config. `solo_mode` tells the UI to skip login and go
    straight to the curriculum for a single local participant;
    `registration_open` gates the hosted-mode sign-up form."""
    cfg = instance_config.get_config(db)
    return {"solo_mode": cfg.solo_mode, "registration_open": cfg.registration_open}


app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(submissions.router)
app.include_router(stats.router)
app.include_router(pathway.router)
app.include_router(settings_api.router)
app.include_router(mentor.router)
app.include_router(downloads.router)
app.include_router(admin.router)
app.include_router(instructor.router)
app.include_router(lab.router)

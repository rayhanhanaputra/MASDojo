"""MASDojo FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api import (
    auth,
    downloads,
    mentor,
    pathway,
    proof,
    settings as settings_api,
    stats,
    submissions,
    tasks,
)
from app.core.config import settings
from app.core.logging import configure_logging


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
def public_config() -> dict[str, object]:
    """Public front-end config. `solo_mode` tells the UI to skip login and go
    straight to the curriculum for a single local participant."""
    return {"solo_mode": settings.solo_mode}


app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(submissions.router)
app.include_router(stats.router)
app.include_router(pathway.router)
app.include_router(settings_api.router)
app.include_router(mentor.router)
app.include_router(proof.router)
app.include_router(downloads.router)

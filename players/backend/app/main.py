"""FastAPI application factory.

Run from the players/ repo root:  PYTHONPATH=. uvicorn backend.app.main:app
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from backend.app.config import settings  # noqa: E402
from backend.app.routers import (  # noqa: E402
    accuracy,
    analytics,
    auth,
    chat,
    comments,
    export,
    meta,
    players,
    watchlists,
)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Players — NFL Draft Prospect Intelligence Platform",
        version="1.0.0",
        description="MVP per PDR v1.1: structured prospect data, multi-axis FSM "
                    "similarity, and a tool-governed AI assistant.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    for router in (meta, players, chat, watchlists, comments, export,
                   analytics, accuracy, auth):
        app.include_router(router.router, prefix="/api")

    if settings.slack_bot_token and settings.slack_signing_secret:
        from backend.app.slack_app import build_slack_handler

        app.mount("/slack", build_slack_handler())
    return app


app = create_app()

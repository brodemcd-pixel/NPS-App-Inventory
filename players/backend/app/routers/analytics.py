"""Usage analytics dashboard + client event ingestion."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db import get_session
from backend.app.domain import USAGE_EVENT_TYPES
from backend.app.services import usage
from backend.app.services.analytics import usage_summary

router = APIRouter()


class EventIn(BaseModel):
    event_type: str
    payload: dict | None = None


@router.get("/analytics/summary")
async def analytics_summary(
    days: int = 30, session: AsyncSession = Depends(get_session)
) -> dict:
    return await usage_summary(session, days=days)


@router.post("/events", status_code=202)
async def ingest_event(
    body: EventIn,
    user_id: str = Header("demo-user", alias="X-User-Id"),
) -> dict:
    if body.event_type in USAGE_EVENT_TYPES:
        await usage.log_event(body.event_type, body.payload or {}, user_id)
    return {"accepted": body.event_type in USAGE_EVENT_TYPES}

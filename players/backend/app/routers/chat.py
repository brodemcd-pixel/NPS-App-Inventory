"""Streaming chat endpoint (SSE, CONTRACT.md §6)."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db import get_session
from backend.app.services import usage
from backend.app.services.assistant import stream_chat

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    history: list[dict] | None = None
    weights: dict[str, float] | None = None


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"


@router.post("/chat")
async def chat(
    body: ChatRequest,
    session: AsyncSession = Depends(get_session),
    user_id: str = Header("demo-user", alias="X-User-Id"),
) -> StreamingResponse:
    await usage.log_event("question_asked", {"message": body.message[:500]}, user_id)

    async def generate():
        async for event, data in stream_chat(
            session, body.message, body.history, body.weights, user_id
        ):
            yield _sse(event, data)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

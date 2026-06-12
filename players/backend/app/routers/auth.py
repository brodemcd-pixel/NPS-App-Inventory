"""Slack -> web identity passthrough (CONTRACT.md §9)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.services.slack_link import verify_slack_token

router = APIRouter()


class TokenExchange(BaseModel):
    token: str


@router.post("/auth/slack/exchange")
async def slack_exchange(body: TokenExchange) -> dict:
    data = verify_slack_token(body.token)
    if data is None:
        raise HTTPException(401, "invalid or expired token")
    return {"user_id": data["user_id"], "name": data.get("name")}

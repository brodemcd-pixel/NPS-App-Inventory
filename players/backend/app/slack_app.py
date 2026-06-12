"""Slack bot (Bolt for Python) — same assistant, same data, same rules (PDR §2.4).

Mounted at /slack only when SLACK_BOT_TOKEN and SLACK_SIGNING_SECRET are set.
Player profile links carry a short-lived signed token so identity follows the user
from Slack into the web app (CONTRACT.md §9).
"""

from __future__ import annotations

import re

from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
from slack_bolt.async_app import AsyncApp
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Route

from backend.app.config import settings
from backend.app.db import async_session
from backend.app.services.assistant import stream_chat
from backend.app.services.slack_link import sign_slack_user

_LINK_RE = re.compile(r"\[([^\]]+)\]\((/players/\d+)\)")


def _to_slack_markup(text: str, token: str) -> str:
    """Markdown links -> Slack links with identity passthrough token."""
    def repl(match: re.Match) -> str:
        url = f"{settings.web_base_url}/auth/slack?token={token}&next={match.group(2)}"
        return f"<{url}|{match.group(1)}>"

    return _LINK_RE.sub(repl, text).replace("**", "*")


async def _answer(message: str, slack_user: str) -> str:
    chunks: list[str] = []
    sources: list[dict] = []
    async with async_session() as session:
        async for event, data in stream_chat(session, message, user_id=slack_user):
            if event == "text":
                chunks.append(data["delta"])
            elif event == "sources":
                sources = data["sources"]
            elif event == "error":
                chunks.append(f"\n:warning: {data['detail']}")
    text = "".join(chunks).strip() or "I had nothing to say — try rephrasing?"
    if sources:
        text += "\n\n*Sources:*\n" + "\n".join(
            f"• {s['operation']}: {s['detail']} ({s['count']} rows)" for s in sources
        )
    return _to_slack_markup(text, sign_slack_user(slack_user))


def build_slack_handler() -> Starlette:
    bolt = AsyncApp(
        token=settings.slack_bot_token,
        signing_secret=settings.slack_signing_secret,
    )

    @bolt.event("app_mention")
    async def on_mention(event, say):
        message = re.sub(r"<@[^>]+>", "", event.get("text", "")).strip()
        await say(await _answer(message, event["user"]))

    @bolt.event("message")
    async def on_dm(event, say):
        if event.get("channel_type") == "im" and not event.get("bot_id"):
            await say(await _answer(event.get("text", ""), event["user"]))

    handler = AsyncSlackRequestHandler(bolt)

    async def endpoint(request: Request):
        return await handler.handle(request)

    return Starlette(routes=[Route("/events", endpoint, methods=["POST"])])

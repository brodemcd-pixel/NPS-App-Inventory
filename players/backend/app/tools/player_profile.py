"""Operation 2: single player profile lookup."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.details import player_detail
from backend.app.tools.common import not_found, resolve_player

TOOL = {
    "name": "player_profile",
    "description": "Full profile for one player: measurables, scouting report, scheme "
                   "context, roles, mental profile, production, draft outcome, flags.",
    "input_schema": {
        "type": "object",
        "properties": {"name_or_id": {"type": "string"}},
        "required": ["name_or_id"],
    },
}


async def run(session: AsyncSession, args: dict) -> dict:
    player = await resolve_player(session, args["name_or_id"])
    if not player:
        return not_found(args["name_or_id"])
    detail = await player_detail(session, player)
    detail.pop("provenance", None)  # too verbose for chat context
    detail["detail"] = f"player_profile {player.name} (id {player.id})"
    detail["count"] = 1
    return detail

"""Operation 11: prospect-to-NFL-team scheme fit."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.team_fit import team_fits
from backend.app.tools.common import brief, not_found, resolve_player

TOOL = {
    "name": "team_fit",
    "description": "Rank NFL teams by scheme fit for a prospect (archetype family match, "
                   "coaching-tree match, functional-role affinity).",
    "input_schema": {
        "type": "object",
        "properties": {
            "name_or_id": {"type": "string"},
            "limit": {"type": "integer", "default": 8},
        },
        "required": ["name_or_id"],
    },
}


async def run(session: AsyncSession, args: dict) -> dict:
    player = await resolve_player(session, args["name_or_id"])
    if not player:
        return not_found(args["name_or_id"])
    fits = await team_fits(session, player, limit=min(32, int(args.get("limit") or 8)))
    return {
        "player": brief(player),
        "teams": fits,
        "detail": f"team_fit {player.name}",
        "count": len(fits),
    }

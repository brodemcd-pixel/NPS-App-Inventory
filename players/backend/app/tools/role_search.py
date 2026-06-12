"""Operation 7: functional-role search."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.domain import ALL_ROLES
from backend.app.services.players_query import run_player_query
from backend.app.tools.common import brief

TOOL = {
    "name": "role_search",
    "description": f"Find prospects by functional role tag. Roles: {', '.join(ALL_ROLES)}.",
    "input_schema": {
        "type": "object",
        "properties": {
            "functional_role": {"type": "string"},
            "limit": {"type": "integer", "default": 10},
        },
        "required": ["functional_role"],
    },
}


async def run(session: AsyncSession, args: dict) -> dict:
    role = args["functional_role"]
    # Forgiving match against the controlled vocabulary.
    if role not in ALL_ROLES:
        low = role.lower()
        role = next((r for r in ALL_ROLES if low in r.lower() or r.lower() in low), role)
    players, total = await run_player_query(
        session, {"role": role, "page_size": min(25, int(args.get("limit") or 10))}
    )
    return {
        "role": role,
        "players": [brief(p) for p in players],
        "total": total,
        "detail": f"role_search '{role}'",
        "count": len(players),
    }

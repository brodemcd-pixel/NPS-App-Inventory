"""Operation 1: filtered list queries (e.g. "5 fastest 40s")."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.players_query import active_filters, run_player_query
from backend.app.tools.common import brief

TOOL = {
    "name": "filtered_list",
    "description": (
        "List draft prospects matching structured filters, with sorting. Use for queries "
        "like '5 fastest 40 times', 'edge rushers under 4.6', 'first-round WRs in 2024'. "
        "Sort keys: grade, forty, pick, percentile, ngs, name, class; prefix '-' for "
        "descending (e.g. '-grade'). Plain 'forty' ascending = fastest first."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "draft_class": {"type": "array", "items": {"type": "integer"}},
            "round": {"type": "array", "items": {"type": "integer"}},
            "position": {"type": "array", "items": {"type": "string"}},
            "position_group": {"type": "array", "items": {"type": "string"}},
            "college": {"type": "string"},
            "conference": {"type": "string"},
            "team": {"type": "string", "description": "NFL team that drafted the player"},
            "forty_max": {"type": "number"},
            "height_min": {"type": "number"},
            "height_max": {"type": "number"},
            "weight_min": {"type": "number"},
            "weight_max": {"type": "number"},
            "red_flag": {"type": "boolean"},
            "green_flag": {"type": "boolean"},
            "sort": {"type": "string"},
            "limit": {"type": "integer", "default": 10},
        },
    },
}


async def run(session: AsyncSession, args: dict) -> dict:
    params = dict(args)
    params["page_size"] = min(50, int(params.pop("limit", 10) or 10))
    players, total = await run_player_query(session, params)
    filters = active_filters(params)
    return {
        "players": [brief(p) for p in players],
        "total": total,
        "detail": f"filtered_list {filters or 'all players'} sort={params.get('sort') or '-grade'}",
        "count": len(players),
    }

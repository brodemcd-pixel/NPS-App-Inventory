"""Operation 4: FSM multi-axis player similarity."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services import similarity as sim
from backend.app.tools.common import brief, not_found, resolve_player

TOOL = {
    "name": "similarity_comparison",
    "description": "Find the most similar prospects to a player using the FSM v1.0 "
                   "multi-axis model (scouting-report, scheme, mental axes). Weights are "
                   "optional and renormalized; default 0.5/0.25/0.25.",
    "input_schema": {
        "type": "object",
        "properties": {
            "name_or_id": {"type": "string"},
            "limit": {"type": "integer", "default": 5},
            "cross_position": {"type": "boolean", "default": False},
            "weights": {
                "type": "object",
                "properties": {
                    "scouting": {"type": "number"},
                    "scheme": {"type": "number"},
                    "mental": {"type": "number"},
                },
            },
        },
        "required": ["name_or_id"],
    },
}


async def run(session: AsyncSession, args: dict) -> dict:
    player = await resolve_player(session, args["name_or_id"])
    if not player:
        return not_found(args["name_or_id"])
    result = await sim.similar_players(
        session,
        player,
        limit=min(15, int(args.get("limit") or 5)),
        weights=args.get("weights"),
        cross_position=bool(args.get("cross_position")),
    )
    items = [
        {
            "player": brief(cand),
            "overall": round(overall, 4),
            "axes": {k: (round(v, 4) if v is not None else None) for k, v in axes.items()},
        }
        for cand, overall, axes in result["items"]
    ]
    w = result["weights_used"]
    return {
        "anchor": brief(player),
        "items": items,
        "weights_used": w,
        "detail": (f"similarity_comparison anchor={player.name} weights="
                   f"{w['scouting']:.2f}/{w['scheme']:.2f}/{w['mental']:.2f}"),
        "count": len(items),
    }

"""Operation 12: head-to-head player comparison."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.similarity import pair_similarity
from backend.app.tools.common import brief, not_found, resolve_player

TOOL = {
    "name": "player_compare",
    "description": "Compare two players head-to-head: measurables, grades, draft "
                   "outcomes and the FSM multi-axis similarity between them.",
    "input_schema": {
        "type": "object",
        "properties": {
            "a_name_or_id": {"type": "string"},
            "b_name_or_id": {"type": "string"},
            "weights": {
                "type": "object",
                "properties": {
                    "scouting": {"type": "number"},
                    "scheme": {"type": "number"},
                    "mental": {"type": "number"},
                },
            },
        },
        "required": ["a_name_or_id", "b_name_or_id"],
    },
}


def _measurables(p) -> dict:
    return {
        "height_in": p.height_in, "weight_lb": p.weight_lb, "forty": p.forty,
        "vertical_in": p.vertical_in, "arm_length_in": p.arm_length_in,
        "hand_size_in": p.hand_size_in, "wingspan_in": p.wingspan_in,
        "ngs_athleticism": p.ngs_athleticism, "class_percentile": p.class_percentile,
    }


async def run(session: AsyncSession, args: dict) -> dict:
    a = await resolve_player(session, args["a_name_or_id"])
    if not a:
        return not_found(args["a_name_or_id"])
    b = await resolve_player(session, args["b_name_or_id"])
    if not b:
        return not_found(args["b_name_or_id"])
    similarity = await pair_similarity(session, a, b, weights=args.get("weights"))
    return {
        "a": {**brief(a), "measurables": _measurables(a)},
        "b": {**brief(b), "measurables": _measurables(b)},
        "similarity": similarity,
        "detail": f"player_compare {a.name} vs {b.name}",
        "count": 2,
    }

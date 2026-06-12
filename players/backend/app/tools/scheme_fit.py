"""Operation 6: scheme-fit query — prospects from a scheme archetype/family."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services import similarity as sim
from backend.app.services.players_query import run_player_query
from backend.app.tools.common import brief

TOOL = {
    "name": "scheme_fit",
    "description": "Find prospects who played in a given scheme archetype (or its close "
                   "family). Offense: Air Raid, Spread/RPO, Pro-Style, West Coast, Power "
                   "Run, Option/Triple, Vertical Play-Action. Defense: 4-3 Attack Front, "
                   "3-4 Two-Gap, 4-2-5 Nickel, 3-3-5 Stack, Press-Man Quarters, Zone-Match.",
    "input_schema": {
        "type": "object",
        "properties": {
            "scheme_archetype": {"type": "string"},
            "position": {"type": "array", "items": {"type": "string"}},
            "include_family": {"type": "boolean", "default": True,
                               "description": "Also include closely related archetypes"},
            "limit": {"type": "integer", "default": 10},
        },
        "required": ["scheme_archetype"],
    },
}


async def run(session: AsyncSession, args: dict) -> dict:
    archetype = args["scheme_archetype"]
    family = {archetype}
    if args.get("include_family", True):
        for fam in sim.SCHEME_FAMILIES:
            if archetype in fam:
                family |= fam
    seen: dict[int, dict] = {}
    limit = min(25, int(args.get("limit") or 10))
    for arch in sorted(family):
        players, _total = await run_player_query(
            session,
            {"scheme": arch, "position": args.get("position"), "page_size": limit},
        )
        for p in players:
            seen.setdefault(p.id, {**brief(p), "scheme_archetype": arch})
    items = sorted(seen.values(), key=lambda r: -(r["nfl_grade"] or 0))[:limit]
    return {
        "scheme_family": sorted(family),
        "players": items,
        "detail": f"scheme_fit {archetype} (family: {', '.join(sorted(family))})",
        "count": len(items),
    }

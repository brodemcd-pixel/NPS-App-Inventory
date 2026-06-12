"""Operation 8: mental/intangible profile queries."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models import MentalProfile, Player
from backend.app.tools.common import brief, not_found, resolve_player
from ml.mental_traits import CORE_TRAITS, QB_TRAITS

ALL_TRAITS = sorted(set(CORE_TRAITS) | set(QB_TRAITS))

TOOL = {
    "name": "mental_profile_query",
    "description": (
        "Query mental/intangible trait profiles. Either pass name_or_id for one player's "
        f"full mental profile, or trait (+ min_score, position) to rank players. Traits: "
        f"{', '.join(ALL_TRAITS)}. Scores are 0..1 (0.5 neutral) and are directional "
        "signals extracted from scouting language and scout tags, not measurements."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "name_or_id": {"type": "string"},
            "trait": {"type": "string"},
            "min_score": {"type": "number", "default": 0.6},
            "position": {"type": "array", "items": {"type": "string"}},
            "limit": {"type": "integer", "default": 10},
        },
    },
}


async def run(session: AsyncSession, args: dict) -> dict:
    if args.get("name_or_id"):
        player = await resolve_player(session, args["name_or_id"])
        if not player:
            return not_found(args["name_or_id"])
        rows = (
            (await session.execute(
                select(MentalProfile).where(MentalProfile.player_id == player.id)
            )).scalars().all()
        )
        traits = [
            {"trait": r.trait, "score": r.score, "source": r.source, "evidence": r.evidence}
            for r in sorted(rows, key=lambda r: -r.score)
        ]
        return {
            "player": brief(player),
            "traits": traits,
            "detail": f"mental_profile_query player={player.name}",
            "count": len(traits),
        }

    trait = (args.get("trait") or "").lower().replace(" ", "_")
    if trait not in ALL_TRAITS:
        return {"error": f"unknown trait '{args.get('trait')}'", "valid_traits": ALL_TRAITS,
                "detail": f"mental_profile_query unknown trait '{args.get('trait')}'"}
    min_score = float(args.get("min_score") or 0.6)
    limit = min(25, int(args.get("limit") or 10))
    stmt = (
        select(Player, func.avg(MentalProfile.score).label("avg_score"))
        .join(MentalProfile, MentalProfile.player_id == Player.id)
        .where(MentalProfile.trait == trait)
        .group_by(Player.id)
        .having(func.avg(MentalProfile.score) >= min_score)
        .order_by(func.avg(MentalProfile.score).desc())
        .limit(limit)
    )
    if args.get("position"):
        stmt = stmt.where(Player.position.in_(args["position"]))
    rows = (await session.execute(stmt)).all()
    return {
        "trait": trait,
        "players": [{**brief(p), "trait_score": round(float(s), 3)} for p, s in rows],
        "detail": f"mental_profile_query trait={trait} min_score={min_score}",
        "count": len(rows),
    }

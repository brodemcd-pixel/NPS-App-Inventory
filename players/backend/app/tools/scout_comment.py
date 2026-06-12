"""Operation 5: scout comment logging (with optional mental trait tags, PDR M5)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models import MentalProfile, ScoutComment
from backend.app.tools.common import not_found, resolve_player
from ml.mental_traits import CORE_TRAITS, QB_TRAITS

VALID_TRAITS = set(CORE_TRAITS) | set(QB_TRAITS)

TOOL = {
    "name": "scout_comment",
    "description": "Log a scout's comment on a player. Optional mental trait tags "
                   "(trait + score 0..1) feed the crowdsourced mental profile.",
    "input_schema": {
        "type": "object",
        "properties": {
            "name_or_id": {"type": "string"},
            "body": {"type": "string"},
            "traits": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "trait": {"type": "string"},
                        "score": {"type": "number"},
                    },
                    "required": ["trait", "score"],
                },
            },
        },
        "required": ["name_or_id", "body"],
    },
}


async def run(session: AsyncSession, args: dict, user_id: str = "assistant") -> dict:
    player = await resolve_player(session, args["name_or_id"])
    if not player:
        return not_found(args["name_or_id"])
    traits = [
        t for t in (args.get("traits") or [])
        if t.get("trait") in VALID_TRAITS and 0.0 <= float(t.get("score", -1)) <= 1.0
    ]
    comment = ScoutComment(
        player_id=player.id, author_id=user_id, author_name=user_id,
        body=args["body"], traits=traits,
    )
    session.add(comment)
    for t in traits:
        session.add(MentalProfile(
            player_id=player.id, trait=t["trait"], score=float(t["score"]),
            evidence=args["body"][:300], source="scout_tag",
        ))
    await session.commit()
    return {
        "saved": True,
        "player": {"id": player.id, "name": player.name},
        "tags_recorded": len(traits),
        "detail": f"scout_comment on {player.name} ({len(traits)} trait tags)",
        "count": 1,
    }

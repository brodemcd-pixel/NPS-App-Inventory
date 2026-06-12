"""Operation 10: NFL outcome lookup (drafted classes back-test data)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models import MockConsensus, NflOutcome
from backend.app.domain import MOCK_MILESTONES
from backend.app.tools.common import brief, not_found, resolve_player

TOOL = {
    "name": "nfl_outcome_lookup",
    "description": "NFL production overlay for a drafted player: per-season games, "
                   "snaps, PFF grade and stats, plus pre-draft mock consensus movement.",
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
    outcomes = (
        (await session.execute(
            select(NflOutcome)
            .where(NflOutcome.player_id == player.id)
            .order_by(NflOutcome.season)
        )).scalars().all()
    )
    mocks = (
        (await session.execute(
            select(MockConsensus).where(MockConsensus.player_id == player.id)
        )).scalars().all()
    )
    order = {m: i for i, m in enumerate(MOCK_MILESTONES)}
    mocks.sort(key=lambda m: order.get(m.milestone, 99))
    return {
        "player": brief(player),
        "drafted": player.draft_pick is not None,
        "nfl_seasons": [
            {"season": o.season, "games": o.games, "snaps": o.snaps,
             "pff_grade": o.pff_grade, "stats": o.stats}
            for o in outcomes
        ],
        "mock_consensus": [
            {"milestone": m.milestone, "consensus_rank": m.consensus_rank} for m in mocks
        ],
        "detail": f"nfl_outcome_lookup {player.name}",
        "count": len(outcomes),
    }

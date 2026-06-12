"""Operation 9: college production stats lookup."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models import Production
from backend.app.services import analytics
from backend.app.tools.common import brief, not_found, resolve_player

TOOL = {
    "name": "production_lookup",
    "description": "College production stats for a player (per-season volume stats and "
                   "team share), plus the trajectory summary (trend, consistency).",
    "input_schema": {
        "type": "object",
        "properties": {
            "name_or_id": {"type": "string"},
            "season": {"type": "integer"},
        },
        "required": ["name_or_id"],
    },
}


async def run(session: AsyncSession, args: dict) -> dict:
    player = await resolve_player(session, args["name_or_id"])
    if not player:
        return not_found(args["name_or_id"])
    stmt = select(Production).where(Production.player_id == player.id)
    if args.get("season"):
        stmt = stmt.where(Production.season == int(args["season"]))
    rows = (await session.execute(stmt.order_by(Production.season))).scalars().all()
    by_season: dict[int, dict] = {}
    for r in rows:
        entry = by_season.setdefault(r.season, {})
        entry[r.stat_category] = r.value
        if r.team_share_pct is not None:
            entry[f"{r.stat_category}_team_share_pct"] = r.team_share_pct
    season_scores = await analytics.season_scores(session, player)
    trend, consistency = analytics.trajectory_summary(season_scores)
    return {
        "player": brief(player),
        "seasons": by_season,
        "sos_tier": player.sos_tier,
        "breakout_age": player.breakout_age,
        "trajectory": {"trend": trend, "consistency": consistency, "seasons": season_scores},
        "detail": f"production_lookup {player.name}"
                  + (f" season={args['season']}" if args.get("season") else ""),
        "count": len(by_season),
    }

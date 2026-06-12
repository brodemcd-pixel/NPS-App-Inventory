"""Operation 3: scouting report text search."""

from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models import Player
from backend.app.tools.common import brief

TOOL = {
    "name": "report_search",
    "description": "Keyword search across scouting report text (overview, strengths, "
                   "weaknesses, sources-tell-us). Returns players whose reports mention "
                   "the phrase, with the matching snippet.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "limit": {"type": "integer", "default": 10},
        },
        "required": ["query"],
    },
}


def _snippet(player: Player, term: str) -> str:
    for section, text in [
        ("overview", player.overview), ("strengths", player.strengths),
        ("weaknesses", player.weaknesses), ("sources_tell_us", player.sources_tell_us),
    ]:
        low = (text or "").lower()
        pos = low.find(term.lower())
        if pos >= 0:
            start = max(0, pos - 60)
            return f"[{section}] …{text[start:pos + len(term) + 90]}…"
    return ""


async def run(session: AsyncSession, args: dict) -> dict:
    term = args["query"].strip()
    limit = min(25, int(args.get("limit") or 10))
    like = f"%{term}%"
    players = (
        (
            await session.execute(
                select(Player)
                .where(or_(
                    Player.overview.ilike(like), Player.strengths.ilike(like),
                    Player.weaknesses.ilike(like), Player.sources_tell_us.ilike(like),
                ))
                .order_by(Player.nfl_grade.desc())
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )
    return {
        "matches": [{**brief(p), "snippet": _snippet(p, term)} for p in players],
        "detail": f"report_search '{term}'",
        "count": len(players),
    }

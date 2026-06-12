"""Shared helpers for assistant tools."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models import Player


async def resolve_player(session: AsyncSession, name_or_id: str | int) -> Player | None:
    """Resolve a player by id or (fuzzy) name."""
    if isinstance(name_or_id, int) or str(name_or_id).isdigit():
        return await session.get(Player, int(name_or_id))
    term = str(name_or_id).strip()
    exact = (
        await session.execute(select(Player).where(Player.name.ilike(term)).limit(1))
    ).scalar_one_or_none()
    if exact:
        return exact
    return (
        await session.execute(
            select(Player)
            .where(Player.name.ilike(f"%{term}%"))
            .order_by(Player.nfl_grade.desc())
            .limit(1)
        )
    ).scalar_one_or_none()


def brief(p: Player) -> dict:
    """Compact player reference used inside tool results."""
    return {
        "id": p.id,
        "name": p.name,
        "position": p.position,
        "college": p.college,
        "draft_class": p.draft_class,
        "nfl_grade": p.nfl_grade,
        "forty": p.forty,
        "draft_round": p.draft_round,
        "draft_pick": p.draft_pick,
        "draft_team": p.draft_team,
    }


def not_found(name_or_id) -> dict:
    return {"error": f"no player matched '{name_or_id}'", "detail": f"player lookup '{name_or_id}' (no match)"}

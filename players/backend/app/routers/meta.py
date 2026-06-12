"""Health + filter metadata endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app import domain
from backend.app.db import get_session
from backend.app.models import Player
from backend.app.services.players_query import SORT_OPTIONS
from ml.mental_traits import CORE_TRAITS, QB_TRAITS

router = APIRouter()


@router.get("/health")
async def health(session: AsyncSession = Depends(get_session)) -> dict:
    count = (await session.execute(select(func.count(Player.id)))).scalar_one()
    return {"status": "ok", "players": count}


@router.get("/meta/filters")
async def meta_filters(session: AsyncSession = Depends(get_session)) -> dict:
    async def distinct(col):
        rows = (await session.execute(select(col).distinct().order_by(col))).scalars().all()
        return [r for r in rows if r is not None]

    return {
        "classes": await distinct(Player.draft_class),
        "positions": domain.POSITIONS,
        "position_groups": domain.POSITION_GROUP_LIST,
        "teams": await distinct(Player.draft_team),
        "colleges": await distinct(Player.college),
        "conferences": await distinct(Player.conference),
        "offense_schemes": domain.OFFENSE_SCHEMES,
        "defense_schemes": domain.DEFENSE_SCHEMES,
        "coaching_trees": domain.COACHING_TREES,
        "roles": domain.ALL_ROLES,
        "traits": sorted(CORE_TRAITS) + sorted(QB_TRAITS),
        "sort_options": SORT_OPTIONS,
    }

"""Player list/detail/similar/team-fit/compare/umap endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db import get_session
from backend.app.models import Player
from backend.app.services import similarity as sim
from backend.app.services import usage
from backend.app.services.details import player_detail
from backend.app.services.players_query import (
    active_filters,
    player_summaries,
    run_player_query,
)
from backend.app.services.team_fit import team_fits

router = APIRouter()


def list_params(
    q: str | None = None,
    draft_class: list[int] | None = Query(None),
    round: list[int] | None = Query(None),
    position: list[str] | None = Query(None),
    position_group: list[str] | None = Query(None),
    team: str | None = None,
    college: str | None = None,
    conference: str | None = None,
    height_min: float | None = None,
    height_max: float | None = None,
    weight_min: float | None = None,
    weight_max: float | None = None,
    forty_max: float | None = None,
    arm_min: float | None = None,
    hand_min: float | None = None,
    wingspan_min: float | None = None,
    scheme: str | None = None,
    coaching_tree: str | None = None,
    role: str | None = None,
    red_flag: bool | None = None,
    green_flag: bool | None = None,
    trait: str | None = None,
    trait_min: float | None = None,
    sort: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> dict:
    return {k: v for k, v in locals().items() if v is not None}


@router.get("/players")
async def list_players(
    params: dict = Depends(list_params),
    session: AsyncSession = Depends(get_session),
    user_id: str = Header("demo-user", alias="X-User-Id"),
) -> dict:
    players, total = await run_player_query(session, params)
    items = await player_summaries(session, players)
    if filters := active_filters(params):
        await usage.log_event("filter_applied", {"filters": filters}, user_id)
    return {
        "items": items,
        "total": total,
        "page": int(params.get("page", 1)),
        "page_size": int(params.get("page_size", 50)),
    }


async def _get_player(session: AsyncSession, player_id: int) -> Player:
    player = await session.get(Player, player_id)
    if player is None:
        raise HTTPException(404, "player not found")
    return player


@router.get("/players/{player_id}")
async def get_player(
    player_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: str = Header("demo-user", alias="X-User-Id"),
) -> dict:
    player = await _get_player(session, player_id)
    detail = await player_detail(session, player)
    await usage.log_event("player_view", {"player_id": player.id, "name": player.name}, user_id)
    return detail


@router.get("/players/{player_id}/similar")
async def similar(
    player_id: int,
    limit: int = 10,
    w_scouting: float | None = None,
    w_scheme: float | None = None,
    w_mental: float | None = None,
    cross_position: bool = False,
    session: AsyncSession = Depends(get_session),
) -> dict:
    player = await _get_player(session, player_id)
    weights = None
    if any(w is not None for w in (w_scouting, w_scheme, w_mental)):
        weights = {"scouting": w_scouting, "scheme": w_scheme, "mental": w_mental}
        weights = {k: v for k, v in weights.items() if v is not None}
    result = await sim.similar_players(
        session, player, limit=min(50, limit), weights=weights, cross_position=cross_position
    )
    candidates = [cand for cand, _overall, _axes in result["items"]]
    summaries = await player_summaries(session, candidates)
    items = [
        {
            "player": summary,
            "overall": round(overall, 4),
            "axes": {k: (round(v, 4) if v is not None else None) for k, v in axes.items()},
        }
        for summary, (_cand, overall, axes) in zip(summaries, result["items"])
    ]
    return {"items": items, "weights_used": result["weights_used"]}


@router.get("/players/{player_id}/team_fit")
async def player_team_fit(
    player_id: int,
    limit: int = 10,
    session: AsyncSession = Depends(get_session),
) -> dict:
    player = await _get_player(session, player_id)
    return {"items": await team_fits(session, player, limit=min(32, limit))}


@router.get("/compare")
async def compare(
    a: int,
    b: int,
    session: AsyncSession = Depends(get_session),
    user_id: str = Header("demo-user", alias="X-User-Id"),
) -> dict:
    player_a = await _get_player(session, a)
    player_b = await _get_player(session, b)
    similarity = await sim.pair_similarity(session, player_a, player_b)
    await usage.log_event("compare_view", {"a": a, "b": b}, user_id)
    return {
        "a": await player_detail(session, player_a),
        "b": await player_detail(session, player_b),
        "similarity": similarity,
    }


@router.get("/umap")
async def umap_coords(session: AsyncSession = Depends(get_session)) -> dict:
    rows = (
        await session.execute(
            select(
                Player.id, Player.name, Player.position, Player.position_group,
                Player.draft_class, Player.umap_x, Player.umap_y,
            ).where(Player.umap_x.is_not(None))
        )
    ).all()
    return {
        "items": [
            {
                "player_id": pid, "name": name, "position": pos,
                "position_group": group, "draft_class": cls, "x": x, "y": y,
            }
            for pid, name, pos, group, cls, x, y in rows
        ]
    }

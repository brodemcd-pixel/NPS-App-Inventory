"""Watchlist CRUD (PDR U1)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db import get_session
from backend.app.models import Player, Watchlist, WatchlistPlayer
from backend.app.services import usage
from backend.app.services.players_query import player_summaries

router = APIRouter()


class WatchlistCreate(BaseModel):
    name: str


class WatchlistAdd(BaseModel):
    player_id: int
    note: str | None = None


async def _owned(session: AsyncSession, watchlist_id: int, user_id: str) -> Watchlist:
    wl = await session.get(Watchlist, watchlist_id)
    if wl is None or wl.owner_id != user_id:
        raise HTTPException(404, "watchlist not found")
    return wl


@router.get("/watchlists")
async def list_watchlists(
    session: AsyncSession = Depends(get_session),
    user_id: str = Header("demo-user", alias="X-User-Id"),
) -> dict:
    lists = (
        (
            await session.execute(
                select(Watchlist)
                .where(Watchlist.owner_id == user_id)
                .order_by(Watchlist.created_at)
            )
        )
        .scalars()
        .all()
    )
    items = []
    for wl in lists:
        entries = (
            await session.execute(
                select(WatchlistPlayer, Player)
                .join(Player, Player.id == WatchlistPlayer.player_id)
                .where(WatchlistPlayer.watchlist_id == wl.id)
                .order_by(WatchlistPlayer.added_at)
            )
        ).all()
        summaries = await player_summaries(session, [p for _e, p in entries])
        items.append(
            {
                "id": wl.id,
                "name": wl.name,
                "created_at": wl.created_at.isoformat() if wl.created_at else None,
                "players": [
                    {
                        **summary,
                        "note": entry.note,
                        "added_at": entry.added_at.isoformat() if entry.added_at else None,
                    }
                    for summary, (entry, _p) in zip(summaries, entries)
                ],
            }
        )
    return {"items": items}


@router.post("/watchlists", status_code=201)
async def create_watchlist(
    body: WatchlistCreate,
    session: AsyncSession = Depends(get_session),
    user_id: str = Header("demo-user", alias="X-User-Id"),
) -> dict:
    wl = Watchlist(owner_id=user_id, name=body.name.strip() or "Untitled")
    session.add(wl)
    await session.commit()
    return {"id": wl.id, "name": wl.name,
            "created_at": wl.created_at.isoformat() if wl.created_at else None,
            "players": []}


@router.delete("/watchlists/{watchlist_id}", status_code=204)
async def delete_watchlist(
    watchlist_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: str = Header("demo-user", alias="X-User-Id"),
) -> None:
    wl = await _owned(session, watchlist_id, user_id)
    await session.delete(wl)
    await session.commit()


@router.post("/watchlists/{watchlist_id}/players", status_code=201)
async def add_player(
    watchlist_id: int,
    body: WatchlistAdd,
    session: AsyncSession = Depends(get_session),
    user_id: str = Header("demo-user", alias="X-User-Id"),
) -> dict:
    await _owned(session, watchlist_id, user_id)
    if await session.get(Player, body.player_id) is None:
        raise HTTPException(404, "player not found")
    existing = await session.get(WatchlistPlayer, (watchlist_id, body.player_id))
    if existing is None:
        session.add(WatchlistPlayer(
            watchlist_id=watchlist_id, player_id=body.player_id, note=body.note
        ))
        await session.commit()
        await usage.log_event(
            "watchlist_add", {"watchlist_id": watchlist_id, "player_id": body.player_id},
            user_id,
        )
    return {"added": existing is None}


@router.delete("/watchlists/{watchlist_id}/players/{player_id}", status_code=204)
async def remove_player(
    watchlist_id: int,
    player_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: str = Header("demo-user", alias="X-User-Id"),
) -> None:
    await _owned(session, watchlist_id, user_id)
    entry = await session.get(WatchlistPlayer, (watchlist_id, player_id))
    if entry is not None:
        await session.delete(entry)
        await session.commit()

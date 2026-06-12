"""Scout comments + crowdsourced mental trait tagging (PDR M5)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db import get_session
from backend.app.models import MentalProfile, Player, ScoutComment
from ml.mental_traits import CORE_TRAITS, QB_TRAITS

router = APIRouter()

VALID_TRAITS = set(CORE_TRAITS) | set(QB_TRAITS)


class TraitTag(BaseModel):
    trait: str
    score: float


class CommentCreate(BaseModel):
    player_id: int
    body: str
    traits: list[TraitTag] | None = None


@router.post("/comments", status_code=201)
async def create_comment(
    payload: CommentCreate,
    session: AsyncSession = Depends(get_session),
    user_id: str = Header("demo-user", alias="X-User-Id"),
) -> dict:
    player = await session.get(Player, payload.player_id)
    if player is None:
        raise HTTPException(404, "player not found")
    tags = [
        t for t in (payload.traits or [])
        if t.trait in VALID_TRAITS and 0.0 <= t.score <= 1.0
    ]
    comment = ScoutComment(
        player_id=player.id,
        author_id=user_id,
        author_name=user_id,
        body=payload.body,
        traits=[t.model_dump() for t in tags],
    )
    session.add(comment)
    for t in tags:
        session.add(MentalProfile(
            player_id=player.id, trait=t.trait, score=t.score,
            evidence=payload.body[:300], source="scout_tag",
        ))
    await session.commit()
    return {
        "id": comment.id,
        "author_name": comment.author_name,
        "body": comment.body,
        "traits": comment.traits,
        "created_at": comment.created_at.isoformat() if comment.created_at else None,
    }

"""FSM model accuracy dashboard (PDR O3)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db import get_session
from backend.app.services.accuracy import compute_accuracy

router = APIRouter()


@router.get("/accuracy")
async def accuracy(session: AsyncSession = Depends(get_session)) -> dict:
    return await compute_accuracy(session)

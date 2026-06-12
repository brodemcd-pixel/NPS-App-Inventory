"""Async engine, session factory and declarative base."""

from __future__ import annotations

import os
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from backend.app.config import settings


class Base(DeclarativeBase):
    pass


# Tests set PLAYERS_DB_NULLPOOL=1 so connections are never reused across event loops
# (pytest-asyncio uses one loop per test).
_engine_kwargs: dict = {"echo": False}
if os.environ.get("PLAYERS_DB_NULLPOOL"):
    _engine_kwargs["poolclass"] = NullPool

engine = create_async_engine(settings.database_url, **_engine_kwargs)

async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency."""
    async with async_session() as session:
        yield session

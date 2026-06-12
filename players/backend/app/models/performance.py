"""College production, NFL outcomes, mock-draft consensus (CONTRACT.md §2 P1/O1/O2)."""

from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db import Base


class Production(Base):
    __tablename__ = "production"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"), index=True
    )
    season: Mapped[int] = mapped_column(Integer)
    stat_category: Mapped[str] = mapped_column(String(40))
    value: Mapped[float] = mapped_column(Float)
    team_share_pct: Mapped[float | None] = mapped_column(Float, nullable=True)


class NflOutcome(Base):
    __tablename__ = "nfl_outcomes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"), index=True
    )
    season: Mapped[int] = mapped_column(Integer)
    games: Mapped[int] = mapped_column(Integer)
    snaps: Mapped[int] = mapped_column(Integer)
    pff_grade: Mapped[float | None] = mapped_column(Float, nullable=True)
    stats: Mapped[dict] = mapped_column(JSONB, default=dict)


class MockConsensus(Base):
    __tablename__ = "mock_consensus"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"), index=True
    )
    milestone: Mapped[str] = mapped_column(String(20))  # see §1 milestones
    consensus_rank: Mapped[int] = mapped_column(Integer)

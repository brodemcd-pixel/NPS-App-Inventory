"""Mental/intangible profiles and cognitive tests (CONTRACT.md §2 M1-M5)."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db import Base


class MentalProfile(Base):
    __tablename__ = "mental_profiles"
    __table_args__ = (Index("ix_mental_profiles_player_trait", "player_id", "trait"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"))
    trait: Mapped[str] = mapped_column(String(60))
    score: Mapped[float] = mapped_column(Float)  # 0..1
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(16))  # nlp | scout_tag | cognitive_test
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class CognitiveTest(Base):
    __tablename__ = "cognitive_tests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"), index=True
    )
    provider: Mapped[str] = mapped_column(String(60))
    composite_score: Mapped[float] = mapped_column(Float)
    percentile: Mapped[float] = mapped_column(Float)
    taken_at: Mapped[date] = mapped_column(Date)

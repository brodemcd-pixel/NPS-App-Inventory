"""College schemes, functional roles, NFL team schemes (CONTRACT.md §2 S1-S5)."""

from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db import Base


class Scheme(Base):
    __tablename__ = "schemes"
    __table_args__ = (Index("ix_schemes_school_year", "school", "year"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    school: Mapped[str] = mapped_column(String(120))
    year: Mapped[int] = mapped_column(Integer)
    side: Mapped[str] = mapped_column(String(8))  # offense | defense
    scheme_archetype: Mapped[str] = mapped_column(String(60))
    coordinator: Mapped[str] = mapped_column(String(120))
    coaching_tree: Mapped[str] = mapped_column(String(60))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class PlayerRole(Base):
    __tablename__ = "player_roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"), index=True
    )
    functional_role: Mapped[str] = mapped_column(String(60))
    source: Mapped[str] = mapped_column(String(16))  # pff | manual | derived
    confidence: Mapped[float] = mapped_column(Float)  # 0..1


class NflTeam(Base):
    __tablename__ = "nfl_teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team: Mapped[str] = mapped_column(String(60))
    season: Mapped[int] = mapped_column(Integer)
    side: Mapped[str] = mapped_column(String(8))  # offense | defense
    scheme_archetype: Mapped[str] = mapped_column(String(60))
    coordinator: Mapped[str] = mapped_column(String(120))
    coaching_tree: Mapped[str] = mapped_column(String(60))

"""Player core table + field provenance (CONTRACT.md §2)."""

from __future__ import annotations

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db import Base


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    draft_class: Mapped[int] = mapped_column(Integer, index=True)
    position: Mapped[str] = mapped_column(String(8), index=True)
    position_group: Mapped[str] = mapped_column(String(8), index=True)
    college: Mapped[str] = mapped_column(String(120))
    conference: Mapped[str] = mapped_column(String(60))

    height_in: Mapped[float] = mapped_column(Float)
    weight_lb: Mapped[int] = mapped_column(Integer)
    forty: Mapped[float | None] = mapped_column(Float, nullable=True)
    vertical_in: Mapped[float | None] = mapped_column(Float, nullable=True)
    broad_in: Mapped[float | None] = mapped_column(Float, nullable=True)
    three_cone: Mapped[float | None] = mapped_column(Float, nullable=True)
    shuttle: Mapped[float | None] = mapped_column(Float, nullable=True)
    bench_reps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    arm_length_in: Mapped[float | None] = mapped_column(Float, nullable=True)
    hand_size_in: Mapped[float | None] = mapped_column(Float, nullable=True)
    wingspan_in: Mapped[float | None] = mapped_column(Float, nullable=True)

    nfl_grade: Mapped[float] = mapped_column(Float)
    ngs_athleticism: Mapped[float | None] = mapped_column(Float, nullable=True)
    class_percentile: Mapped[float] = mapped_column(Float)

    draft_round: Mapped[int | None] = mapped_column(Integer, nullable=True)
    draft_pick: Mapped[int | None] = mapped_column(Integer, nullable=True)
    draft_team: Mapped[str | None] = mapped_column(String(60), nullable=True)

    overview: Mapped[str] = mapped_column(Text, default="")
    strengths: Mapped[str] = mapped_column(Text, default="")
    weaknesses: Mapped[str] = mapped_column(Text, default="")
    sources_tell_us: Mapped[str] = mapped_column(Text, default="")

    red_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    green_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    flag_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    sos_tier: Mapped[int] = mapped_column(Integer, default=3)  # 1=weakest..5=strongest
    breakout_age: Mapped[float | None] = mapped_column(Float, nullable=True)

    embedding: Mapped[list[float] | None] = mapped_column(Vector(384), nullable=True)
    umap_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    umap_y: Mapped[float | None] = mapped_column(Float, nullable=True)


class FieldProvenance(Base):
    __tablename__ = "field_provenance"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"), index=True
    )
    field_name: Mapped[str] = mapped_column(String(60))
    source: Mapped[str] = mapped_column(String(120))
    source_url: Mapped[str | None] = mapped_column(String(400), nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

"""Field provenance helpers (CONTRACT.md §1/§8)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models import FieldProvenance, Player

SEED_SOURCE = "SYNTHETIC_SEED"

MEASURABLE_FIELDS = [
    "height_in", "weight_lb", "forty", "vertical_in", "broad_in", "three_cone",
    "shuttle", "bench_reps", "arm_length_in", "hand_size_in", "wingspan_in",
]
GRADE_FIELDS = ["nfl_grade", "ngs_athleticism", "class_percentile"]
REPORT_FIELDS = ["overview", "strengths", "weaknesses", "sources_tell_us"]

PROVENANCE_FIELDS = MEASURABLE_FIELDS + GRADE_FIELDS + REPORT_FIELDS


def seed_provenance_rows(player: Player) -> list[FieldProvenance]:
    """Provenance rows for every non-null measurable/grade/report field."""
    rows = []
    for field in PROVENANCE_FIELDS:
        if getattr(player, field, None) is not None:
            rows.append(
                FieldProvenance(player_id=player.id, field_name=field, source=SEED_SOURCE)
            )
    return rows


async def write_seed_provenance(session: AsyncSession, player: Player) -> None:
    session.add_all(seed_provenance_rows(player))

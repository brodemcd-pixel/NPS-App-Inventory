"""PlayerDetail assembly (CONTRACT.md §6 GET /api/players/{id})."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ml.mental_traits import CORE_TRAITS, QB_TRAITS

from backend.app.domain import MOCK_MILESTONES, side_for_position_group
from backend.app.models import (
    CognitiveTest,
    FieldProvenance,
    MentalProfile,
    MockConsensus,
    NflOutcome,
    Player,
    PlayerRole,
    Production,
    Scheme,
    ScoutComment,
)
from backend.app.services import analytics
from backend.app.services.players_query import player_summaries


def _aggregate_traits(rows: list[MentalProfile], trait_names: set[str]) -> list[dict]:
    by_trait: dict[str, list[MentalProfile]] = {}
    for r in rows:
        if r.trait in trait_names:
            by_trait.setdefault(r.trait, []).append(r)
    out = []
    for trait, items in by_trait.items():
        out.append(
            {
                "trait": trait,
                "score": round(sum(i.score for i in items) / len(items), 3),
                "sources": sorted({i.source for i in items}),
                "evidence": [i.evidence for i in items if i.evidence],
            }
        )
    return sorted(out, key=lambda t: -t["score"])


async def player_detail(session: AsyncSession, player: Player) -> dict:
    detail = (await player_summaries(session, [player]))[0]

    seasons = (
        (
            await session.execute(
                select(Production.season)
                .where(Production.player_id == player.id)
                .distinct()
                .order_by(Production.season)
            )
        )
        .scalars()
        .all()
    )
    side = side_for_position_group(player.position_group)
    scheme_rows: list[Scheme] = []
    if seasons:
        scheme_rows = (
            (
                await session.execute(
                    select(Scheme)
                    .where(
                        Scheme.school == player.college,
                        Scheme.year.in_(seasons),
                        Scheme.side == side,
                    )
                    .order_by(Scheme.year)
                )
            )
            .scalars()
            .all()
        )

    roles = (
        (
            await session.execute(
                select(PlayerRole).where(PlayerRole.player_id == player.id)
            )
        )
        .scalars()
        .all()
    )

    mental_rows = (
        (
            await session.execute(
                select(MentalProfile).where(MentalProfile.player_id == player.id)
            )
        )
        .scalars()
        .all()
    )
    cognitive = (
        await session.execute(
            select(CognitiveTest)
            .where(CognitiveTest.player_id == player.id)
            .order_by(CognitiveTest.taken_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    production = (
        (
            await session.execute(
                select(Production)
                .where(Production.player_id == player.id)
                .order_by(Production.season, Production.stat_category)
            )
        )
        .scalars()
        .all()
    )

    season_scores = await analytics.season_scores(session, player)
    trend, consistency = analytics.trajectory_summary(season_scores)

    outcomes = (
        (
            await session.execute(
                select(NflOutcome)
                .where(NflOutcome.player_id == player.id)
                .order_by(NflOutcome.season)
            )
        )
        .scalars()
        .all()
    )

    mocks = (
        (
            await session.execute(
                select(MockConsensus).where(MockConsensus.player_id == player.id)
            )
        )
        .scalars()
        .all()
    )
    mock_order = {m: i for i, m in enumerate(MOCK_MILESTONES)}
    mocks.sort(key=lambda m: mock_order.get(m.milestone, 99))

    comments = (
        (
            await session.execute(
                select(ScoutComment)
                .where(ScoutComment.player_id == player.id)
                .order_by(ScoutComment.created_at.desc())
            )
        )
        .scalars()
        .all()
    )

    provenance = (
        (
            await session.execute(
                select(FieldProvenance).where(FieldProvenance.player_id == player.id)
            )
        )
        .scalars()
        .all()
    )

    detail.update(
        {
            "measurables": {
                "height_in": player.height_in,
                "weight_lb": player.weight_lb,
                "forty": player.forty,
                "vertical_in": player.vertical_in,
                "broad_in": player.broad_in,
                "three_cone": player.three_cone,
                "shuttle": player.shuttle,
                "bench_reps": player.bench_reps,
                "arm_length_in": player.arm_length_in,
                "hand_size_in": player.hand_size_in,
                "wingspan_in": player.wingspan_in,
            },
            "report": {
                "overview": player.overview,
                "strengths": player.strengths,
                "weaknesses": player.weaknesses,
                "sources_tell_us": player.sources_tell_us,
            },
            "flags": {
                "red_flag": player.red_flag,
                "green_flag": player.green_flag,
                "notes": player.flag_notes,
            },
            "scheme_context": [
                {
                    "season": s.year,
                    "scheme_archetype": s.scheme_archetype,
                    "coordinator": s.coordinator,
                    "coaching_tree": s.coaching_tree,
                    "side": s.side,
                }
                for s in scheme_rows
            ],
            "roles": [
                {
                    "functional_role": r.functional_role,
                    "source": r.source,
                    "confidence": r.confidence,
                }
                for r in roles
            ],
            "mental_profile": {
                "core": _aggregate_traits(mental_rows, set(CORE_TRAITS)),
                "qb": _aggregate_traits(mental_rows, set(QB_TRAITS)),
                "cognitive": (
                    {
                        "provider": cognitive.provider,
                        "composite_score": cognitive.composite_score,
                        "percentile": cognitive.percentile,
                        "taken_at": cognitive.taken_at.isoformat(),
                    }
                    if cognitive
                    else None
                ),
            },
            "production": [
                {
                    "season": p.season,
                    "stat_category": p.stat_category,
                    "value": p.value,
                    "team_share_pct": p.team_share_pct,
                }
                for p in production
            ],
            "trajectory": {
                "breakout_age": player.breakout_age,
                "seasons": season_scores,
                "trend": trend,
                "consistency": consistency,
            },
            "nfl_outcomes": [
                {
                    "season": o.season,
                    "games": o.games,
                    "snaps": o.snaps,
                    "pff_grade": o.pff_grade,
                    "stats": o.stats,
                }
                for o in outcomes
            ],
            "mock_consensus": [
                {"milestone": m.milestone, "consensus_rank": m.consensus_rank}
                for m in mocks
            ],
            "sos_tier": player.sos_tier,
            "comments": [
                {
                    "id": c.id,
                    "author_name": c.author_name,
                    "body": c.body,
                    "traits": c.traits or [],
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                }
                for c in comments
            ],
            "provenance": [
                {
                    "field_name": p.field_name,
                    "source": p.source,
                    "retrieved_at": p.retrieved_at.isoformat() if p.retrieved_at else None,
                }
                for p in provenance
            ],
            "umap": {"x": player.umap_x, "y": player.umap_y},
        }
    )
    return detail

"""Production trajectory scoring + usage analytics summary (CONTRACT.md §6)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np
from sqlalchemy import func, literal_column, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models import Player, Production, UsageEvent

# Position-relevant volume stats with weights converting each category to a roughly
# comparable "yardage-equivalent" volume (TDs ~ 20 yds, sacks/tfl/turnovers weighted up).
RELEVANT_STATS: dict[str, dict[str, float]] = {
    "QB": {"pass_yards": 1.0, "pass_td": 20.0, "rush_yards": 0.8, "rush_td": 20.0},
    "RB": {"rush_yards": 1.0, "rush_td": 20.0, "rec_yards": 1.0, "rec_td": 20.0,
           "receptions": 5.0},
    "WR": {"rec_yards": 1.0, "rec_td": 20.0, "receptions": 5.0, "targets": 2.0},
    "TE": {"rec_yards": 1.0, "rec_td": 20.0, "receptions": 5.0, "targets": 2.0},
    "OL": {"snaps": 1.0},
    "DL": {"sacks": 60.0, "tfl": 30.0, "pressures": 12.0, "tackles": 8.0},
    "LB": {"tackles": 8.0, "tfl": 30.0, "sacks": 60.0, "interceptions": 80.0,
           "pass_breakups": 25.0},
    "DB": {"tackles": 8.0, "interceptions": 80.0, "pass_breakups": 25.0, "tfl": 30.0},
}


async def season_scores(session: AsyncSession, player: Player) -> list[dict]:
    """Season production scores 0..100 for a player.

    Formula: for each (player, season) compute a weighted volume sum over the
    position-group-relevant stat categories (RELEVANT_STATS). The season score is the
    percentile rank of that volume among ALL player-seasons of the same position group
    in the dataset: score = 100 * (#strictly_lower + 0.5*#ties_excl_self) / (N - 1)
    (100.0 when N == 1). Computed on demand, never stored.
    """
    weights = RELEVANT_STATS.get(player.position_group, {"snaps": 1.0})
    rows = await session.execute(
        select(Production.player_id, Production.season, Production.stat_category,
               Production.value)
        .join(Player, Player.id == Production.player_id)
        .where(Player.position_group == player.position_group,
               Production.stat_category.in_(list(weights)))
    )
    volumes: dict[tuple[int, int], float] = {}
    for pid, season, cat, value in rows.all():
        key = (pid, season)
        volumes[key] = volumes.get(key, 0.0) + weights[cat] * (value or 0.0)
    all_vols = np.array(list(volumes.values()), dtype=np.float64)
    n = len(all_vols)
    out = []
    for (pid, season), vol in sorted(volumes.items()):
        if pid != player.id:
            continue
        if n <= 1:
            score = 100.0
        else:
            lower = float(np.sum(all_vols < vol))
            ties = float(np.sum(all_vols == vol)) - 1.0
            score = 100.0 * (lower + 0.5 * ties) / (n - 1)
        out.append({"season": season, "score": round(score, 1)})
    return out


def trajectory_summary(seasons: list[dict]) -> tuple[str, float]:
    """(trend, consistency) from season scores.

    trend = sign of the least-squares slope of score over season index
    (>+1.5 pts/season ascending, <-1.5 declining, else flat).
    consistency = 1 - stdev(scores)/50 clamped to [0, 1] (50 = half the 0..100 range).
    """
    scores = np.array([s["score"] for s in seasons], dtype=np.float64)
    if len(scores) < 2:
        return "flat", 1.0
    slope = float(np.polyfit(np.arange(len(scores)), scores, 1)[0])
    trend = "ascending" if slope > 1.5 else "declining" if slope < -1.5 else "flat"
    consistency = float(max(0.0, min(1.0, 1.0 - np.std(scores) / 50.0)))
    return trend, round(consistency, 2)


async def usage_summary(session: AsyncSession, days: int = 30) -> dict:
    since = datetime.now(timezone.utc) - timedelta(days=days)

    counts = dict(
        (
            await session.execute(
                select(UsageEvent.event_type, func.count())
                .where(UsageEvent.created_at >= since)
                .group_by(UsageEvent.event_type)
            )
        ).all()
    )
    # "Sessions" approximated as distinct (user, day) pairs.
    sessions = (
        await session.execute(
            select(
                func.count(
                    func.distinct(
                        func.concat(
                            func.coalesce(UsageEvent.user_id, "anon"),
                            ":",
                            func.date_trunc("day", UsageEvent.created_at),
                        )
                    )
                )
            ).where(UsageEvent.created_at >= since)
        )
    ).scalar_one()

    viewed = (
        await session.execute(
            select(UsageEvent.payload["player_id"].as_integer(), func.count())
            .where(UsageEvent.created_at >= since,
                   UsageEvent.event_type == "player_view")
            # GROUP BY 1: the JSON path renders as a fresh bind param each time, which
            # Postgres would reject as a non-grouped expression.
            .group_by(literal_column("1"))
            .order_by(func.count().desc())
            .limit(5)
        )
    ).all()
    most_discussed = []
    if viewed:
        names = dict(
            (
                await session.execute(
                    select(Player.id, Player.name).where(
                        Player.id.in_([pid for pid, _ in viewed if pid is not None])
                    )
                )
            ).all()
        )
        most_discussed = [
            {"player_id": pid, "name": names.get(pid, "unknown"), "count": count}
            for pid, count in viewed
            if pid is not None
        ]

    filter_rows = (
        await session.execute(
            select(UsageEvent.payload).where(
                UsageEvent.created_at >= since,
                UsageEvent.event_type == "filter_applied",
            )
        )
    ).scalars().all()
    filter_counts: dict[str, int] = {}
    for payload in filter_rows:
        for key, value in (payload or {}).items():
            if isinstance(value, list):
                value = ",".join(str(v) for v in value)
            label = f"{key}={value}"
            filter_counts[label] = filter_counts.get(label, 0) + 1
    common_filters = [
        {"filter": k, "count": v}
        for k, v in sorted(filter_counts.items(), key=lambda kv: -kv[1])[:10]
    ]

    per_day = (
        await session.execute(
            select(
                func.to_char(func.date_trunc("day", UsageEvent.created_at), "YYYY-MM-DD"),
                func.count(),
            )
            .where(UsageEvent.created_at >= since,
                   UsageEvent.event_type == "question_asked")
            .group_by(literal_column("1"))
            .order_by(literal_column("1"))
        )
    ).all()

    return {
        "page_views": counts.get("page_view", 0) + counts.get("player_view", 0),
        "questions_asked": counts.get("question_asked", 0),
        "exports": counts.get("export", 0),
        "sessions": int(sessions),
        "most_discussed": most_discussed,
        "common_filters": common_filters,
        "questions_per_day": [{"date": d, "count": c} for d, c in per_day],
    }

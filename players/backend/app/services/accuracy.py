"""Model accuracy backtest — FSM v0.2 vs v1.0 (CONTRACT.md §6 /api/accuracy, O3).

For each drafted player (classes 2022-2024) with NFL outcomes:
- actual outcome score = mean over NFL seasons of
  100 * (0.6 * pff_grade/100 + 0.4 * min(snaps / (17*65), 1))
- predicted = mean actual outcome of the top-5 comps (same position group, excluding
  self, drawn from the same backtest pool) ranked by each model's similarity.
Reported: Spearman rank correlation (numpy tie-aware rank Pearson) and MAE.
"""

from __future__ import annotations

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models import NflOutcome, Player
from backend.app.services import similarity as sim

BACKTEST_CLASSES = [2022, 2023, 2024]
SNAP_CAP = 17 * 65  # full-season snap denominator


def outcome_score(outcomes: list[NflOutcome]) -> float | None:
    if not outcomes:
        return None
    per_season = []
    for o in outcomes:
        pff_norm = max(0.0, min(1.0, (o.pff_grade or 0.0) / 100.0))
        snap_share = min(1.0, (o.snaps or 0) / SNAP_CAP)
        per_season.append(100.0 * (0.6 * pff_norm + 0.4 * snap_share))
    return float(np.mean(per_season))


def _ranks(values: np.ndarray) -> np.ndarray:
    """Average ranks with tie handling (1-based)."""
    order = np.argsort(values, kind="stable")
    ranks = np.empty(len(values), dtype=np.float64)
    i = 0
    while i < len(values):
        j = i
        while j + 1 < len(values) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def spearman(a: np.ndarray, b: np.ndarray) -> float | None:
    if len(a) < 2:
        return None
    ra, rb = _ranks(np.asarray(a, dtype=np.float64)), _ranks(np.asarray(b, dtype=np.float64))
    if np.std(ra) == 0 or np.std(rb) == 0:
        return 0.0
    return float(np.corrcoef(ra, rb)[0, 1])


async def compute_accuracy(session: AsyncSession) -> dict:
    players = (
        (
            await session.execute(
                select(Player).where(
                    Player.draft_class.in_(BACKTEST_CLASSES),
                    Player.draft_round.is_not(None),
                )
            )
        )
        .scalars()
        .all()
    )
    outcome_rows = (
        (
            await session.execute(
                select(NflOutcome).where(NflOutcome.player_id.in_([p.id for p in players]))
            )
        )
        .scalars()
        .all()
    )
    by_player: dict[int, list[NflOutcome]] = {}
    for o in outcome_rows:
        by_player.setdefault(o.player_id, []).append(o)

    pool = [p for p in players if by_player.get(p.id)]
    actual = {p.id: outcome_score(by_player[p.id]) for p in pool}

    # Precompute axis inputs once for the whole pool.
    schemes = await sim.load_final_schemes(session, pool)
    roles = await sim.load_roles(session, [p.id for p in pool])
    mentals = await sim.load_mental_vectors(session, [p.id for p in pool])
    embeddings = {
        p.id: (np.asarray(p.embedding, dtype=np.float64) if p.embedding is not None else None)
        for p in pool
    }

    def axes_for(a: Player, b: Player) -> dict[str, float | None]:
        ea, eb = embeddings[a.id], embeddings[b.id]
        scouting = None
        if ea is not None and eb is not None:
            na, nb = np.linalg.norm(ea), np.linalg.norm(eb)
            scouting = (
                float(max(0.0, min(1.0, np.dot(ea, eb) / (na * nb))))
                if na > 0 and nb > 0
                else 0.0
            )
        scheme_score, _ = sim.scheme_axis(
            schemes.get(a.id), schemes.get(b.id), roles.get(a.id, []), roles.get(b.id, [])
        )
        return {
            "scouting": scouting,
            "scheme": scheme_score,
            "mental": sim.mental_axis(mentals.get(a.id), mentals.get(b.id)),
        }

    models = [
        ("FSM v0.2", sim.V02_WEIGHTS, {"scouting": 1.0}),
        ("FSM v1.0", sim.DEFAULT_WEIGHTS, dict(sim.DEFAULT_WEIGHTS)),
    ]
    predictions: dict[str, dict[int, float]] = {name: {} for name, _, _ in models}
    for target in pool:
        candidates = [
            c for c in pool if c.id != target.id and c.position_group == target.position_group
        ]
        if not candidates:
            continue
        for name, weights, _ in models:
            scored = sorted(
                ((sim.blend(axes_for(target, c), weights), c) for c in candidates),
                key=lambda t: -t[0],
            )
            top = [c for _, c in scored[:5]]
            predictions[name][target.id] = float(np.mean([actual[c.id] for c in top]))

    def metrics(pred: dict[int, float], ids: list[int]) -> tuple[float | None, float | None, int]:
        ids = [i for i in ids if i in pred]
        if not ids:
            return None, None, 0
        y = np.array([actual[i] for i in ids])
        yhat = np.array([pred[i] for i in ids])
        return spearman(y, yhat), float(np.mean(np.abs(y - yhat))), len(ids)

    pool_ids = [p.id for p in pool]
    model_rows = []
    for name, _, reported_weights in models:
        rho, mae, n = metrics(predictions[name], pool_ids)
        model_rows.append(
            {
                "name": name,
                "weights": reported_weights,
                "spearman": round(rho, 3) if rho is not None else None,
                "mae": round(mae, 1) if mae is not None else None,
                "n": n,
            }
        )

    per_class = []
    for cls in BACKTEST_CLASSES:
        cls_ids = [p.id for p in pool if p.draft_class == cls]
        v02, _, _ = metrics(predictions["FSM v0.2"], cls_ids)
        v10, _, _ = metrics(predictions["FSM v1.0"], cls_ids)
        per_class.append(
            {
                "draft_class": cls,
                "v02_spearman": round(v02, 3) if v02 is not None else None,
                "v10_spearman": round(v10, 3) if v10 is not None else None,
            }
        )

    return {
        "classes": BACKTEST_CLASSES,
        "models": model_rows,
        "per_class": per_class,
        "method": "top-5 comp outcome prediction; outcome score = "
                  "0.6*pff_grade_norm + 0.4*snap_share",
    }

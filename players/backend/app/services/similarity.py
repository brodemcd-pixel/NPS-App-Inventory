"""Multi-axis similarity — FSM v1.0 (CONTRACT.md §5).

Axes:
- scouting: pgvector cosine similarity over report embeddings (SQL, clamped 0..1)
- scheme:   0.5*archetype + 0.2*tree + 0.3*role_jaccard
- mental:   cosine over 9-dim core-trait vectors; null when either player has no rows

Blend: weighted mean; missing (null) axes are dropped and remaining weights renormalized.
FSM v0.2 = weights {scouting: 1, scheme: 0, mental: 0}.
"""

from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.domain import side_for_position_group
from backend.app.models import MentalProfile, Player, PlayerRole, Production, Scheme

CORE_TRAIT_ORDER = [
    "football_iq", "processing_speed", "leadership", "coachability", "poise",
    "decision_making", "instincts", "anticipation", "motor",
]

DEFAULT_WEIGHTS = {"scouting": 0.50, "scheme": 0.25, "mental": 0.25}
V02_WEIGHTS = {"scouting": 1.0, "scheme": 0.0, "mental": 0.0}

SCHEME_FAMILIES: list[set[str]] = [
    {"Air Raid", "Spread/RPO"},
    {"West Coast", "Pro-Style"},
    {"Power Run", "Option/Triple"},
    {"Vertical Play-Action"},
    {"4-3 Attack Front", "4-2-5 Nickel"},
    {"3-4 Two-Gap", "3-3-5 Stack"},
    {"Press-Man Quarters"},
    {"Zone-Match"},
]


def same_family(a: str | None, b: str | None) -> bool:
    if not a or not b:
        return False
    return any(a in fam and b in fam for fam in SCHEME_FAMILIES)


def archetype_score(a: str | None, b: str | None) -> float:
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    return 0.5 if same_family(a, b) else 0.0


def role_jaccard(roles_a: Iterable[str], roles_b: Iterable[str]) -> float:
    sa, sb = set(roles_a), set(roles_b)
    if not sa and not sb:
        return 0.0
    union = sa | sb
    return len(sa & sb) / len(union) if union else 0.0


def scheme_axis(
    scheme_a: Scheme | None,
    scheme_b: Scheme | None,
    roles_a: Iterable[str],
    roles_b: Iterable[str],
) -> tuple[float, dict]:
    arch = archetype_score(
        scheme_a.scheme_archetype if scheme_a else None,
        scheme_b.scheme_archetype if scheme_b else None,
    )
    tree = (
        1.0
        if scheme_a and scheme_b and scheme_a.coaching_tree == scheme_b.coaching_tree
        else 0.0
    )
    role = role_jaccard(roles_a, roles_b)
    score = 0.5 * arch + 0.2 * tree + 0.3 * role
    return score, {"archetype": arch, "tree": tree, "role": role}


def mental_vector(rows: Sequence[tuple[str, float]]) -> np.ndarray | None:
    """9-dim core-trait vector (mean score per trait, 0 if absent); None if no rows."""
    by_trait: dict[str, list[float]] = {}
    for trait, score in rows:
        if trait in CORE_TRAIT_ORDER:
            by_trait.setdefault(trait, []).append(score)
    if not by_trait:
        return None
    return np.array(
        [np.mean(by_trait[t]) if t in by_trait else 0.0 for t in CORE_TRAIT_ORDER],
        dtype=np.float64,
    )


def mental_axis(va: np.ndarray | None, vb: np.ndarray | None) -> float | None:
    if va is None or vb is None:
        return None
    na, nb = np.linalg.norm(va), np.linalg.norm(vb)
    if na == 0 or nb == 0:
        return 0.0
    return float(max(0.0, min(1.0, np.dot(va, vb) / (na * nb))))


def blend(axes: dict[str, float | None], weights: dict[str, float]) -> float:
    """Weighted blend; null axes dropped, remaining weights renormalized."""
    usable = {k: v for k, v in axes.items() if v is not None and weights.get(k, 0.0) > 0}
    total = sum(weights[k] for k in usable)
    if total <= 0:
        return 0.0
    return sum(weights[k] * v for k, v in usable.items()) / total


def normalize_weights(weights: dict[str, float] | None) -> dict[str, float]:
    w = dict(DEFAULT_WEIGHTS)
    if weights:
        for k in w:
            if weights.get(k) is not None:
                w[k] = max(0.0, float(weights[k]))
    total = sum(w.values())
    if total <= 0:
        return dict(DEFAULT_WEIGHTS)
    return {k: v / total for k, v in w.items()}


# ---------------------------------------------------------------------------
# Batch context loaders


async def load_final_schemes(
    session: AsyncSession, players: Sequence[Player]
) -> dict[int, Scheme | None]:
    """Scheme row for each player's final college season (CONTRACT.md §2 join rule)."""
    ids = [p.id for p in players]
    if not ids:
        return {}
    rows = await session.execute(
        select(Production.player_id, func.max(Production.season))
        .where(Production.player_id.in_(ids))
        .group_by(Production.player_id)
    )
    final_season = dict(rows.all())
    schools = {p.college for p in players}
    schemes = (
        (await session.execute(select(Scheme).where(Scheme.school.in_(schools))))
        .scalars()
        .all()
    )
    by_key = {(s.school, s.year, s.side): s for s in schemes}
    out: dict[int, Scheme | None] = {}
    for p in players:
        season = final_season.get(p.id)
        side = side_for_position_group(p.position_group)
        out[p.id] = by_key.get((p.college, season, side)) if season else None
    return out


async def load_roles(session: AsyncSession, player_ids: Sequence[int]) -> dict[int, list[str]]:
    out: dict[int, list[str]] = {pid: [] for pid in player_ids}
    if not player_ids:
        return out
    rows = await session.execute(
        select(PlayerRole.player_id, PlayerRole.functional_role).where(
            PlayerRole.player_id.in_(player_ids)
        )
    )
    for pid, role in rows.all():
        out.setdefault(pid, []).append(role)
    return out


async def load_mental_vectors(
    session: AsyncSession, player_ids: Sequence[int]
) -> dict[int, np.ndarray | None]:
    out: dict[int, np.ndarray | None] = {pid: None for pid in player_ids}
    if not player_ids:
        return out
    rows = await session.execute(
        select(MentalProfile.player_id, MentalProfile.trait, MentalProfile.score).where(
            MentalProfile.player_id.in_(player_ids),
            MentalProfile.trait.in_(CORE_TRAIT_ORDER),
        )
    )
    grouped: dict[int, list[tuple[str, float]]] = {}
    for pid, trait, score in rows.all():
        grouped.setdefault(pid, []).append((trait, score))
    for pid, traits in grouped.items():
        out[pid] = mental_vector(traits)
    return out


async def scouting_similarities(
    session: AsyncSession, player: Player, candidate_ids: Sequence[int]
) -> dict[int, float | None]:
    """Cosine similarity via pgvector (1 - cosine_distance), clamped to 0..1."""
    if player.embedding is None or not candidate_ids:
        return {pid: None for pid in candidate_ids}
    rows = await session.execute(
        select(
            Player.id,
            (1 - Player.embedding.cosine_distance(player.embedding)).label("sim"),
        ).where(Player.id.in_(candidate_ids))
    )
    out: dict[int, float | None] = {pid: None for pid in candidate_ids}
    for pid, sim in rows.all():
        out[pid] = max(0.0, min(1.0, float(sim))) if sim is not None else None
    return out


# ---------------------------------------------------------------------------
# High-level operations


async def similar_players(
    session: AsyncSession,
    player: Player,
    limit: int = 10,
    weights: dict[str, float] | None = None,
    cross_position: bool = False,
) -> dict:
    w = normalize_weights(weights)
    stmt = select(Player).where(Player.id != player.id)
    if not cross_position:
        stmt = stmt.where(Player.position_group == player.position_group)
    candidates = (await session.execute(stmt)).scalars().all()
    cand_ids = [c.id for c in candidates]

    scouting = await scouting_similarities(session, player, cand_ids)
    all_players = [player] + list(candidates)
    schemes = await load_final_schemes(session, all_players)
    roles = await load_roles(session, [p.id for p in all_players])
    mentals = await load_mental_vectors(session, [p.id for p in all_players])

    scored = []
    for cand in candidates:
        sch, _ = scheme_axis(
            schemes.get(player.id), schemes.get(cand.id),
            roles.get(player.id, []), roles.get(cand.id, []),
        )
        axes = {
            "scouting": scouting.get(cand.id),
            "scheme": sch,
            "mental": mental_axis(mentals.get(player.id), mentals.get(cand.id)),
        }
        scored.append((cand, blend(axes, w), axes))
    scored.sort(key=lambda t: -t[1])
    return {"items": scored[:limit], "weights_used": w}


async def pair_similarity(
    session: AsyncSession, a: Player, b: Player, weights: dict[str, float] | None = None
) -> dict:
    w = normalize_weights(weights)
    scouting = (await scouting_similarities(session, a, [b.id])).get(b.id)
    schemes = await load_final_schemes(session, [a, b])
    roles = await load_roles(session, [a.id, b.id])
    mentals = await load_mental_vectors(session, [a.id, b.id])
    sch, components = scheme_axis(
        schemes.get(a.id), schemes.get(b.id), roles.get(a.id, []), roles.get(b.id, [])
    )
    axes = {
        "scouting": scouting,
        "scheme": sch,
        "mental": mental_axis(mentals.get(a.id), mentals.get(b.id)),
    }
    return {
        "overall": round(blend(axes, w), 4),
        "axes": {k: (round(v, 4) if v is not None else None) for k, v in axes.items()},
        "weights_used": w,
        "scheme_components": components,
    }

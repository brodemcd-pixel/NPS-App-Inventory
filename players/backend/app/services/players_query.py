"""Shared player filter/sort/pagination query builder.

Used by GET /api/players, the `filtered_list` assistant tool, and XLSX export so all
three share one implementation (CONTRACT.md §6 filters).
"""

from __future__ import annotations

from typing import Any, Sequence

from sqlalchemy import Select, case, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.domain import OFFENSE_GROUPS
from backend.app.models import MentalProfile, Player, PlayerRole, Production, Scheme
from backend.app.services import similarity as sim

SORT_COLUMNS = {
    "grade": Player.nfl_grade,
    "forty": Player.forty,
    "pick": Player.draft_pick,
    "percentile": Player.class_percentile,
    "ngs": Player.ngs_athleticism,
    "name": Player.name,
    "class": Player.draft_class,
}

SORT_OPTIONS = [
    {"key": "grade", "label": "NFL grade"},
    {"key": "forty", "label": "40-yard dash"},
    {"key": "pick", "label": "Draft pick"},
    {"key": "percentile", "label": "Class percentile"},
    {"key": "ngs", "label": "NGS athleticism"},
    {"key": "name", "label": "Name"},
    {"key": "class", "label": "Draft class"},
]

FILTER_KEYS = [
    "q", "draft_class", "round", "position", "position_group", "team", "college",
    "conference", "height_min", "height_max", "weight_min", "weight_max", "forty_max",
    "arm_min", "hand_min", "wingspan_min", "scheme", "coaching_tree", "role",
    "red_flag", "green_flag", "trait", "trait_min",
]


def _as_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def _final_season_subq():
    return (
        select(func.max(Production.season))
        .where(Production.player_id == Player.id)
        .correlate(Player)
        .scalar_subquery()
    )


def _side_expr():
    return case(
        (Player.position_group.in_(sorted(OFFENSE_GROUPS)), "offense"), else_="defense"
    )


def _scheme_exists(archetype: str | None = None, tree: str | None = None):
    conditions = [
        Scheme.school == Player.college,
        Scheme.year == _final_season_subq(),
        Scheme.side == _side_expr(),
    ]
    if archetype:
        conditions.append(Scheme.scheme_archetype == archetype)
    if tree:
        conditions.append(Scheme.coaching_tree == tree)
    return exists(select(Scheme.id).where(*conditions))


def build_player_query(params: dict[str, Any]) -> Select:
    stmt = select(Player)
    if params.get("q"):
        stmt = stmt.where(Player.name.ilike(f"%{params['q']}%"))
    if classes := _as_list(params.get("draft_class")):
        stmt = stmt.where(Player.draft_class.in_([int(c) for c in classes]))
    if rounds := _as_list(params.get("round")):
        stmt = stmt.where(Player.draft_round.in_([int(r) for r in rounds]))
    if positions := _as_list(params.get("position")):
        stmt = stmt.where(Player.position.in_(positions))
    if groups := _as_list(params.get("position_group")):
        stmt = stmt.where(Player.position_group.in_(groups))
    if params.get("team"):
        stmt = stmt.where(Player.draft_team == params["team"])
    if params.get("college"):
        stmt = stmt.where(Player.college == params["college"])
    if params.get("conference"):
        stmt = stmt.where(Player.conference == params["conference"])
    for key, col, op in [
        ("height_min", Player.height_in, ">="),
        ("height_max", Player.height_in, "<="),
        ("weight_min", Player.weight_lb, ">="),
        ("weight_max", Player.weight_lb, "<="),
        ("forty_max", Player.forty, "<="),
        ("arm_min", Player.arm_length_in, ">="),
        ("hand_min", Player.hand_size_in, ">="),
        ("wingspan_min", Player.wingspan_in, ">="),
    ]:
        if params.get(key) is not None:
            value = float(params[key])
            stmt = stmt.where(col >= value if op == ">=" else col <= value)
    if params.get("scheme"):
        stmt = stmt.where(_scheme_exists(archetype=params["scheme"]))
    if params.get("coaching_tree"):
        stmt = stmt.where(_scheme_exists(tree=params["coaching_tree"]))
    if params.get("role"):
        stmt = stmt.where(
            exists(
                select(PlayerRole.id).where(
                    PlayerRole.player_id == Player.id,
                    PlayerRole.functional_role == params["role"],
                )
            )
        )
    if params.get("red_flag") is not None:
        stmt = stmt.where(Player.red_flag.is_(bool(params["red_flag"])))
    if params.get("green_flag") is not None:
        stmt = stmt.where(Player.green_flag.is_(bool(params["green_flag"])))
    if params.get("trait"):
        trait_min = float(params.get("trait_min") or 0.6)
        stmt = stmt.where(
            exists(
                select(MentalProfile.id).where(
                    MentalProfile.player_id == Player.id,
                    MentalProfile.trait == params["trait"],
                    MentalProfile.score >= trait_min,
                )
            )
        )
    return stmt


def apply_sort(stmt: Select, sort: str | None) -> Select:
    sort = sort or "-grade"
    desc = sort.startswith("-")
    key = sort.lstrip("-")
    col = SORT_COLUMNS.get(key, Player.nfl_grade)
    order = col.desc() if desc else col.asc()
    return stmt.order_by(order.nulls_last(), Player.id.asc())


async def run_player_query(
    session: AsyncSession, params: dict[str, Any]
) -> tuple[list[Player], int]:
    """Apply filters + sort + pagination; returns (players, total)."""
    stmt = build_player_query(params)
    total = (
        await session.execute(select(func.count()).select_from(stmt.subquery()))
    ).scalar_one()
    page = max(1, int(params.get("page") or 1))
    page_size = min(200, max(1, int(params.get("page_size") or 50)))
    stmt = apply_sort(stmt, params.get("sort"))
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    players = (await session.execute(stmt)).scalars().all()
    return list(players), int(total)


async def player_summaries(
    session: AsyncSession, players: Sequence[Player]
) -> list[dict]:
    """PlayerSummary dicts (CONTRACT.md §6), batch-loading scheme context and roles."""
    schemes = await sim.load_final_schemes(session, players)
    roles = await sim.load_roles(session, [p.id for p in players])
    out = []
    for p in players:
        scheme = schemes.get(p.id)
        out.append(
            {
                "id": p.id,
                "name": p.name,
                "draft_class": p.draft_class,
                "position": p.position,
                "position_group": p.position_group,
                "college": p.college,
                "conference": p.conference,
                "height_in": p.height_in,
                "weight_lb": p.weight_lb,
                "forty": p.forty,
                "nfl_grade": p.nfl_grade,
                "ngs_athleticism": p.ngs_athleticism,
                "class_percentile": p.class_percentile,
                "draft_round": p.draft_round,
                "draft_pick": p.draft_pick,
                "draft_team": p.draft_team,
                "scheme_archetype": scheme.scheme_archetype if scheme else None,
                "coaching_tree": scheme.coaching_tree if scheme else None,
                "roles": sorted(roles.get(p.id, [])),
                "red_flag": p.red_flag,
                "green_flag": p.green_flag,
            }
        )
    return out


def active_filters(params: dict[str, Any]) -> dict[str, Any]:
    """Subset of params that are actual filters (for usage-event payloads)."""
    return {
        k: v
        for k, v in params.items()
        if k in FILTER_KEYS and v not in (None, [], "")
    }

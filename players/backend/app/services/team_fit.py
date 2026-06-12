"""Player -> NFL team scheme fit (CONTRACT.md §6 /api/players/{id}/team_fit).

fit uses the scheme-axis formula (0.5*archetype + 0.2*tree + 0.3*role) comparing the
player's final-college-season scheme/roles against each NFL team's scheme. Teams have
no functional-role rows, so the role component is the fraction of the player's roles
that are compatible with the team's scheme archetype (static affinity map below).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.domain import side_for_position_group
from backend.app.models import NflTeam, Player
from backend.app.services import similarity as sim

# Which functional roles thrive in each scheme archetype.
ROLE_SCHEME_AFFINITY: dict[str, set[str]] = {
    "Air Raid": {"pocket passer", "rhythm/timing", "slot", "deep threat", "X receiver",
                 "Z receiver", "screen-game target", "satellite back", "big slot",
                 "pass-set technician", "zone blocker"},
    "Spread/RPO": {"dual-threat", "RPO operator", "slot", "motion/jet specialist",
                   "screen-game target", "zone runner", "satellite back",
                   "move/F tight end", "big slot", "zone blocker"},
    "Pro-Style": {"pocket passer", "rhythm/timing", "X receiver", "Z receiver",
                  "three-down back", "gap runner", "inline Y", "power/gap blocker",
                  "pass-set technician"},
    "West Coast": {"rhythm/timing", "pocket passer", "Z receiver", "slot",
                   "screen-game target", "three-down back", "zone runner",
                   "move/F tight end", "zone blocker", "pass-set technician"},
    "Power Run": {"gap runner", "three-down back", "inline Y", "power/gap blocker",
                  "dual-threat", "big slot"},
    "Option/Triple": {"dual-threat", "RPO operator", "gap runner", "zone runner",
                      "motion/jet specialist", "power/gap blocker"},
    "Vertical Play-Action": {"pocket passer", "deep threat", "X receiver",
                             "three-down back", "zone runner", "inline Y",
                             "move/F tight end", "zone blocker", "pass-set technician"},
    "4-3 Attack Front": {"speed rusher", "wide-9 specialist", "three-tech penetrator",
                         "gap shooter", "run-and-chase", "blitzer", "edge setter"},
    "3-4 Two-Gap": {"power rusher", "edge setter", "two-gap nose", "blitzer",
                    "coverage backer", "box safety"},
    "4-2-5 Nickel": {"speed rusher", "gap shooter", "three-tech penetrator",
                     "nickel defender", "overhang", "coverage backer", "split-safety"},
    "3-3-5 Stack": {"blitzer", "run-and-chase", "overhang", "two-gap nose",
                    "power rusher", "single-high free", "box safety"},
    "Press-Man Quarters": {"press-man corner", "single-high free", "box safety",
                           "edge setter", "coverage backer"},
    "Zone-Match": {"off-zone corner", "nickel defender", "split-safety",
                   "coverage backer", "single-high free", "run-and-chase"},
}


def role_affinity(roles: list[str], archetype: str) -> float:
    if not roles:
        return 0.0
    compatible = ROLE_SCHEME_AFFINITY.get(archetype, set())
    return len([r for r in roles if r in compatible]) / len(roles)


async def team_fits(session: AsyncSession, player: Player, limit: int = 10) -> list[dict]:
    side = side_for_position_group(player.position_group)
    teams = (
        (await session.execute(select(NflTeam).where(NflTeam.side == side)))
        .scalars()
        .all()
    )
    scheme = (await sim.load_final_schemes(session, [player])).get(player.id)
    roles = (await sim.load_roles(session, [player.id])).get(player.id, [])

    items = []
    for team in teams:
        arch = sim.archetype_score(
            scheme.scheme_archetype if scheme else None, team.scheme_archetype
        )
        tree = (
            1.0 if scheme and scheme.coaching_tree == team.coaching_tree else 0.0
        )
        role = role_affinity(roles, team.scheme_archetype)
        fit = 0.5 * arch + 0.2 * tree + 0.3 * role
        items.append(
            {
                "team": team.team,
                "season": team.season,
                "scheme_archetype": team.scheme_archetype,
                "coordinator": team.coordinator,
                "coaching_tree": team.coaching_tree,
                "fit": round(fit, 4),
                "components": {"archetype": arch, "tree": tree, "role": round(role, 4)},
            }
        )
    items.sort(key=lambda i: -i["fit"])
    return items[:limit]

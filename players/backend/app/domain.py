"""Domain enums and vocabularies (CONTRACT.md §1)."""

from __future__ import annotations

POSITIONS = ["QB", "RB", "WR", "TE", "OT", "IOL", "EDGE", "DT", "LB", "CB", "S"]

POSITION_GROUPS = {
    "QB": "QB",
    "RB": "RB",
    "WR": "WR",
    "TE": "TE",
    "OT": "OL",
    "IOL": "OL",
    "EDGE": "DL",
    "DT": "DL",
    "LB": "LB",
    "CB": "DB",
    "S": "DB",
}

POSITION_GROUP_LIST = ["QB", "RB", "WR", "TE", "OL", "DL", "LB", "DB"]

OFFENSE_GROUPS = {"QB", "RB", "WR", "TE", "OL"}

OFFENSE_SCHEMES = [
    "Air Raid",
    "Spread/RPO",
    "Pro-Style",
    "West Coast",
    "Power Run",
    "Option/Triple",
    "Vertical Play-Action",
]

DEFENSE_SCHEMES = [
    "4-3 Attack Front",
    "3-4 Two-Gap",
    "4-2-5 Nickel",
    "3-3-5 Stack",
    "Press-Man Quarters",
    "Zone-Match",
]

COACHING_TREES = [
    "Shanahan", "McVay", "Leach", "Saban", "Belichick", "Reid", "Kelly", "Carroll", "Fangio",
]

FUNCTIONAL_ROLES = {
    "QB": ["pocket passer", "rhythm/timing", "dual-threat", "RPO operator"],
    "RB": ["three-down back", "zone runner", "gap runner", "satellite back"],
    "WR": ["X receiver", "Z receiver", "slot", "motion/jet specialist",
           "screen-game target", "deep threat"],
    "TE": ["inline Y", "move/F tight end", "big slot"],
    "OL": ["zone blocker", "power/gap blocker", "pass-set technician"],
    "EDGE": ["edge setter", "speed rusher", "power rusher", "wide-9 specialist"],
    "DT": ["two-gap nose", "three-tech penetrator", "gap shooter"],
    "LB": ["run-and-chase", "blitzer", "coverage backer", "overhang"],
    "CB": ["press-man corner", "off-zone corner", "nickel defender"],
    "S": ["single-high free", "box safety", "split-safety"],
}

ALL_ROLES = sorted({r for roles in FUNCTIONAL_ROLES.values() for r in roles})

MOCK_MILESTONES = ["post_season", "senior_bowl", "post_combine", "pre_draft"]

STAT_CATEGORIES = [
    "targets", "receptions", "rec_yards", "rec_td", "rush_att", "rush_yards", "rush_td",
    "pass_att", "pass_yards", "pass_td", "interceptions_thrown", "tackles", "tfl", "sacks",
    "pass_breakups", "interceptions", "pressures", "snaps",
]

USAGE_EVENT_TYPES = [
    "page_view", "question_asked", "filter_applied", "export", "watchlist_add",
    "player_view", "compare_view",
]


def side_for_position_group(position_group: str) -> str:
    return "offense" if position_group in OFFENSE_GROUPS else "defense"

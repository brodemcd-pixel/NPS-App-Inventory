"""Deterministic synthetic seed data generator (CONTRACT.md §8).

Produces data/seed/*.json: 100 fictional players across the 2022–2026 draft classes
with scouting reports, schemes, roles, production arcs, NFL outcomes, mock-draft
consensus, NFL team schemes and cognitive tests. Run from the players/ directory:

    python3 data/generate_seed.py

All output is reproducible (single RNG, seed 20260612). Names are fictional; the data
is for development/demo only and every loaded field is tagged SYNTHETIC_SEED provenance.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.domain import (  # noqa: E402
    DEFENSE_SCHEMES,
    FUNCTIONAL_ROLES,
    MOCK_MILESTONES,
    OFFENSE_SCHEMES,
    POSITION_GROUPS,
)
from ml.mental_traits import CORE_TRAITS, QB_TRAITS, extract_traits  # noqa: E402

rng = random.Random(20260612)
OUT = ROOT / "data" / "seed"

CLASSES = [2022, 2023, 2024, 2025, 2026]
DRAFTED_CLASSES = {2022, 2023, 2024, 2025}
OUTCOME_CLASSES = {2022, 2023, 2024}

# 20 players per class.
CLASS_POSITIONS = ["QB", "QB", "RB", "RB", "WR", "WR", "WR", "TE", "OT", "OT", "IOL",
                   "EDGE", "EDGE", "DT", "LB", "LB", "CB", "CB", "S", "S"]

FIRST_NAMES = [
    "Darius", "Malik", "Jaylen", "Cooper", "Brock", "Tyrese", "Kendall", "Amari",
    "Roman", "Dax", "Zion", "Caleb", "Marcus", "Trent", "Jalen", "Quincy", "Devon",
    "Bryce", "Kameron", "Elijah", "Tobias", "Rashad", "Colt", "Deion", "Maverick",
    "Isaiah", "Jordan", "Trey", "Cassius", "Dominic", "Xavier", "Grant", "Hollis",
    "Terrell", "Wyatt", "Donovan", "Ezekiel", "Lamar", "Pierce", "Solomon",
]
LAST_NAMES = [
    "Whitfield", "Calloway", "Renfro", "Stallworth", "Beaumont", "Okafor", "Lattimore",
    "Greenwood", "Hargrove", "Talbot", "Vandiver", "McCray", "Ellison", "Pemberton",
    "Ridgeway", "Sandoval", "Kirkland", "Abernathy", "Donahue", "Strickland",
    "Holloway", "Marsh", "Quintero", "Bellamy", "Thorne", "Eastman", "Falk",
    "Granger", "Hutto", "Iverson", "Jessup", "Kowalski", "Loveless", "Mercer",
    "Northcutt", "Overstreet", "Prather", "Quarles", "Rowell", "Satterfield",
]
COORD_FIRST = ["Bill", "Dan", "Greg", "Tom", "Rich", "Steve", "Mike", "Joe", "Pat",
               "Chip", "Lane", "Gus", "Hal", "Norv", "Wade", "Kirby", "Lincoln", "Matt"]
COORD_LAST = ["Aldrich", "Boggs", "Carver", "Drummond", "Eberle", "Fitch", "Garrison",
              "Hobbs", "Ingles", "Jarrett", "Knox", "Lubbock", "Mertz", "Nolan",
              "Osgood", "Pruitt", "Rourke", "Slocum", "Tubbs", "Veach", "Womack"]

COLLEGES = [
    ("Alabama", "SEC"), ("Georgia", "SEC"), ("LSU", "SEC"), ("Tennessee", "SEC"),
    ("Texas A&M", "SEC"), ("Florida", "SEC"),
    ("Ohio State", "Big Ten"), ("Michigan", "Big Ten"), ("Penn State", "Big Ten"),
    ("Wisconsin", "Big Ten"), ("Iowa", "Big Ten"),
    ("Texas", "Big 12"), ("Oklahoma", "Big 12"), ("Texas Tech", "Big 12"),
    ("Baylor", "Big 12"), ("TCU", "Big 12"),
    ("Clemson", "ACC"), ("Florida State", "ACC"), ("Miami", "ACC"),
    ("North Carolina", "ACC"),
    ("USC", "Pac-12"), ("Oregon", "Pac-12"), ("Washington", "Pac-12"), ("Utah", "Pac-12"),
    ("Cincinnati", "AAC"), ("Houston", "AAC"), ("UCF", "AAC"), ("Memphis", "AAC"),
    ("Boise State", "Mountain West"), ("San Diego State", "Mountain West"),
    ("Appalachian State", "Sun Belt"), ("Coastal Carolina", "Sun Belt"),
]
SOS_BY_CONF = {"SEC": 5, "Big Ten": 5, "Big 12": 4, "ACC": 4, "Pac-12": 4,
               "AAC": 3, "Mountain West": 2, "Sun Belt": 2}

NFL_TEAMS = [
    "Arizona Cardinals", "Atlanta Falcons", "Baltimore Ravens", "Buffalo Bills",
    "Carolina Panthers", "Chicago Bears", "Cincinnati Bengals", "Cleveland Browns",
    "Dallas Cowboys", "Denver Broncos", "Detroit Lions", "Green Bay Packers",
    "Houston Texans", "Indianapolis Colts", "Jacksonville Jaguars", "Kansas City Chiefs",
    "Las Vegas Raiders", "Los Angeles Chargers", "Los Angeles Rams", "Miami Dolphins",
    "Minnesota Vikings", "New England Patriots", "New Orleans Saints", "New York Giants",
    "New York Jets", "Philadelphia Eagles", "Pittsburgh Steelers", "San Francisco 49ers",
    "Seattle Seahawks", "Tampa Bay Buccaneers", "Tennessee Titans", "Washington Commanders",
]

OFF_TREES = ["Shanahan", "McVay", "Leach", "Reid", "Kelly"]
DEF_TREES = ["Saban", "Belichick", "Carroll", "Fangio"]
TREE_SCHEMES = {  # plausible archetypes per offensive tree
    "Shanahan": ["West Coast", "Pro-Style", "Vertical Play-Action"],
    "McVay": ["West Coast", "Vertical Play-Action", "Pro-Style"],
    "Leach": ["Air Raid", "Spread/RPO"],
    "Reid": ["West Coast", "Spread/RPO"],
    "Kelly": ["Spread/RPO", "Option/Triple", "Power Run"],
}

# Physical profile per position: (height μ/σ, weight μ/σ, forty μ/σ, bench μ).
PHYS = {
    "QB":   (75.0, 1.4, 218, 10, 4.80, 0.12, 0),
    "RB":   (70.5, 1.2, 212, 10, 4.50, 0.07, 19),
    "WR":   (72.5, 1.8, 198, 11, 4.45, 0.08, 14),
    "TE":   (76.5, 1.2, 250, 9,  4.70, 0.08, 19),
    "OT":   (78.0, 1.2, 315, 12, 5.15, 0.11, 25),
    "IOL":  (76.0, 1.1, 312, 11, 5.18, 0.10, 27),
    "EDGE": (75.5, 1.3, 258, 11, 4.66, 0.09, 23),
    "DT":   (75.0, 1.3, 305, 14, 5.05, 0.11, 28),
    "LB":   (73.5, 1.2, 235, 9,  4.62, 0.09, 22),
    "CB":   (71.5, 1.3, 192, 8,  4.44, 0.07, 13),
    "S":    (72.5, 1.2, 203, 8,  4.52, 0.07, 16),
}

# Position skill prose: (strengths pool, weaknesses pool). Shared vocabulary within a
# position keeps embedding similarity meaningful.
SKILLS = {
    "QB": (["Layered touch to all three levels with a quick, repeatable release.",
            "Throws with rhythm and timing from the pocket and off play-action.",
            "Arm strength to drive the deep out from the far hash."],
           ["Footwork gets noisy when forced off his spot.",
            "Ball placement drifts high when he speeds up his process."]),
    "RB": (["Runs behind his pads with excellent contact balance through the hole.",
            "One-cut burst to turn a crease into an explosive gain.",
            "Soft hands out of the backfield on swings and angle routes."],
           ["Pass protection technique is underdeveloped against pressure looks.",
            "Long speed is marginal once he reaches the second level."]),
    "WR": (["Sudden off the line with sharp, sink-and-go route breaks.",
            "Strong hands at the catch point and tracks the deep ball naturally.",
            "Creates separation late in the down and works back to the football."],
           ["Release package is limited against physical press coverage.",
            "Concentration drops show up in traffic over the middle."]),
    "TE": (["Flexes out and wins the seam against safeties with build-up speed.",
            "Frames the football well away from his body in contested spots.",
            "Functional in-line blocker who covers up defenders on the move."],
           ["Below-average play strength as a point-of-attack blocker.",
            "Stride builds slowly out of his stance into routes."]),
    "OT": (["Smooth, controlled pass sets with independent hands and a firm anchor.",
            "Climbs to the second level under control and covers up linebackers.",
            "Plays with excellent knee bend and recovers with efficient footwork."],
           ["Oversets against inside counters and lunges when beaten to the spot.",
            "Hand placement is sloppy and wide, inviting the long-arm."]),
    "IOL": (["Squares up rushers with a strong anchor and heavy, accurate hands.",
             "Moves bodies in the run game with leverage and leg drive.",
             "Processes stunts and games smoothly, passing off twists cleanly."],
            ["Limited range when asked to pull and cut off speed in space.",
             "Pad level rises late in games and he loses leverage battles."]),
    "EDGE": (["Explosive first step that consistently threatens the corner.",
              "Converts speed to power with a heavy long-arm and active hands.",
              "Bends the arc with ankle flexion to flatten at the top of the rush."],
             ["Rush plan stalls when his first move is stopped.",
              "Plays tall against the run and gets washed by down blocks."]),
    "DT": (["Wins with a quick, violent first step into the backfield.",
            "Stacks and sheds single blocks with strong, heavy hands.",
            "Holds his ground against double teams and resets the line of scrimmage."],
           ["Pad level rises as a rusher and he loses leverage inside.",
            "Limited closing burst once the pocket breaks down."]),
    "LB": (["Triggers downhill fast and arrives with thump at the contact point.",
            "Fluid hips to carry tight ends down the seam in man coverage.",
            "Scrapes over the top of blocks and finishes as a tackler."],
           ["Gets stuck on climbing blocks when he hesitates at the snap.",
            "Overruns the football and takes inconsistent angles in pursuit."]),
    "CB": (["Mirrors releases with loose hips and patient feet at the line.",
            "Drives downhill on throws in front and arrives at the catch point on time.",
            "Stays in phase vertically and finds the football at the top of the route."],
           ["Grabby at the top of routes when he loses position.",
            "Run support is reluctant and his tackling form is inconsistent."]),
    "S": (["Ranges from the deep middle with smooth transitions and closing burst.",
           "Plays the alley with urgency and strikes through the ball-carrier.",
           "Communicates rotations and aligns the back end pre-snap."],
          ["False-steps on play-action and surrenders the post.",
           "Takes aggressive angles that leak big plays over the top."]),
}

# Trait prose containing ml.mental_traits lexicon phrases (positive, negative).
TRAIT_SENTENCES = {
    "football_iq": ("A cerebral, smart player who wins with football IQ before the snap.",
                    "Football IQ is below the line for the position and shows up as busts on tape."),
    "processing_speed": ("Processes quickly and plays fast mentally, and he diagnoses run versus pass in a blink.",
                         "Slow to read pattern distribution and late to react against motion."),
    "leadership": ("Two-year captain and vocal presence who sets the tone for the room.",
                   "Quiet by nature and leadership is limited to his own preparation."),
    "coachability": ("A sponge for instruction who applies corrections within a series; staff praises his coachability.",
                     "Can be stubborn and resists coaching when asked to change his technique."),
    "poise": ("Unflappable in chaos; his composure never wavers in hostile environments.",
              "Gets rattled by interior pressure and panics when his first option is gone."),
    "decision_making": ("Outstanding decision-making; he takes care of the football in critical moments.",
                        "Forces throws into coverage and his judgment is questionable under duress."),
    "instincts": ("Natural feel for spacing with a nose for the ball; sniffs out screens early.",
                  "A robotic, mechanical mover who plays without instincts in zone."),
    "anticipation": ("Elite anticipation — beats the snap and jumps routes the moment they declare.",
                     "Waits to see it before pulling the trigger, and late ball placement follows."),
    "motor": ("Relentless motor; high effort and plays to the whistle on every snap.",
              "Takes plays off and his effort wanes when the script flips."),
}
QB_TRAIT_SENTENCES = {
    "audibles": ("Trusted to audible at the line and kills the play into favorable boxes.",
                 "Rarely checks at the line; the audible menu was kept off his plate."),
    "protection_calls": ("Sets protections himself and handles mike points like a pro.",
                         "Protection calls were managed from the sideline, a poor sign for his readiness."),
    "defense_reading": ("Advanced pre-snap read habits; identifies coverage rotation before the snap.",
                        "Coverage recognition is lacking and disguised shells fool him post-snap."),
    "safety_manipulation": ("Manipulates safeties with his eyes and looks defenders off the hash.",
                            "Never moves the safety; his eye discipline is poor and stares lead defenders to the ball."),
    "progression_discipline": ("Works through reads with discipline and takes the check-down when it is there.",
                               "Locks onto his first read and stares down receivers under pressure."),
}

SOURCES_POOL = [
    "Sources tell us the staff considered him their most reliable practice player.",
    "Sources tell us he was the first one in the building most mornings.",
    "Sources tell us position coaches trust him with the install ahead of schedule.",
    "Sources tell us scouts left campus impressed by his interview command.",
    "Sources tell us teammates voted him a captain in back-to-back seasons.",
    "Sources tell us there is some buzz he could rise on draft weekend.",
]
RED_NOTES = [
    "Missed time in college after an unresolved locker-room dispute.",
    "Two soft-tissue injuries in consecutive seasons raise durability questions.",
    "A suspension for a violation of team rules cost him two games.",
    "Teams are doing extra background work after an offseason citation.",
]
GREEN_NOTES = [
    "Universally praised character; community service award winner.",
    "Coaches describe him as the hardest worker on the roster.",
    "Graduated early with honors while starting three seasons.",
]

ROLE_KEY = {p: ("OL" if p in ("OT", "IOL") else p) for p in PHYS}


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def pick_name(used: set[str]) -> str:
    while True:
        name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
        if name not in used:
            used.add(name)
            return name


def build_school_schemes() -> list[dict]:
    """One offense + defense scheme row per school per year 2018–2025, with ~20%/yr
    coordinator turnover."""
    rows = []
    for school, _conf in COLLEGES:
        for side, trees, archetypes in (
            ("offense", OFF_TREES, OFFENSE_SCHEMES),
            ("defense", DEF_TREES, DEFENSE_SCHEMES),
        ):
            tree = rng.choice(trees)
            arch = rng.choice(TREE_SCHEMES[tree]) if side == "offense" else rng.choice(archetypes)
            coord = f"{rng.choice(COORD_FIRST)} {rng.choice(COORD_LAST)}"
            for year in range(2018, 2026):
                if year > 2018 and rng.random() < 0.20:  # coordinator change
                    tree = rng.choice(trees)
                    arch = rng.choice(TREE_SCHEMES[tree]) if side == "offense" else rng.choice(archetypes)
                    coord = f"{rng.choice(COORD_FIRST)} {rng.choice(COORD_LAST)}"
                rows.append({"school": school, "year": year, "side": side,
                             "scheme_archetype": arch, "coordinator": coord,
                             "coaching_tree": tree, "notes": None})
    return rows


def measurables(pos: str) -> dict:
    h_mu, h_sd, w_mu, w_sd, f_mu, f_sd, bench_mu = PHYS[pos]
    height = round(clamp(rng.gauss(h_mu, h_sd), h_mu - 3, h_mu + 3), 1)
    weight = int(clamp(rng.gauss(w_mu, w_sd), w_mu - 30, w_mu + 30))
    forty = round(clamp(rng.gauss(f_mu, f_sd), f_mu - 0.18, f_mu + 0.25), 2)
    speed_z = (f_mu - forty) / f_sd  # positive = faster than positional average
    m = {
        "height_in": height,
        "weight_lb": weight,
        "forty": forty if rng.random() > 0.07 else None,
        "vertical_in": round(clamp(rng.gauss(33 + 2.2 * speed_z - (weight - 230) * 0.02, 2.2), 24, 44), 1),
        "broad_in": round(clamp(rng.gauss(118 + 4 * speed_z - (weight - 230) * 0.05, 4), 95, 140), 0),
        "three_cone": round(clamp(rng.gauss(f_mu + 2.35 - 0.06 * speed_z, 0.12), 6.5, 8.4), 2),
        "shuttle": round(clamp(rng.gauss(f_mu - 0.25 - 0.04 * speed_z, 0.10), 3.9, 5.1), 2),
        "bench_reps": (int(clamp(rng.gauss(bench_mu, 3), 8, 40)) if bench_mu else None),
        "arm_length_in": round(clamp(rng.gauss(31.5 + (height - 73) * 0.45, 0.8), 28.5, 36.5), 2),
        "hand_size_in": round(clamp(rng.gauss(9.4 + (height - 73) * 0.1, 0.4), 8.0, 11.0), 2),
        "wingspan_in": round(clamp(rng.gauss(height * 1.02 + 1.5, 1.2), height, height + 8), 1),
    }
    for key in ("vertical_in", "broad_in", "three_cone", "shuttle"):
        if rng.random() < 0.10:
            m[key] = None
    return m, speed_z


def make_report(name, pos, college, scheme, roles, traits, qb_traits) -> dict:
    group = ROLE_KEY[pos]
    pros, cons = SKILLS[pos]
    role_txt = roles[0]
    overview = (
        f"{name} is a {role_txt} from {college}'s {scheme['scheme_archetype']} "
        f"{scheme['side']} under {scheme['coordinator']} ({scheme['coaching_tree']} tree). "
        + rng.choice(pros)
        + f" Projects as a scheme-versatile {group} with starter upside if the development "
          f"curve holds."
    )
    strengths = " ".join(
        rng.sample(pros, k=2)
        + [TRAIT_SENTENCES[t][0] for t, positive in traits if positive]
        + [QB_TRAIT_SENTENCES[t][0] for t, positive in qb_traits if positive]
    )
    weaknesses = " ".join(
        rng.sample(cons, k=rng.choice([1, 2]))
        + [TRAIT_SENTENCES[t][1] for t, positive in traits if not positive]
        + [QB_TRAIT_SENTENCES[t][1] for t, positive in qb_traits if not positive]
    )
    sources = " ".join(rng.sample(SOURCES_POOL, k=rng.choice([1, 2])))
    return {"overview": overview, "strengths": strengths,
            "weaknesses": weaknesses, "sources_tell_us": sources}


def production_rows(idx, pos, seasons, peak_quality, breakout_season) -> list[dict]:
    """Position-appropriate stat lines with an arc peaking near the player's quality."""
    rows = []
    n = len(seasons)
    for i, season in enumerate(seasons):
        if season < breakout_season:
            level = 0.25 + 0.15 * i / max(1, n - 1)
        else:
            level = clamp(0.55 + 0.45 * (i + 1) / n * peak_quality + rng.uniform(-0.08, 0.08), 0.2, 1.0)
        snaps = int(200 + 700 * level)
        stats: list[tuple[str, float, float | None]] = [("snaps", snaps, None)]
        if pos == "QB":
            att = int(180 + 420 * level)
            stats += [("pass_att", att, None),
                      ("pass_yards", int(att * rng.uniform(6.4, 8.8) * level + 400), None),
                      ("pass_td", int(4 + 32 * level), None),
                      ("interceptions_thrown", int(clamp(rng.gauss(11 - 6 * level, 2), 1, 16)), None),
                      ("rush_yards", int(rng.uniform(-40, 550) * level), None)]
        elif pos == "RB":
            att = int(60 + 220 * level)
            stats += [("rush_att", att, round(clamp(15 + 45 * level, 5, 70), 1)),
                      ("rush_yards", int(att * rng.uniform(4.2, 6.4)), round(clamp(14 + 40 * level, 5, 60), 1)),
                      ("rush_td", int(1 + 14 * level), None),
                      ("receptions", int(6 + 40 * level), None),
                      ("rec_yards", int(40 + 380 * level), None)]
        elif pos in ("WR", "TE"):
            tgt = int(25 + (115 if pos == "WR" else 80) * level)
            share = round(clamp(5 + 38 * level, 4, 45), 1)
            stats += [("targets", tgt, share),
                      ("receptions", int(tgt * rng.uniform(0.58, 0.72)), None),
                      ("rec_yards", int(tgt * rng.uniform(7.5, 11.5)), share),
                      ("rec_td", int(1 + 12 * level), None)]
        elif pos in ("EDGE", "DT"):
            stats += [("tackles", int(15 + 50 * level), None),
                      ("tfl", round(2 + 17 * level, 1), None),
                      ("sacks", round((1 + 12 * level) * (0.7 if pos == "DT" else 1.0), 1), None),
                      ("pressures", int(8 + 60 * level), None)]
        elif pos == "LB":
            stats += [("tackles", int(35 + 90 * level), None),
                      ("tfl", round(2 + 14 * level, 1), None),
                      ("sacks", round(0.5 + 5 * level, 1), None),
                      ("interceptions", int(rng.random() < level) + int(rng.random() < level * 0.5), None)]
        elif pos in ("CB", "S"):
            stats += [("tackles", int(20 + 55 * level), None),
                      ("pass_breakups", int(2 + 13 * level), None),
                      ("interceptions", int(rng.random() < level) + int(rng.random() < level * 0.7), None)]
        rows += [{"player_index": idx, "season": season, "stat_category": cat,
                  "value": float(val), "team_share_pct": share}
                 for cat, val, share in stats]
    return rows


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    schemes = build_school_schemes()
    scheme_by_key = {(s["school"], s["year"], s["side"]): s for s in schemes}

    players, roles_out, production_out = [], [], []
    outcomes_out, mocks_out, cognitive_out = [], [], []
    used_names: set[str] = set()

    for draft_class in CLASSES:
        class_rows = []
        for pos in CLASS_POSITIONS:
            name = pick_name(used_names)
            college, conference = rng.choice(COLLEGES)
            group = POSITION_GROUPS[pos]
            side = "offense" if group in ("QB", "RB", "WR", "TE", "OL") else "defense"
            n_seasons = rng.choice([2, 3, 3, 4])
            seasons = list(range(draft_class - n_seasons, draft_class))
            final_scheme = scheme_by_key[(college, seasons[-1], side)]

            m, speed_z = measurables(pos)
            grade = round(clamp(rng.gauss(6.25, 0.38), 5.70, 7.45), 2)
            quality = (grade - 5.7) / 1.75  # 0..1
            ngs = round(clamp(55 + 28 * speed_z * 0.5 + 35 * quality + rng.gauss(0, 6), 45, 99), 1)

            role_pool = FUNCTIONAL_ROLES[ROLE_KEY[pos]]
            roles = rng.sample(role_pool, k=rng.choice([1, 2, 2]))

            red = rng.random() < 0.08
            green = (not red) and rng.random() < 0.15
            n_traits = rng.choice([2, 3, 3, 4, 5])
            trait_names = rng.sample(list(CORE_TRAITS), k=n_traits)
            neg_bias = 0.45 if red else (0.10 if green else 0.25)
            traits = [(t, rng.random() > neg_bias) for t in trait_names]
            qb_traits = []
            if pos == "QB":
                qb_traits = [(t, rng.random() > neg_bias)
                             for t in rng.sample(list(QB_TRAITS), k=rng.choice([1, 2, 3]))]

            report = make_report(name, pos, college, final_scheme, roles, traits, qb_traits)
            breakout_season = seasons[max(0, n_seasons - 1 - int(quality * 2))]
            breakout_age = round(18.0 + (breakout_season - seasons[0]) + rng.uniform(0.4, 1.4), 1)

            player = {
                "name": name, "draft_class": draft_class, "position": pos,
                "position_group": group, "college": college, "conference": conference,
                **m,
                "nfl_grade": grade, "ngs_athleticism": ngs, "class_percentile": 0.0,
                "draft_round": None, "draft_pick": None, "draft_team": None,
                **report,
                "red_flag": red, "green_flag": green,
                "flag_notes": rng.choice(RED_NOTES) if red else (rng.choice(GREEN_NOTES) if green else None),
                "sos_tier": SOS_BY_CONF[conference],
                "breakout_age": breakout_age,
                "college_seasons": seasons,
            }
            class_rows.append((player, roles, quality, breakout_season))

        # Class percentile from grade rank within class.
        ranked = sorted(class_rows, key=lambda r: -r[0]["nfl_grade"])
        for rank, (player, *_rest) in enumerate(ranked):
            player["class_percentile"] = round(100 * (1 - rank / (len(ranked) - 1)), 1)

        # Draft outcomes: ~15% undrafted; pick order = grade + noise.
        if draft_class in DRAFTED_CLASSES:
            order = sorted(class_rows, key=lambda r: -(r[0]["nfl_grade"] + rng.gauss(0, 0.18)))
            n_drafted = len(order) - 3  # 17 of 20
            for i, (player, *_rest) in enumerate(order[:n_drafted]):
                pick = int(clamp(1 + (i / max(1, n_drafted - 1)) ** 1.25 * 250 + rng.uniform(0, 6), 1, 257))
                bounds = [(1, 32), (2, 64), (3, 100), (4, 135), (5, 170), (6, 220), (7, 257)]
                player["draft_round"] = next(r for r, hi in bounds if pick <= hi)
                player["draft_pick"] = pick
                player["draft_team"] = rng.choice(NFL_TEAMS)

        for player, roles, quality, breakout_season in class_rows:
            idx = len(players)
            players.append(player)
            for j, role in enumerate(roles):
                source = "manual" if rng.random() < 0.2 else "derived"
                roles_out.append({
                    "player_index": idx, "functional_role": role, "source": source,
                    "confidence": 1.0 if source == "manual" else round(rng.uniform(0.70, 0.95), 2),
                })
            production_out += production_rows(idx, player["position"],
                                              player["college_seasons"], quality, breakout_season)

            # Mock consensus: drift across milestones; combine standouts rise.
            base = clamp(int(1 + (1 - quality) * 230 + rng.gauss(0, 18)), 1, 250)
            rank = base
            for milestone in MOCK_MILESTONES:
                if milestone == "post_combine" and (player["ngs_athleticism"] or 0) > 85:
                    rank -= rng.randint(8, 25)
                rank = int(clamp(rank + rng.gauss(0, 10), 1, 250))
                mocks_out.append({"player_index": idx, "milestone": milestone,
                                  "consensus_rank": rank})

            # NFL outcomes for drafted 2022–2024 players, seasons through 2025.
            if player["draft_class"] in OUTCOME_CLASSES and player["draft_pick"]:
                q = clamp(0.55 * quality + 0.25 * (1 - player["draft_pick"] / 257)
                          + 0.20 * rng.random(), 0.05, 1.0)
                for k, season in enumerate(range(player["draft_class"], 2026)):
                    yr = clamp(q + 0.05 * k + rng.gauss(0, 0.08), 0.02, 1.0)
                    games = int(clamp(rng.gauss(7 + 10 * yr, 2.5), 0, 17))
                    snaps = int(clamp(rng.gauss(1050 * yr * (0.75 if k == 0 else 1.0), 90), 0, 1100))
                    stats = {"games_started": int(games * clamp(yr + rng.uniform(-0.2, 0.1), 0, 1)),
                             "snap_pct": round(100 * snaps / 1100, 1),
                             "pro_bowl": bool(yr > 0.85 and k >= 1)}
                    outcomes_out.append({
                        "player_index": idx, "season": season, "games": games,
                        "snaps": snaps,
                        "pff_grade": round(clamp(45 + 45 * yr + rng.gauss(0, 5), 40.0, 92.0), 1),
                        "stats": stats,
                    })

    # Cognitive tests for ~15 players.
    for idx in rng.sample(range(len(players)), 15):
        p = players[idx]
        cognitive_out.append({
            "player_index": idx, "provider": "S2 Cognition",
            "composite_score": round(rng.uniform(40, 99), 1),
            "percentile": round(rng.uniform(5, 99), 1),
            "taken_at": f"{p['draft_class']}-0{rng.choice([2, 3])}-{rng.randint(10, 28):02d}",
        })

    # NFL team scheme mapping, season 2025.
    nfl_teams_out = []
    for team in NFL_TEAMS:
        off_tree = rng.choice(OFF_TREES)
        nfl_teams_out.append({"team": team, "season": 2025, "side": "offense",
                              "scheme_archetype": rng.choice(TREE_SCHEMES[off_tree]),
                              "coordinator": f"{rng.choice(COORD_FIRST)} {rng.choice(COORD_LAST)}",
                              "coaching_tree": off_tree})
        nfl_teams_out.append({"team": team, "season": 2025, "side": "defense",
                              "scheme_archetype": rng.choice(DEFENSE_SCHEMES),
                              "coordinator": f"{rng.choice(COORD_FIRST)} {rng.choice(COORD_LAST)}",
                              "coaching_tree": rng.choice(DEF_TREES)})

    files = {
        "players.json": players, "schemes.json": schemes, "roles.json": roles_out,
        "production.json": production_out, "nfl_outcomes.json": outcomes_out,
        "nfl_teams.json": nfl_teams_out, "mock_consensus.json": mocks_out,
        "cognitive.json": cognitive_out,
    }
    for fname, data in files.items():
        (OUT / fname).write_text(json.dumps(data, indent=2) + "\n")

    validate(players, schemes, roles_out, production_out, outcomes_out, mocks_out, cognitive_out)
    for fname, data in files.items():
        print(f"  {fname}: {len(data)} records")


def validate(players, schemes, roles, production, outcomes, mocks, cognitive) -> None:
    scheme_keys = {(s["school"], s["year"], s["side"]) for s in schemes}
    n = len(players)
    for rows in (roles, production, outcomes, mocks, cognitive):
        assert all(0 <= r["player_index"] < n for r in rows), "bad player_index"
    for p in players:
        side = "offense" if p["position_group"] in ("QB", "RB", "WR", "TE", "OL") else "defense"
        for season in p["college_seasons"]:
            assert (p["college"], season, side) in scheme_keys, f"missing scheme {p['college']} {season}"
    assert sum(1 for p in players if p["draft_class"] == 2026 and p["draft_pick"]) == 0

    # NLP extraction sanity: reports must yield traits (QBs incl. QB sub-traits).
    extracted, qb_ok, qb_total = 0, 0, 0
    for p in players:
        traits = extract_traits({k: p[k] for k in
                                 ("overview", "strengths", "weaknesses", "sources_tell_us")},
                                p["position"])
        if len([t for t in traits if not t["qb"]]) >= 2:
            extracted += 1
        if p["position"] == "QB":
            qb_total += 1
            qb_ok += bool([t for t in traits if t["qb"]])
    print(f"validated: {n} players; >=2 core traits for {extracted}/{n}; "
          f"QB sub-traits for {qb_ok}/{qb_total} QBs")
    assert extracted >= int(0.9 * n), "trait extraction too sparse"
    assert qb_ok == qb_total, "QB sub-trait extraction failed"


if __name__ == "__main__":
    main()

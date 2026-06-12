"""Test fixtures: real Postgres (TEST_DATABASE_URL) with a compact inline dataset."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://players:players@localhost:5432/players_test"
)
os.environ["PLAYERS_DB_NULLPOOL"] = "1"  # one event loop per test (pytest-asyncio)
os.environ["PLAYERS_ENCODER"] = "lite"
os.environ["ANTHROPIC_API_KEY"] = ""  # force the offline chat engine

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from backend.app.db import Base, async_session, engine  # noqa: E402
from backend.app.models import (  # noqa: E402
    MentalProfile,
    MockConsensus,
    NflOutcome,
    NflTeam,
    Player,
    PlayerRole,
    Production,
    Scheme,
)
from backend.app.services.encoder import ReportEncoder  # noqa: E402

ENCODER = ReportEncoder(mode="lite")

# (name, class, pos, group, college, conf, height, weight, forty, grade, round, pick)
_PLAYERS = [
    ("Ace Alpha", 2024, "WR", "WR", "Texas Tech", "Big 12", 73.0, 200, 4.38, 6.8, 1, 20),
    ("Bo Bravo", 2024, "WR", "WR", "Texas Tech", "Big 12", 72.0, 195, 4.45, 6.5, 2, 40),
    ("Cy Charlie", 2023, "WR", "WR", "Alabama", "SEC", 74.0, 210, 4.52, 6.2, 3, 70),
    ("Dee Delta", 2022, "WR", "WR", "Iowa", "Big Ten", 71.0, 188, 4.60, 6.0, 5, 150),
    ("Ed Echo", 2024, "CB", "DB", "Alabama", "SEC", 72.0, 195, 4.40, 6.7, 1, 12),
    ("Fox Foxtrot", 2023, "CB", "DB", "Houston", "AAC", 71.0, 185, 4.48, 6.1, 4, 110),
    ("Gus Golf", 2022, "QB", "QB", "USC", "Pac-12", 75.0, 220, 4.75, 6.9, 1, 3),
    ("Hal Hotel", 2026, "QB", "QB", "Oregon", "Pac-12", 76.0, 225, 4.80, 6.4, None, None),
    ("Ike India", 2022, "EDGE", "DL", "Georgia", "SEC", 76.0, 255, 4.60, 7.0, 1, 5),
    ("Jay Juliett", 2023, "EDGE", "DL", "Georgia", "SEC", 75.0, 260, 4.70, 6.3, 2, 50),
]

_REPORTS = {
    "Ace Alpha": ("Sudden slot receiver who wins deep with elite anticipation.",
                  "Relentless motor; plays to the whistle. A cerebral, smart player "
                  "who wins with football IQ.", "Limited against press.", ""),
    "Bo Bravo": ("Sudden slot receiver with deep speed.",
                 "Smart player with high football IQ and strong hands.",
                 "Takes plays off and his effort wanes late.", ""),
    "Cy Charlie": ("Big-bodied X receiver, contested catch winner.",
                   "Team captain and vocal presence who sets the tone.",
                   "Slow to read coverage rotations.", ""),
    "Dee Delta": ("Possession receiver from a pro-style attack.",
                  "Coachable; a sponge for instruction.", "Marginal long speed.", ""),
    "Ed Echo": ("Press-man corner with loose hips.",
                "Elite anticipation — jumps routes the moment they declare.",
                "Grabby at the top of routes.", ""),
    "Fox Foxtrot": ("Zone corner with good instincts and a nose for the ball.",
                    "Natural feel for spacing.", "Gets rattled by tempo.", ""),
    "Gus Golf": ("Pocket passer with rhythm and timing.",
                 "Sets protections himself and handles mike points like a pro. "
                 "Manipulates safeties with his eyes.",
                 "Forces throws into coverage under duress.", ""),
    "Hal Hotel": ("Dual-threat quarterback in a spread attack.",
                  "Works through reads with discipline and takes the check-down.",
                  "Locks onto his first read under pressure.", ""),
    "Ike India": ("Explosive speed rusher who bends the arc.",
                  "Relentless motor; nonstop effort on every snap.",
                  "Plays tall against the run.", ""),
    "Jay Juliett": ("Power rusher who converts speed to power.",
                    "High effort with a relentless motor.",
                    "Rush plan stalls when stopped.", ""),
}

_SCHEMES = [
    ("Texas Tech", 2023, "offense", "Air Raid", "OC One", "Leach"),
    ("Alabama", 2022, "offense", "Pro-Style", "OC Two", "Saban"),
    ("Alabama", 2023, "defense", "Press-Man Quarters", "DC Three", "Saban"),
    ("Iowa", 2021, "offense", "Pro-Style", "OC Four", "Shanahan"),
    ("Houston", 2022, "defense", "Zone-Match", "DC Five", "Carroll"),
    ("USC", 2021, "offense", "West Coast", "OC Six", "Reid"),
    ("Oregon", 2025, "offense", "Spread/RPO", "OC Seven", "Kelly"),
    ("Georgia", 2021, "defense", "3-4 Two-Gap", "DC Eight", "Saban"),
    ("Georgia", 2022, "defense", "3-4 Two-Gap", "DC Eight", "Saban"),
]

_ROLES = {
    "Ace Alpha": ["slot", "deep threat"], "Bo Bravo": ["slot"],
    "Cy Charlie": ["X receiver"], "Dee Delta": ["Z receiver"],
    "Ed Echo": ["press-man corner"], "Fox Foxtrot": ["off-zone corner"],
    "Gus Golf": ["pocket passer"], "Hal Hotel": ["dual-threat"],
    "Ike India": ["speed rusher"], "Jay Juliett": ["power rusher"],
}

# Final college season per player (drives the scheme join).
_FINAL_SEASON = {
    "Ace Alpha": 2023, "Bo Bravo": 2023, "Cy Charlie": 2022, "Dee Delta": 2021,
    "Ed Echo": 2023, "Fox Foxtrot": 2022, "Gus Golf": 2021, "Hal Hotel": 2025,
    "Ike India": 2021, "Jay Juliett": 2022,
}

_MENTAL = {  # subset; Hal Hotel deliberately has NO mental rows (axis dropout test)
    "Ace Alpha": [("anticipation", 0.8), ("motor", 0.85), ("football_iq", 0.8)],
    "Bo Bravo": [("football_iq", 0.75), ("motor", 0.2)],
    "Cy Charlie": [("leadership", 0.8), ("processing_speed", 0.3)],
    "Dee Delta": [("coachability", 0.75)],
    "Ed Echo": [("anticipation", 0.85)],
    "Fox Foxtrot": [("instincts", 0.7), ("poise", 0.25)],
    "Gus Golf": [("decision_making", 0.3), ("leadership", 0.7)],
    "Ike India": [("motor", 0.9)],
    "Jay Juliett": [("motor", 0.8)],
}

_NFL = {  # (season, games, snaps, pff)
    "Gus Golf": [(2022, 17, 1050, 82.0), (2023, 16, 1000, 85.0)],
    "Ike India": [(2022, 15, 800, 78.0), (2023, 17, 900, 80.0)],
    "Dee Delta": [(2022, 8, 200, 55.0)],
    "Cy Charlie": [(2023, 12, 600, 68.0)],
    "Ace Alpha": [(2024, 14, 700, 72.0)],
    "Ed Echo": [(2024, 16, 950, 76.0)],
    "Fox Foxtrot": [(2023, 10, 400, 60.0)],
    "Jay Juliett": [(2023, 13, 500, 62.0)],
}


async def _insert_fixture() -> None:
    async with async_session() as session:
        for i, (name, cls, pos, group, college, conf, h, w, forty, grade, rnd, pick) in enumerate(
            _PLAYERS, start=1
        ):
            ov, st, wk, src = _REPORTS[name]
            p = Player(
                id=i, name=name, draft_class=cls, position=pos, position_group=group,
                college=college, conference=conf, height_in=h, weight_lb=w, forty=forty,
                arm_length_in=32.0, hand_size_in=9.5, wingspan_in=h + 4,
                nfl_grade=grade, ngs_athleticism=80.0, class_percentile=50.0,
                draft_round=rnd, draft_pick=pick,
                draft_team="Dallas Cowboys" if pick else None,
                overview=ov, strengths=st, weaknesses=wk, sources_tell_us=src,
                red_flag=(name == "Bo Bravo"), green_flag=(name == "Ace Alpha"),
                sos_tier=4, breakout_age=19.5,
                embedding=ENCODER.encode_player(ov, st, wk, src).tolist(),
                umap_x=float(i), umap_y=float(-i),
            )
            session.add(p)
        await session.flush()

        for row in _SCHEMES:
            session.add(Scheme(school=row[0], year=row[1], side=row[2],
                               scheme_archetype=row[3], coordinator=row[4],
                               coaching_tree=row[5]))
        for i, (name, *_rest) in enumerate(_PLAYERS, start=1):
            for role in _ROLES[name]:
                session.add(PlayerRole(player_id=i, functional_role=role,
                                       source="derived", confidence=0.9))
            for trait, score in _MENTAL.get(name, []):
                session.add(MentalProfile(player_id=i, trait=trait, score=score,
                                          evidence="fixture", source="nlp"))
            final = _FINAL_SEASON[name]
            for season in (final - 1, final):
                session.add(Production(player_id=i, season=season,
                                       stat_category="snaps",
                                       value=600 + 100 * (season == final),
                                       team_share_pct=None))
                session.add(Production(player_id=i, season=season,
                                       stat_category="rec_yards" if _PLAYERS[i-1][3] == "WR" else "tackles",
                                       value=700 + 200 * (season == final),
                                       team_share_pct=25.0))
            for season, games, snaps, pff in _NFL.get(name, []):
                session.add(NflOutcome(player_id=i, season=season, games=games,
                                       snaps=snaps, pff_grade=pff, stats={}))
            for j, milestone in enumerate(
                ["post_season", "senior_bowl", "post_combine", "pre_draft"]
            ):
                session.add(MockConsensus(player_id=i, milestone=milestone,
                                          consensus_rank=10 * i + j))
        session.add(NflTeam(team="Las Vegas Raiders", season=2025, side="offense",
                            scheme_archetype="Air Raid", coordinator="NFL OC",
                            coaching_tree="Leach"))
        session.add(NflTeam(team="San Francisco 49ers", season=2025, side="offense",
                            scheme_archetype="West Coast", coordinator="NFL OC2",
                            coaching_tree="Shanahan"))
        await session.commit()
        await session.execute(
            text("SELECT setval(pg_get_serial_sequence('players','id'), "
                 "(SELECT max(id) FROM players))")
        )
        await session.commit()


@pytest_asyncio.fixture()
async def db():
    """Fresh schema + fixture data per test (NullPool keeps loops isolated)."""
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await _insert_fixture()
    yield
    await engine.dispose()


@pytest_asyncio.fixture()
async def client(db):
    from backend.app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture()
def anyio_backend():
    return "asyncio"

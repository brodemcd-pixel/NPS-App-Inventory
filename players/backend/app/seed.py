"""Seed loader: data/seed/*.json -> database (CONTRACT.md §8).

    python -m backend.app.seed --reset      # drop/recreate tables, then load
    python -m backend.app.seed --if-empty   # load only when players table is empty

Computes report embeddings (ReportEncoder), NLP mental profiles
(ml.mental_traits.extract_traits), 2-D map coordinates (umap-learn if installed,
PCA fallback otherwise) and SYNTHETIC_SEED provenance rows.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
from sqlalchemy import func, select, text  # noqa: E402

from backend.app.db import Base, async_session, engine  # noqa: E402
from backend.app.models import (  # noqa: E402
    CognitiveTest,
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
from backend.app.services.provenance import seed_provenance_rows  # noqa: E402
from ml.mental_traits import extract_traits  # noqa: E402

SEED_DIR = ROOT / "data" / "seed"


def _load(name: str) -> list[dict]:
    path = SEED_DIR / name
    if not path.exists():
        raise SystemExit(f"seed file missing: {path} — run `python3 data/generate_seed.py` first")
    return json.loads(path.read_text())


def project_2d(embeddings: np.ndarray) -> np.ndarray:
    """UMAP if available, else PCA via SVD (top 2 components)."""
    try:  # pragma: no cover - depends on optional install
        import umap

        return umap.UMAP(
            n_neighbors=15, min_dist=0.1, n_components=2, random_state=42
        ).fit_transform(embeddings)
    except ImportError:
        centered = embeddings - embeddings.mean(axis=0)
        _, _, vt = np.linalg.svd(centered, full_matrices=False)
        coords = centered @ vt[:2].T
        # Scale to a UMAP-like range for consistent frontend rendering.
        span = np.abs(coords).max() or 1.0
        return coords / span * 10.0


async def seed(reset: bool, if_empty: bool) -> None:
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        if reset:
            await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        if if_empty:
            count = (await session.execute(select(func.count(Player.id)))).scalar_one()
            if count:
                print(f"database already seeded ({count} players); skipping")
                return

        encoder = ReportEncoder()
        players_raw = _load("players.json")

        players: list[Player] = []
        embeddings = np.zeros((len(players_raw), 384), dtype=np.float32)
        for i, raw in enumerate(players_raw):
            raw = dict(raw)
            raw.pop("college_seasons")
            player = Player(id=i + 1, **raw)
            embeddings[i] = encoder.encode_player(
                player.overview, player.strengths, player.weaknesses, player.sources_tell_us
            )
            player.embedding = embeddings[i].tolist()
            players.append(player)

        coords = project_2d(embeddings)
        for player, (x, y) in zip(players, coords):
            player.umap_x, player.umap_y = round(float(x), 4), round(float(y), 4)

        session.add_all(players)
        # Flush so FK targets exist before dependent rows (no ORM relationships are
        # defined, so the unit of work cannot infer insert ordering on its own).
        await session.flush()

        for player in players:
            session.add_all(seed_provenance_rows(player))
            sections = {
                "overview": player.overview,
                "strengths": player.strengths,
                "weaknesses": player.weaknesses,
                "sources_tell_us": player.sources_tell_us,
            }
            for hit in extract_traits(sections, player.position):
                session.add(
                    MentalProfile(
                        player_id=player.id,
                        trait=hit["trait"],
                        score=hit["score"],
                        evidence=hit["evidence"],
                        source="nlp",
                    )
                )

        session.add_all(
            Scheme(**row) for row in _load("schemes.json")
        )
        session.add_all(
            PlayerRole(
                player_id=r["player_index"] + 1,
                functional_role=r["functional_role"],
                source=r["source"],
                confidence=r["confidence"],
            )
            for r in _load("roles.json")
        )
        session.add_all(
            Production(
                player_id=r["player_index"] + 1,
                season=r["season"],
                stat_category=r["stat_category"],
                value=r["value"],
                team_share_pct=r["team_share_pct"],
            )
            for r in _load("production.json")
        )
        session.add_all(
            NflOutcome(
                player_id=r["player_index"] + 1,
                season=r["season"],
                games=r["games"],
                snaps=r["snaps"],
                pff_grade=r["pff_grade"],
                stats=r["stats"],
            )
            for r in _load("nfl_outcomes.json")
        )
        session.add_all(NflTeam(**row) for row in _load("nfl_teams.json"))
        session.add_all(
            MockConsensus(
                player_id=r["player_index"] + 1,
                milestone=r["milestone"],
                consensus_rank=r["consensus_rank"],
            )
            for r in _load("mock_consensus.json")
        )
        session.add_all(
            CognitiveTest(
                player_id=r["player_index"] + 1,
                provider=r["provider"],
                composite_score=r["composite_score"],
                percentile=r["percentile"],
                taken_at=date.fromisoformat(r["taken_at"]),
            )
            for r in _load("cognitive.json")
        )

        await session.commit()

        # Postgres: keep the id sequence ahead of the explicit ids we inserted.
        await session.execute(
            text("SELECT setval(pg_get_serial_sequence('players','id'), "
                 "(SELECT max(id) FROM players))")
        )
        await session.commit()
        n_mental = (await session.execute(select(func.count(MentalProfile.id)))).scalar_one()
        print(f"seeded {len(players)} players, {n_mental} mental-profile rows")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reset", action="store_true", help="drop and recreate all tables")
    parser.add_argument("--if-empty", action="store_true", help="no-op when already seeded")
    args = parser.parse_args()
    asyncio.run(seed(reset=args.reset, if_empty=args.if_empty))


if __name__ == "__main__":
    main()

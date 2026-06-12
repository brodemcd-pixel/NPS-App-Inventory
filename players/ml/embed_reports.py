"""Recompute report embeddings for all players (FSM scouting axis).

    PYTHONPATH=. python ml/embed_reports.py [--encoder lite|e5]

Run after report text changes or when switching encoder modes; stored embeddings are
only comparable within one mode.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from backend.app.db import async_session  # noqa: E402
from backend.app.models import Player  # noqa: E402
from backend.app.services.encoder import ReportEncoder  # noqa: E402


async def main(encoder_mode: str | None) -> None:
    encoder = ReportEncoder(mode=encoder_mode)
    async with async_session() as session:
        players = (await session.execute(select(Player))).scalars().all()
        for player in players:
            player.embedding = encoder.encode_player(
                player.overview, player.strengths, player.weaknesses,
                player.sources_tell_us,
            ).tolist()
        await session.commit()
    print(f"re-embedded {len(players)} players (mode={encoder.mode})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--encoder", choices=["lite", "e5"], default=None,
                        help="override PLAYERS_ENCODER")
    args = parser.parse_args()
    asyncio.run(main(args.encoder))

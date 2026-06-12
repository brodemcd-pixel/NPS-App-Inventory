"""Re-run NLP mental-trait extraction over all scouting reports (PDR M1/M3).

    PYTHONPATH=. python ml/extract_mental_traits.py

Replaces mental_profiles rows with source='nlp'; scout tags and cognitive-test rows
are preserved. Run after report text or lexicon changes.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import delete, select  # noqa: E402

from backend.app.db import async_session  # noqa: E402
from backend.app.models import MentalProfile, Player  # noqa: E402
from ml.mental_traits import extract_traits  # noqa: E402


async def main() -> None:
    async with async_session() as session:
        await session.execute(delete(MentalProfile).where(MentalProfile.source == "nlp"))
        players = (await session.execute(select(Player))).scalars().all()
        rows = 0
        for player in players:
            sections = {
                "overview": player.overview,
                "strengths": player.strengths,
                "weaknesses": player.weaknesses,
                "sources_tell_us": player.sources_tell_us,
            }
            for hit in extract_traits(sections, player.position):
                session.add(MentalProfile(
                    player_id=player.id, trait=hit["trait"], score=hit["score"],
                    evidence=hit["evidence"], source="nlp",
                ))
                rows += 1
        await session.commit()
    print(f"extracted {rows} nlp trait rows across {len(players)} players")


if __name__ == "__main__":
    asyncio.run(main())

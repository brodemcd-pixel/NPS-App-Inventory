"""Recompute the 2-D cluster-map projection from stored embeddings.

    PYTHONPATH=. python ml/umap_project.py

Uses umap-learn (n_neighbors=15, min_dist=0.1, random_state=42) when installed;
otherwise falls back to PCA (top-2 SVD components) so the map always renders.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402
from sqlalchemy import select  # noqa: E402

from backend.app.db import async_session  # noqa: E402
from backend.app.models import Player  # noqa: E402
from backend.app.seed import project_2d  # noqa: E402


async def main() -> None:
    async with async_session() as session:
        players = (
            (await session.execute(select(Player).where(Player.embedding.is_not(None))))
            .scalars()
            .all()
        )
        if not players:
            print("no embedded players; run ml/embed_reports.py first")
            return
        matrix = np.array([p.embedding for p in players], dtype=np.float32)
        coords = project_2d(matrix)
        for player, (x, y) in zip(players, coords):
            player.umap_x, player.umap_y = round(float(x), 4), round(float(y), 4)
        await session.commit()
    print(f"projected {len(players)} players to 2-D")


if __name__ == "__main__":
    asyncio.run(main())

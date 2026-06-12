"""FSM back-test: comp-based outcome prediction vs actual NFL outcomes (PDR O3).

    PYTHONPATH=. python ml/evaluate_fsm.py

Prints the same comparison the /api/accuracy dashboard serves: FSM v0.2
(scouting-only) vs FSM v1.0 (multi-axis) on the 2022–2024 classes.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.db import async_session  # noqa: E402
from backend.app.services.accuracy import compute_accuracy  # noqa: E402


async def main() -> None:
    async with async_session() as session:
        result = await compute_accuracy(session)

    print(f"Back-test classes: {result['classes']}  |  method: {result['method']}\n")
    print(f"{'model':<10} {'weights (sct/sch/men)':<24} {'spearman':>9} {'mae':>7} {'n':>5}")
    for m in result["models"]:
        w = m["weights"]
        weights = f"{w.get('scouting', 0):.2f}/{w.get('scheme', 0):.2f}/{w.get('mental', 0):.2f}"
        spearman = "—" if m["spearman"] is None else f"{m['spearman']:+.3f}"
        mae = "—" if m["mae"] is None else f"{m['mae']:.1f}"
        print(f"{m['name']:<10} {weights:<24} {spearman:>9} {mae:>7} {m['n']:>5}")

    print("\nper-class spearman (v0.2 -> v1.0):")
    for row in result["per_class"]:
        v02 = "—" if row["v02_spearman"] is None else f"{row['v02_spearman']:+.3f}"
        v10 = "—" if row["v10_spearman"] is None else f"{row['v10_spearman']:+.3f}"
        print(f"  {row['draft_class']}: {v02} -> {v10}")


if __name__ == "__main__":
    asyncio.run(main())

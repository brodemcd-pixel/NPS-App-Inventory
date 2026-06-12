# ML pipeline

Run everything from the `players/` directory with `PYTHONPATH=.`.

Pipeline order (after `data/generate_seed.py` + `python -m backend.app.seed --reset`,
which already performs steps 1–3 inline):

1. `python ml/embed_reports.py` — report embeddings (e5-small via `--encoder e5`, or the
   deterministic lite hasher). Stored in `players.embedding` (pgvector, 384-dim).
2. `python ml/umap_project.py` — 2-D cluster map coordinates (UMAP, PCA fallback).
3. `python ml/extract_mental_traits.py` — lexicon + sentiment extraction of mental
   traits from report text into `mental_profiles` (source `nlp`); QB pre-snap
   sub-traits included. Scout tags / cognitive rows are never touched.
4. `python ml/evaluate_fsm.py` — back-test FSM v0.2 vs v1.0 comp accuracy against
   actual NFL outcomes (same computation as the `/accuracy` dashboard).

`ml/mental_traits.py` holds the trait lexicon and extraction logic; the encoder lives in
`backend/app/services/encoder.py` and is shared by the seeder, the API and these scripts.

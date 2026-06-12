# Players — NFL Draft Prospect Intelligence Platform

Players combines structured prospect data, an AI assistant with a fixed, auditable
operation set, and a multi-axis similarity model (FSM v1.0) into a single research
interface for evaluating NFL draft prospects across the 2022–2026 classes.

This repository implements the full MVP end-state defined in
*Players — PDR MVP v1.1* (May 2026): the production baseline (player database,
assistant, similarity model, web app, Slack bot) plus all planned enhancements —
scheme intelligence, mental & intangibles profiling, production analytics, outcome
tracking, and workflow features.

> **Data note:** this build ships with a deterministic **synthetic** dataset
> (100 fictional players, fabricated scouting reports, fabricated coordinators) so the
> entire system runs end-to-end with zero licensed data. The schema, seed pipeline, and
> per-field provenance are designed for the real NFL.com / PFF / Sports Reference feeds
> described in PDR §6 — drop conforming JSON into `data/seed/` and re-run the seeder.

## Architecture

```
frontend/   Next.js 14 + React 18 + Tailwind 3 — table, profile, compare, watchlists,
            UMAP map, usage & model-accuracy dashboards, streaming chat panel
backend/    FastAPI (Python 3.11, SQLAlchemy 2.0 async, asyncpg) — REST API, SSE chat,
            assistant tool registry (12 operations), similarity engine, exports,
            Slack bot (Bolt); schema created from SQLAlchemy models by the seeder
            (models are Alembic-ready once a migration baseline is wanted)
ml/         Embedding pipeline (e5-small or deterministic lite encoder), UMAP/PCA
            projection, mental-trait NLP extraction, FSM back-test evaluation
data/       Synthetic seed generator + generated seed JSON
PostgreSQL 16 + pgvector — relational data + 384-dim report embeddings in one store
```

See `CONTRACT.md` for the full internal spec (schema, API shapes, similarity math,
tool definitions) that all components are built against.

### FSM v1.0 — multi-axis similarity

| Axis | Source | Default weight |
|---|---|---|
| Scouting report | 384-dim embeddings, cosine via pgvector (section-weighted: overview 0.50, strengths 0.25, weaknesses 0.25) | 0.50 |
| Scheme | archetype family match + coaching-tree match + functional-role Jaccard | 0.25 |
| Mental | cosine over 9 core trait scores (NLP extraction + scout tags) | 0.25 |

Weights are user-adjustable per query (UI sliders and assistant arguments); missing axes
are dropped and weights renormalized. "FSM v0.2" (scouting-only) is kept as the baseline
in the model-accuracy dashboard (`/accuracy`), which back-tests comp-based outcome
prediction against actual 2022–2024 NFL outcomes.

### Assistant (12 operations)

`filtered_list`, `player_profile`, `report_search`, `similarity_comparison`,
`scout_comment`, `scheme_fit`, `role_search`, `mental_profile_query`,
`production_lookup`, `nfl_outcome_lookup`, `team_fit`, `player_compare`.

Rulebook: the assistant only answers via tools; every response carries a **Sources**
block assembled from the actual lookups performed; similarity scores appear only when
produced by the FSM; opinion (scouting language) is labeled separately from measurement.
With no `ANTHROPIC_API_KEY` set, an offline rule-based router executes the same tools and
emits the same response/SSE format, so the product is fully demoable without a key.

## Quickstart

### Docker (recommended)

```bash
cp .env.example .env        # edit as needed; works as-is for local demo
docker compose up --build
# web: http://localhost:3000   api: http://localhost:8000/docs
```

The backend container seeds the database on first start (`--if-empty`).

### Manual

```bash
# 1. Postgres 16 with pgvector, databases 'players' (and 'players_test' for pytest)
# 2. Backend (from this directory)
pip install -r requirements.txt          # + requirements-optional.txt for e5/UMAP/spaCy/PDF
cp .env.example .env
PYTHONPATH=. python -m backend.app.seed --reset
PYTHONPATH=. uvicorn backend.app.main:app --reload --port 8000

# 3. Frontend
cd frontend && npm install && npm run dev   # http://localhost:3000
```

### ML pipeline (rerun after data changes)

```bash
PYTHONPATH=. python ml/embed_reports.py          # recompute report embeddings
PYTHONPATH=. python ml/umap_project.py           # recompute 2-D map coords
PYTHONPATH=. python ml/extract_mental_traits.py  # re-extract NLP mental profiles
PYTHONPATH=. python ml/evaluate_fsm.py           # FSM v0.2 vs v1.0 back-test table
```

### Tests

```bash
PYTHONPATH=. python -m pytest backend/tests -q   # uses TEST_DATABASE_URL
cd frontend && npm run build                     # type-checks the frontend
```

## Configuration

All knobs are environment variables — see `.env.example`. Highlights:

| Variable | Effect |
|---|---|
| `ANTHROPIC_API_KEY` | empty → offline rule-based assistant; set → Claude with streaming tool use |
| `PLAYERS_ENCODER` | `lite` (default, deterministic, no downloads) or `e5` (e5-small, requires optional deps; re-seed after switching) |
| `SLACK_BOT_TOKEN` / `SLACK_SIGNING_SECRET` | unset → Slack bot disabled; set → Bolt app mounted at `/slack/events` |
| `SECRET_KEY` | signs Slack→web identity-passthrough tokens |

## PDR feature coverage

All 23 PDR features are implemented: S1–S5 (scheme tables, coaching trees, role tags,
scheme axis, NFL team mapping), M1–M6 (NLP trait extraction, red/green flags, QB
pre-snap sub-profile, S2 Cognition slot, scout tagging, mental axis), P1–P3 (production,
SOS tier, trajectory), O1–O3 (NFL outcomes, mock-draft consensus, accuracy dashboard),
U1–U6 (watchlists, compare view, XLSX/PDF export, position-specific filters, scheme-fit
assistant ops, consolidated profile).

### Deliberate MVP simplifications (vs. PDR letter)

- **Auth**: demo identity via `X-User-Id` header + signed Slack passthrough tokens.
  NextAuth.js + Slack OAuth is the documented production path, not yet wired.
- **Encoder default** is the deterministic `lite` hasher so dev/test environments need no
  model downloads; `PLAYERS_ENCODER=e5` enables the PDR's e5-small.
- **PDF export** requires WeasyPrint (optional install); the endpoint returns 501 with a
  clear message otherwise. XLSX export always works.
- **Deployment**: Dockerfiles + compose are provided; Railway/Fly.io config is left to
  the deployment step.

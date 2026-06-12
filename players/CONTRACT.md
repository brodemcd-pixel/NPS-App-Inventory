# Players — Internal Build Contract

This file is the single source of truth that `backend/`, `frontend/`, `ml/`, and `data/`
are built against. If something here conflicts with intuition, this file wins.
It implements the PDR "Players — NFL Draft Prospect Intelligence Platform, MVP v1.1".

## 0. Monorepo layout

```
players/
  backend/            FastAPI app (Python 3.11, SQLAlchemy 2.0 async, asyncpg, pgvector)
    app/
      main.py         FastAPI factory, router mounting, CORS, usage-event middleware
      config.py       pydantic-settings Settings (env-driven)
      db.py           async engine/session, Base
      seed.py         seed loader: reads ../data/seed/*.json -> DB (python -m app.seed)
      models/         SQLAlchemy models (one file per domain)
      routers/        chat, players, similar, compare, export, watchlists, teams,
                      analytics, accuracy, umap, comments, auth, meta
      services/       encoder.py, similarity.py, assistant.py, exporting.py,
                      analytics.py, accuracy.py, provenance.py, slack_link.py
      tools/          Claude tool definitions; registry.py + one module per operation
    tests/            pytest; integration tests use the real Postgres (TEST_DATABASE_URL)
  frontend/           Next.js 14 (App Router, TypeScript, Tailwind 3)
  ml/                 mental_traits.py (lexicon+extraction), embed_reports.py,
                      umap_project.py, extract_mental_traits.py, evaluate_fsm.py
  data/
    generate_seed.py  deterministic synthetic data generator (seeded RNG)
    seed/*.json       generated seed files (committed)
  docker-compose.yml  postgres+pgvector, backend, frontend
  requirements.txt    Python deps for backend+ml (core)
  requirements-optional.txt  heavy/optional: sentence-transformers, umap-learn, spacy, weasyprint
  .env.example
```

Python imports: backend and ml share one Python environment. Backend modules may import
`ml.*` and ml scripts may import `backend.app.*`. Both resolve because all entry points
add the `players/` repo root to `sys.path` (each entry script does
`sys.path.insert(0, <players root>)` when run directly) and uvicorn is launched from
`players/` with `PYTHONPATH=.` as `uvicorn backend.app.main:app`.
Therefore **the import name of the backend package is `backend.app`, not `app`.**

## 1. Domain enums and vocabularies

### Positions
`position`: QB, RB, WR, TE, OT, IOL, EDGE, DT, LB, CB, S
`position_group` mapping: QB→QB, RB→RB, WR→WR, TE→TE, OT/IOL→OL, EDGE/DT→DL, LB→LB, CB/S→DB

### Offensive scheme archetypes (7)
`Air Raid`, `Spread/RPO`, `Pro-Style`, `West Coast`, `Power Run`, `Option/Triple`, `Vertical Play-Action`

### Defensive scheme archetypes (6)
`4-3 Attack Front`, `3-4 Two-Gap`, `4-2-5 Nickel`, `3-3-5 Stack`, `Press-Man Quarters`, `Zone-Match`

### Coaching trees
`Shanahan`, `McVay`, `Leach`, `Saban`, `Belichick`, `Reid`, `Kelly`, `Carroll`, `Fangio`

### Functional roles (by position)
- QB: `pocket passer`, `rhythm/timing`, `dual-threat`, `RPO operator`
- RB: `three-down back`, `zone runner`, `gap runner`, `satellite back`
- WR: `X receiver`, `Z receiver`, `slot`, `motion/jet specialist`, `screen-game target`, `deep threat`
- TE: `inline Y`, `move/F tight end`, `big slot`
- OT/IOL: `zone blocker`, `power/gap blocker`, `pass-set technician`
- EDGE: `edge setter`, `speed rusher`, `power rusher`, `wide-9 specialist`
- DT: `two-gap nose`, `three-tech penetrator`, `gap shooter`
- LB: `run-and-chase`, `blitzer`, `coverage backer`, `overhang`
- CB: `press-man corner`, `off-zone corner`, `nickel defender`
- S: `single-high free`, `box safety`, `split-safety`

### Mental traits — core 9 (apply to all positions)
`football_iq`, `processing_speed`, `leadership`, `coachability`, `poise`,
`decision_making`, `instincts`, `anticipation`, `motor`

### QB pre-snap sub-traits (5)
`audibles`, `protection_calls`, `defense_reading`, `safety_manipulation`, `progression_discipline`

### Mock draft milestones (ordered)
`post_season`, `senior_bowl`, `post_combine`, `pre_draft`

### Provenance sources used in seed
All synthetic rows carry provenance source `"SYNTHETIC_SEED"`. Field provenance rows are
written for measurables + grades + reports per player.

## 2. Database schema (PostgreSQL 16 + pgvector)

All tables created by SQLAlchemy models; Alembic holds a single baseline migration.
`embedding` columns use `pgvector` `Vector(384)`.

```
players(id PK, name, draft_class int, position, position_group, college, conference,
        height_in float, weight_lb int, forty float?, vertical_in float?, broad_in float?,
        three_cone float?, shuttle float?, bench_reps int?,
        arm_length_in float?, hand_size_in float?, wingspan_in float?,
        nfl_grade float, ngs_athleticism float?, class_percentile float,
        draft_round int?, draft_pick int?, draft_team str?,
        overview text, strengths text, weaknesses text, sources_tell_us text,
        red_flag bool default false, green_flag bool default false, flag_notes text?,
        sos_tier int (1=weakest..5=strongest), breakout_age float?,
        embedding vector(384)?, umap_x float?, umap_y float?)

field_provenance(id PK, player_id FK, field_name, source, source_url?, retrieved_at timestamptz)

schemes(id PK, school, year int, side enum('offense','defense'), scheme_archetype,
        coordinator, coaching_tree, notes?)        -- school-year lookup table (S1, S2)

player_roles(id PK, player_id FK, functional_role, source enum('pff','manual','derived'),
             confidence float 0..1)                -- (S3)

mental_profiles(id PK, player_id FK, trait, score float 0..1, evidence text?,
                source enum('nlp','scout_tag','cognitive_test'), created_at)  -- (M1,M3,M5)

cognitive_tests(id PK, player_id FK, provider, composite_score float, percentile float,
                taken_at date)                     -- (M4)

production(id PK, player_id FK, season int, stat_category, value float,
           team_share_pct float?)                  -- (P1)
  stat_category vocab: targets, receptions, rec_yards, rec_td, rush_att, rush_yards,
  rush_td, pass_att, pass_yards, pass_td, interceptions_thrown, tackles, tfl, sacks,
  pass_breakups, interceptions, pressures, snaps

nfl_outcomes(id PK, player_id FK, season int, games int, snaps int,
             pff_grade float?, stats jsonb)        -- (O1)

nfl_teams(id PK, team, season int, side enum('offense','defense'),
          scheme_archetype, coordinator, coaching_tree)   -- (S5)

mock_consensus(id PK, player_id FK, milestone enum(see §1), consensus_rank int)  -- (O2)

watchlists(id PK, owner_id str, name, created_at)
watchlist_players(watchlist_id FK, player_id FK, added_at, note?, PK(watchlist_id,player_id))

scout_comments(id PK, player_id FK, author_id, author_name, body text,
               traits jsonb (list[{trait,score}]), created_at)

usage_events(id PK, event_type, payload jsonb, user_id?, created_at)
  event_type vocab: page_view, question_asked, filter_applied, export, watchlist_add,
  player_view, compare_view
```

SQLAlchemy model class names (importable from `backend.app.models`): `Player`,
`FieldProvenance`, `Scheme`, `PlayerRole`, `MentalProfile`, `CognitiveTest`, `Production`,
`NflOutcome`, `NflTeam`, `MockConsensus`, `Watchlist`, `WatchlistPlayer`, `ScoutComment`,
`UsageEvent`. Async session factory: `backend.app.db.async_session` (callable context
manager), `backend.app.db.Base`, engine from `DATABASE_URL`.

Player ↔ scheme join: `schemes.school == players.college AND schemes.year == production.season`
(player's college seasons come from `production`). "Current scheme context" for a player =
scheme row for his **final** college season. Side = offense for QB/RB/WR/TE/OT/IOL,
defense for EDGE/DT/LB/CB/S.

## 3. Embedding encoder (shared, deterministic)

`backend/app/services/encoder.py` — already written; do not rewrite. Interface:

```python
encoder = ReportEncoder()           # mode from env PLAYERS_ENCODER: "lite" (default) | "e5"
encoder.encode_passage(text) -> np.ndarray(float32, 384, L2-normalized; zeros if blank)
encoder.encode_query(text)   -> same
encoder.encode_player(overview, strengths, weaknesses, sources_tell_us) -> 384-dim
    # section weights 0.50/0.25/0.25/0.00, then L2 normalize
```

"e5" mode uses sentence-transformers `intfloat/e5-small` with `passage: `/`query: ` prefixes.
"lite" mode is a deterministic hashing encoder (blake2b unigrams+bigrams) — used in dev/tests.

## 4. Mental trait extraction (shared)

`ml/mental_traits.py` — already written; do not rewrite. Interface:

```python
from ml.mental_traits import extract_traits, CORE_TRAITS, QB_TRAITS
extract_traits(sections: dict[str, str], position: str) -> list[dict]
# sections keys: overview, strengths, weaknesses, sources_tell_us
# returns [{"trait": str, "score": float 0..1, "evidence": str, "qb": bool}]
```

Scores: keyword hits scored by sentiment of surrounding window; strengths section biases
positive, weaknesses negative. spaCy used if importable, regex fallback otherwise.

## 5. Multi-axis similarity (FSM v1.0)

`backend/app/services/similarity.py`:

- **Scouting axis**: cosine similarity via pgvector (`1 - (embedding <=> :q)`), 0..1 clamp.
- **Scheme axis**: `0.5 * archetype + 0.2 * tree + 0.3 * role_jaccard` where
  archetype = 1.0 same archetype else 0.5 if same family else 0.0
  (families: {Air Raid, Spread/RPO} | {West Coast, Pro-Style} | {Power Run, Option/Triple}
  | {Vertical Play-Action} ; defense: {4-3 Attack Front, 4-2-5 Nickel} |
  {3-4 Two-Gap, 3-3-5 Stack} | {Press-Man Quarters} | {Zone-Match});
  tree = 1.0 if same coaching tree else 0.0;
  role_jaccard = Jaccard over functional role sets.
- **Mental axis**: cosine over 9-dim core-trait vectors (mean score per trait, 0 if absent).
  If either player has no mental rows, axis is `null`.
- **Blend**: weights default `{scouting: 0.50, scheme: 0.25, mental: 0.25}`, user-overridable
  per query. Missing axes are dropped and remaining weights renormalized.
- v0.2 ("scouting-only") = blend with weights {1,0,0} — used by the accuracy dashboard.

Similarity candidates restricted to same `position_group` by default;
`cross_position=true` disables that.

## 6. REST API (FastAPI, prefix `/api`)

Conventions: JSON; errors `{"detail": str}`; user identity from `X-User-Id` header
(default `"demo-user"` when absent — demo auth, see §9). Pagination
`{"items": [...], "total": int, "page": int, "page_size": int}`.

### Meta
- `GET /api/health` → `{"status":"ok","players":int}`
- `GET /api/meta/filters` → distinct values:
  `{classes:[int], positions:[], position_groups:[], teams:[], colleges:[], conferences:[],
    offense_schemes:[], defense_schemes:[], coaching_trees:[], roles:[], traits:[],
    sort_options:[{key,label}]}`

### Players
- `GET /api/players` — filters (all optional, repeatable where noted):
  `q` (name ILIKE), `draft_class` (multi), `round` (multi), `position` (multi),
  `position_group` (multi), `team`, `college`, `conference`,
  `height_min,height_max,weight_min,weight_max,forty_max,arm_min,hand_min,wingspan_min`,
  `scheme`, `coaching_tree`, `role`, `red_flag` (bool), `green_flag` (bool),
  `trait` + `trait_min` (float, default 0.6),
  `sort` ∈ `grade|forty|pick|percentile|ngs|name|class` with optional `-` prefix for desc
  (default `-grade`), `page` (1-based, default 1), `page_size` (default 50, max 200).
  Items are **PlayerSummary**:
  ```json
  {"id":1,"name":"...","draft_class":2024,"position":"WR","position_group":"WR",
   "college":"...","conference":"...","height_in":73.5,"weight_lb":205,"forty":4.45,
   "nfl_grade":6.30,"ngs_athleticism":87.0,"class_percentile":91.2,
   "draft_round":2,"draft_pick":41,"draft_team":"...","scheme_archetype":"Spread/RPO",
   "coaching_tree":"Leach","roles":["slot","deep threat"],"red_flag":false,
   "green_flag":true}
  ```
- `GET /api/players/{id}` — **PlayerDetail**: PlayerSummary fields plus
  ```json
  {"measurables":{"height_in":...,"weight_lb":...,"forty":...,"vertical_in":...,
     "broad_in":...,"three_cone":...,"shuttle":...,"bench_reps":...,
     "arm_length_in":...,"hand_size_in":...,"wingspan_in":...},
   "report":{"overview":"...","strengths":"...","weaknesses":"...","sources_tell_us":"..."},
   "flags":{"red_flag":false,"green_flag":true,"notes":null},
   "scheme_context":[{"season":2023,"scheme_archetype":"...","coordinator":"...",
                      "coaching_tree":"...","side":"offense"}],
   "roles":[{"functional_role":"slot","source":"derived","confidence":0.85}],
   "mental_profile":{"core":[{"trait":"football_iq","score":0.78,"sources":["nlp","scout_tag"],
                              "evidence":["..."]}],
                     "qb":[{"trait":"audibles","score":0.7,"sources":["nlp"],"evidence":["..."]}],
                     "cognitive":{"provider":"S2 Cognition","composite_score":78.0,
                                  "percentile":88.0,"taken_at":"2024-02-15"} | null},
   "production":[{"season":2023,"stat_category":"rec_yards","value":1180,"team_share_pct":31.2}],
   "trajectory":{"breakout_age":19.8,"seasons":[{"season":2022,"score":41.0},...],
                 "trend":"ascending|flat|declining","consistency":0.82},
   "nfl_outcomes":[{"season":2024,"games":16,"snaps":890,"pff_grade":74.1,"stats":{...}}],
   "mock_consensus":[{"milestone":"post_season","consensus_rank":38},...],
   "sos_tier":4,"comments":[{"id":1,"author_name":"...","body":"...","traits":[...],
                             "created_at":"..."}],
   "provenance":[{"field_name":"forty","source":"SYNTHETIC_SEED","retrieved_at":"..."}],
   "umap":{"x":1.2,"y":-3.4}}
  ```
  `trajectory.seasons[].score` = season production score 0..100 (see analytics service);
  computed, not stored.
- `GET /api/players/{id}/similar?limit=10&w_scouting=0.5&w_scheme=0.25&w_mental=0.25&cross_position=false`
  → `{"items":[{"player":PlayerSummary,"overall":0.83,
                "axes":{"scouting":0.86,"scheme":0.9,"mental":0.65|null}}],
      "weights_used":{"scouting":0.5,"scheme":0.25,"mental":0.25}}`
- `GET /api/players/{id}/team_fit?limit=10` → ranked NFL teams:
  `{"items":[{"team":"...","season":2025,"scheme_archetype":"...","coordinator":"...",
              "coaching_tree":"...","fit":0.82,
              "components":{"archetype":1.0,"tree":1.0,"role":0.6}}]}`
  fit = same formula as scheme axis, player scheme/roles vs team scheme.
- `GET /api/compare?a={id}&b={id}` →
  `{"a":PlayerDetail,"b":PlayerDetail,
    "similarity":{"overall":0.74,"axes":{...},"weights_used":{...}}}`
- `GET /api/umap` → `{"items":[{"player_id":1,"name":"...","position":"WR",
    "position_group":"WR","draft_class":2024,"x":1.2,"y":3.4}]}`

### Chat (SSE)
- `POST /api/chat` body:
  `{"message": str, "history": [{"role":"user"|"assistant","content":str}] (optional),
    "weights": {"scouting":..,"scheme":..,"mental":..} (optional)}`
  Response `text/event-stream`, events in order:
  ```
  event: tool   data: {"name":"filtered_list","input":{...}}        (0..n, as they run)
  event: text   data: {"delta":"..."}                               (0..n)
  event: sources data: {"sources":[{"operation":"filtered_list","detail":"players where ...","count":5}]}
  event: done   data: {}
  event: error  data: {"detail":"..."}                              (on failure)
  ```
  If `ANTHROPIC_API_KEY` unset, an **offline router** answers: regex/keyword intent matching
  over the 12 operations, executes the matched tool directly, formats a plain-text answer,
  and still emits the same event sequence (so the UI works without a key).

### Watchlists (U1)
- `GET /api/watchlists` → `{"items":[{"id":1,"name":"...","created_at":"...",
    "players":[PlayerSummary+{"note":str?,"added_at":"..."}]}]}`
- `POST /api/watchlists` `{"name":str}` → watchlist
- `DELETE /api/watchlists/{id}` → 204
- `POST /api/watchlists/{id}/players` `{"player_id":int,"note":str?}` → 201
- `DELETE /api/watchlists/{id}/players/{player_id}` → 204

### Comments / scout tags (M5)
- `POST /api/comments` `{"player_id":int,"body":str,"traits":[{"trait":str,"score":float}]?}`
  → comment; also inserts `mental_profiles` rows with source `scout_tag` for each tag.

### Export (U3)
- `GET /api/export/players.xlsx?{same filters as GET /api/players}` → XLSX download
- `GET /api/export/players/{id}.pdf` → PDF profile (WeasyPrint; `501` + detail if not installed)
- `GET /api/export/compare.pdf?a=&b=` → PDF compare (same 501 rule)

### Dashboards
- `GET /api/analytics/summary?days=30` →
  `{"page_views":int,"questions_asked":int,"exports":int,"sessions":int,
    "most_discussed":[{"player_id":int,"name":"...","count":int}],
    "common_filters":[{"filter":"position_group=WR","count":int}],
    "questions_per_day":[{"date":"2026-06-01","count":int}]}`
- `GET /api/accuracy` (O3) →
  `{"classes":[2022,2023,2024],
    "models":[{"name":"FSM v0.2","weights":{"scouting":1.0},
               "spearman":0.41,"mae":11.2,"n":58},
              {"name":"FSM v1.0","weights":{"scouting":0.5,"scheme":0.25,"mental":0.25},
               "spearman":0.52,"mae":9.8,"n":58}],
    "per_class":[{"draft_class":2022,"v02_spearman":...,"v10_spearman":...}],
    "method":"top-5 comp outcome prediction; outcome score = 0.6*pff_grade_norm + 0.4*snap_share"}`
  Backtest: for each drafted player (classes 2022–2024) with NFL outcomes, predict outcome
  score from mean outcome of top-5 comps (excluding self) under each model; report Spearman
  rank correlation and MAE vs actual.

### Auth (Slack→web passthrough, §9)
- `POST /api/auth/slack/exchange` `{"token":str}` → `{"user_id":"U123","name":str?}` or 401.
  Token = `itsdangerous.URLSafeTimedSerializer(SECRET_KEY, salt="slack-link")` of
  `{"user_id":...,"name":...}`, max_age 600s.

### Usage logging
Backend middleware/handlers insert `usage_events` rows: `question_asked` on /api/chat,
`export` on /api/export/*, `player_view` on GET /api/players/{id}, `compare_view`,
`filter_applied` on /api/players when filters present (payload = filter dict),
`watchlist_add`. Frontend may also `POST /api/events` `{"event_type":"page_view","payload":{}}`.

## 7. Assistant (12 operations)

`backend/app/tools/` — one module per tool, each exporting
`TOOL = {"name", "description", "input_schema"}` and `async def run(session, args) -> dict`.
`registry.py` collects all. Tool names:

1. `filtered_list` — args mirror GET /api/players filters; returns rows + count
2. `player_profile` — `{name_or_id}` fuzzy name match
3. `report_search` — `{query, limit}` ILIKE/keyword search over report sections
4. `similarity_comparison` — `{name_or_id, limit, weights?}` multi-axis FSM
5. `scout_comment` — `{name_or_id, body, traits?}` writes comment (+ scout tags)
6. `scheme_fit` — `{scheme_archetype, position?, limit}` players from that scheme family
7. `role_search` — `{functional_role, limit}`
8. `mental_profile_query` — `{trait, min_score?, position?, limit}` or `{name_or_id}` for one player
9. `production_lookup` — `{name_or_id, season?}`
10. `nfl_outcome_lookup` — `{name_or_id}`
11. `team_fit` — `{name_or_id, limit}` ranked NFL team fits
12. `player_compare` — `{a_name_or_id, b_name_or_id}`

System prompt rulebook (must be embedded): answer only via tools; every response ends with
a Sources block (the backend assembles it from actual tool calls — the model is told sources
are appended automatically); similarity scores only when produced by the FSM tools; label
opinion (scouting language) separately from measurement (combine/production data).
Model: env `ANTHROPIC_MODEL`, default `claude-sonnet-4-6`. Streaming via SDK
`client.messages.stream`; agentic loop while `stop_reason == "tool_use"`.

## 8. Seed data files (`data/seed/`)

Deterministic output of `data/generate_seed.py` (RNG seed 20260612). All names fictional.
~100 players: 20 per class, classes 2022–2026, positions spread across all 11.

- `players.json`: list of player dicts — all `players` columns except id/embedding/umap
  (loader assigns ids in list order starting at 1), plus `"college_seasons":[int]`.
- `schemes.json`: school-year-side scheme rows covering every (college, season) that appears.
- `roles.json`: `{"player_index": int (0-based into players.json), "functional_role", "source", "confidence"}`
- `production.json`: `{"player_index", "season", "stat_category", "value", "team_share_pct"}`
- `nfl_outcomes.json`: `{"player_index", "season", "games", "snaps", "pff_grade", "stats"}`
  (only drafted players, classes 2022–2024; seasons class_year..2025)
- `nfl_teams.json`: 32 teams × season 2025 × offense+defense rows.
- `mock_consensus.json`: `{"player_index", "milestone", "consensus_rank"}` all 4 milestones.
- `cognitive.json`: `{"player_index", "provider":"S2 Cognition", "composite_score",
  "percentile", "taken_at"}` (~15% of players).

Draft outcomes: classes 2022–2025 have round/pick/team; 2026 undrafted (nulls).
Reports: templated position+scheme-aware scouting prose seeded with mental-trait keywords
so NLP extraction produces a meaningful `mental_profiles` table.

`backend/app/seed.py` loads these, computes embeddings (encoder), runs
`ml.mental_traits.extract_traits` per player (source `nlp`), computes UMAP/PCA 2-D coords
(umap-learn if importable, else PCA via numpy SVD), writes provenance rows.
Idempotent: `python -m backend.app.seed --reset` drops/recreates tables first.

## 9. Auth model (MVP demo)

Web: demo identity — frontend keeps `user_id` in localStorage (default `demo-user`),
sends as `X-User-Id`. Slack→web passthrough: bot links to
`{WEB_BASE_URL}/auth/slack?token=<signed>`; that page calls `/api/auth/slack/exchange`
and stores the returned user_id. NextAuth.js is the documented production path, not wired.

## 10. Slack bot

`backend/app/slack_app.py` (Bolt for Python, optional): mounted at `/slack/events` only when
`SLACK_BOT_TOKEN` + `SLACK_SIGNING_SECRET` set. App-mention + DM → same assistant service
(non-streaming; final text). Player names in responses hyperlinked to web profile with
signed token.

## 11. Environment variables (see .env.example)

```
DATABASE_URL=postgresql+asyncpg://players:players@localhost:5432/players
TEST_DATABASE_URL=postgresql+asyncpg://players:players@localhost:5432/players_test
SECRET_KEY=change-me
ANTHROPIC_API_KEY=            # optional; offline router used when empty
ANTHROPIC_MODEL=claude-sonnet-4-6
PLAYERS_ENCODER=lite          # lite | e5
WEB_BASE_URL=http://localhost:3000
BACKEND_CORS_ORIGINS=http://localhost:3000
SLACK_BOT_TOKEN=              # optional
SLACK_SIGNING_SECRET=         # optional
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 12. Frontend routes & components (Next.js 14 App Router, TS, Tailwind)

- `/` — ProspectTable: filter sidebar (incl. position-specific measurable filters U4 that
  appear when a position group is selected: OL→arm_min, QB→hand_min, DB→wingspan_min),
  sortable columns, pagination, row → profile; ChatPanel as right-side drawer (persistent
  across pages via layout), watchlist add buttons, "Export XLSX" honoring current filters.
- `/players/[id]` — PlayerProfile (U6): header (name/pos/class/college/grade/draft),
  measurables grid w/ provenance tooltips, report sections, scheme context card,
  roles chips, mental profile bars (core + QB sub-profile + cognitive),
  red/green flag banner, production table + trajectory sparkline (inline SVG),
  mock consensus mini-timeline, NFL outcomes table, similar players card with
  weight sliders (scouting/scheme/mental), team-fit card, comments + tag form,
  "Export PDF" button.
- `/compare` — CompareView (U2): two player search pickers (`?a=&b=` URL state),
  parallel columns of all dimensions + similarity breakdown header, export PDF.
- `/watchlists` — WatchlistManager (U1).
- `/map` — UMAP scatter (SVG, color by position_group, hover tooltip, click → profile).
- `/dashboard` — usage analytics (cards + bar/line charts, plain SVG).
- `/accuracy` — model accuracy dashboard (O3): v0.2 vs v1.0 table + per-class bars.
- `/auth/slack` — token exchange page.
- Charts: hand-rolled SVG components (no chart lib). API client in `lib/api.ts` using
  `NEXT_PUBLIC_API_URL`. Chat consumes SSE via `fetch` + ReadableStream parser in
  `lib/sse.ts`.

## 13. Testing expectations

- Unit (no DB): encoder determinism/normalization/section weights; mental extraction on
  crafted text (positive vs negative context); similarity blend math incl. axis dropout +
  renormalization; scheme-axis component math; offline chat router intent matching.
- Integration (real Postgres at TEST_DATABASE_URL): seed a small fixture subset, exercise
  /api/players filters+sort, /players/{id}, /similar, /compare, /watchlists CRUD,
  /export/players.xlsx, /api/chat offline-mode SSE, /api/accuracy.
- Frontend: `npm run build` must pass (type-checks). No e2e harness required.

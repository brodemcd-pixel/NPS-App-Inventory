// Typed API client for the Players backend (CONTRACT.md §6).
// All requests carry X-User-Id from localStorage 'players_user_id' (default 'demo-user').

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ---------------------------------------------------------------------------
// Shared shapes (§6)
// ---------------------------------------------------------------------------

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface PlayerSummary {
  id: number;
  name: string;
  draft_class: number;
  position: string;
  position_group: string;
  college: string;
  conference: string;
  height_in: number | null;
  weight_lb: number | null;
  forty: number | null;
  nfl_grade: number;
  ngs_athleticism: number | null;
  class_percentile: number;
  draft_round: number | null;
  draft_pick: number | null;
  draft_team: string | null;
  scheme_archetype: string | null;
  coaching_tree: string | null;
  roles: string[];
  red_flag: boolean;
  green_flag: boolean;
}

export interface WatchlistPlayerSummary extends PlayerSummary {
  note: string | null;
  added_at: string;
}

export interface Measurables {
  height_in: number | null;
  weight_lb: number | null;
  forty: number | null;
  vertical_in: number | null;
  broad_in: number | null;
  three_cone: number | null;
  shuttle: number | null;
  bench_reps: number | null;
  arm_length_in: number | null;
  hand_size_in: number | null;
  wingspan_in: number | null;
}

export interface Report {
  overview: string;
  strengths: string;
  weaknesses: string;
  sources_tell_us: string;
}

export interface Flags {
  red_flag: boolean;
  green_flag: boolean;
  notes: string | null;
}

export interface SchemeContextRow {
  season: number;
  scheme_archetype: string;
  coordinator: string;
  coaching_tree: string;
  side: "offense" | "defense";
}

export interface RoleDetail {
  functional_role: string;
  source: "pff" | "manual" | "derived";
  confidence: number;
}

export interface MentalTraitEntry {
  trait: string;
  score: number;
  sources: string[];
  evidence: string[];
}

export interface CognitiveTest {
  provider: string;
  composite_score: number;
  percentile: number;
  taken_at: string;
}

export interface MentalProfile {
  core: MentalTraitEntry[];
  qb: MentalTraitEntry[];
  cognitive: CognitiveTest | null;
}

export interface ProductionRow {
  season: number;
  stat_category: string;
  value: number;
  team_share_pct: number | null;
}

export interface TrajectorySeason {
  season: number;
  score: number;
}

export interface Trajectory {
  breakout_age: number | null;
  seasons: TrajectorySeason[];
  trend: "ascending" | "flat" | "declining";
  consistency: number;
}

export interface NflOutcome {
  season: number;
  games: number;
  snaps: number;
  pff_grade: number | null;
  stats: Record<string, number>;
}

export interface MockConsensusPoint {
  milestone: "post_season" | "senior_bowl" | "post_combine" | "pre_draft";
  consensus_rank: number;
}

export interface ScoutComment {
  id: number;
  author_name: string;
  body: string;
  traits: { trait: string; score: number }[];
  created_at: string;
}

export interface ProvenanceRow {
  field_name: string;
  source: string;
  retrieved_at: string;
}

export interface PlayerDetail extends Omit<PlayerSummary, "roles"> {
  measurables: Measurables;
  report: Report;
  flags: Flags;
  scheme_context: SchemeContextRow[];
  roles: RoleDetail[];
  mental_profile: MentalProfile;
  production: ProductionRow[];
  trajectory: Trajectory;
  nfl_outcomes: NflOutcome[];
  mock_consensus: MockConsensusPoint[];
  sos_tier: number;
  comments: ScoutComment[];
  provenance: ProvenanceRow[];
  umap: { x: number; y: number } | null;
}

export interface SimilarityAxes {
  scouting: number | null;
  scheme: number | null;
  mental: number | null;
}

export interface SimilarityWeights {
  scouting: number;
  scheme: number;
  mental: number;
}

export interface SimilarItem {
  player: PlayerSummary;
  overall: number;
  axes: SimilarityAxes;
}

export interface SimilarResponse {
  items: SimilarItem[];
  weights_used: SimilarityWeights;
}

export interface TeamFitItem {
  team: string;
  season: number;
  scheme_archetype: string;
  coordinator: string;
  coaching_tree: string;
  fit: number;
  components: { archetype: number; tree: number; role: number };
}

export interface CompareResponse {
  a: PlayerDetail;
  b: PlayerDetail;
  similarity: {
    overall: number;
    axes: SimilarityAxes;
    weights_used: SimilarityWeights;
  };
}

export interface UmapPoint {
  player_id: number;
  name: string;
  position: string;
  position_group: string;
  draft_class: number;
  x: number;
  y: number;
}

export interface MetaFilters {
  classes: number[];
  positions: string[];
  position_groups: string[];
  teams: string[];
  colleges: string[];
  conferences: string[];
  offense_schemes: string[];
  defense_schemes: string[];
  coaching_trees: string[];
  roles: string[];
  traits: string[];
  sort_options: { key: string; label: string }[];
}

export interface Watchlist {
  id: number;
  name: string;
  created_at: string;
  players: WatchlistPlayerSummary[];
}

export interface AnalyticsSummary {
  page_views: number;
  questions_asked: number;
  exports: number;
  sessions: number;
  most_discussed: { player_id: number; name: string; count: number }[];
  common_filters: { filter: string; count: number }[];
  questions_per_day: { date: string; count: number }[];
}

export interface AccuracyModel {
  name: string;
  weights: Partial<SimilarityWeights>;
  spearman: number;
  mae: number;
  n: number;
}

export interface AccuracyResponse {
  classes: number[];
  models: AccuracyModel[];
  per_class: {
    draft_class: number;
    v02_spearman: number;
    v10_spearman: number;
  }[];
  method: string;
}

export interface ChatTurn {
  role: "user" | "assistant";
  content: string;
}

export interface ChatSource {
  operation: string;
  detail: string;
  count: number;
}

// ---------------------------------------------------------------------------
// Player list query params
// ---------------------------------------------------------------------------

export interface PlayerQuery {
  q?: string;
  draft_class?: number[];
  round?: number[];
  position?: string[];
  position_group?: string[];
  team?: string;
  college?: string;
  conference?: string;
  height_min?: number;
  height_max?: number;
  weight_min?: number;
  weight_max?: number;
  forty_max?: number;
  arm_min?: number;
  hand_min?: number;
  wingspan_min?: number;
  scheme?: string;
  coaching_tree?: string;
  role?: string;
  red_flag?: boolean;
  green_flag?: boolean;
  trait?: string;
  trait_min?: number;
  sort?: string;
  page?: number;
  page_size?: number;
}

export function buildQuery(
  params: Record<string, unknown> | undefined
): string {
  if (!params) return "";
  const sp = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") continue;
    if (Array.isArray(value)) {
      for (const v of value) {
        if (v !== undefined && v !== null && v !== "") sp.append(key, String(v));
      }
    } else {
      sp.append(key, String(value));
    }
  }
  const qs = sp.toString();
  return qs ? `?${qs}` : "";
}

// ---------------------------------------------------------------------------
// Core fetch
// ---------------------------------------------------------------------------

export function getUserId(): string {
  if (typeof window === "undefined") return "demo-user";
  try {
    return window.localStorage.getItem("players_user_id") || "demo-user";
  } catch {
    return "demo-user";
  }
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "X-User-Id": getUserId(),
      ...(init?.headers || {}),
    },
  });
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (body && typeof body.detail === "string") detail = body.detail;
    } catch {
      // keep default detail
    }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

// ---------------------------------------------------------------------------
// Endpoints
// ---------------------------------------------------------------------------

export const api = {
  health: () => request<{ status: string; players: number }>("/api/health"),

  metaFilters: () => request<MetaFilters>("/api/meta/filters"),

  players: (query: PlayerQuery = {}) =>
    request<Paginated<PlayerSummary>>(
      `/api/players${buildQuery(query as Record<string, unknown>)}`
    ),

  player: (id: number | string) => request<PlayerDetail>(`/api/players/${id}`),

  similar: (
    id: number | string,
    opts: {
      limit?: number;
      w_scouting?: number;
      w_scheme?: number;
      w_mental?: number;
      cross_position?: boolean;
    } = {}
  ) =>
    request<SimilarResponse>(
      `/api/players/${id}/similar${buildQuery(opts as Record<string, unknown>)}`
    ),

  teamFit: (id: number | string, limit = 8) =>
    request<{ items: TeamFitItem[] }>(
      `/api/players/${id}/team_fit?limit=${limit}`
    ),

  compare: (a: number | string, b: number | string) =>
    request<CompareResponse>(`/api/compare?a=${a}&b=${b}`),

  umap: () => request<{ items: UmapPoint[] }>("/api/umap"),

  watchlists: () => request<{ items: Watchlist[] }>("/api/watchlists"),

  createWatchlist: (name: string) =>
    request<Watchlist>("/api/watchlists", {
      method: "POST",
      body: JSON.stringify({ name }),
    }),

  deleteWatchlist: (id: number) =>
    request<void>(`/api/watchlists/${id}`, { method: "DELETE" }),

  addWatchlistPlayer: (watchlistId: number, playerId: number, note?: string) =>
    request<unknown>(`/api/watchlists/${watchlistId}/players`, {
      method: "POST",
      body: JSON.stringify({ player_id: playerId, note: note || undefined }),
    }),

  removeWatchlistPlayer: (watchlistId: number, playerId: number) =>
    request<void>(`/api/watchlists/${watchlistId}/players/${playerId}`, {
      method: "DELETE",
    }),

  postComment: (
    playerId: number,
    body: string,
    traits?: { trait: string; score: number }[]
  ) =>
    request<ScoutComment>("/api/comments", {
      method: "POST",
      body: JSON.stringify({
        player_id: playerId,
        body,
        traits: traits && traits.length ? traits : undefined,
      }),
    }),

  analyticsSummary: (days = 30) =>
    request<AnalyticsSummary>(`/api/analytics/summary?days=${days}`),

  accuracy: () => request<AccuracyResponse>("/api/accuracy"),

  slackExchange: (token: string) =>
    request<{ user_id: string; name?: string }>("/api/auth/slack/exchange", {
      method: "POST",
      body: JSON.stringify({ token }),
    }),
};

// ---------------------------------------------------------------------------
// Export download URLs (browser navigation — triggers file download)
// ---------------------------------------------------------------------------

export function exportPlayersXlsxUrl(query: PlayerQuery): string {
  return `${API_BASE}/api/export/players.xlsx${buildQuery(
    query as Record<string, unknown>
  )}`;
}

export function exportPlayerPdfUrl(id: number | string): string {
  return `${API_BASE}/api/export/players/${id}.pdf`;
}

export function exportComparePdfUrl(
  a: number | string,
  b: number | string
): string {
  return `${API_BASE}/api/export/compare.pdf?a=${a}&b=${b}`;
}

// ---------------------------------------------------------------------------
// Usage events (fire-and-forget)
// ---------------------------------------------------------------------------

export function postEvent(
  eventType: string,
  payload: Record<string, unknown> = {}
): void {
  try {
    fetch(`${API_BASE}/api/events`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-User-Id": getUserId(),
      },
      body: JSON.stringify({ event_type: eventType, payload }),
      keepalive: true,
    }).catch(() => {
      /* fire-and-forget */
    });
  } catch {
    /* fire-and-forget */
  }
}

// ---------------------------------------------------------------------------
// Chat (SSE over fetch). Returns the raw Response for streaming.
// ---------------------------------------------------------------------------

export async function chatRequest(
  message: string,
  history: ChatTurn[],
  weights?: SimilarityWeights
): Promise<Response> {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-User-Id": getUserId(),
    },
    body: JSON.stringify({
      message,
      history: history.length ? history : undefined,
      weights,
    }),
  });
  if (!res.ok) {
    let detail = `Chat request failed (${res.status})`;
    try {
      const body = await res.json();
      if (body && typeof body.detail === "string") detail = body.detail;
    } catch {
      /* keep default */
    }
    throw new ApiError(res.status, detail);
  }
  return res;
}

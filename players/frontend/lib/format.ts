import type { PlayerSummary } from "./api";

/** 73.5 -> 6'1.5" */
export function formatHeight(heightIn: number | null | undefined): string {
  if (heightIn === null || heightIn === undefined) return "—";
  const feet = Math.floor(heightIn / 12);
  const inches = Math.round((heightIn - feet * 12) * 2) / 2;
  if (inches === 12) return `${feet + 1}'0"`;
  const inchStr = Number.isInteger(inches) ? String(inches) : inches.toFixed(1);
  return `${feet}'${inchStr}"`;
}

export function formatHtWt(
  heightIn: number | null | undefined,
  weightLb: number | null | undefined
): string {
  const h = formatHeight(heightIn);
  const w = weightLb === null || weightLb === undefined ? "—" : String(weightLb);
  return `${h} ${w}`;
}

export function fmt(
  value: number | null | undefined,
  digits = 2
): string {
  if (value === null || value === undefined) return "—";
  return value.toFixed(digits);
}

export function fmtInt(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return String(Math.round(value));
}

export function fmtPct01(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return `${Math.round(value * 100)}%`;
}

/** Draft outcome line: "Rd 2 · #41 · DAL" | "2026 (eligible)" | "Undrafted" */
export function formatDraftOutcome(
  p: Pick<PlayerSummary, "draft_class" | "draft_round" | "draft_pick" | "draft_team">
): string {
  if (p.draft_round != null && p.draft_pick != null) {
    return `Rd ${p.draft_round} · #${p.draft_pick}${
      p.draft_team ? ` · ${p.draft_team}` : ""
    }`;
  }
  if (p.draft_class >= 2026) return `${p.draft_class} (eligible)`;
  return "Undrafted";
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function traitLabel(trait: string): string {
  return trait
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

export const MILESTONE_LABELS: Record<string, string> = {
  post_season: "Post-Season",
  senior_bowl: "Senior Bowl",
  post_combine: "Post-Combine",
  pre_draft: "Pre-Draft",
};

export const STAT_LABELS: Record<string, string> = {
  targets: "Targets",
  receptions: "Receptions",
  rec_yards: "Rec Yards",
  rec_td: "Rec TD",
  rush_att: "Rush Att",
  rush_yards: "Rush Yards",
  rush_td: "Rush TD",
  pass_att: "Pass Att",
  pass_yards: "Pass Yards",
  pass_td: "Pass TD",
  interceptions_thrown: "INT Thrown",
  tackles: "Tackles",
  tfl: "TFL",
  sacks: "Sacks",
  pass_breakups: "PBU",
  interceptions: "INT",
  pressures: "Pressures",
  snaps: "Snaps",
};

export function statLabel(key: string): string {
  return STAT_LABELS[key] || traitLabel(key);
}

export const POSITION_GROUP_COLORS: Record<string, string> = {
  QB: "#f59e0b",
  RB: "#22c55e",
  WR: "#38bdf8",
  TE: "#a78bfa",
  OL: "#f472b6",
  DL: "#ef4444",
  LB: "#fb923c",
  DB: "#2dd4bf",
};

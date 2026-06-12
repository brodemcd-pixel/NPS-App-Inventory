"use client";

import type { MockConsensusPoint, TrajectorySeason } from "@/lib/api";
import { MILESTONE_LABELS } from "@/lib/format";

// ---------------------------------------------------------------------------
// Trajectory sparkline: SVG line of season production scores (0..100)
// ---------------------------------------------------------------------------

export function TrajectorySparkline({
  seasons,
}: {
  seasons: TrajectorySeason[];
}) {
  const W = 280;
  const H = 72;
  const PAD = 14;
  if (seasons.length === 0) {
    return <div className="text-xs text-slate-500">No season data.</div>;
  }
  const sorted = [...seasons].sort((a, b) => a.season - b.season);
  const xs = (i: number) =>
    sorted.length === 1
      ? W / 2
      : PAD + (i * (W - 2 * PAD)) / (sorted.length - 1);
  const ys = (score: number) => H - PAD - (score / 100) * (H - 2 * PAD);
  const points = sorted.map((s, i) => `${xs(i)},${ys(s.score)}`).join(" ");

  return (
    <svg
      viewBox={`0 0 ${W} ${H + 14}`}
      className="w-full max-w-[320px]"
      role="img"
      aria-label="Production trajectory"
    >
      <polyline
        points={points}
        fill="none"
        stroke="#38bdf8"
        strokeWidth={2}
        strokeLinejoin="round"
        strokeLinecap="round"
      />
      {sorted.map((s, i) => (
        <g key={s.season}>
          <circle cx={xs(i)} cy={ys(s.score)} r={3} fill="#38bdf8" />
          <text
            x={xs(i)}
            y={H + 10}
            textAnchor="middle"
            fontSize={9}
            fill="#64748b"
          >
            {s.season}
          </text>
          <text
            x={xs(i)}
            y={ys(s.score) - 6}
            textAnchor="middle"
            fontSize={9}
            fill="#94a3b8"
          >
            {Math.round(s.score)}
          </text>
        </g>
      ))}
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Mock-draft consensus mini line chart (inverted y: rank 1 on top)
// ---------------------------------------------------------------------------

const MILESTONE_ORDER = [
  "post_season",
  "senior_bowl",
  "post_combine",
  "pre_draft",
] as const;

export function MockConsensusChart({
  points,
}: {
  points: MockConsensusPoint[];
}) {
  const W = 300;
  const H = 90;
  const PAD = 18;
  const ordered = MILESTONE_ORDER.map((m) =>
    points.find((p) => p.milestone === m)
  ).filter((p): p is MockConsensusPoint => p !== undefined);

  if (ordered.length === 0) {
    return <div className="text-xs text-slate-500">No mock-draft data.</div>;
  }

  const ranks = ordered.map((p) => p.consensus_rank);
  const minRank = Math.min(...ranks);
  const maxRank = Math.max(...ranks);
  const span = Math.max(1, maxRank - minRank);

  const xs = (i: number) =>
    ordered.length === 1
      ? W / 2
      : PAD + (i * (W - 2 * PAD)) / (ordered.length - 1);
  // Inverted axis: rank 1 (best) at the top.
  const ys = (rank: number) =>
    PAD + ((rank - minRank) / span) * (H - 2 * PAD);

  return (
    <svg
      viewBox={`0 0 ${W} ${H + 18}`}
      className="w-full max-w-[340px]"
      role="img"
      aria-label="Mock draft consensus"
    >
      <polyline
        points={ordered.map((p, i) => `${xs(i)},${ys(p.consensus_rank)}`).join(" ")}
        fill="none"
        stroke="#a78bfa"
        strokeWidth={2}
        strokeLinejoin="round"
        strokeLinecap="round"
      />
      {ordered.map((p, i) => (
        <g key={p.milestone}>
          <circle cx={xs(i)} cy={ys(p.consensus_rank)} r={3} fill="#a78bfa" />
          <text
            x={xs(i)}
            y={ys(p.consensus_rank) - 6}
            textAnchor="middle"
            fontSize={9}
            fill="#c4b5fd"
          >
            #{p.consensus_rank}
          </text>
          <text
            x={xs(i)}
            y={H + 14}
            textAnchor="middle"
            fontSize={8}
            fill="#64748b"
          >
            {MILESTONE_LABELS[p.milestone] || p.milestone}
          </text>
        </g>
      ))}
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Vertical bar chart (questions per day on /dashboard)
// ---------------------------------------------------------------------------

export function DailyBarChart({
  data,
}: {
  data: { date: string; count: number }[];
}) {
  const W = 720;
  const H = 160;
  const PAD = 24;
  if (data.length === 0) {
    return <div className="text-xs text-slate-500">No data in window.</div>;
  }
  const max = Math.max(1, ...data.map((d) => d.count));
  const bw = (W - 2 * PAD) / data.length;
  return (
    <svg
      viewBox={`0 0 ${W} ${H + 26}`}
      className="w-full"
      role="img"
      aria-label="Questions per day"
    >
      {data.map((d, i) => {
        const h = (d.count / max) * (H - PAD);
        const x = PAD + i * bw;
        const showLabel =
          data.length <= 12 || i % Math.ceil(data.length / 10) === 0;
        return (
          <g key={d.date}>
            <rect
              x={x + bw * 0.12}
              y={H - h}
              width={bw * 0.76}
              height={Math.max(h, d.count > 0 ? 2 : 0)}
              rx={2}
              fill="#0ea5e9"
              opacity={0.85}
            >
              <title>{`${d.date}: ${d.count}`}</title>
            </rect>
            {d.count > 0 && h > 14 && (
              <text
                x={x + bw / 2}
                y={H - h - 4}
                textAnchor="middle"
                fontSize={9}
                fill="#7dd3fc"
              >
                {d.count}
              </text>
            )}
            {showLabel && (
              <text
                x={x + bw / 2}
                y={H + 14}
                textAnchor="middle"
                fontSize={8}
                fill="#64748b"
              >
                {d.date.slice(5)}
              </text>
            )}
          </g>
        );
      })}
      <line x1={PAD} y1={H} x2={W - PAD} y2={H} stroke="#1f2d49" />
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Grouped bar chart (per-class Spearman on /accuracy)
// ---------------------------------------------------------------------------

export function GroupedBarChart({
  groups,
  series,
}: {
  groups: { label: string; values: number[] }[];
  series: { name: string; color: string }[];
}) {
  const W = 560;
  const H = 180;
  const PAD = 30;
  if (groups.length === 0) {
    return <div className="text-xs text-slate-500">No data.</div>;
  }
  const max = Math.max(
    0.1,
    ...groups.flatMap((g) => g.values.map((v) => Math.abs(v)))
  );
  const gw = (W - 2 * PAD) / groups.length;
  const bw = (gw * 0.7) / series.length;

  return (
    <div>
      <svg
        viewBox={`0 0 ${W} ${H + 26}`}
        className="w-full max-w-[640px]"
        role="img"
        aria-label="Per-class accuracy"
      >
        {groups.map((g, gi) => {
          const gx = PAD + gi * gw + gw * 0.15;
          return (
            <g key={g.label}>
              {g.values.map((v, si) => {
                const h = (Math.max(0, v) / max) * (H - PAD);
                return (
                  <g key={si}>
                    <rect
                      x={gx + si * bw}
                      y={H - h}
                      width={bw * 0.85}
                      height={Math.max(h, 1)}
                      rx={2}
                      fill={series[si]?.color || "#38bdf8"}
                      opacity={0.9}
                    >
                      <title>{`${g.label} · ${series[si]?.name}: ${v.toFixed(3)}`}</title>
                    </rect>
                    <text
                      x={gx + si * bw + (bw * 0.85) / 2}
                      y={H - h - 4}
                      textAnchor="middle"
                      fontSize={9}
                      fill="#94a3b8"
                    >
                      {v.toFixed(2)}
                    </text>
                  </g>
                );
              })}
              <text
                x={PAD + gi * gw + gw / 2}
                y={H + 16}
                textAnchor="middle"
                fontSize={10}
                fill="#94a3b8"
              >
                {g.label}
              </text>
            </g>
          );
        })}
        <line x1={PAD} y1={H} x2={W - PAD} y2={H} stroke="#1f2d49" />
      </svg>
      <div className="mt-1 flex gap-4">
        {series.map((s) => (
          <span key={s.name} className="flex items-center gap-1.5 text-[11px] text-slate-400">
            <span
              className="inline-block h-2.5 w-2.5 rounded-sm"
              style={{ backgroundColor: s.color }}
            />
            {s.name}
          </span>
        ))}
      </div>
    </div>
  );
}

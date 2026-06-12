"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { api, UmapPoint } from "@/lib/api";
import { Card, ErrorBox, Loading } from "@/components/ui";

const GROUP_COLORS: Record<string, string> = {
  QB: "#f59e0b",
  RB: "#84cc16",
  WR: "#38bdf8",
  TE: "#2dd4bf",
  OL: "#a78bfa",
  DL: "#fb7185",
  LB: "#f97316",
  DB: "#e879f9",
};

const W = 860;
const H = 620;
const PAD = 36;

export default function MapPage() {
  const router = useRouter();
  const [points, setPoints] = useState<UmapPoint[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [classFilter, setClassFilter] = useState<number | null>(null);
  const [hover, setHover] = useState<UmapPoint | null>(null);

  useEffect(() => {
    api
      .umap()
      .then((r) => setPoints(r.items))
      .catch((e) => setError(String(e)));
  }, []);

  const classes = useMemo(
    () =>
      points
        ? Array.from(new Set(points.map((p) => p.draft_class))).sort()
        : [],
    [points]
  );

  const scaled = useMemo(() => {
    if (!points) return [];
    const xs = points.map((p) => p.x);
    const ys = points.map((p) => p.y);
    const [minX, maxX] = [Math.min(...xs), Math.max(...xs)];
    const [minY, maxY] = [Math.min(...ys), Math.max(...ys)];
    const sx = (x: number) =>
      PAD + ((x - minX) / Math.max(1e-9, maxX - minX)) * (W - 2 * PAD);
    const sy = (y: number) =>
      PAD + ((y - minY) / Math.max(1e-9, maxY - minY)) * (H - 2 * PAD);
    return points.map((p) => ({ ...p, px: sx(p.x), py: sy(p.y) }));
  }, [points]);

  if (error) return <ErrorBox message={error} />;
  if (!points) return <Loading label="Loading similarity map…" />;

  return (
    <div className="space-y-4">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-100">
            Report similarity map
          </h1>
          <p className="text-xs text-slate-500">
            2-D projection of scouting-report embeddings. Position groups cluster
            naturally; hybrid players sit on cluster borders. Click a point to open
            the profile.
          </p>
        </div>
        <div className="flex gap-1.5">
          <button
            onClick={() => setClassFilter(null)}
            className={`rounded px-2 py-1 text-xs ${
              classFilter === null
                ? "bg-sky-600 text-white"
                : "bg-slate-800 text-slate-300 hover:bg-slate-700"
            }`}
          >
            All classes
          </button>
          {classes.map((c) => (
            <button
              key={c}
              onClick={() => setClassFilter(classFilter === c ? null : c)}
              className={`rounded px-2 py-1 text-xs tabular-nums ${
                classFilter === c
                  ? "bg-sky-600 text-white"
                  : "bg-slate-800 text-slate-300 hover:bg-slate-700"
              }`}
            >
              {c}
            </button>
          ))}
        </div>
      </div>

      <Card>
        <div className="relative">
          <svg
            viewBox={`0 0 ${W} ${H}`}
            className="w-full rounded bg-slate-950"
            onMouseLeave={() => setHover(null)}
          >
            {scaled.map((p) => {
              const dim = classFilter !== null && p.draft_class !== classFilter;
              return (
                <circle
                  key={p.player_id}
                  cx={p.px}
                  cy={p.py}
                  r={hover?.player_id === p.player_id ? 8 : 5}
                  fill={GROUP_COLORS[p.position_group] ?? "#94a3b8"}
                  opacity={dim ? 0.12 : 0.85}
                  stroke={hover?.player_id === p.player_id ? "#fff" : "none"}
                  className="cursor-pointer transition-all"
                  onMouseEnter={() => setHover(p)}
                  onClick={() => router.push(`/players/${p.player_id}`)}
                />
              );
            })}
          </svg>
          {hover && (
            <div className="pointer-events-none absolute left-2 top-2 rounded border border-slate-700 bg-slate-900/95 px-3 py-2 text-xs shadow-lg">
              <div className="font-semibold text-slate-100">{hover.name}</div>
              <div className="text-slate-400">
                {hover.position} · class of {hover.draft_class}
              </div>
            </div>
          )}
        </div>
        <div className="mt-3 flex flex-wrap gap-3">
          {Object.entries(GROUP_COLORS).map(([group, color]) => (
            <span key={group} className="flex items-center gap-1.5 text-xs text-slate-300">
              <span
                className="inline-block h-2.5 w-2.5 rounded-full"
                style={{ backgroundColor: color }}
              />
              {group}
            </span>
          ))}
        </div>
      </Card>
    </div>
  );
}

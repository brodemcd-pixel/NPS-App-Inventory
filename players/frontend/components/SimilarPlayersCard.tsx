"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { api, type SimilarResponse } from "@/lib/api";
import { fmt } from "@/lib/format";
import { Card, HBar, Loading } from "./ui";

const AXES: { key: "scouting" | "scheme" | "mental"; label: string; color: string }[] = [
  { key: "scouting", label: "Scouting", color: "#38bdf8" },
  { key: "scheme", label: "Scheme", color: "#a78bfa" },
  { key: "mental", label: "Mental", color: "#34d399" },
];

export default function SimilarPlayersCard({ playerId }: { playerId: number }) {
  const [weights, setWeights] = useState({ scouting: 0.5, scheme: 0.25, mental: 0.25 });
  const [data, setData] = useState<SimilarResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const total = weights.scouting + weights.scheme + weights.mental;
  const norm = (v: number) => (total > 0 ? v / total : 0);

  const fetchSimilar = useCallback(
    (w: { scouting: number; scheme: number; mental: number }) => {
      setLoading(true);
      setError(null);
      api
        .similar(playerId, {
          limit: 8,
          w_scouting: w.scouting,
          w_scheme: w.scheme,
          w_mental: w.mental,
        })
        .then((res) => {
          setData(res);
          setLoading(false);
        })
        .catch((e) => {
          setError(e instanceof Error ? e.message : "Failed to load");
          setLoading(false);
        });
    },
    [playerId]
  );

  useEffect(() => {
    fetchSimilar({ scouting: 0.5, scheme: 0.25, mental: 0.25 });
  }, [fetchSimilar]);

  const commit = () => fetchSimilar(weights);

  return (
    <Card title="Similar Players (FSM v1.0)">
      <div className="mb-3 space-y-2">
        {AXES.map((axis) => (
          <div key={axis.key}>
            <div className="mb-0.5 flex justify-between text-[11px] text-slate-400">
              <span>{axis.label}</span>
              <span className="num">
                {weights[axis.key].toFixed(2)}{" "}
                <span className="text-slate-600">
                  (→ {(norm(weights[axis.key]) * 100).toFixed(0)}%)
                </span>
              </span>
            </div>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={weights[axis.key]}
              onChange={(e) =>
                setWeights((w) => ({ ...w, [axis.key]: Number(e.target.value) }))
              }
              onMouseUp={commit}
              onTouchEnd={commit}
              onKeyUp={(e) => {
                if (e.key.startsWith("Arrow")) commit();
              }}
              aria-label={`${axis.label} weight`}
            />
          </div>
        ))}
        {data && (
          <div className="num text-[10px] text-slate-600">
            Weights used: scouting {fmt(data.weights_used.scouting)} · scheme{" "}
            {fmt(data.weights_used.scheme)} · mental {fmt(data.weights_used.mental)}
          </div>
        )}
      </div>

      {error && <div className="text-xs text-red-400">{error}</div>}
      {loading && <Loading label="Computing similarity…" />}

      {!loading && data && data.items.length === 0 && (
        <div className="text-xs text-slate-500">No comparable players found.</div>
      )}

      {!loading && data && (
        <ul className="divide-y divide-ink-800">
          {data.items.map((item) => (
            <li key={item.player.id} className="py-2">
              <div className="mb-1 flex items-center justify-between gap-2">
                <Link
                  href={`/players/${item.player.id}`}
                  className="truncate text-xs font-medium text-slate-100 hover:text-sky-300"
                >
                  {item.player.name}
                  <span className="ml-1.5 text-slate-500">
                    {item.player.position} · {item.player.draft_class} ·{" "}
                    {item.player.college}
                  </span>
                </Link>
                <span className="num text-sm font-bold text-sky-300">
                  {(item.overall * 100).toFixed(0)}
                </span>
              </div>
              <div className="grid grid-cols-3 gap-2">
                {AXES.map((axis) => {
                  const v = item.axes[axis.key];
                  return (
                    <div key={axis.key}>
                      <div className="mb-0.5 flex justify-between text-[10px] text-slate-500">
                        <span>{axis.label}</span>
                        <span className="num">
                          {v == null ? "—" : (v * 100).toFixed(0)}
                        </span>
                      </div>
                      <HBar value={v} color={axis.color} height={5} />
                    </div>
                  );
                })}
              </div>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

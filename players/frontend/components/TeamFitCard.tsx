"use client";

import { useEffect, useState } from "react";
import { api, type TeamFitItem } from "@/lib/api";
import { fmt } from "@/lib/format";
import { Card, HBar, Loading } from "./ui";

export default function TeamFitCard({ playerId }: { playerId: number }) {
  const [items, setItems] = useState<TeamFitItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .teamFit(playerId, 8)
      .then((res) => {
        if (!cancelled) setItems(res.items);
      })
      .catch((e) => {
        if (!cancelled)
          setError(e instanceof Error ? e.message : "Failed to load team fits");
      });
    return () => {
      cancelled = true;
    };
  }, [playerId]);

  return (
    <Card title="Team Fit (Top 8)">
      {error && <div className="text-xs text-red-400">{error}</div>}
      {!items && !error && <Loading label="Ranking team fits…" />}
      {items && items.length === 0 && (
        <div className="text-xs text-slate-500">No team fit data.</div>
      )}
      {items && (
        <ul className="divide-y divide-ink-800">
          {items.slice(0, 8).map((t) => (
            <li key={`${t.team}-${t.season}`} className="py-2">
              <div className="mb-1 flex items-center justify-between gap-2">
                <span className="truncate text-xs font-medium text-slate-100">
                  {t.team}
                  <span className="ml-1.5 text-[10px] text-slate-500">
                    {t.scheme_archetype} · {t.coordinator} ({t.coaching_tree})
                  </span>
                </span>
                <span className="num text-sm font-bold text-emerald-300">
                  {(t.fit * 100).toFixed(0)}
                </span>
              </div>
              <HBar value={t.fit} color="#34d399" height={6} />
              <div className="num mt-1 flex gap-3 text-[10px] text-slate-500">
                <span>archetype {fmt(t.components.archetype, 1)}</span>
                <span>tree {fmt(t.components.tree, 1)}</span>
                <span>role {fmt(t.components.role, 2)}</span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

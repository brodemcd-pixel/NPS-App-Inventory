"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import {
  api,
  exportComparePdfUrl,
  type CompareResponse,
  type Measurables,
  type PlayerDetail,
} from "@/lib/api";
import {
  fmt,
  fmtInt,
  formatDraftOutcome,
  formatHeight,
  statLabel,
  traitLabel,
} from "@/lib/format";
import PlayerPicker from "./PlayerPicker";
import { Card, Chip, ErrorBox, HBar, Loading } from "./ui";

// direction: 1 = higher is better, -1 = lower is better
const MEASURABLE_ROWS: {
  key: keyof Measurables;
  label: string;
  dir: 1 | -1;
  format: (v: number) => string;
}[] = [
  { key: "height_in", label: "Height", dir: 1, format: (v) => formatHeight(v) },
  { key: "weight_lb", label: "Weight", dir: 1, format: (v) => `${Math.round(v)} lb` },
  { key: "forty", label: "40-Yard", dir: -1, format: (v) => `${v.toFixed(2)}s` },
  { key: "vertical_in", label: "Vertical", dir: 1, format: (v) => `${v.toFixed(1)}"` },
  { key: "broad_in", label: "Broad", dir: 1, format: (v) => `${v.toFixed(0)}"` },
  { key: "three_cone", label: "3-Cone", dir: -1, format: (v) => `${v.toFixed(2)}s` },
  { key: "shuttle", label: "Shuttle", dir: -1, format: (v) => `${v.toFixed(2)}s` },
  { key: "bench_reps", label: "Bench", dir: 1, format: (v) => `${Math.round(v)}` },
  { key: "arm_length_in", label: "Arm", dir: 1, format: (v) => `${v.toFixed(2)}"` },
  { key: "hand_size_in", label: "Hand", dir: 1, format: (v) => `${v.toFixed(2)}"` },
  { key: "wingspan_in", label: "Wingspan", dir: 1, format: (v) => `${v.toFixed(1)}"` },
];

const REPORT_SECTIONS: { key: "overview" | "strengths" | "weaknesses" | "sources_tell_us"; label: string }[] = [
  { key: "overview", label: "Overview" },
  { key: "strengths", label: "Strengths" },
  { key: "weaknesses", label: "Weaknesses" },
  { key: "sources_tell_us", label: "What Sources Tell Us" },
];

function ColumnHeader({ p }: { p: PlayerDetail }) {
  return (
    <div className="rounded-lg border border-ink-700 bg-ink-900 p-4">
      <Link
        href={`/players/${p.id}`}
        className="text-lg font-bold text-slate-50 hover:text-sky-300"
      >
        {p.name}
      </Link>
      <div className="mt-0.5 text-xs text-slate-400">
        {p.position} · {p.college} · Class of{" "}
        <span className="num">{p.draft_class}</span>
      </div>
      <div className="num mt-2 flex gap-5 text-xs text-slate-300">
        <span>
          Grade <strong className="text-sky-300">{fmt(p.nfl_grade)}</strong>
        </span>
        <span>{formatDraftOutcome(p)}</span>
      </div>
    </div>
  );
}

function mentalMap(p: PlayerDetail): Map<string, number> {
  const m = new Map<string, number>();
  for (const t of p.mental_profile.core) m.set(t.trait, t.score);
  return m;
}

export default function CompareView() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const a = searchParams.get("a");
  const b = searchParams.get("b");

  const [data, setData] = useState<CompareResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!a || !b) {
      setData(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    api
      .compare(a, b)
      .then((res) => {
        if (cancelled) return;
        setData(res);
        setLoading(false);
      })
      .catch((e) => {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : "Failed to load comparison");
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [a, b]);

  function setParam(key: "a" | "b", id: number) {
    const sp = new URLSearchParams(searchParams.toString());
    sp.set(key, String(id));
    router.replace(`/compare?${sp.toString()}`);
  }

  const traitRows = useMemo(() => {
    if (!data) return [];
    const ma = mentalMap(data.a);
    const mb = mentalMap(data.b);
    const all = Array.from(new Set([...ma.keys(), ...mb.keys()]));
    return all.map((trait) => ({
      trait,
      a: ma.get(trait) ?? null,
      b: mb.get(trait) ?? null,
    }));
  }, [data]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <h1 className="text-lg font-bold text-slate-100">Side-by-Side Compare</h1>
        {a && b && (
          <button
            onClick={() => {
              window.location.href = exportComparePdfUrl(a, b);
            }}
            className="rounded border border-ink-600 bg-ink-800 px-3 py-1.5 text-xs font-medium text-slate-200 hover:border-sky-700 hover:text-sky-300"
          >
            ⬇ Export PDF
          </button>
        )}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <PlayerPicker
          label="Player A"
          selectedName={data?.a.name || (a ? `#${a}` : null)}
          onSelect={(p) => setParam("a", p.id)}
        />
        <PlayerPicker
          label="Player B"
          selectedName={data?.b.name || (b ? `#${b}` : null)}
          onSelect={(p) => setParam("b", p.id)}
        />
      </div>

      {!a || !b ? (
        <div className="rounded-lg border border-ink-700 bg-ink-900 p-8 text-center text-sm text-slate-500">
          Pick two players to compare.
        </div>
      ) : loading ? (
        <Loading label="Loading comparison…" />
      ) : error ? (
        <ErrorBox message={error} />
      ) : data ? (
        <>
          {/* Similarity header */}
          <Card title="FSM Similarity">
            <div className="flex flex-wrap items-center gap-8">
              <div>
                <div className="text-[10px] uppercase tracking-widest text-slate-500">
                  Overall
                </div>
                <div className="num text-3xl font-black text-sky-300">
                  {(data.similarity.overall * 100).toFixed(0)}
                </div>
              </div>
              {(
                [
                  ["scouting", "Scouting", "#38bdf8"],
                  ["scheme", "Scheme", "#a78bfa"],
                  ["mental", "Mental", "#34d399"],
                ] as const
              ).map(([key, label, color]) => {
                const v = data.similarity.axes[key];
                const w = data.similarity.weights_used[key];
                return (
                  <div key={key} className="w-36">
                    <div className="mb-0.5 flex justify-between text-[11px] text-slate-400">
                      <span>
                        {label}{" "}
                        <span className="num text-slate-600">
                          (w {w != null ? w.toFixed(2) : "—"})
                        </span>
                      </span>
                      <span className="num">
                        {v == null ? "n/a" : (v * 100).toFixed(0)}
                      </span>
                    </div>
                    <HBar value={v} color={color} height={6} />
                  </div>
                );
              })}
            </div>
          </Card>

          <div className="grid gap-4 md:grid-cols-2">
            <ColumnHeader p={data.a} />
            <ColumnHeader p={data.b} />
          </div>

          {/* Measurables with better-value highlighting */}
          <Card title="Measurables (better value highlighted)">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-[10px] uppercase tracking-wider text-slate-500">
                  <th className="py-1 text-left">Metric</th>
                  <th className="py-1 text-right">{data.a.name}</th>
                  <th className="py-1 text-right">{data.b.name}</th>
                </tr>
              </thead>
              <tbody>
                {MEASURABLE_ROWS.map((row) => {
                  const va = data.a.measurables[row.key];
                  const vb = data.b.measurables[row.key];
                  let aBetter = false;
                  let bBetter = false;
                  if (va != null && vb != null && va !== vb) {
                    aBetter = (va - vb) * row.dir > 0;
                    bBetter = !aBetter;
                  }
                  return (
                    <tr key={row.key} className="border-t border-ink-800">
                      <td className="py-1.5 text-slate-400">{row.label}</td>
                      <td
                        className={`num py-1.5 text-right ${
                          aBetter
                            ? "font-bold text-emerald-300"
                            : "text-slate-300"
                        }`}
                      >
                        {va == null ? "—" : row.format(va)}
                      </td>
                      <td
                        className={`num py-1.5 text-right ${
                          bBetter
                            ? "font-bold text-emerald-300"
                            : "text-slate-300"
                        }`}
                      >
                        {vb == null ? "—" : row.format(vb)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </Card>

          {/* Reports */}
          {REPORT_SECTIONS.map((s) => (
            <div key={s.key} className="grid gap-4 md:grid-cols-2">
              {[data.a, data.b].map((p) => (
                <Card key={p.id} title={`${s.label} — ${p.name}`}>
                  <p className="whitespace-pre-wrap text-xs leading-relaxed text-slate-300">
                    {p.report[s.key] || "—"}
                  </p>
                </Card>
              ))}
            </div>
          ))}

          {/* Scheme context */}
          <div className="grid gap-4 md:grid-cols-2">
            {[data.a, data.b].map((p) => (
              <Card key={p.id} title={`Scheme Context — ${p.name}`}>
                {p.scheme_context.length === 0 ? (
                  <div className="text-xs text-slate-500">No scheme data.</div>
                ) : (
                  <ul className="space-y-1.5">
                    {[...p.scheme_context]
                      .sort((x, y) => y.season - x.season)
                      .map((s) => (
                        <li
                          key={s.season}
                          className="flex items-center gap-2 text-xs text-slate-300"
                        >
                          <span className="num text-slate-500">{s.season}</span>
                          <Chip tone="sky">{s.scheme_archetype}</Chip>
                          <span className="truncate text-slate-400">
                            {s.coordinator} ({s.coaching_tree})
                          </span>
                        </li>
                      ))}
                  </ul>
                )}
              </Card>
            ))}
          </div>

          {/* Mental bars side by side */}
          <Card title="Mental Profile (core traits)">
            {traitRows.length === 0 ? (
              <div className="text-xs text-slate-500">
                No mental profile data for either player.
              </div>
            ) : (
              <div className="space-y-2">
                <div className="grid grid-cols-[140px_1fr_1fr] gap-3 text-[10px] uppercase tracking-wider text-slate-500">
                  <span>Trait</span>
                  <span>{data.a.name}</span>
                  <span>{data.b.name}</span>
                </div>
                {traitRows.map((row) => (
                  <div
                    key={row.trait}
                    className="grid grid-cols-[140px_1fr_1fr] items-center gap-3"
                  >
                    <span className="text-xs text-slate-300">
                      {traitLabel(row.trait)}
                    </span>
                    {[row.a, row.b].map((v, i) => (
                      <div key={i} className="flex items-center gap-2">
                        <div className="flex-1">
                          <HBar value={v} color={i === 0 ? "#38bdf8" : "#a78bfa"} height={6} />
                        </div>
                        <span className="num w-8 text-right text-[11px] text-slate-400">
                          {v == null ? "—" : v.toFixed(2)}
                        </span>
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Production */}
          <div className="grid gap-4 md:grid-cols-2">
            {[data.a, data.b].map((p) => {
              const seasons = new Map<number, typeof p.production>();
              for (const r of p.production) {
                const list = seasons.get(r.season) || [];
                list.push(r);
                seasons.set(r.season, list);
              }
              const grouped = [...seasons.entries()].sort((x, y) => y[0] - x[0]);
              return (
                <Card key={p.id} title={`Production — ${p.name}`}>
                  {grouped.length === 0 ? (
                    <div className="text-xs text-slate-500">
                      No production data.
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {grouped.map(([season, rows]) => (
                        <div key={season}>
                          <div className="num mb-0.5 text-xs font-bold text-slate-300">
                            {season}
                          </div>
                          <table className="w-full text-xs">
                            <tbody>
                              {rows.map((r, i) => (
                                <tr key={i} className="border-t border-ink-800">
                                  <td className="py-1 pr-2 text-slate-400">
                                    {statLabel(r.stat_category)}
                                  </td>
                                  <td className="num py-1 pr-2 text-right text-slate-200">
                                    {Number.isInteger(r.value)
                                      ? r.value
                                      : r.value.toFixed(1)}
                                  </td>
                                  <td className="num py-1 text-right text-slate-500">
                                    {r.team_share_pct == null
                                      ? "—"
                                      : `${r.team_share_pct.toFixed(1)}%`}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      ))}
                    </div>
                  )}
                </Card>
              );
            })}
          </div>

          {/* NFL outcomes */}
          <div className="grid gap-4 md:grid-cols-2">
            {[data.a, data.b].map((p) => (
              <Card key={p.id} title={`NFL Outcomes — ${p.name}`}>
                {p.nfl_outcomes.length === 0 ? (
                  <div className="text-xs text-slate-500">
                    {p.draft_class >= 2026
                      ? `${p.draft_class} (eligible) — no NFL data yet.`
                      : "No NFL outcome data."}
                  </div>
                ) : (
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="text-left text-[10px] uppercase tracking-wider text-slate-500">
                        <th className="py-1 pr-2">Season</th>
                        <th className="py-1 pr-2 text-right">G</th>
                        <th className="py-1 pr-2 text-right">Snaps</th>
                        <th className="py-1 text-right">PFF</th>
                      </tr>
                    </thead>
                    <tbody>
                      {[...p.nfl_outcomes]
                        .sort((x, y) => y.season - x.season)
                        .map((o) => (
                          <tr key={o.season} className="border-t border-ink-800">
                            <td className="num py-1 pr-2 text-slate-300">
                              {o.season}
                            </td>
                            <td className="num py-1 pr-2 text-right text-slate-300">
                              {fmtInt(o.games)}
                            </td>
                            <td className="num py-1 pr-2 text-right text-slate-300">
                              {fmtInt(o.snaps)}
                            </td>
                            <td className="num py-1 text-right font-semibold text-sky-300">
                              {fmt(o.pff_grade, 1)}
                            </td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                )}
              </Card>
            ))}
          </div>
        </>
      ) : null}
    </div>
  );
}

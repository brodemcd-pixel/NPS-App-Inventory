"use client";

import { useEffect, useMemo, useState } from "react";
import {
  api,
  exportPlayerPdfUrl,
  type Measurables,
  type PlayerDetail,
  type ProvenanceRow,
} from "@/lib/api";
import {
  fmt,
  fmtInt,
  formatDate,
  formatDraftOutcome,
  formatHeight,
  statLabel,
} from "@/lib/format";
import { Card, Chip, ErrorBox, Loading } from "./ui";
import { MockConsensusChart, TrajectorySparkline } from "./charts";
import MentalProfileCard from "./MentalProfileCard";
import SimilarPlayersCard from "./SimilarPlayersCard";
import TeamFitCard from "./TeamFitCard";
import CommentsSection from "./CommentsSection";
import WatchlistButton from "./WatchlistButton";

const FALLBACK_TRAITS = [
  "football_iq",
  "processing_speed",
  "leadership",
  "coachability",
  "poise",
  "decision_making",
  "instincts",
  "anticipation",
  "motor",
  "audibles",
  "protection_calls",
  "defense_reading",
  "safety_manipulation",
  "progression_discipline",
];

const MEASURABLE_FIELDS: {
  key: keyof Measurables;
  label: string;
  format: (v: number) => string;
}[] = [
  { key: "height_in", label: "Height", format: (v) => formatHeight(v) },
  { key: "weight_lb", label: "Weight", format: (v) => `${Math.round(v)} lb` },
  { key: "forty", label: "40-Yard", format: (v) => `${v.toFixed(2)}s` },
  { key: "vertical_in", label: "Vertical", format: (v) => `${v.toFixed(1)}"` },
  { key: "broad_in", label: "Broad", format: (v) => `${v.toFixed(0)}"` },
  { key: "three_cone", label: "3-Cone", format: (v) => `${v.toFixed(2)}s` },
  { key: "shuttle", label: "Shuttle", format: (v) => `${v.toFixed(2)}s` },
  { key: "bench_reps", label: "Bench", format: (v) => `${Math.round(v)} reps` },
  { key: "arm_length_in", label: "Arm", format: (v) => `${v.toFixed(2)}"` },
  { key: "hand_size_in", label: "Hand", format: (v) => `${v.toFixed(2)}"` },
  { key: "wingspan_in", label: "Wingspan", format: (v) => `${v.toFixed(1)}"` },
];

function provenanceTitle(
  provenance: ProvenanceRow[],
  field: string
): string | undefined {
  const row = provenance.find((p) => p.field_name === field);
  if (!row) return undefined;
  return `Source: ${row.source} · retrieved ${formatDate(row.retrieved_at)}`;
}

const REPORT_SECTIONS: { key: "overview" | "strengths" | "weaknesses" | "sources_tell_us"; label: string }[] = [
  { key: "overview", label: "Overview" },
  { key: "strengths", label: "Strengths" },
  { key: "weaknesses", label: "Weaknesses" },
  { key: "sources_tell_us", label: "What Sources Tell Us" },
];

export default function PlayerProfile({ playerId }: { playerId: string }) {
  const [player, setPlayer] = useState<PlayerDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [traits, setTraits] = useState<string[]>(FALLBACK_TRAITS);

  useEffect(() => {
    let cancelled = false;
    setPlayer(null);
    setError(null);
    api
      .player(playerId)
      .then((p) => {
        if (!cancelled) setPlayer(p);
      })
      .catch((e) => {
        if (!cancelled)
          setError(e instanceof Error ? e.message : "Failed to load player");
      });
    api
      .metaFilters()
      .then((m) => {
        if (!cancelled && m.traits.length) setTraits(m.traits);
      })
      .catch(() => {
        /* fallback list */
      });
    return () => {
      cancelled = true;
    };
  }, [playerId]);

  const productionBySeason = useMemo(() => {
    if (!player) return [];
    const map = new Map<number, typeof player.production>();
    for (const row of player.production) {
      const list = map.get(row.season) || [];
      list.push(row);
      map.set(row.season, list);
    }
    return [...map.entries()].sort((a, b) => b[0] - a[0]);
  }, [player]);

  if (error) return <ErrorBox message={error} />;
  if (!player) return <Loading label="Loading player profile…" />;

  const flagged = player.flags.red_flag || player.flags.green_flag;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="rounded-lg border border-ink-700 bg-ink-900 p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-slate-50">{player.name}</h1>
              <Chip tone="sky">{player.position}</Chip>
              <Chip>{player.position_group}</Chip>
            </div>
            <div className="mt-1 text-sm text-slate-400">
              {player.college} · {player.conference} · Class of{" "}
              <span className="num">{player.draft_class}</span> · SoS Tier{" "}
              <span className="num">{player.sos_tier}</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <WatchlistButton playerId={player.id} />
            <button
              onClick={() => {
                window.location.href = exportPlayerPdfUrl(player.id);
              }}
              className="rounded border border-ink-600 bg-ink-800 px-3 py-1.5 text-xs font-medium text-slate-200 hover:border-sky-700 hover:text-sky-300"
            >
              ⬇ Export PDF
            </button>
          </div>
        </div>

        <div className="mt-4 flex flex-wrap gap-6">
          <div>
            <div className="text-[10px] uppercase tracking-widest text-slate-500">
              NFL Grade
            </div>
            <div className="num text-xl font-bold text-sky-300">
              {fmt(player.nfl_grade)}
            </div>
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-widest text-slate-500">
              Class Percentile
            </div>
            <div className="num text-xl font-bold text-slate-200">
              {fmt(player.class_percentile, 1)}
            </div>
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-widest text-slate-500">
              NGS Athleticism
            </div>
            <div className="num text-xl font-bold text-slate-200">
              {fmt(player.ngs_athleticism, 1)}
            </div>
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-widest text-slate-500">
              Draft Outcome
            </div>
            <div className="text-xl font-bold text-slate-200">
              {formatDraftOutcome(player)}
            </div>
          </div>
        </div>

        {flagged && (
          <div
            className={`mt-4 rounded border px-3 py-2 text-xs ${
              player.flags.red_flag
                ? "border-red-800/70 bg-red-950/40 text-red-200"
                : "border-emerald-800/70 bg-emerald-950/40 text-emerald-200"
            }`}
          >
            <strong className="mr-2 uppercase tracking-wider">
              {player.flags.red_flag ? "● Red flag" : "● Green flag"}
            </strong>
            {player.flags.notes || "No additional notes."}
          </div>
        )}
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        {/* Main column */}
        <div className="space-y-4 lg:col-span-2">
          <Card title="Measurables (hover for provenance)">
            <div className="grid grid-cols-3 gap-2 sm:grid-cols-4 md:grid-cols-6">
              {MEASURABLE_FIELDS.map((f) => {
                const v = player.measurables[f.key];
                return (
                  <div
                    key={f.key}
                    title={provenanceTitle(player.provenance, f.key)}
                    className="rounded border border-ink-700 bg-ink-850 px-2 py-1.5"
                  >
                    <div className="text-[9px] uppercase tracking-widest text-slate-500">
                      {f.label}
                    </div>
                    <div className="num text-sm font-semibold text-slate-200">
                      {v == null ? "—" : f.format(v)}
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>

          <div className="grid gap-4 md:grid-cols-2">
            {REPORT_SECTIONS.map((s) => (
              <Card
                key={s.key}
                title={s.label}
              >
                <p
                  className="whitespace-pre-wrap text-xs leading-relaxed text-slate-300"
                  title={provenanceTitle(player.provenance, s.key)}
                >
                  {player.report[s.key] || "—"}
                </p>
              </Card>
            ))}
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <Card title="Scheme Context">
              {player.scheme_context.length === 0 ? (
                <div className="text-xs text-slate-500">No scheme data.</div>
              ) : (
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-left text-[10px] uppercase tracking-wider text-slate-500">
                      <th className="py-1 pr-2">Season</th>
                      <th className="py-1 pr-2">Archetype</th>
                      <th className="py-1 pr-2">Coordinator</th>
                      <th className="py-1">Tree</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[...player.scheme_context]
                      .sort((a, b) => b.season - a.season)
                      .map((s) => (
                        <tr key={s.season} className="border-t border-ink-800">
                          <td className="num py-1.5 pr-2 text-slate-400">
                            {s.season}
                          </td>
                          <td className="py-1.5 pr-2">
                            <Chip tone="sky">{s.scheme_archetype}</Chip>
                          </td>
                          <td className="py-1.5 pr-2 text-slate-300">
                            {s.coordinator}
                          </td>
                          <td className="py-1.5 text-slate-400">
                            {s.coaching_tree}
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              )}
            </Card>

            <Card title="Functional Roles">
              {player.roles.length === 0 ? (
                <div className="text-xs text-slate-500">No role data.</div>
              ) : (
                <div className="flex flex-wrap gap-1.5">
                  {player.roles.map((r, i) => (
                    <Chip
                      key={i}
                      tone="amber"
                      title={`source: ${r.source}`}
                    >
                      {r.functional_role}{" "}
                      <span className="num ml-1 text-amber-500/80">
                        {(r.confidence * 100).toFixed(0)}%
                      </span>
                    </Chip>
                  ))}
                </div>
              )}
            </Card>
          </div>

          <MentalProfileCard profile={player.mental_profile} />

          <Card title="College Production">
            {productionBySeason.length === 0 ? (
              <div className="text-xs text-slate-500">No production data.</div>
            ) : (
              <div className="grid gap-4 md:grid-cols-2">
                {productionBySeason.map(([season, rows]) => (
                  <div key={season}>
                    <div className="num mb-1 text-xs font-bold text-slate-300">
                      {season}
                    </div>
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="text-left text-[10px] uppercase tracking-wider text-slate-500">
                          <th className="py-0.5 pr-2">Stat</th>
                          <th className="py-0.5 pr-2 text-right">Value</th>
                          <th className="py-0.5 text-right">Team Share</th>
                        </tr>
                      </thead>
                      <tbody>
                        {rows.map((r, i) => (
                          <tr key={i} className="border-t border-ink-800">
                            <td className="py-1 pr-2 text-slate-300">
                              {statLabel(r.stat_category)}
                            </td>
                            <td className="num py-1 pr-2 text-right text-slate-200">
                              {Number.isInteger(r.value)
                                ? r.value
                                : r.value.toFixed(1)}
                            </td>
                            <td className="num py-1 text-right text-slate-400">
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

          <div className="grid gap-4 md:grid-cols-2">
            <Card title="Production Trajectory">
              <TrajectorySparkline seasons={player.trajectory.seasons} />
              <div className="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-xs text-slate-400">
                <span>
                  Trend:{" "}
                  <strong
                    className={
                      player.trajectory.trend === "ascending"
                        ? "text-emerald-300"
                        : player.trajectory.trend === "declining"
                          ? "text-red-300"
                          : "text-slate-200"
                    }
                  >
                    {player.trajectory.trend}
                  </strong>
                </span>
                <span className="num">
                  Consistency:{" "}
                  <strong className="text-slate-200">
                    {fmt(player.trajectory.consistency)}
                  </strong>
                </span>
                <span className="num">
                  Breakout age:{" "}
                  <strong className="text-slate-200">
                    {fmt(player.trajectory.breakout_age, 1)}
                  </strong>
                </span>
              </div>
            </Card>

            <Card title="Mock Draft Consensus">
              <MockConsensusChart points={player.mock_consensus} />
            </Card>
          </div>

          {player.nfl_outcomes.length > 0 && (
            <Card title="NFL Outcomes">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-left text-[10px] uppercase tracking-wider text-slate-500">
                    <th className="py-1 pr-2">Season</th>
                    <th className="py-1 pr-2 text-right">Games</th>
                    <th className="py-1 pr-2 text-right">Snaps</th>
                    <th className="py-1 pr-2 text-right">PFF Grade</th>
                    <th className="py-1">Key Stats</th>
                  </tr>
                </thead>
                <tbody>
                  {[...player.nfl_outcomes]
                    .sort((a, b) => b.season - a.season)
                    .map((o) => (
                      <tr key={o.season} className="border-t border-ink-800">
                        <td className="num py-1.5 pr-2 text-slate-300">
                          {o.season}
                        </td>
                        <td className="num py-1.5 pr-2 text-right text-slate-300">
                          {fmtInt(o.games)}
                        </td>
                        <td className="num py-1.5 pr-2 text-right text-slate-300">
                          {fmtInt(o.snaps)}
                        </td>
                        <td className="num py-1.5 pr-2 text-right font-semibold text-sky-300">
                          {fmt(o.pff_grade, 1)}
                        </td>
                        <td className="num py-1.5 text-slate-400">
                          {o.stats && Object.keys(o.stats).length > 0
                            ? Object.entries(o.stats)
                                .map(([k, v]) => `${statLabel(k)} ${v}`)
                                .join(" · ")
                            : "—"}
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </Card>
          )}

          <CommentsSection
            playerId={player.id}
            initialComments={player.comments}
            traitOptions={traits}
          />
        </div>

        {/* Side column */}
        <div className="space-y-4">
          <SimilarPlayersCard playerId={player.id} />
          <TeamFitCard playerId={player.id} />
        </div>
      </div>
    </div>
  );
}

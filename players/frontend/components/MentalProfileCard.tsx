"use client";

import { useState } from "react";
import type { MentalProfile, MentalTraitEntry } from "@/lib/api";
import { fmt, formatDate, traitLabel } from "@/lib/format";
import { Card, Chip, HBar } from "./ui";

const SOURCE_TONES: Record<string, "sky" | "amber" | "green"> = {
  nlp: "sky",
  scout_tag: "amber",
  cognitive_test: "green",
};

function TraitBar({ entry }: { entry: MentalTraitEntry }) {
  const [expanded, setExpanded] = useState(false);
  const hasEvidence = entry.evidence && entry.evidence.length > 0;
  return (
    <div className="py-1">
      <button
        type="button"
        onClick={() => hasEvidence && setExpanded((v) => !v)}
        className={`block w-full text-left ${hasEvidence ? "cursor-pointer" : "cursor-default"}`}
        title={hasEvidence ? "Click for evidence" : undefined}
      >
        <div className="mb-0.5 flex items-center justify-between gap-2">
          <span className="flex items-center gap-1.5 text-xs text-slate-300">
            {traitLabel(entry.trait)}
            {entry.sources.map((s) => (
              <Chip key={s} tone={SOURCE_TONES[s] || "slate"}>
                {s}
              </Chip>
            ))}
            {hasEvidence && (
              <span className="text-[10px] text-slate-600">
                {expanded ? "▾" : "▸"}
              </span>
            )}
          </span>
          <span className="num text-xs font-semibold text-sky-300">
            {fmt(entry.score)}
          </span>
        </div>
        <HBar value={entry.score} />
      </button>
      {expanded && hasEvidence && (
        <ul className="mt-1.5 space-y-1 border-l-2 border-ink-600 pl-2">
          {entry.evidence.map((e, i) => (
            <li key={i} className="text-[11px] italic leading-snug text-slate-500">
              “{e}”
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function MentalProfileCard({
  profile,
}: {
  profile: MentalProfile;
}) {
  const hasAny =
    profile.core.length > 0 || profile.qb.length > 0 || profile.cognitive;
  return (
    <Card title="Mental Profile">
      {!hasAny && (
        <div className="text-xs text-slate-500">
          No mental profile data for this player.
        </div>
      )}

      {profile.core.length > 0 && (
        <div className="divide-y divide-ink-800">
          {profile.core.map((t) => (
            <TraitBar key={t.trait} entry={t} />
          ))}
        </div>
      )}

      {profile.qb.length > 0 && (
        <div className="mt-4">
          <div className="mb-1 text-[10px] font-semibold uppercase tracking-widest text-amber-400/80">
            QB Pre-Snap Sub-Profile
          </div>
          <div className="divide-y divide-ink-800">
            {profile.qb.map((t) => (
              <TraitBar key={t.trait} entry={t} />
            ))}
          </div>
        </div>
      )}

      {profile.cognitive && (
        <div className="mt-4 rounded border border-emerald-900/60 bg-emerald-950/30 p-3">
          <div className="mb-1 text-[10px] font-semibold uppercase tracking-widest text-emerald-400">
            Cognitive Test
          </div>
          <div className="flex flex-wrap gap-x-6 gap-y-1 text-xs text-slate-300">
            <span>{profile.cognitive.provider}</span>
            <span className="num">
              Composite{" "}
              <strong className="text-emerald-300">
                {fmt(profile.cognitive.composite_score, 1)}
              </strong>
            </span>
            <span className="num">
              Percentile{" "}
              <strong className="text-emerald-300">
                {fmt(profile.cognitive.percentile, 1)}
              </strong>
            </span>
            <span className="text-slate-500">
              {formatDate(profile.cognitive.taken_at)}
            </span>
          </div>
        </div>
      )}
    </Card>
  );
}

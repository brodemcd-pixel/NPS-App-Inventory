"use client";

import type { ReactNode } from "react";

export function Loading({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 py-8 text-sm text-slate-500">
      <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-slate-600 border-t-sky-400" />
      {label}
    </div>
  );
}

export function ErrorBox({ message }: { message: string }) {
  return (
    <div className="my-4 rounded border border-red-800/60 bg-red-950/40 px-4 py-3 text-sm text-red-300">
      {message}
    </div>
  );
}

export function Card({
  title,
  children,
  className = "",
  actions,
}: {
  title?: ReactNode;
  children: ReactNode;
  className?: string;
  actions?: ReactNode;
}) {
  return (
    <section
      className={`rounded-lg border border-ink-700 bg-ink-900 p-4 ${className}`}
    >
      {(title || actions) && (
        <div className="mb-3 flex items-center justify-between gap-2">
          {title && (
            <h2 className="text-xs font-semibold uppercase tracking-widest text-slate-400">
              {title}
            </h2>
          )}
          {actions}
        </div>
      )}
      {children}
    </section>
  );
}

export function Chip({
  children,
  tone = "slate",
  title,
}: {
  children: ReactNode;
  tone?: "slate" | "sky" | "green" | "red" | "amber";
  title?: string;
}) {
  const tones: Record<string, string> = {
    slate: "border-slate-600/60 bg-slate-800/60 text-slate-300",
    sky: "border-sky-700/60 bg-sky-950/60 text-sky-300",
    green: "border-emerald-700/60 bg-emerald-950/60 text-emerald-300",
    red: "border-red-700/60 bg-red-950/60 text-red-300",
    amber: "border-amber-700/60 bg-amber-950/60 text-amber-300",
  };
  return (
    <span
      title={title}
      className={`inline-flex items-center whitespace-nowrap rounded-full border px-2 py-0.5 text-[11px] ${tones[tone]}`}
    >
      {children}
    </span>
  );
}

export function FlagDots({
  red,
  green,
  notes,
}: {
  red: boolean;
  green: boolean;
  notes?: string | null;
}) {
  if (!red && !green) return null;
  return (
    <span className="inline-flex items-center gap-1" title={notes || undefined}>
      {red && (
        <span
          className="inline-block h-2 w-2 rounded-full bg-red-500"
          title={notes ? `Red flag: ${notes}` : "Red flag"}
        />
      )}
      {green && (
        <span
          className="inline-block h-2 w-2 rounded-full bg-emerald-500"
          title={notes ? `Green flag: ${notes}` : "Green flag"}
        />
      )}
    </span>
  );
}

/** Horizontal score bar for 0..1 values. */
export function HBar({
  value,
  color = "#38bdf8",
  height = 8,
}: {
  value: number | null | undefined;
  color?: string;
  height?: number;
}) {
  const pct = value == null ? 0 : Math.max(0, Math.min(1, value)) * 100;
  return (
    <div
      className="w-full overflow-hidden rounded-sm bg-ink-700"
      style={{ height }}
    >
      <div
        className="h-full rounded-sm transition-all"
        style={{ width: `${pct}%`, backgroundColor: color }}
      />
    </div>
  );
}

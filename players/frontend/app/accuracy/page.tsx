"use client";

import { useEffect, useState } from "react";
import { AccuracyResponse, api } from "@/lib/api";
import { GroupedBarChart } from "@/components/charts";
import { Card, ErrorBox, Loading } from "@/components/ui";

export default function AccuracyPage() {
  const [data, setData] = useState<AccuracyResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .accuracy()
      .then(setData)
      .catch((e) => setError(String(e)));
  }, []);

  if (error) return <ErrorBox message={error} />;
  if (!data) return <Loading label="Running back-test…" />;

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-semibold text-slate-100">Model accuracy</h1>
        <p className="mt-1 max-w-3xl text-xs text-slate-500">
          Back-test of comp-based outcome prediction against actual NFL outcomes for the{" "}
          {data.classes.join(" / ")} classes. Method: {data.method}. Spearman: rank
          correlation between predicted and actual outcome scores (higher is better).
          MAE: mean absolute error of the predicted outcome score (lower is better).
        </p>
      </div>

      <Card title="FSM v0.2 (scouting-only) vs FSM v1.0 (multi-axis)">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-800 text-left text-xs uppercase tracking-wide text-slate-500">
              <th className="py-1.5 pr-3">Model</th>
              <th className="px-3 py-1.5">Weights (scouting / scheme / mental)</th>
              <th className="px-3 py-1.5">Spearman ρ</th>
              <th className="px-3 py-1.5">MAE</th>
              <th className="px-3 py-1.5">n</th>
            </tr>
          </thead>
          <tbody>
            {data.models.map((m) => (
              <tr key={m.name} className="border-b border-slate-800/60">
                <td className="py-2 pr-3 font-medium text-slate-200">{m.name}</td>
                <td className="px-3 py-2 tabular-nums text-slate-400">
                  {(m.weights.scouting ?? 0).toFixed(2)} /{" "}
                  {(m.weights.scheme ?? 0).toFixed(2)} /{" "}
                  {(m.weights.mental ?? 0).toFixed(2)}
                </td>
                <td className="px-3 py-2 tabular-nums">
                  {m.spearman === null ? "—" : m.spearman.toFixed(3)}
                </td>
                <td className="px-3 py-2 tabular-nums">
                  {m.mae === null ? "—" : m.mae.toFixed(1)}
                </td>
                <td className="px-3 py-2 tabular-nums text-slate-400">{m.n}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      <Card title="Spearman ρ by draft class">
        <GroupedBarChart
          groups={data.per_class.map((c) => ({
            label: String(c.draft_class),
            values: [c.v02_spearman ?? 0, c.v10_spearman ?? 0],
          }))}
          series={[
            { name: "FSM v0.2", color: "#64748b" },
            { name: "FSM v1.0", color: "#38bdf8" },
          ]}
        />
        <p className="mt-2 text-xs text-slate-500">
          Synthetic demo data produces weak absolute correlations; the dashboard exists to
          track the v0.2 → v1.0 delta as real outcome data accumulates.
        </p>
      </Card>
    </div>
  );
}

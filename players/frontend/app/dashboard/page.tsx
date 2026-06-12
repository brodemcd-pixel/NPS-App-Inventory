"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AnalyticsSummary, api } from "@/lib/api";
import { DailyBarChart } from "@/components/charts";
import { Card, ErrorBox, Loading } from "@/components/ui";

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <Card className="flex-1">
      <div className="text-3xl font-semibold tabular-nums text-slate-100">
        {value.toLocaleString()}
      </div>
      <div className="mt-1 text-xs uppercase tracking-wide text-slate-500">{label}</div>
    </Card>
  );
}

export default function DashboardPage() {
  const [data, setData] = useState<AnalyticsSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [days, setDays] = useState(30);

  useEffect(() => {
    setData(null);
    api
      .analyticsSummary(days)
      .then(setData)
      .catch((e) => setError(String(e)));
  }, [days]);

  if (error) return <ErrorBox message={error} />;

  return (
    <div className="space-y-5">
      <div className="flex items-end justify-between">
        <h1 className="text-xl font-semibold text-slate-100">Usage analytics</h1>
        <div className="flex gap-1.5">
          {[7, 30, 90].map((d) => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={`rounded px-2 py-1 text-xs ${
                days === d
                  ? "bg-sky-600 text-white"
                  : "bg-slate-800 text-slate-300 hover:bg-slate-700"
              }`}
            >
              {d}d
            </button>
          ))}
        </div>
      </div>

      {!data ? (
        <Loading label="Loading analytics…" />
      ) : (
        <>
          <div className="flex gap-4">
            <Stat label="Page views" value={data.page_views} />
            <Stat label="Questions asked" value={data.questions_asked} />
            <Stat label="Exports" value={data.exports} />
            <Stat label="Sessions" value={data.sessions} />
          </div>

          <Card title="Questions per day">
            <DailyBarChart data={data.questions_per_day} />
          </Card>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <Card title="Most-discussed players">
              {data.most_discussed.length === 0 ? (
                <p className="text-xs text-slate-500">No player views in window.</p>
              ) : (
                <ol className="space-y-1.5 text-sm">
                  {data.most_discussed.map((p, i) => (
                    <li key={p.player_id} className="flex justify-between">
                      <span>
                        <span className="mr-2 tabular-nums text-slate-500">{i + 1}.</span>
                        <Link
                          href={`/players/${p.player_id}`}
                          className="text-sky-400 hover:underline"
                        >
                          {p.name}
                        </Link>
                      </span>
                      <span className="tabular-nums text-slate-400">{p.count}</span>
                    </li>
                  ))}
                </ol>
              )}
            </Card>

            <Card title="Common filters">
              {data.common_filters.length === 0 ? (
                <p className="text-xs text-slate-500">No filters applied in window.</p>
              ) : (
                <ol className="space-y-1.5 text-sm">
                  {data.common_filters.map((f) => (
                    <li key={f.filter} className="flex justify-between">
                      <code className="text-xs text-slate-300">{f.filter}</code>
                      <span className="tabular-nums text-slate-400">{f.count}</span>
                    </li>
                  ))}
                </ol>
              )}
            </Card>
          </div>
        </>
      )}
    </div>
  );
}

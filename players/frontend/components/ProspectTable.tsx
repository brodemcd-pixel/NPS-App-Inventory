"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  api,
  exportPlayersXlsxUrl,
  type MetaFilters,
  type Paginated,
  type PlayerQuery,
  type PlayerSummary,
} from "@/lib/api";
import { fmt, formatDraftOutcome, formatHtWt } from "@/lib/format";
import FilterSidebar, { EMPTY_FILTERS, type TableFilters } from "./FilterSidebar";
import WatchlistButton from "./WatchlistButton";
import { Chip, ErrorBox, FlagDots, Loading } from "./ui";

const PAGE_SIZE = 50;

interface SortState {
  key: string;
  desc: boolean;
}

const COLUMNS: { label: string; sortKey?: string; align?: "right" }[] = [
  { label: "Player", sortKey: "name" },
  { label: "Class", sortKey: "class", align: "right" },
  { label: "Pos" },
  { label: "College" },
  { label: "Ht/Wt", align: "right" },
  { label: "40", sortKey: "forty", align: "right" },
  { label: "Grade", sortKey: "grade", align: "right" },
  { label: "Pctl", sortKey: "percentile", align: "right" },
  { label: "NGS", sortKey: "ngs", align: "right" },
  { label: "Draft", sortKey: "pick" },
  { label: "Scheme" },
  { label: "" },
];

function num(v: string): number | undefined {
  if (v.trim() === "") return undefined;
  const n = Number(v);
  return Number.isFinite(n) ? n : undefined;
}

function filtersToQuery(f: TableFilters, sort: SortState, page: number): PlayerQuery {
  return {
    q: f.q.trim() || undefined,
    draft_class: f.draft_class.length ? f.draft_class : undefined,
    round: f.round.length ? f.round : undefined,
    position: f.position.length ? f.position : undefined,
    position_group: f.position_group.length ? f.position_group : undefined,
    team: f.team || undefined,
    college: f.college || undefined,
    conference: f.conference || undefined,
    height_min: num(f.height_min),
    height_max: num(f.height_max),
    weight_min: num(f.weight_min),
    weight_max: num(f.weight_max),
    forty_max: num(f.forty_max),
    arm_min: f.position_group.includes("OL") ? num(f.arm_min) : undefined,
    hand_min: f.position_group.includes("QB") ? num(f.hand_min) : undefined,
    wingspan_min: f.position_group.includes("DB") ? num(f.wingspan_min) : undefined,
    scheme: f.scheme || undefined,
    coaching_tree: f.coaching_tree || undefined,
    role: f.role || undefined,
    red_flag: f.red_flag || undefined,
    green_flag: f.green_flag || undefined,
    trait: f.trait || undefined,
    trait_min: f.trait ? f.trait_min : undefined,
    sort: `${sort.desc ? "-" : ""}${sort.key}`,
    page,
    page_size: PAGE_SIZE,
  };
}

export default function ProspectTable() {
  const [meta, setMeta] = useState<MetaFilters | null>(null);
  const [filters, setFilters] = useState<TableFilters>(EMPTY_FILTERS);
  const [sort, setSort] = useState<SortState>({ key: "grade", desc: true });
  const [page, setPage] = useState(1);
  const [data, setData] = useState<Paginated<PlayerSummary> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.metaFilters().then(setMeta).catch(() => setMeta(null));
  }, []);

  // Reset to page 1 when filters or sort change.
  const filterKey = useMemo(
    () => JSON.stringify({ filters, sort }),
    [filters, sort]
  );
  useEffect(() => {
    setPage(1);
  }, [filterKey]);

  // Debounced fetch.
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    const t = setTimeout(() => {
      api
        .players(filtersToQuery(filters, sort, page))
        .then((res) => {
          if (cancelled) return;
          setData(res);
          setError(null);
          setLoading(false);
        })
        .catch((e) => {
          if (cancelled) return;
          setError(e instanceof Error ? e.message : "Failed to load players");
          setLoading(false);
        });
    }, 300);
    return () => {
      cancelled = true;
      clearTimeout(t);
    };
  }, [filters, sort, page]);

  function toggleSort(key: string) {
    setSort((prev) =>
      prev.key === key
        ? { key, desc: !prev.desc }
        : { key, desc: key !== "name" && key !== "forty" }
    );
  }

  function exportXlsx() {
    const query = filtersToQuery(filters, sort, page);
    delete query.page;
    delete query.page_size;
    window.location.href = exportPlayersXlsxUrl(query);
  }

  const total = data?.total ?? 0;
  const lastPage = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const from = total === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;
  const to = Math.min(page * PAGE_SIZE, total);

  return (
    <div className="flex gap-5">
      <aside className="w-60 shrink-0 rounded-lg border border-ink-700 bg-ink-900 p-3">
        <FilterSidebar meta={meta} filters={filters} onChange={setFilters} />
      </aside>

      <div className="min-w-0 flex-1">
        <div className="mb-3 flex items-center justify-between gap-3">
          <div>
            <h1 className="text-lg font-bold text-slate-100">
              Prospect Board
            </h1>
            <div className="text-xs text-slate-500">
              {loading && !data
                ? "Loading prospects…"
                : `${total} prospects · showing ${from}–${to}`}
            </div>
          </div>
          <button
            onClick={exportXlsx}
            className="rounded border border-ink-600 bg-ink-800 px-3 py-1.5 text-xs font-medium text-slate-200 hover:border-sky-700 hover:text-sky-300"
          >
            ⬇ Export XLSX
          </button>
        </div>

        {error && <ErrorBox message={error} />}

        <div className="overflow-x-auto rounded-lg border border-ink-700">
          <table className="w-full border-collapse text-xs">
            <thead>
              <tr className="bg-ink-850 text-[10px] uppercase tracking-wider text-slate-500">
                {COLUMNS.map((c) => (
                  <th
                    key={c.label || "actions"}
                    className={`whitespace-nowrap px-3 py-2 ${
                      c.align === "right" ? "text-right" : "text-left"
                    } ${c.sortKey ? "cursor-pointer select-none hover:text-sky-300" : ""}`}
                    onClick={c.sortKey ? () => toggleSort(c.sortKey!) : undefined}
                  >
                    {c.label}
                    {c.sortKey && sort.key === c.sortKey && (
                      <span className="ml-1 text-sky-400">
                        {sort.desc ? "▼" : "▲"}
                      </span>
                    )}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading && !data && (
                <tr>
                  <td colSpan={COLUMNS.length}>
                    <Loading label="Loading prospects…" />
                  </td>
                </tr>
              )}
              {data && data.items.length === 0 && (
                <tr>
                  <td
                    colSpan={COLUMNS.length}
                    className="px-3 py-8 text-center text-slate-500"
                  >
                    No prospects match the current filters.
                  </td>
                </tr>
              )}
              {data?.items.map((p) => (
                <tr
                  key={p.id}
                  className={`group border-t border-ink-800 hover:bg-ink-850 ${
                    loading ? "opacity-60" : ""
                  }`}
                >
                  <td className="whitespace-nowrap px-3 py-1.5">
                    <span className="flex items-center gap-2">
                      <Link
                        href={`/players/${p.id}`}
                        className="font-medium text-slate-100 hover:text-sky-300"
                      >
                        {p.name}
                      </Link>
                      <FlagDots red={p.red_flag} green={p.green_flag} />
                    </span>
                  </td>
                  <td className="num px-3 py-1.5 text-right text-slate-400">
                    {p.draft_class}
                  </td>
                  <td className="px-3 py-1.5 text-slate-300">{p.position}</td>
                  <td className="max-w-[140px] truncate px-3 py-1.5 text-slate-400">
                    {p.college}
                  </td>
                  <td className="num whitespace-nowrap px-3 py-1.5 text-right text-slate-300">
                    {formatHtWt(p.height_in, p.weight_lb)}
                  </td>
                  <td className="num px-3 py-1.5 text-right text-slate-300">
                    {fmt(p.forty)}
                  </td>
                  <td className="num px-3 py-1.5 text-right font-semibold text-sky-300">
                    {fmt(p.nfl_grade)}
                  </td>
                  <td className="num px-3 py-1.5 text-right text-slate-400">
                    {fmt(p.class_percentile, 1)}
                  </td>
                  <td className="num px-3 py-1.5 text-right text-slate-400">
                    {fmt(p.ngs_athleticism, 1)}
                  </td>
                  <td className="whitespace-nowrap px-3 py-1.5 text-slate-400">
                    {formatDraftOutcome(p)}
                  </td>
                  <td className="px-3 py-1.5">
                    {p.scheme_archetype ? (
                      <Chip tone="sky">{p.scheme_archetype}</Chip>
                    ) : (
                      <span className="text-slate-600">—</span>
                    )}
                  </td>
                  <td className="px-3 py-1.5 text-right">
                    <span className="opacity-0 transition-opacity group-hover:opacity-100">
                      <WatchlistButton playerId={p.id} />
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mt-3 flex items-center justify-between text-xs text-slate-500">
          <div className="num">
            {total > 0 ? `Showing ${from}–${to} of ${total}` : "0 results"}
          </div>
          <div className="flex items-center gap-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
              className="rounded border border-ink-600 bg-ink-800 px-2.5 py-1 text-slate-300 hover:border-sky-700 disabled:opacity-40"
            >
              ← Prev
            </button>
            <span className="num">
              Page {page} / {lastPage}
            </span>
            <button
              disabled={page >= lastPage}
              onClick={() => setPage((p) => p + 1)}
              className="rounded border border-ink-600 bg-ink-800 px-2.5 py-1 text-slate-300 hover:border-sky-700 disabled:opacity-40"
            >
              Next →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

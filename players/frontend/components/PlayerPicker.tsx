"use client";

import { useEffect, useRef, useState } from "react";
import { api, type PlayerSummary } from "@/lib/api";

export default function PlayerPicker({
  label,
  selectedName,
  onSelect,
}: {
  label: string;
  selectedName: string | null;
  onSelect: (player: PlayerSummary) => void;
}) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<PlayerSummary[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  // Debounced search
  useEffect(() => {
    const q = query.trim();
    if (!q) {
      setResults([]);
      return;
    }
    setLoading(true);
    const t = setTimeout(() => {
      api
        .players({ q, page_size: 10, sort: "-grade" })
        .then((res) => {
          setResults(res.items);
          setLoading(false);
        })
        .catch(() => {
          setResults([]);
          setLoading(false);
        });
    }, 250);
    return () => clearTimeout(t);
  }, [query]);

  useEffect(() => {
    function onDocClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, []);

  return (
    <div ref={ref} className="relative w-full">
      <div className="mb-1 text-[10px] font-semibold uppercase tracking-widest text-slate-500">
        {label}
      </div>
      <input
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        placeholder={selectedName || "Search player…"}
        className="w-full rounded border border-ink-600 bg-ink-850 px-3 py-2 text-sm text-slate-200 placeholder-slate-500 outline-none focus:border-sky-700"
      />
      {open && query.trim() && (
        <div className="absolute z-30 mt-1 max-h-64 w-full overflow-y-auto rounded-lg border border-ink-600 bg-ink-850 shadow-xl shadow-black/50">
          {loading && (
            <div className="px-3 py-2 text-xs text-slate-500">Searching…</div>
          )}
          {!loading && results.length === 0 && (
            <div className="px-3 py-2 text-xs text-slate-500">No matches.</div>
          )}
          {results.map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => {
                onSelect(p);
                setQuery("");
                setOpen(false);
              }}
              className="flex w-full items-center justify-between px-3 py-2 text-left text-xs hover:bg-ink-700"
            >
              <span className="font-medium text-slate-200">{p.name}</span>
              <span className="text-slate-500">
                {p.position} · {p.draft_class} · {p.college}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

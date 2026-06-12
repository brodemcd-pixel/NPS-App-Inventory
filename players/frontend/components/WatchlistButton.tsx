"use client";

import { useEffect, useRef, useState } from "react";
import { api, postEvent, type Watchlist } from "@/lib/api";

export default function WatchlistButton({ playerId }: { playerId: number }) {
  const [open, setOpen] = useState(false);
  const [lists, setLists] = useState<Watchlist[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [newName, setNewName] = useState("");
  const [busy, setBusy] = useState(false);
  const [addedTo, setAddedTo] = useState<number[]>([]);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    setError(null);
    api
      .watchlists()
      .then((res) => setLists(res.items))
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load"));

    function onDocClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, [open]);

  async function addTo(watchlistId: number) {
    setBusy(true);
    setError(null);
    try {
      await api.addWatchlistPlayer(watchlistId, playerId);
      postEvent("watchlist_add", { watchlist_id: watchlistId, player_id: playerId });
      setAddedTo((prev) => [...prev, watchlistId]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to add");
    } finally {
      setBusy(false);
    }
  }

  async function createAndAdd() {
    const name = newName.trim();
    if (!name) return;
    setBusy(true);
    setError(null);
    try {
      const wl = await api.createWatchlist(name);
      await api.addWatchlistPlayer(wl.id, playerId);
      postEvent("watchlist_add", { watchlist_id: wl.id, player_id: playerId });
      setNewName("");
      setAddedTo((prev) => [...prev, wl.id]);
      const res = await api.watchlists();
      setLists(res.items);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div ref={ref} className="relative inline-block">
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          setOpen((v) => !v);
        }}
        title="Add to watchlist"
        className="rounded border border-ink-600 bg-ink-800 px-2 py-0.5 text-[11px] text-slate-300 hover:border-sky-700 hover:text-sky-300"
      >
        + Watchlist
      </button>
      {open && (
        <div className="absolute right-0 top-7 z-30 w-60 rounded-lg border border-ink-600 bg-ink-850 p-2 shadow-xl shadow-black/50">
          <div className="mb-1 px-1 text-[10px] font-semibold uppercase tracking-widest text-slate-500">
            Add to watchlist
          </div>
          {error && (
            <div className="mb-1 px-1 text-[11px] text-red-400">{error}</div>
          )}
          {lists === null && !error && (
            <div className="px-1 py-2 text-[11px] text-slate-500">Loading…</div>
          )}
          {lists && lists.length === 0 && (
            <div className="px-1 py-1 text-[11px] text-slate-500">
              No watchlists yet.
            </div>
          )}
          {lists && (
            <ul className="max-h-44 overflow-y-auto">
              {lists.map((wl) => {
                const already =
                  addedTo.includes(wl.id) ||
                  wl.players.some((p) => p.id === playerId);
                return (
                  <li key={wl.id}>
                    <button
                      type="button"
                      disabled={busy || already}
                      onClick={() => void addTo(wl.id)}
                      className="flex w-full items-center justify-between rounded px-2 py-1 text-left text-xs text-slate-300 hover:bg-ink-700 disabled:opacity-50"
                    >
                      <span className="truncate">{wl.name}</span>
                      {already ? (
                        <span className="text-emerald-400">✓</span>
                      ) : (
                        <span className="num text-slate-600">
                          {wl.players.length}
                        </span>
                      )}
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
          <div className="mt-2 flex gap-1 border-t border-ink-700 pt-2">
            <input
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") void createAndAdd();
              }}
              placeholder="New watchlist…"
              className="min-w-0 flex-1 rounded border border-ink-600 bg-ink-900 px-2 py-1 text-xs text-slate-200 placeholder-slate-600 outline-none focus:border-sky-700"
            />
            <button
              type="button"
              disabled={busy || !newName.trim()}
              onClick={() => void createAndAdd()}
              className="rounded bg-sky-700 px-2 py-1 text-xs text-white hover:bg-sky-600 disabled:opacity-40"
            >
              Create
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

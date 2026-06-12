"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { api, Watchlist } from "@/lib/api";
import { Card, Chip, ErrorBox, FlagDots, Loading } from "@/components/ui";
import { formatHtWt } from "@/lib/format";

export default function WatchlistsPage() {
  const [lists, setLists] = useState<Watchlist[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [newName, setNewName] = useState("");
  const [busy, setBusy] = useState(false);

  const reload = useCallback(() => {
    api
      .watchlists()
      .then((r) => setLists(r.items))
      .catch((e) => setError(String(e)));
  }, []);

  useEffect(reload, [reload]);

  async function create() {
    if (!newName.trim()) return;
    setBusy(true);
    try {
      await api.createWatchlist(newName.trim());
      setNewName("");
      reload();
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function remove(id: number) {
    await api.deleteWatchlist(id).catch((e) => setError(String(e)));
    reload();
  }

  async function removePlayer(watchlistId: number, playerId: number) {
    await api
      .removeWatchlistPlayer(watchlistId, playerId)
      .catch((e) => setError(String(e)));
    reload();
  }

  return (
    <div className="space-y-5">
      <div className="flex items-end justify-between">
        <h1 className="text-xl font-semibold text-slate-100">Watchlists</h1>
        <div className="flex gap-2">
          <input
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && create()}
            placeholder="New watchlist name…"
            className="rounded border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm text-slate-200 placeholder:text-slate-500 focus:border-sky-500 focus:outline-none"
          />
          <button
            onClick={create}
            disabled={busy || !newName.trim()}
            className="rounded bg-sky-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-sky-500 disabled:opacity-40"
          >
            Create
          </button>
        </div>
      </div>

      {error && <ErrorBox message={error} />}
      {lists === null ? (
        <Loading label="Loading watchlists…" />
      ) : lists.length === 0 ? (
        <Card>
          <p className="text-sm text-slate-400">
            No watchlists yet. Create one above, then add players from the{" "}
            <Link href="/" className="text-sky-400 hover:underline">
              prospect table
            </Link>{" "}
            or a player profile.
          </p>
        </Card>
      ) : (
        lists.map((wl) => (
          <Card
            key={wl.id}
            title={
              <div className="flex items-center justify-between">
                <span>
                  {wl.name}{" "}
                  <span className="ml-2 text-xs font-normal text-slate-500">
                    {wl.players.length} player{wl.players.length === 1 ? "" : "s"}
                  </span>
                </span>
                <button
                  onClick={() => remove(wl.id)}
                  className="text-xs text-rose-400 hover:text-rose-300"
                >
                  Delete list
                </button>
              </div>
            }
          >
            {wl.players.length === 0 ? (
              <p className="text-xs text-slate-500">Empty list.</p>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-800 text-left text-xs uppercase tracking-wide text-slate-500">
                    <th className="py-1.5 pr-3">Player</th>
                    <th className="px-3 py-1.5">Class</th>
                    <th className="px-3 py-1.5">Pos</th>
                    <th className="px-3 py-1.5">College</th>
                    <th className="px-3 py-1.5">Ht/Wt</th>
                    <th className="px-3 py-1.5">Grade</th>
                    <th className="px-3 py-1.5">Scheme</th>
                    <th className="px-3 py-1.5">Note</th>
                    <th className="px-3 py-1.5"></th>
                  </tr>
                </thead>
                <tbody>
                  {wl.players.map((p) => (
                    <tr
                      key={p.id}
                      className="border-b border-slate-800/60 hover:bg-slate-800/40"
                    >
                      <td className="py-1.5 pr-3">
                        <Link
                          href={`/players/${p.id}`}
                          className="font-medium text-sky-400 hover:underline"
                        >
                          {p.name}
                        </Link>{" "}
                        <FlagDots red={p.red_flag} green={p.green_flag} />
                      </td>
                      <td className="px-3 py-1.5 tabular-nums">{p.draft_class}</td>
                      <td className="px-3 py-1.5">{p.position}</td>
                      <td className="px-3 py-1.5">{p.college}</td>
                      <td className="px-3 py-1.5 tabular-nums">
                        {formatHtWt(p.height_in, p.weight_lb)}
                      </td>
                      <td className="px-3 py-1.5 tabular-nums">
                        {p.nfl_grade?.toFixed(2) ?? "—"}
                      </td>
                      <td className="px-3 py-1.5">
                        {p.scheme_archetype ? <Chip>{p.scheme_archetype}</Chip> : "—"}
                      </td>
                      <td className="px-3 py-1.5 text-xs text-slate-400">
                        {p.note || "—"}
                      </td>
                      <td className="px-3 py-1.5 text-right">
                        <button
                          onClick={() => removePlayer(wl.id, p.id)}
                          className="text-xs text-slate-500 hover:text-rose-400"
                          title="Remove from list"
                        >
                          ✕
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </Card>
        ))
      )}
    </div>
  );
}

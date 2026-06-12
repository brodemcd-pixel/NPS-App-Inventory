"use client";

import { useState } from "react";
import { api, type ScoutComment } from "@/lib/api";
import { fmt, formatDate, traitLabel } from "@/lib/format";
import { Card, Chip } from "./ui";

interface TagDraft {
  trait: string;
  score: number;
}

export default function CommentsSection({
  playerId,
  initialComments,
  traitOptions,
}: {
  playerId: number;
  initialComments: ScoutComment[];
  traitOptions: string[];
}) {
  const [comments, setComments] = useState<ScoutComment[]>(initialComments);
  const [body, setBody] = useState("");
  const [tags, setTags] = useState<TagDraft[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function addTag() {
    const used = new Set(tags.map((t) => t.trait));
    const next = traitOptions.find((t) => !used.has(t)) || traitOptions[0];
    if (!next) return;
    setTags((prev) => [...prev, { trait: next, score: 0.7 }]);
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const text = body.trim();
    if (!text || busy) return;
    setBusy(true);
    setError(null);
    try {
      const created = await api.postComment(
        playerId,
        text,
        tags.length ? tags : undefined
      );
      setComments((prev) => [created, ...prev]);
      setBody("");
      setTags([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to post comment");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card title={`Scout Comments (${comments.length})`}>
      <form onSubmit={submit} className="mb-4">
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          rows={3}
          placeholder="Add a scouting note…"
          className="w-full resize-y rounded border border-ink-600 bg-ink-850 px-3 py-2 text-xs text-slate-200 placeholder-slate-600 outline-none focus:border-sky-700"
        />

        {tags.map((tag, i) => (
          <div key={i} className="mt-2 flex items-center gap-2">
            <select
              value={tag.trait}
              onChange={(e) =>
                setTags((prev) =>
                  prev.map((t, j) => (j === i ? { ...t, trait: e.target.value } : t))
                )
              }
              className="rounded border border-ink-600 bg-ink-850 px-2 py-1 text-xs text-slate-200 outline-none focus:border-sky-700"
            >
              {traitOptions.map((t) => (
                <option key={t} value={t}>
                  {traitLabel(t)}
                </option>
              ))}
            </select>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={tag.score}
              onChange={(e) =>
                setTags((prev) =>
                  prev.map((t, j) =>
                    j === i ? { ...t, score: Number(e.target.value) } : t
                  )
                )
              }
              className="flex-1"
              aria-label={`Score for ${tag.trait}`}
            />
            <span className="num w-9 text-right text-xs text-sky-300">
              {tag.score.toFixed(2)}
            </span>
            <button
              type="button"
              onClick={() => setTags((prev) => prev.filter((_, j) => j !== i))}
              className="rounded px-1.5 text-slate-500 hover:text-red-400"
              aria-label="Remove tag"
            >
              ✕
            </button>
          </div>
        ))}

        <div className="mt-2 flex items-center justify-between">
          <button
            type="button"
            onClick={addTag}
            disabled={traitOptions.length === 0}
            className="text-[11px] text-slate-400 hover:text-sky-300 disabled:opacity-40"
          >
            + Tag mental trait
          </button>
          <button
            type="submit"
            disabled={busy || !body.trim()}
            className="rounded bg-sky-700 px-3 py-1.5 text-xs font-medium text-white hover:bg-sky-600 disabled:opacity-40"
          >
            {busy ? "Posting…" : "Post comment"}
          </button>
        </div>
        {error && <div className="mt-2 text-xs text-red-400">{error}</div>}
      </form>

      {comments.length === 0 ? (
        <div className="text-xs text-slate-500">No comments yet.</div>
      ) : (
        <ul className="space-y-3">
          {comments.map((c) => (
            <li key={c.id} className="rounded border border-ink-700 bg-ink-850 p-3">
              <div className="mb-1 flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-200">
                  {c.author_name}
                </span>
                <span className="text-[10px] text-slate-500">
                  {formatDate(c.created_at)}
                </span>
              </div>
              <p className="whitespace-pre-wrap text-xs leading-relaxed text-slate-300">
                {c.body}
              </p>
              {c.traits && c.traits.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {c.traits.map((t, i) => (
                    <Chip key={i} tone="amber">
                      {traitLabel(t.trait)} {fmt(t.score)}
                    </Chip>
                  ))}
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

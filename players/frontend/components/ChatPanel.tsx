"use client";

import { useEffect, useRef, useState } from "react";
import { chatRequest, type ChatSource, type ChatTurn } from "@/lib/api";
import { readSSE, parseData } from "@/lib/sse";
import Markdown from "./Markdown";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  tools: string[];
  sources: ChatSource[] | null;
  error: string | null;
}

const HISTORY_TURNS = 10;

export default function ChatPanel() {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [streaming, setStreaming] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, open]);

  function patchLast(patch: (m: ChatMessage) => ChatMessage) {
    setMessages((prev) => {
      if (prev.length === 0) return prev;
      const next = prev.slice();
      next[next.length - 1] = patch(next[next.length - 1]);
      return next;
    });
  }

  async function send() {
    const message = input.trim();
    if (!message || streaming) return;

    // History = last ~10 turns of completed conversation, before this message.
    const history: ChatTurn[] = messages
      .filter((m) => m.content && !m.error)
      .map((m) => ({ role: m.role, content: m.content }))
      .slice(-HISTORY_TURNS);

    setInput("");
    setMessages((prev) => [
      ...prev,
      { role: "user", content: message, tools: [], sources: null, error: null },
      { role: "assistant", content: "", tools: [], sources: null, error: null },
    ]);
    setStreaming(true);

    try {
      const res = await chatRequest(message, history);
      if (!res.body) throw new Error("No response stream");
      for await (const msg of readSSE(res.body)) {
        if (msg.event === "tool") {
          const data = parseData<{ name: string }>(msg);
          if (data?.name) {
            patchLast((m) => ({ ...m, tools: [...m.tools, data.name] }));
          }
        } else if (msg.event === "text") {
          const data = parseData<{ delta: string }>(msg);
          if (data?.delta) {
            patchLast((m) => ({ ...m, content: m.content + data.delta }));
          }
        } else if (msg.event === "sources") {
          const data = parseData<{ sources: ChatSource[] }>(msg);
          if (data?.sources) {
            patchLast((m) => ({ ...m, sources: data.sources }));
          }
        } else if (msg.event === "error") {
          const data = parseData<{ detail: string }>(msg);
          patchLast((m) => ({
            ...m,
            error: data?.detail || "Assistant error",
          }));
        } else if (msg.event === "done") {
          break;
        }
      }
    } catch (err) {
      patchLast((m) => ({
        ...m,
        error: err instanceof Error ? err.message : "Chat request failed",
      }));
    } finally {
      setStreaming(false);
    }
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void send();
    }
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="fixed bottom-5 right-5 z-50 flex items-center gap-2 rounded-full border border-sky-700 bg-ink-800 px-4 py-2.5 text-sm font-medium text-sky-300 shadow-lg shadow-black/40 hover:bg-ink-700"
        aria-label="Open scouting assistant"
      >
        <span className="inline-block h-2 w-2 rounded-full bg-sky-400" />
        Assistant
      </button>
    );
  }

  return (
    <aside className="fixed inset-y-0 right-0 z-50 flex w-full max-w-[400px] flex-col border-l border-ink-700 bg-ink-900 shadow-2xl shadow-black/60">
      <div className="flex items-center justify-between border-b border-ink-700 px-4 py-3">
        <div>
          <div className="text-sm font-semibold text-slate-100">
            Scouting Assistant
          </div>
          <div className="text-[11px] text-slate-500">
            Tool-grounded answers with sources
          </div>
        </div>
        <button
          onClick={() => setOpen(false)}
          className="rounded px-2 py-1 text-slate-400 hover:bg-ink-700 hover:text-slate-200"
          aria-label="Collapse assistant panel"
        >
          ⇥
        </button>
      </div>

      <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto px-4 py-3">
        {messages.length === 0 && (
          <div className="rounded border border-ink-700 bg-ink-850 p-3 text-xs leading-relaxed text-slate-400">
            Ask about prospects, e.g. “Who are the top WRs in the 2025 class
            under a 4.45 forty?” or “Compare the mental profiles of two QBs.”
          </div>
        )}
        {messages.map((m, i) =>
          m.role === "user" ? (
            <div key={i} className="flex justify-end">
              <div className="max-w-[85%] rounded-lg bg-sky-900/50 px-3 py-2 text-sm text-sky-100">
                {m.content}
              </div>
            </div>
          ) : (
            <div key={i} className="flex justify-start">
              <div className="max-w-[95%] space-y-2">
                {m.tools.length > 0 && (
                  <div className="space-y-0.5">
                    {m.tools.map((t, j) => (
                      <div
                        key={j}
                        className="font-mono text-[11px] text-slate-500"
                      >
                        ⚙ {t}…
                      </div>
                    ))}
                  </div>
                )}
                {(m.content || (!m.error && streaming && i === messages.length - 1)) && (
                  <div className="rounded-lg bg-ink-800 px-3 py-2 text-sm leading-relaxed text-slate-200">
                    {m.content ? (
                      <Markdown text={m.content} />
                    ) : (
                      <span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-slate-600 border-t-sky-400" />
                    )}
                  </div>
                )}
                {m.error && (
                  <div className="rounded border border-red-800/60 bg-red-950/40 px-3 py-2 text-xs text-red-300">
                    {m.error}
                  </div>
                )}
                {m.sources && m.sources.length > 0 && (
                  <div className="rounded border border-ink-600 bg-ink-850 px-3 py-2">
                    <div className="mb-1 text-[10px] font-semibold uppercase tracking-widest text-slate-500">
                      Sources
                    </div>
                    <ul className="space-y-1">
                      {m.sources.map((s, j) => (
                        <li key={j} className="text-[11px] text-slate-400">
                          <span className="font-mono text-sky-400">
                            {s.operation}
                          </span>{" "}
                          — {s.detail}{" "}
                          <span className="num text-slate-500">
                            ({s.count})
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )
        )}
      </div>

      <div className="border-t border-ink-700 p-3">
        <div className="flex items-end gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            rows={2}
            placeholder="Ask the assistant…"
            className="flex-1 resize-none rounded border border-ink-600 bg-ink-850 px-3 py-2 text-sm text-slate-200 placeholder-slate-600 outline-none focus:border-sky-700"
          />
          <button
            onClick={() => void send()}
            disabled={streaming || !input.trim()}
            className="rounded bg-sky-700 px-3 py-2 text-sm font-medium text-white hover:bg-sky-600 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {streaming ? "…" : "Send"}
          </button>
        </div>
      </div>
    </aside>
  );
}

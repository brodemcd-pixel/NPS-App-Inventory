"use client";

import Link from "next/link";
import type { ReactNode } from "react";

// Markdown-lite: **bold**, [text](url) links (internal links via next/link),
// and line breaks. Anything else renders as plain text.

const TOKEN_RE = /\*\*([^*]+)\*\*|\[([^\]]+)\]\(([^)\s]+)\)/g;

function renderLine(line: string, keyBase: string): ReactNode[] {
  const out: ReactNode[] = [];
  let last = 0;
  let i = 0;
  TOKEN_RE.lastIndex = 0;
  for (;;) {
    const m = TOKEN_RE.exec(line);
    if (!m) break;
    if (m.index > last) out.push(line.slice(last, m.index));
    if (m[1] !== undefined) {
      out.push(
        <strong key={`${keyBase}-b${i}`} className="font-semibold text-slate-100">
          {m[1]}
        </strong>
      );
    } else {
      const text = m[2];
      const href = m[3];
      if (href.startsWith("/")) {
        out.push(
          <Link
            key={`${keyBase}-l${i}`}
            href={href}
            className="text-sky-400 underline decoration-sky-700 underline-offset-2 hover:text-sky-300"
          >
            {text}
          </Link>
        );
      } else {
        out.push(
          <a
            key={`${keyBase}-l${i}`}
            href={href}
            target="_blank"
            rel="noreferrer"
            className="text-sky-400 underline decoration-sky-700 underline-offset-2 hover:text-sky-300"
          >
            {text}
          </a>
        );
      }
    }
    last = m.index + m[0].length;
    i += 1;
  }
  if (last < line.length) out.push(line.slice(last));
  return out;
}

export default function Markdown({ text }: { text: string }) {
  const lines = text.split("\n");
  return (
    <>
      {lines.map((line, i) => (
        <span key={i}>
          {i > 0 && <br />}
          {renderLine(line, `ln${i}`)}
        </span>
      ))}
    </>
  );
}

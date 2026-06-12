"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Prospects" },
  { href: "/compare", label: "Compare" },
  { href: "/watchlists", label: "Watchlists" },
  { href: "/map", label: "Map" },
  { href: "/dashboard", label: "Usage" },
  { href: "/accuracy", label: "Model Accuracy" },
];

export default function NavBar() {
  const pathname = usePathname();
  return (
    <header className="sticky top-0 z-40 border-b border-ink-700 bg-ink-900/95 backdrop-blur">
      <div className="mx-auto flex h-12 max-w-[1600px] items-center gap-6 px-4">
        <Link href="/" className="flex items-center gap-2">
          <span className="inline-flex h-6 w-6 items-center justify-center rounded bg-sky-600 text-xs font-black text-white">
            P
          </span>
          <span className="text-sm font-bold uppercase tracking-[0.2em] text-slate-100">
            Players
          </span>
        </Link>
        <nav className="flex items-center gap-1 text-sm">
          {LINKS.map((l) => {
            const active =
              l.href === "/"
                ? pathname === "/" || pathname.startsWith("/players")
                : pathname.startsWith(l.href);
            return (
              <Link
                key={l.href}
                href={l.href}
                className={`rounded px-3 py-1.5 transition-colors ${
                  active
                    ? "bg-ink-700 text-sky-300"
                    : "text-slate-400 hover:bg-ink-800 hover:text-slate-200"
                }`}
              >
                {l.label}
              </Link>
            );
          })}
        </nav>
        <div className="ml-auto text-[11px] uppercase tracking-widest text-slate-600">
          Draft Intelligence · 2022–2026
        </div>
      </div>
    </header>
  );
}

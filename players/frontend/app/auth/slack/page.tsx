"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { Card } from "@/components/ui";

function SlackAuthInner() {
  const params = useSearchParams();
  const router = useRouter();
  const [status, setStatus] = useState<"working" | "ok" | "failed">("working");

  useEffect(() => {
    const token = params.get("token");
    const next = params.get("next") || "/";
    if (!token) {
      setStatus("failed");
      return;
    }
    api
      .slackExchange(token)
      .then((r) => {
        window.localStorage.setItem("players_user_id", r.user_id);
        if (r.name) window.localStorage.setItem("players_user_name", r.name);
        setStatus("ok");
        router.replace(next.startsWith("/") ? next : "/");
      })
      .catch(() => setStatus("failed"));
  }, [params, router]);

  return (
    <div className="mx-auto mt-20 max-w-md">
      <Card title="Slack sign-in">
        {status === "working" && (
          <p className="text-sm text-slate-400">Verifying your Slack identity…</p>
        )}
        {status === "ok" && (
          <p className="text-sm text-emerald-400">Signed in — redirecting…</p>
        )}
        {status === "failed" && (
          <p className="text-sm text-rose-400">
            This sign-in link is invalid or has expired (links are valid for 10 minutes).
            Ask the Slack bot for a fresh link.
          </p>
        )}
      </Card>
    </div>
  );
}

export default function SlackAuthPage() {
  return (
    <Suspense>
      <SlackAuthInner />
    </Suspense>
  );
}

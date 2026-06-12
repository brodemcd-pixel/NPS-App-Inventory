"use client";

import { useEffect } from "react";
import { usePathname } from "next/navigation";
import { postEvent } from "@/lib/api";

export default function PageViewTracker() {
  const pathname = usePathname();
  useEffect(() => {
    if (pathname) postEvent("page_view", { path: pathname });
  }, [pathname]);
  return null;
}

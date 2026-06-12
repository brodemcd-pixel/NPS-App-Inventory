import { Suspense } from "react";
import CompareView from "@/components/CompareView";

export default function ComparePage() {
  return (
    <Suspense>
      <CompareView />
    </Suspense>
  );
}

"use client";

import { useEffect, useState } from "react";

import { apiGet, ControlTestResult } from "@/lib/api";

export function ControlTestHistory({ controlId }: { controlId: number }) {
  const [results, setResults] = useState<ControlTestResult[]>([]);

  useEffect(() => {
    apiGet<ControlTestResult[]>(`/api/v1/controls/${controlId}/test-history`).then(setResults).catch(() => {});
  }, [controlId]);

  return (
    <div className="sm:col-span-2">
      <p className="mb-1 text-xs font-medium uppercase tracking-wide text-zinc-500">Test History</p>
      <ul className="flex flex-col gap-1">
        {results.map((r) => (
          <li key={r.id} className="text-sm">
            <span className={r.result === "Pass" ? "text-green-600" : "text-red-600"}>{r.result}</span>
            {" — "}
            {new Date(r.tested_at).toLocaleString()}
            {r.detail && <span className="text-zinc-500"> ({r.detail})</span>}
          </li>
        ))}
        {results.length === 0 && <li className="text-sm text-zinc-400">No tests run yet.</li>}
      </ul>
    </div>
  );
}

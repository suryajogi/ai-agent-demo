"use client";

import { useEffect, useState } from "react";

import { apiGet, DashboardStats } from "@/lib/api";

const METRICS: {
  key: keyof DashboardStats;
  label: string;
  accent: string;
  icon: string;
  note: (value: number) => string;
}[] = [
  {
    key: "totalRisks",
    label: "Total Profiled Risks",
    accent: "border-red-600",
    icon: "📊",
    note: (value) => `${value} entries under active risk management`,
  },
  {
    key: "openIssues",
    label: "Open GRC Issues",
    accent: "border-orange-500",
    icon: "⚠️",
    note: (value) => (value > 0 ? "Requires remediation action" : "No open issues"),
  },
  {
    key: "activeControls",
    label: "Controls Under Monitor",
    accent: "border-green-600",
    icon: "🛡️",
    note: () => "Mitigation tracking stable",
  },
  {
    key: "pendingAssessments",
    label: "Pending Assessments",
    accent: "border-blue-500",
    icon: "📝",
    note: (value) => (value > 0 ? "Assigned to system assessors" : "All assessments complete"),
  },
];

export function MetricBanner() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiGet<DashboardStats>("/api/v1/dashboard/stats")
      .then((data) => {
        setStats(data);
        setError(null);
      })
      .catch((err: Error) => {
        setError(err.message);
      });
  }, []);

  if (error) {
    return (
      <div className="rounded-2xl border border-red-200 bg-red-50 px-6 py-4 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
        Could not reach the GRC metrics API — start the backend with{" "}
        <code className="font-mono">uvicorn main:app --reload --port 8000</code> from{" "}
        <code className="font-mono">backend/</code>.
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {METRICS.map(({ key, label, accent, icon, note }) => (
        <div
          key={key}
          className={`rounded-lg border-l-4 ${accent} bg-white p-5 text-left shadow-sm transition hover:shadow dark:bg-zinc-950`}
        >
          <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500">{label}</p>
          <p className="mt-1 text-3xl font-bold text-zinc-800 tabular-nums dark:text-zinc-100">
            {stats ? (
              stats[key]
            ) : (
              <span className="animate-pulse text-zinc-300 dark:text-zinc-700">–</span>
            )}
          </p>
          <p className="mt-2 text-xs font-medium text-zinc-500 dark:text-zinc-400">
            {icon} {stats ? note(stats[key]) : "Loading…"}
          </p>
        </div>
      ))}
    </div>
  );
}

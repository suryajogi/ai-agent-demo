"use client";

import Link from "next/link";

import { MetricBanner } from "./MetricBanner";

export default function Home() {
  return (
    <div className="flex min-h-full flex-1 flex-col items-center justify-center px-6 py-16">
      <div className="w-full max-w-2xl text-center">
        <p className="text-sm font-medium uppercase tracking-wide text-zinc-500">
          ServiceNow GRC Replication
        </p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight">Risk Management Suite</h1>

        <div className="mt-6">
          <MetricBanner />
        </div>

        <div className="mt-10 grid gap-4 sm:grid-cols-2">
          <Link
            href="/workspace"
            className="rounded-2xl border border-zinc-200 bg-white p-6 text-left shadow-sm transition hover:border-zinc-400 dark:border-zinc-800 dark:bg-zinc-950 dark:hover:border-zinc-600"
          >
            <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">Interface A</p>
            <h2 className="mt-1 text-lg font-semibold">GRC Workspace Dashboard</h2>
            <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
              Create risks, controls, issues, departments, and launch assessments.
            </p>
          </Link>
          <Link
            href="/assessor"
            className="rounded-2xl border border-zinc-200 bg-white p-6 text-left shadow-sm transition hover:border-zinc-400 dark:border-zinc-800 dark:bg-zinc-950 dark:hover:border-zinc-600"
          >
            <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">Interface B</p>
            <h2 className="mt-1 text-lg font-semibold">Assessor Portal</h2>
            <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
              Answer your assigned questionnaire and compute a risk score.
            </p>
          </Link>
        </div>
      </div>
    </div>
  );
}

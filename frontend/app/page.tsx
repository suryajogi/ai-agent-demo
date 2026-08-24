"use client";

import { useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function Home() {
  const [message, setMessage] = useState("Connecting to FastAPI…");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/hello`)
      .then(async (res) => {
        if (!res.ok) {
          throw new Error(`Backend responded with ${res.status}`);
        }
        return res.json() as Promise<{ message: string }>;
      })
      .then((data) => {
        setMessage(data.message);
        setError(null);
      })
      .catch((err: Error) => {
        setError(err.message);
        setMessage("Could not reach the FastAPI backend.");
      });
  }, []);

  return (
    <div className="flex min-h-full flex-1 flex-col items-center justify-center px-6">
      <main className="w-full max-w-md rounded-2xl border border-zinc-200 bg-white p-8 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
        <p className="text-sm font-medium uppercase tracking-wide text-zinc-500">
          Next.js → FastAPI
        </p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight">{message}</h1>
        {error ? (
          <p className="mt-3 text-sm text-red-600 dark:text-red-400">
            {error}. Start the API with{" "}
            <code className="font-mono">
              uvicorn main:app --reload --port 8000
            </code>{" "}
            from <code className="font-mono">backend/</code>.
          </p>
        ) : (
          <p className="mt-3 text-sm text-zinc-600 dark:text-zinc-400">
            Fetched from <code className="font-mono">{API_URL}/hello</code>
          </p>
        )}
      </main>
    </div>
  );
}

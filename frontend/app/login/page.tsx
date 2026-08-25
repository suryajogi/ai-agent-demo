"use client";

import { FormEvent, Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { login } from "@/lib/api";
import { Field, inputClass, SubmitButton } from "../workspace/ui";

function LoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await login(username, password);
      router.push(params.get("next") ?? "/workspace");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-full flex-1 flex-col items-center justify-center px-6 py-16">
      <div className="w-full max-w-sm">
        <p className="text-center text-xs font-medium uppercase tracking-wide text-zinc-500">
          ServiceNow GRC Replication
        </p>
        <h1 className="mt-1 text-center text-2xl font-semibold tracking-tight">Sign in</h1>
        <p className="mt-2 text-center text-sm text-zinc-600 dark:text-zinc-400">
          Reads stay open without an account — sign in to create, edit, or delete records.
        </p>

        <form
          onSubmit={handleSubmit}
          className="mt-8 grid gap-3 rounded-xl border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-950"
        >
          <Field label="Username">
            <input
              required
              autoFocus
              className={inputClass}
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g. user.001"
            />
          </Field>
          <Field label="Password">
            <input
              required
              type="password"
              className={inputClass}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </Field>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <SubmitButton disabled={submitting}>{submitting ? "Signing in…" : "Sign in"}</SubmitButton>
          <p className="text-xs text-zinc-500">
            Demo accounts: any seeded <code>user.NNN</code>, password <code>changeme123</code>.
          </p>
        </form>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  );
}

"use client";

import { FormEvent, useState } from "react";

import { apiPost, Department } from "@/lib/api";

import { Field, inputClass, SubmitButton } from "./ui";

export function DepartmentForm({ onCreated }: { onCreated: (d: Department) => void }) {
  const [name, setName] = useState("");
  const [managerId, setManagerId] = useState("");
  const [costCenter, setCostCenter] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const created = await apiPost<Department>("/api/v1/departments", {
        name,
        manager_id: managerId || null,
        cost_center: costCenter || null,
      });
      onCreated(created);
      setName("");
      setManagerId("");
      setCostCenter("");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="grid gap-3 sm:grid-cols-3">
      <Field label="Name">
        <input
          required
          className={inputClass}
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
      </Field>
      <Field label="Manager ID">
        <input
          className={inputClass}
          value={managerId}
          onChange={(e) => setManagerId(e.target.value)}
          placeholder="e.g. mgr.chen"
        />
      </Field>
      <Field label="Cost Center">
        <input
          className={inputClass}
          value={costCenter}
          onChange={(e) => setCostCenter(e.target.value)}
          placeholder="e.g. CC-100"
        />
      </Field>
      {error && <p className="sm:col-span-3 text-sm text-red-600">{error}</p>}
      <div className="sm:col-span-3">
        <SubmitButton disabled={submitting}>
          {submitting ? "Creating…" : "Create Department"}
        </SubmitButton>
      </div>
    </form>
  );
}

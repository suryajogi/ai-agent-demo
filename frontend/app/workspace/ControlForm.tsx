"use client";

import { FormEvent, useState } from "react";

import { apiPost, CONTROL_STATUSES, Control, Entity, Risk } from "@/lib/api";

import { Field, inputClass, SubmitButton } from "./ui";

export function ControlForm({
  entities,
  risks,
  onCreated,
}: {
  entities: Entity[];
  risks: Risk[];
  onCreated: (c: Control) => void;
}) {
  const [form, setForm] = useState({
    name: "",
    description: "",
    status: "Draft",
    entity_id: "",
    risk_id: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const created = await apiPost<Control>("/api/v1/controls", {
        name: form.name,
        description: form.description || null,
        status: form.status,
        entity_id: form.entity_id ? Number(form.entity_id) : null,
        risk_id: form.risk_id ? Number(form.risk_id) : null,
      });
      onCreated(created);
      setForm((f) => ({ ...f, name: "", description: "" }));
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="grid gap-3 sm:grid-cols-2">
      <Field label="Name">
        <input
          required
          className={inputClass}
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
        />
      </Field>
      <Field label="Status">
        <select
          className={inputClass}
          value={form.status}
          onChange={(e) => setForm({ ...form, status: e.target.value })}
        >
          {CONTROL_STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </Field>
      <Field label="Entity">
        <select
          className={inputClass}
          value={form.entity_id}
          onChange={(e) => setForm({ ...form, entity_id: e.target.value })}
        >
          <option value="">— none —</option>
          {entities.map((ent) => (
            <option key={ent.id} value={ent.id}>
              {ent.name}
            </option>
          ))}
        </select>
      </Field>
      <Field label="Mitigates Risk">
        <select
          className={inputClass}
          value={form.risk_id}
          onChange={(e) => setForm({ ...form, risk_id: e.target.value })}
        >
          <option value="">— none —</option>
          {risks.map((r) => (
            <option key={r.id} value={r.id}>
              {r.name}
            </option>
          ))}
        </select>
      </Field>
      <div className="sm:col-span-2">
        <Field label="Description">
          <textarea
            className={inputClass}
            rows={2}
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
          />
        </Field>
      </div>
      {error && <p className="sm:col-span-2 text-sm text-red-600">{error}</p>}
      <div className="sm:col-span-2">
        <SubmitButton disabled={submitting}>
          {submitting ? "Creating…" : "Create Control"}
        </SubmitButton>
      </div>
    </form>
  );
}

"use client";

import { FormEvent, useState } from "react";

import { apiPost, Entity, Risk, RISK_STATES } from "@/lib/api";

import { Field, inputClass, SubmitButton } from "./ui";

export function RiskForm({
  entities,
  onCreated,
}: {
  entities: Entity[];
  onCreated: (r: Risk) => void;
}) {
  const [form, setForm] = useState({
    name: "",
    description: "",
    entity_id: "",
    assigned_to: "",
    state: "Draft",
    inherent_likelihood: "3",
    inherent_impact: "3",
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const created = await apiPost<Risk>("/api/v1/risks", {
        name: form.name,
        description: form.description || null,
        entity_id: form.entity_id ? Number(form.entity_id) : null,
        assigned_to: form.assigned_to || null,
        state: form.state,
        inherent_likelihood: Number(form.inherent_likelihood),
        inherent_impact: Number(form.inherent_impact),
      });
      onCreated(created);
      setForm((f) => ({ ...f, name: "", description: "", assigned_to: "" }));
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
      <Field label="Assigned To">
        <input
          className={inputClass}
          value={form.assigned_to}
          onChange={(e) => setForm({ ...form, assigned_to: e.target.value })}
          placeholder="e.g. j.chen"
        />
      </Field>
      <Field label="State">
        <select
          className={inputClass}
          value={form.state}
          onChange={(e) => setForm({ ...form, state: e.target.value })}
        >
          {RISK_STATES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </Field>
      <Field label="Inherent Likelihood (1-5)">
        <input
          type="number"
          min={1}
          max={5}
          className={inputClass}
          value={form.inherent_likelihood}
          onChange={(e) => setForm({ ...form, inherent_likelihood: e.target.value })}
        />
      </Field>
      <Field label="Inherent Impact (1-5)">
        <input
          type="number"
          min={1}
          max={5}
          className={inputClass}
          value={form.inherent_impact}
          onChange={(e) => setForm({ ...form, inherent_impact: e.target.value })}
        />
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
        <SubmitButton disabled={submitting}>{submitting ? "Creating…" : "Create Risk"}</SubmitButton>
      </div>
    </form>
  );
}

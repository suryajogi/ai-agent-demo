"use client";

import { FormEvent, useState } from "react";

import { apiPost, apiPut, Entity, Risk, RISK_STATES } from "@/lib/api";

import { Field, inputClass, SubmitButton } from "./ui";

export function RiskForm({
  entities,
  record,
  onSaved,
  onCancel,
}: {
  entities: Entity[];
  record?: Risk;
  onSaved: (r: Risk) => void;
  onCancel?: () => void;
}) {
  const isEdit = !!record;
  const [form, setForm] = useState({
    name: record?.name ?? "",
    description: record?.description ?? "",
    entity_id: record?.entity_id != null ? String(record.entity_id) : "",
    assigned_to: record?.assigned_to ?? "",
    state: record?.state ?? "Draft",
    inherent_likelihood: record?.inherent_likelihood != null ? String(record.inherent_likelihood) : "3",
    inherent_impact: record?.inherent_impact != null ? String(record.inherent_impact) : "3",
    residual_likelihood: record?.residual_likelihood != null ? String(record.residual_likelihood) : "",
    residual_impact: record?.residual_impact != null ? String(record.residual_impact) : "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const payload = {
        name: form.name,
        description: form.description || null,
        entity_id: form.entity_id ? Number(form.entity_id) : null,
        assigned_to: form.assigned_to || null,
        state: form.state,
        inherent_likelihood: Number(form.inherent_likelihood),
        inherent_impact: Number(form.inherent_impact),
        residual_likelihood: form.residual_likelihood ? Number(form.residual_likelihood) : null,
        residual_impact: form.residual_impact ? Number(form.residual_impact) : null,
      };
      const saved = isEdit
        ? await apiPut<Risk>(`/api/v1/risks/${record!.id}`, payload)
        : await apiPost<Risk>("/api/v1/risks", payload);
      onSaved(saved);
      if (!isEdit) setForm((f) => ({ ...f, name: "", description: "", assigned_to: "" }));
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
      {isEdit && (
        <>
          <Field label="Residual Likelihood (1-5)">
            <input
              type="number"
              min={1}
              max={5}
              className={inputClass}
              value={form.residual_likelihood}
              onChange={(e) => setForm({ ...form, residual_likelihood: e.target.value })}
            />
          </Field>
          <Field label="Residual Impact (1-5)">
            <input
              type="number"
              min={1}
              max={5}
              className={inputClass}
              value={form.residual_impact}
              onChange={(e) => setForm({ ...form, residual_impact: e.target.value })}
            />
          </Field>
        </>
      )}
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
      <div className="flex items-center gap-3 sm:col-span-2">
        <SubmitButton disabled={submitting}>
          {submitting ? (isEdit ? "Saving…" : "Creating…") : isEdit ? "Save Changes" : "Create Risk"}
        </SubmitButton>
        {onCancel && (
          <button type="button" onClick={onCancel} className="text-sm text-zinc-500 hover:underline">
            Cancel
          </button>
        )}
      </div>
    </form>
  );
}

"use client";

import { FormEvent, useState } from "react";

import { apiPost, apiPut, CONTROL_STATUSES, Control, Entity, Risk } from "@/lib/api";

import { Field, inputClass, SubmitButton } from "./ui";

export function ControlForm({
  entities,
  risks,
  record,
  onSaved,
  onCancel,
}: {
  entities: Entity[];
  risks: Risk[];
  record?: Control;
  onSaved: (c: Control) => void;
  onCancel?: () => void;
}) {
  const isEdit = !!record;
  const [form, setForm] = useState({
    name: record?.name ?? "",
    description: record?.description ?? "",
    status: record?.status ?? "Draft",
    entity_id: record?.entity_id != null ? String(record.entity_id) : "",
    risk_id: record?.risk_id != null ? String(record.risk_id) : "",
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
        status: form.status,
        entity_id: form.entity_id ? Number(form.entity_id) : null,
        risk_id: form.risk_id ? Number(form.risk_id) : null,
      };
      const saved = isEdit
        ? await apiPut<Control>(`/api/v1/controls/${record!.id}`, payload)
        : await apiPost<Control>("/api/v1/controls", payload);
      onSaved(saved);
      if (!isEdit) setForm((f) => ({ ...f, name: "", description: "" }));
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
      <div className="flex items-center gap-3 sm:col-span-2">
        <SubmitButton disabled={submitting}>
          {submitting ? (isEdit ? "Saving…" : "Creating…") : isEdit ? "Save Changes" : "Create Control"}
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

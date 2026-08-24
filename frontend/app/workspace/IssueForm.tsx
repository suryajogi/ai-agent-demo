"use client";

import { FormEvent, useState } from "react";

import {
  apiPost,
  apiPut,
  Control,
  ISSUE_PRIORITIES,
  ISSUE_SOURCES,
  ISSUE_STATES,
  Issue,
  Risk,
} from "@/lib/api";

import { Field, inputClass, SubmitButton } from "./ui";

export function IssueForm({
  risks,
  controls,
  record,
  onSaved,
  onCancel,
}: {
  risks: Risk[];
  controls: Control[];
  record?: Issue;
  onSaved: (i: Issue) => void;
  onCancel?: () => void;
}) {
  const isEdit = !!record;
  const [form, setForm] = useState({
    title: record?.title ?? "",
    description: record?.description ?? "",
    source: record?.source ?? "Manual",
    priority: record?.priority ?? "Medium",
    state: record?.state ?? "New",
    assigned_to: record?.assigned_to ?? "",
    risk_id: record?.risk_id != null ? String(record.risk_id) : "",
    control_id: record?.control_id != null ? String(record.control_id) : "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const payload = {
        title: form.title,
        description: form.description || null,
        source: form.source,
        priority: form.priority,
        state: isEdit ? form.state : "New",
        assigned_to: form.assigned_to || null,
        risk_id: form.risk_id ? Number(form.risk_id) : null,
        control_id: form.control_id ? Number(form.control_id) : null,
      };
      const saved = isEdit
        ? await apiPut<Issue>(`/api/v1/issues/${record!.id}`, payload)
        : await apiPost<Issue>("/api/v1/issues", payload);
      onSaved(saved);
      if (!isEdit) setForm((f) => ({ ...f, title: "", description: "", assigned_to: "" }));
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="grid gap-3 sm:grid-cols-2">
      <Field label="Title">
        <input
          required
          className={inputClass}
          value={form.title}
          onChange={(e) => setForm({ ...form, title: e.target.value })}
        />
      </Field>
      <Field label="Assigned To">
        <input
          className={inputClass}
          value={form.assigned_to}
          onChange={(e) => setForm({ ...form, assigned_to: e.target.value })}
        />
      </Field>
      <Field label="Source">
        <select
          className={inputClass}
          value={form.source}
          onChange={(e) => setForm({ ...form, source: e.target.value })}
        >
          {ISSUE_SOURCES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </Field>
      <Field label="Priority">
        <select
          className={inputClass}
          value={form.priority}
          onChange={(e) => setForm({ ...form, priority: e.target.value })}
        >
          {ISSUE_PRIORITIES.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
      </Field>
      {isEdit && (
        <Field label="State">
          <select
            className={inputClass}
            value={form.state}
            onChange={(e) => setForm({ ...form, state: e.target.value })}
          >
            {ISSUE_STATES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </Field>
      )}
      <Field label="Related Risk">
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
      <Field label="Related Control">
        <select
          className={inputClass}
          value={form.control_id}
          onChange={(e) => setForm({ ...form, control_id: e.target.value })}
        >
          <option value="">— none —</option>
          {controls.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
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
          {submitting ? (isEdit ? "Saving…" : "Creating…") : isEdit ? "Save Changes" : "Log Issue"}
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

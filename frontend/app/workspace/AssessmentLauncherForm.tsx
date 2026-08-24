"use client";

import { FormEvent, useState } from "react";

import {
  apiPost,
  apiPut,
  ASSESSMENT_STATES,
  AssessmentTemplate,
  Risk,
  RiskAssessment,
} from "@/lib/api";

import { Field, inputClass, SubmitButton } from "./ui";

export function AssessmentLauncherForm({
  risks,
  templates,
  record,
  onSaved,
  onCancel,
}: {
  risks: Risk[];
  templates: AssessmentTemplate[];
  record?: RiskAssessment;
  onSaved: (a: RiskAssessment) => void;
  onCancel?: () => void;
}) {
  const isEdit = !!record;
  const [form, setForm] = useState({
    risk_id: record?.risk_id != null ? String(record.risk_id) : "",
    assessor_id: record?.assessor_id ?? "",
    template_id: record?.template_id != null ? String(record.template_id) : templates[0] ? String(templates[0].id) : "",
    state: record?.state ?? "Not Started",
    comments: record?.comments ?? "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const payload = {
        risk_id: form.risk_id ? Number(form.risk_id) : null,
        assessor_id: form.assessor_id || null,
        template_id: form.template_id ? Number(form.template_id) : null,
        state: isEdit ? form.state : "Not Started",
        comments: form.comments || null,
      };
      const saved = isEdit
        ? await apiPut<RiskAssessment>(`/api/v1/risk-assessments/${record!.id}`, payload)
        : await apiPost<RiskAssessment>("/api/v1/risk-assessments", payload);
      onSaved(saved);
      if (!isEdit) setForm((f) => ({ ...f, assessor_id: "", comments: "" }));
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="grid gap-3 sm:grid-cols-2">
      <Field label="Risk to Assess">
        <select
          required
          className={inputClass}
          value={form.risk_id}
          onChange={(e) => setForm({ ...form, risk_id: e.target.value })}
        >
          <option value="">— select a risk —</option>
          {risks.map((r) => (
            <option key={r.id} value={r.id}>
              {r.name}
            </option>
          ))}
        </select>
      </Field>
      <Field label="Assign To (business user)">
        <input
          required
          className={inputClass}
          value={form.assessor_id}
          onChange={(e) => setForm({ ...form, assessor_id: e.target.value })}
          placeholder="e.g. s.washington"
        />
      </Field>
      <Field label="Questionnaire Template">
        <select
          className={inputClass}
          value={form.template_id}
          onChange={(e) => setForm({ ...form, template_id: e.target.value })}
        >
          {templates.map((t) => (
            <option key={t.id} value={t.id}>
              {t.name}
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
            {ASSESSMENT_STATES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </Field>
      )}
      <Field label="Comments">
        <input
          className={inputClass}
          value={form.comments}
          onChange={(e) => setForm({ ...form, comments: e.target.value })}
        />
      </Field>
      {error && <p className="sm:col-span-2 text-sm text-red-600">{error}</p>}
      <div className="flex items-center gap-3 sm:col-span-2">
        <SubmitButton disabled={submitting}>
          {submitting
            ? isEdit
              ? "Saving…"
              : "Launching…"
            : isEdit
              ? "Save Changes"
              : "Launch Risk Assessment"}
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

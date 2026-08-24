"use client";

import { FormEvent, useState } from "react";

import { apiPost, AssessmentTemplate, Risk, RiskAssessment } from "@/lib/api";

import { Field, inputClass, SubmitButton } from "./ui";

export function AssessmentLauncherForm({
  risks,
  templates,
  onCreated,
}: {
  risks: Risk[];
  templates: AssessmentTemplate[];
  onCreated: (a: RiskAssessment) => void;
}) {
  const [form, setForm] = useState({
    risk_id: "",
    assessor_id: "",
    template_id: templates[0] ? String(templates[0].id) : "",
    comments: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const created = await apiPost<RiskAssessment>("/api/v1/risk-assessments", {
        risk_id: form.risk_id ? Number(form.risk_id) : null,
        assessor_id: form.assessor_id || null,
        template_id: form.template_id ? Number(form.template_id) : null,
        state: "Not Started",
        comments: form.comments || null,
      });
      onCreated(created);
      setForm((f) => ({ ...f, assessor_id: "", comments: "" }));
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
      <Field label="Comments">
        <input
          className={inputClass}
          value={form.comments}
          onChange={(e) => setForm({ ...form, comments: e.target.value })}
        />
      </Field>
      {error && <p className="sm:col-span-2 text-sm text-red-600">{error}</p>}
      <div className="sm:col-span-2">
        <SubmitButton disabled={submitting}>
          {submitting ? "Launching…" : "Launch Risk Assessment"}
        </SubmitButton>
      </div>
    </form>
  );
}

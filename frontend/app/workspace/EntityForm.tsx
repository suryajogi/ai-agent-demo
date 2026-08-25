"use client";

import { FormEvent, useState } from "react";

import { apiPost, apiPut, CRITICALITY_TIERS, Department, ENTITY_TYPES, Entity } from "@/lib/api";

import { Field, inputClass, SubmitButton } from "./ui";

export function EntityForm({
  departments,
  record,
  onSaved,
  onCancel,
}: {
  departments: Department[];
  record?: Entity;
  onSaved: (e: Entity) => void;
  onCancel?: () => void;
}) {
  const isEdit = !!record;
  const [form, setForm] = useState({
    name: record?.name ?? "",
    type: record?.type ?? "Application",
    department_id: record?.department_id != null ? String(record.department_id) : "",
    owner_id: record?.owner_id ?? "",
    status: record?.status ?? "Active",
    contract_end_date: record?.contract_end_date ?? "",
    criticality_tier: record?.criticality_tier ?? "",
    last_due_diligence_date: record?.last_due_diligence_date ?? "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const isVendor = form.type === "Vendor";

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const payload = {
        name: form.name,
        type: form.type,
        department_id: form.department_id ? Number(form.department_id) : null,
        owner_id: form.owner_id || null,
        status: form.status,
        contract_end_date: isVendor ? form.contract_end_date || null : null,
        criticality_tier: isVendor ? form.criticality_tier || null : null,
        last_due_diligence_date: isVendor ? form.last_due_diligence_date || null : null,
      };
      const saved = isEdit
        ? await apiPut<Entity>(`/api/v1/entities/${record!.id}`, payload)
        : await apiPost<Entity>("/api/v1/entities", payload);
      onSaved(saved);
      if (!isEdit) setForm((f) => ({ ...f, name: "", owner_id: "" }));
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
      <Field label="Type">
        <select
          className={inputClass}
          value={form.type}
          onChange={(e) => setForm({ ...form, type: e.target.value })}
        >
          {ENTITY_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </Field>
      <Field label="Department">
        <select
          className={inputClass}
          value={form.department_id}
          onChange={(e) => setForm({ ...form, department_id: e.target.value })}
        >
          <option value="">— none —</option>
          {departments.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name}
            </option>
          ))}
        </select>
      </Field>
      <Field label="Owner">
        <input
          className={inputClass}
          value={form.owner_id}
          onChange={(e) => setForm({ ...form, owner_id: e.target.value })}
          placeholder="e.g. OWNER-501"
        />
      </Field>
      <Field label="Status">
        <select
          className={inputClass}
          value={form.status}
          onChange={(e) => setForm({ ...form, status: e.target.value })}
        >
          <option value="Active">Active</option>
          <option value="Inactive">Inactive</option>
        </select>
      </Field>
      {isVendor && (
        <>
          <Field label="Criticality Tier">
            <select
              className={inputClass}
              value={form.criticality_tier}
              onChange={(e) => setForm({ ...form, criticality_tier: e.target.value })}
            >
              <option value="">— none —</option>
              {CRITICALITY_TIERS.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Contract End Date">
            <input
              type="date"
              className={inputClass}
              value={form.contract_end_date}
              onChange={(e) => setForm({ ...form, contract_end_date: e.target.value })}
            />
          </Field>
          <Field label="Last Due Diligence Date">
            <input
              type="date"
              className={inputClass}
              value={form.last_due_diligence_date}
              onChange={(e) => setForm({ ...form, last_due_diligence_date: e.target.value })}
            />
          </Field>
        </>
      )}
      {error && <p className="sm:col-span-2 text-sm text-red-600">{error}</p>}
      <div className="flex items-center gap-3 sm:col-span-2">
        <SubmitButton disabled={submitting}>
          {submitting ? (isEdit ? "Saving…" : "Creating…") : isEdit ? "Save Changes" : "Create Entity"}
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

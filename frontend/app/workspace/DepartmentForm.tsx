"use client";

import { FormEvent, useState } from "react";

import { apiPost, apiPut, Department } from "@/lib/api";

import { Field, inputClass, SubmitButton } from "./ui";

export function DepartmentForm({
  record,
  onSaved,
  onCancel,
}: {
  record?: Department;
  onSaved: (d: Department) => void;
  onCancel?: () => void;
}) {
  const isEdit = !!record;
  const [name, setName] = useState(record?.name ?? "");
  const [managerId, setManagerId] = useState(record?.manager_id ?? "");
  const [costCenter, setCostCenter] = useState(record?.cost_center ?? "");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const payload = {
        name,
        manager_id: managerId || null,
        cost_center: costCenter || null,
      };
      const saved = isEdit
        ? await apiPut<Department>(`/api/v1/departments/${record!.id}`, payload)
        : await apiPost<Department>("/api/v1/departments", payload);
      onSaved(saved);
      if (!isEdit) {
        setName("");
        setManagerId("");
        setCostCenter("");
      }
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
      <div className="flex items-center gap-3 sm:col-span-3">
        <SubmitButton disabled={submitting}>
          {submitting ? (isEdit ? "Saving…" : "Creating…") : isEdit ? "Save Changes" : "Create Department"}
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

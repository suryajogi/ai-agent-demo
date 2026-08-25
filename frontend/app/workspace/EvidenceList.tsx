"use client";

import { ChangeEvent, useEffect, useState } from "react";

import { API_URL, apiDelete, apiGet, apiUpload, EvidenceAttachment } from "@/lib/api";

export function EvidenceList({ recordType, recordId }: { recordType: string; recordId: number }) {
  const [attachments, setAttachments] = useState<EvidenceAttachment[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function reload() {
    apiGet<EvidenceAttachment[]>(`/api/v1/evidence?record_type=${recordType}&record_id=${recordId}`)
      .then(setAttachments)
      .catch((err) => setError((err as Error).message));
  }

  useEffect(reload, [recordType, recordId]);

  async function handleUpload(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("record_type", recordType);
      formData.append("record_id", String(recordId));
      formData.append("file", file);
      await apiUpload("/api/v1/evidence", formData);
      reload();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  async function handleDelete(id: number) {
    await apiDelete(`/api/v1/evidence/${id}`);
    setAttachments((prev) => prev.filter((a) => a.id !== id));
  }

  return (
    <div className="sm:col-span-2">
      <p className="mb-1 text-xs font-medium uppercase tracking-wide text-zinc-500">Evidence</p>
      <ul className="mb-2 flex flex-col gap-1">
        {attachments.map((a) => (
          <li key={a.id} className="flex items-center justify-between text-sm">
            <a
              href={`${API_URL}/api/v1/evidence/${a.id}/download`}
              target="_blank"
              rel="noreferrer"
              className="text-zinc-900 hover:underline dark:text-zinc-100"
            >
              {a.file_name}
            </a>
            <button onClick={() => handleDelete(a.id)} className="text-red-600 hover:underline dark:text-red-400">
              Delete
            </button>
          </li>
        ))}
        {attachments.length === 0 && <li className="text-sm text-zinc-400">No evidence attached.</li>}
      </ul>
      <input type="file" onChange={handleUpload} disabled={uploading} className="text-sm" />
      {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
    </div>
  );
}

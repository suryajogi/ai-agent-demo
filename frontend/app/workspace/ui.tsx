"use client";

import { ReactNode, useState } from "react";

export function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="flex flex-col gap-1 text-sm">
      <span className="font-medium text-zinc-600 dark:text-zinc-400">{label}</span>
      {children}
    </label>
  );
}

export const inputClass =
  "rounded-md border border-zinc-300 bg-white px-3 py-1.5 text-sm text-zinc-900 focus:border-zinc-500 focus:outline-none dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100";

export function SubmitButton({
  children,
  disabled,
}: {
  children: ReactNode;
  disabled?: boolean;
}) {
  return (
    <button
      type="submit"
      disabled={disabled}
      className="mt-1 rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-zinc-700 disabled:opacity-50 dark:bg-white dark:text-zinc-900 dark:hover:bg-zinc-200"
    >
      {children}
    </button>
  );
}

export function Card({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
      <h2 className="mb-4 text-base font-semibold">{title}</h2>
      {children}
    </section>
  );
}

interface Column<T> {
  header: string;
  render: (row: T) => ReactNode;
  // Optional: a comparable value for this column. Presence of this makes the
  // header clickable/sortable; omit it for columns that don't have a
  // meaningful sort order (e.g. an action badge).
  sortValue?: (row: T) => string | number | null;
}

function compareValues(a: string | number | null, b: string | number | null): number {
  if (a == null && b == null) return 0;
  if (a == null) return 1; // nulls sort last regardless of direction
  if (b == null) return -1;
  if (typeof a === "number" && typeof b === "number") return a - b;
  return String(a).localeCompare(String(b));
}

export function DataTable<T extends { id: number }>({
  rows,
  columns,
  onDelete,
  onRowClick,
}: {
  rows: T[];
  columns: Column<T>[];
  onDelete?: (id: number) => void;
  onRowClick?: (row: T) => void;
}) {
  const [sort, setSort] = useState<{ header: string; direction: "asc" | "desc" } | null>(null);

  function toggleSort(column: Column<T>) {
    if (!column.sortValue) return;
    setSort((prev) => {
      if (!prev || prev.header !== column.header) return { header: column.header, direction: "asc" };
      if (prev.direction === "asc") return { header: column.header, direction: "desc" };
      return null; // third click clears sorting
    });
  }

  const sortColumn = sort ? columns.find((c) => c.header === sort.header) : undefined;
  const sortedRows =
    sort && sortColumn?.sortValue
      ? [...rows].sort((a, b) => {
          const cmp = compareValues(sortColumn.sortValue!(a), sortColumn.sortValue!(b));
          return sort.direction === "asc" ? cmp : -cmp;
        })
      : rows;

  return (
    <div className="overflow-x-auto rounded-lg border border-zinc-200 dark:border-zinc-800">
      <table className="w-full text-sm">
        <thead className="bg-zinc-50 dark:bg-zinc-900">
          <tr>
            {columns.map((c) => (
              <th
                key={c.header}
                onClick={() => toggleSort(c)}
                className={`px-3 py-2 text-left font-medium text-zinc-500 ${
                  c.sortValue ? "cursor-pointer select-none hover:text-zinc-800 dark:hover:text-zinc-200" : ""
                }`}
              >
                {c.header}
                {sort?.header === c.header && (sort.direction === "asc" ? " ▲" : " ▼")}
              </th>
            ))}
            {onDelete && <th className="px-3 py-2" />}
          </tr>
        </thead>
        <tbody>
          {sortedRows.map((row) => (
            <tr
              key={row.id}
              onClick={onRowClick ? () => onRowClick(row) : undefined}
              className={`border-t border-zinc-100 dark:border-zinc-800 ${
                onRowClick ? "cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-900" : ""
              }`}
            >
              {columns.map((c) => (
                <td key={c.header} className="px-3 py-2">
                  {c.render(row)}
                </td>
              ))}
              {onDelete && (
                <td className="px-3 py-2 text-right">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDelete(row.id);
                    }}
                    className="text-red-600 hover:underline dark:text-red-400"
                  >
                    Delete
                  </button>
                </td>
              )}
            </tr>
          ))}
          {rows.length === 0 && (
            <tr>
              <td
                colSpan={columns.length + (onDelete ? 1 : 0)}
                className="px-3 py-6 text-center text-zinc-400"
              >
                No records yet.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

// --- Record view/edit modal ---------------------------------------------------

export function Modal({
  title,
  onClose,
  children,
}: {
  title: string;
  onClose: () => void;
  children: ReactNode;
}) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={onClose}
    >
      <div
        className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-xl border border-zinc-200 bg-white p-6 shadow-lg dark:border-zinc-800 dark:bg-zinc-950"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">{title}</h2>
          <button
            onClick={onClose}
            aria-label="Close"
            className="text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200"
          >
            ✕
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

export function ReadField({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="flex flex-col gap-1 text-sm">
      <span className="font-medium text-zinc-500">{label}</span>
      <span className="text-zinc-900 dark:text-zinc-100">
        {value === null || value === undefined || value === "" ? "—" : value}
      </span>
    </div>
  );
}

export function DetailModal<T>({
  title,
  record,
  onClose,
  onSaved,
  renderView,
  renderEdit,
}: {
  title: string;
  record: T;
  onClose: () => void;
  onSaved: (updated: T) => void;
  renderView: (record: T) => ReactNode;
  renderEdit: (record: T, onSaved: (updated: T) => void, onCancel: () => void) => ReactNode;
}) {
  const [editing, setEditing] = useState(false);

  function handleSaved(updated: T) {
    onSaved(updated);
    onClose();
  }

  return (
    <Modal title={title} onClose={onClose}>
      {editing ? (
        renderEdit(record, handleSaved, () => setEditing(false))
      ) : (
        <div className="grid gap-4">
          <div className="grid gap-3 sm:grid-cols-2">{renderView(record)}</div>
          <div>
            <button
              onClick={() => setEditing(true)}
              className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-zinc-700 dark:bg-white dark:text-zinc-900 dark:hover:bg-zinc-200"
            >
              Edit
            </button>
          </div>
        </div>
      )}
    </Modal>
  );
}

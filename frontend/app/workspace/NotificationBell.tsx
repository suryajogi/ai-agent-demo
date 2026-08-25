"use client";

import { useState } from "react";

import { apiGet, apiPost, isLoggedIn, NotificationItem } from "@/lib/api";
import { inputClass } from "./ui";

export function NotificationBell() {
  const [recipient, setRecipient] = useState("");
  const [items, setItems] = useState<NotificationItem[] | null>(null);
  const [open, setOpen] = useState(false);

  function check() {
    if (!recipient) return;
    apiGet<NotificationItem[]>(`/api/v1/notifications/mine?recipient=${encodeURIComponent(recipient)}`).then((data) => {
      setItems(data);
      setOpen(true);
    });
  }

  async function markRead(id: number) {
    await apiPost(`/api/v1/notifications/${id}/read`, {});
    setItems((prev) => prev?.map((n) => (n.id === id ? { ...n, read_at: new Date().toISOString() } : n)) ?? null);
  }

  async function runCheck() {
    if (!isLoggedIn()) return;
    const result = await apiPost<{ created_count: number; skipped_count: number }>(
      "/api/v1/notifications/run-check",
      {}
    );
    alert(`Notification check: ${result.created_count} new, ${result.skipped_count} already existed.`);
  }

  const unread = items?.filter((n) => !n.read_at).length ?? 0;

  return (
    <div className="relative">
      <div className="flex items-center gap-2">
        <input
          className={`${inputClass} w-32`}
          placeholder="Identity, e.g. ANALYST-701"
          value={recipient}
          onChange={(e) => setRecipient(e.target.value)}
        />
        <button onClick={check} className="text-sm text-zinc-500 hover:underline">
          🔔{unread > 0 && <span className="ml-1 text-red-600">{unread}</span>}
        </button>
        {isLoggedIn() && (
          <button onClick={runCheck} className="text-xs text-zinc-500 hover:underline">
            Run overdue check
          </button>
        )}
      </div>
      {open && items && (
        <div className="absolute right-0 z-40 mt-2 w-80 rounded-md border border-zinc-200 bg-white p-3 shadow-lg dark:border-zinc-800 dark:bg-zinc-950">
          <div className="mb-2 flex items-center justify-between">
            <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">Notifications</p>
            <button onClick={() => setOpen(false)} className="text-zinc-400 hover:text-zinc-700">
              ✕
            </button>
          </div>
          <ul className="flex flex-col gap-2">
            {items.map((n) => (
              <li key={n.id} className="text-sm">
                <p className={n.read_at ? "text-zinc-400" : "font-medium"}>{n.subject}</p>
                {n.body && <p className="text-xs text-zinc-500">{n.body}</p>}
                {!n.read_at && (
                  <button onClick={() => markRead(n.id)} className="text-xs text-zinc-500 hover:underline">
                    Mark read
                  </button>
                )}
              </li>
            ))}
            {items.length === 0 && <li className="text-sm text-zinc-400">No notifications.</li>}
          </ul>
        </div>
      )}
    </div>
  );
}

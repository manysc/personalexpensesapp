"use client";

import type { ActionItem } from "@/types/expense";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

const TYPE_LABELS: Record<ActionItem["type"], string> = {
  rent_unpaid: "Rent",
  utility_changed: "Utility",
  statement_unverified: "Statement",
  statement_not_stored: "Not in app",
  statement_not_imported: "Not imported",
};

const TYPE_STYLES: Record<ActionItem["type"], string> = {
  rent_unpaid: "bg-red-50 text-red-700 border-red-200",
  utility_changed: "bg-amber-50 text-amber-700 border-amber-200",
  statement_unverified: "bg-orange-50 text-orange-800 border-orange-200",
  statement_not_stored: "bg-sky-50 text-sky-800 border-sky-200",
  statement_not_imported: "bg-sky-50 text-sky-800 border-sky-200",
};

const FALLBACK_STYLE = "bg-gray-50 text-gray-700 border-gray-200";

interface Action {
  label: string;
  title: string;
  run: (id: number) => Promise<Response>;
}

const resolve = (id: number) => fetch(`/api/expenses/action-items/${id}/resolve`, { method: "POST" });
const load = (id: number) => fetch(`/api/expenses/action-items/${id}/load`, { method: "POST" });

// What can be done about each kind of item. Resolving a "not in app" item keeps that
// transaction out of the app: later imports leave it out too.
const ACTIONS: Partial<Record<ActionItem["type"], Action[]>> = {
  statement_not_stored: [
    { label: "Load", title: "Add this transaction to the app", run: load },
    { label: "Keep out", title: "It was removed on purpose: leave it out, also on future imports", run: resolve },
  ],
  statement_not_imported: [
    { label: "Load all", title: "Add these transactions to the app", run: load },
    { label: "Dismiss", title: "Hide this notification", run: resolve },
  ],
};

const DEFAULT_ACTIONS: Action[] = [{ label: "Resolve", title: "Mark as done", run: resolve }];

export default function ActionList() {
  const [items, setItems] = useState<ActionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyIds, setBusyIds] = useState<Set<number>>(new Set());
  const [failedIds, setFailedIds] = useState<Set<number>>(new Set());

  const refresh = useCallback(async () => {
    try {
      const res = await fetch("/api/expenses/action-items");
      if (!res.ok) throw new Error(`Error ${res.status}: ${res.statusText}`);
      setItems((await res.json()) as ActionItem[]);
    } catch {
      // Keep showing what we have.
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function handleAction(id: number, action: Action) {
    setBusyIds((prev) => new Set(prev).add(id));
    setFailedIds((prev) => {
      const next = new Set(prev);
      next.delete(id);
      return next;
    });
    try {
      const res = await action.run(id);
      if (!res.ok) throw new Error(`Error ${res.status}: ${res.statusText}`);
      // Loading can settle other items of the same statement too, so re-read the list.
      await refresh();
    } catch {
      setFailedIds((prev) => new Set(prev).add(id));
    } finally {
      setBusyIds((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    }
  }

  if (loading || items.length === 0) return null;

  return (
    <div className="print:hidden rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <h2 className="mb-3 text-sm font-semibold text-gray-800">
        Action Items
        <span className="ml-2 text-xs font-normal text-gray-400">({items.length})</span>
      </h2>
      <ul className="space-y-2">
        {items.map((item) => (
          <li
            key={item.id}
            className={`flex items-center justify-between gap-4 rounded-md border px-3 py-2 text-sm ${TYPE_STYLES[item.type] ?? FALLBACK_STYLE}`}
          >
            <div className="flex items-center gap-2">
              <span className="shrink-0 rounded-full bg-white/60 px-2 py-0.5 text-xs font-semibold">
                {TYPE_LABELS[item.type] ?? item.type}
              </span>
              <span>{item.message}</span>
              {failedIds.has(item.id) && (
                <span className="shrink-0 text-xs font-semibold text-red-700">Failed, try again</span>
              )}
            </div>
            <div className="flex shrink-0 items-center gap-2">
              {item.type === "statement_unverified" && (
                <Link
                  href="/import"
                  className="text-xs font-medium underline underline-offset-2 hover:opacity-75"
                >
                  Import page
                </Link>
              )}
              {(ACTIONS[item.type] ?? DEFAULT_ACTIONS).map((action) => (
                <button
                  key={action.label}
                  title={action.title}
                  onClick={() => handleAction(item.id, action)}
                  disabled={busyIds.has(item.id)}
                  className="rounded border border-current px-2 py-1 text-xs font-medium hover:bg-white/50 disabled:opacity-50"
                >
                  {action.label}
                </button>
              ))}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

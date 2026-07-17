"use client";

import type { ActionItem } from "@/types/expense";
import { useEffect, useState } from "react";

const TYPE_LABELS: Record<ActionItem["type"], string> = {
  rent_unpaid: "Rent",
  utility_changed: "Utility",
};

const TYPE_STYLES: Record<ActionItem["type"], string> = {
  rent_unpaid: "bg-red-50 text-red-700 border-red-200",
  utility_changed: "bg-amber-50 text-amber-700 border-amber-200",
};

export default function ActionList() {
  const [items, setItems] = useState<ActionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [resolvingIds, setResolvingIds] = useState<Set<number>>(new Set());

  useEffect(() => {
    let cancelled = false;
    fetch("/api/expenses/action-items")
      .then((res) => {
        if (!res.ok) throw new Error(`Error ${res.status}: ${res.statusText}`);
        return res.json() as Promise<ActionItem[]>;
      })
      .then((json) => {
        if (!cancelled) {
          setItems(json);
          setLoading(false);
        }
      })
      .catch(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleResolve(id: number) {
    setResolvingIds((prev) => new Set(prev).add(id));
    try {
      const res = await fetch(`/api/expenses/action-items/${id}/resolve`, { method: "POST" });
      if (!res.ok) throw new Error(`Error ${res.status}: ${res.statusText}`);
      setItems((prev) => prev.filter((item) => item.id !== id));
    } catch {
      // Leave the item in place so the user can retry.
    } finally {
      setResolvingIds((prev) => {
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
            className={`flex items-center justify-between gap-4 rounded-md border px-3 py-2 text-sm ${TYPE_STYLES[item.type]}`}
          >
            <div className="flex items-center gap-2">
              <span className="rounded-full bg-white/60 px-2 py-0.5 text-xs font-semibold">
                {TYPE_LABELS[item.type]}
              </span>
              <span>{item.message}</span>
            </div>
            <button
              onClick={() => handleResolve(item.id)}
              disabled={resolvingIds.has(item.id)}
              className="shrink-0 rounded border border-current px-2 py-1 text-xs font-medium hover:bg-white/50 disabled:opacity-50"
            >
              Resolve
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

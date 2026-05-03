"use client";

import type { Expense } from "@/types/expense";
import { useEffect, useState } from "react";

interface Props {
  expense: Expense;
}

const selectClass =
  "rounded border border-gray-300 px-2 py-1 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50";

export default function CategoryEditor({ expense }: Props) {
  const [category, setCategory] = useState(expense.category ?? "");
  const [overridden, setOverridden] = useState(expense.overridden);
  const [editing, setEditing] = useState(false);
  const [selected, setSelected] = useState(expense.category ?? "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [categories, setCategories] = useState<string[]>([]);

  useEffect(() => {
    if (!editing) return;
    fetch("/api/categories")
      .then((r) => r.json() as Promise<string[]>)
      .then(setCategories)
      .catch(() => setCategories([]));
  }, [editing]);

  async function handleSave() {
    if (!selected) return;
    setSaving(true);
    setError(null);
    try {
      const res = await fetch(`/api/expenses/${expense.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ category: selected }),
      });
      if (!res.ok) throw new Error(`Error ${res.status}: ${res.statusText}`);
      const updated: Expense = await res.json();
      setCategory(updated.category ?? "");
      setOverridden(updated.overridden);
      setEditing(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  }

  function handleCancel() {
    setSelected(category);
    setError(null);
    setEditing(false);
  }

  return (
    <div className="flex flex-col gap-1">
      {editing ? (
        <div className="flex items-center gap-2">
          <select
            value={selected}
            onChange={(e) => setSelected(e.target.value)}
            className={selectClass}
            autoFocus
            disabled={saving}
          >
            <option value="" disabled>
              — select a category —
            </option>
            {categories.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
          <button
            onClick={handleSave}
            disabled={saving || !selected}
            className="rounded bg-blue-600 px-3 py-1 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? "Saving…" : "Save"}
          </button>
          <button
            onClick={handleCancel}
            disabled={saving}
            className="rounded border border-gray-300 px-3 py-1 text-xs font-medium text-gray-600 hover:bg-gray-50 disabled:opacity-50"
          >
            Cancel
          </button>
        </div>
      ) : (
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-900">{category || "—"}</span>
          {overridden && (
            <span className="inline-block rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700">
              overridden
            </span>
          )}
          <button
            onClick={() => {
              setSelected(category);
              setEditing(true);
            }}
            className="rounded border border-gray-300 px-2 py-0.5 text-xs text-gray-500 hover:bg-gray-50 hover:text-gray-700"
          >
            Edit
          </button>
        </div>
      )}
      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  );
}

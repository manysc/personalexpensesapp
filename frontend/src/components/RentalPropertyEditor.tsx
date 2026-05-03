"use client";

import type { Expense, RentalProperty } from "@/types/expense";
import { useEffect, useState } from "react";

interface Props {
  expense: Expense;
}

const selectClass =
  "rounded border border-gray-300 px-2 py-1 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50";

export default function RentalPropertyEditor({ expense }: Props) {
  const [propertyId, setPropertyId] = useState<number | null>(expense.property_id);
  const [editing, setEditing] = useState(false);
  const [selected, setSelected] = useState<string>(
    expense.property_id != null ? String(expense.property_id) : ""
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [properties, setProperties] = useState<RentalProperty[]>([]);

  useEffect(() => {
    if (!editing) return;
    fetch("/api/rental-properties")
      .then((r) => r.json() as Promise<RentalProperty[]>)
      .then(setProperties)
      .catch(() => setProperties([]));
  }, [editing]);

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      const res = await fetch(`/api/expenses/${expense.id}/property`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ property_id: selected ? Number(selected) : null }),
      });
      if (!res.ok) throw new Error(`Error ${res.status}: ${res.statusText}`);
      const updated: Expense = await res.json();
      setPropertyId(updated.property_id);
      setEditing(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  }

  function handleCancel() {
    setSelected(propertyId != null ? String(propertyId) : "");
    setError(null);
    setEditing(false);
  }

  const currentAlias =
    properties.find((p) => p.id === propertyId)?.alias ?? null;

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
            <option value="">— none —</option>
            {properties.map((p) => (
              <option key={p.id} value={String(p.id)}>
                {p.alias}
              </option>
            ))}
          </select>
          <button
            onClick={handleSave}
            disabled={saving}
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
          {propertyId != null ? (
            <span className="inline-block rounded-full bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700">
              {currentAlias ?? `#${propertyId}`}
            </span>
          ) : (
            <span className="text-sm text-gray-400">—</span>
          )}
          <button
            onClick={() => setEditing(true)}
            className="rounded border border-gray-200 px-2 py-0.5 text-xs text-gray-500 hover:border-gray-400 hover:text-gray-700"
          >
            Edit
          </button>
        </div>
      )}
      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  );
}

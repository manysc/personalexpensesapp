"use client";

import type { Category, RentalProperty } from "@/types/expense";
import { useEffect, useState } from "react";

interface Props {
  selectedIds: Set<number>;
  onClear: () => void;
  onApplied: (updatedIds: number[]) => void;
}

type Field = "category" | "property_id" | "comments";

const FIELD_LABELS: Record<Field, string> = {
  category: "Category",
  property_id: "Property",
  comments: "Comments",
};

const selectClass =
  "rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50";

export default function BulkEditBar({ selectedIds, onClear, onApplied }: Props) {
  const [field, setField] = useState<Field>("category");
  const [categoryValue, setCategoryValue] = useState("");
  const [propertyValue, setPropertyValue] = useState("");
  const [commentsValue, setCommentsValue] = useState("");
  const [categories, setCategories] = useState<Category[]>([]);
  const [properties, setProperties] = useState<RentalProperty[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/categories")
      .then((r) => r.json() as Promise<Category[]>)
      .then(setCategories)
      .catch(() => {});
    fetch("/api/rental-properties")
      .then((r) => r.json() as Promise<RentalProperty[]>)
      .then(setProperties)
      .catch(() => {});
  }, []);

  async function handleApply() {
    setSaving(true);
    setError(null);

    const body: Record<string, unknown> = { ids: Array.from(selectedIds) };
    if (field === "category") body.category = categoryValue || null;
    if (field === "property_id") body.property_id = propertyValue ? parseInt(propertyValue, 10) : null;
    if (field === "comments") body.comments = commentsValue || null;

    try {
      const res = await fetch("/api/expenses/bulk-update", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(`Error ${res.status}: ${res.statusText}`);
      const updatedIds = (await res.json()) as number[];
      onApplied(updatedIds);
      onClear();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to apply");
    } finally {
      setSaving(false);
    }
  }

  if (selectedIds.size === 0) return null;

  return (
    <div className="flex flex-wrap items-center gap-3 rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 text-sm shadow-sm">
      <span className="font-medium text-blue-800">
        {selectedIds.size} selected
      </span>

      <span className="text-blue-300">|</span>

      <span className="text-blue-700">Set</span>

      {/* Field picker */}
      <select
        value={field}
        onChange={(e) => setField(e.target.value as Field)}
        className={selectClass}
        disabled={saving}
      >
        {(Object.keys(FIELD_LABELS) as Field[]).map((f) => (
          <option key={f} value={f}>
            {FIELD_LABELS[f]}
          </option>
        ))}
      </select>

      <span className="text-blue-700">to</span>

      {/* Value picker — changes based on field */}
      {field === "category" && (
        <select
          value={categoryValue}
          onChange={(e) => setCategoryValue(e.target.value)}
          className={selectClass}
          disabled={saving}
        >
          <option value="">— clear —</option>
          {categories.map((c) => (
            <option key={c.id} value={c.name}>
              {c.name}
            </option>
          ))}
        </select>
      )}

      {field === "property_id" && (
        <select
          value={propertyValue}
          onChange={(e) => setPropertyValue(e.target.value)}
          className={selectClass}
          disabled={saving}
        >
          <option value="">— clear —</option>
          {properties.map((p) => (
            <option key={p.id} value={String(p.id)}>
              {p.alias}
            </option>
          ))}
        </select>
      )}

      {field === "comments" && (
        <input
          type="text"
          value={commentsValue}
          onChange={(e) => setCommentsValue(e.target.value)}
          placeholder="Enter comments…"
          className={selectClass + " min-w-[200px]"}
          disabled={saving}
        />
      )}

      <button
        onClick={handleApply}
        disabled={saving}
        className="rounded-md bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-50"
      >
        {saving ? "Applying…" : "Apply"}
      </button>

      <button
        onClick={onClear}
        disabled={saving}
        className="rounded-md border border-blue-300 px-3 py-1.5 text-xs font-medium text-blue-700 hover:bg-blue-100 disabled:opacity-50"
      >
        Cancel
      </button>

      {error && <span className="text-xs text-red-600">{error}</span>}
    </div>
  );
}

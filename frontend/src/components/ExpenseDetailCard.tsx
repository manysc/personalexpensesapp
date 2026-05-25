"use client";

import AddExpenseModal from "@/components/AddExpenseModal";
import type { Category, Expense, RentalProperty, Vehicle } from "@/types/expense";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

interface Props {
  expense: Expense;
  staticFields: { label: string; value: string }[];
}

const inputClass =
  "w-full rounded border border-gray-300 px-2 py-1 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50";

export default function ExpenseDetailCard({ expense, staticFields }: Props) {
  const router = useRouter();
  const [overridden, setOverridden] = useState(expense.overridden);

  // Committed values (shown in view mode)
  const [category, setCategory] = useState(expense.category ?? "");
  const [propertyId, setPropertyId] = useState<number | null>(expense.property_id);
  const [vehicleId, setVehicleId] = useState<number | null>(expense.vehicle_id);
  const [comments, setComments] = useState(expense.comments ?? "");

  // Draft values (used while editing)
  const [draftCategory, setDraftCategory] = useState(category);
  const [draftPropertyId, setDraftPropertyId] = useState<string>(
    expense.property_id != null ? String(expense.property_id) : ""
  );
  const [draftVehicleId, setDraftVehicleId] = useState<string>(
    expense.vehicle_id != null ? String(expense.vehicle_id) : ""
  );
  const [draftComments, setDraftComments] = useState(comments);

  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Options loaded once when entering edit mode
  const [categories, setCategories] = useState<string[]>([]);
  const [properties, setProperties] = useState<RentalProperty[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);

  useEffect(() => {
    if (!editing) return;
    fetch("/api/categories")
      .then((r) => r.json() as Promise<Category[]>)
      .then((data) => setCategories(data.map((c) => c.name)))
      .catch(() => setCategories([]));
    fetch("/api/rental-properties")
      .then((r) => r.json() as Promise<RentalProperty[]>)
      .then(setProperties)
      .catch(() => setProperties([]));
    fetch("/api/vehicles")
      .then((r) => r.json() as Promise<Vehicle[]>)
      .then(setVehicles)
      .catch(() => setVehicles([]));
  }, [editing]);

  function handleEdit() {
    setDraftCategory(category);
    setDraftPropertyId(propertyId != null ? String(propertyId) : "");
    setDraftVehicleId(vehicleId != null ? String(vehicleId) : "");
    setDraftComments(comments);
    setError(null);
    setEditing(true);
  }

  function handleCancel() {
    setError(null);
    setEditing(false);
  }

  async function handleDelete() {
    if (!window.confirm(`Delete expense #${expense.id}? This cannot be undone.`)) return;
    setDeleting(true);
    setError(null);
    try {
      const res = await fetch(`/api/expenses/${expense.id}`, { method: "DELETE" });
      if (!res.ok && res.status !== 204) throw new Error(`Error ${res.status}: ${res.statusText}`);
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete");
      setDeleting(false);
    }
  }

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      const body: Record<string, unknown> = {
        category: draftCategory || null,
        property_id: draftPropertyId ? Number(draftPropertyId) : null,
        vehicle_id: draftVehicleId ? Number(draftVehicleId) : null,
        comments: draftComments || null,
      };
      const res = await fetch(`/api/expenses/${expense.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(`Error ${res.status}: ${res.statusText}`);
      const updated: Expense = await res.json();
      setCategory(updated.category ?? "");
      setPropertyId(updated.property_id);
      setVehicleId(updated.vehicle_id);
      setComments(updated.comments ?? "");
      setOverridden(updated.overridden);
      setEditing(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  }

  const propertyAlias =
    properties.find((p) => p.id === propertyId)?.alias ?? null;
  const vehicleAlias =
    vehicles.find((v) => v.id === vehicleId)?.alias ?? null;

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-5 border-b border-gray-200">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-semibold text-gray-900">Expense Details</h1>
            <p className="mt-1 text-sm text-gray-500">ID #{expense.id}</p>
          </div>
          <div className="flex items-center gap-3">
            {overridden && (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 16 16"
                  fill="currentColor"
                  className="h-3.5 w-3.5"
                  aria-hidden="true"
                >
                  <path d="M13.488 2.513a1.75 1.75 0 0 0-2.475 0L4.75 8.774a2.75 2.75 0 0 0-.596.892l-.79 2.232a.75.75 0 0 0 .95.95l2.233-.79a2.75 2.75 0 0 0 .89-.596l6.262-6.262a1.75 1.75 0 0 0 0-2.475Z" />
                </svg>
                Manually edited
              </span>
            )}
            <button
              onClick={() => setShowAddModal(true)}
              disabled={editing || deleting}
              className="rounded border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-600 hover:bg-gray-50 disabled:opacity-50"
            >
              Add expense
            </button>
            {!editing && (
              <button
                onClick={handleEdit}
                disabled={deleting}
                className="rounded border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-600 hover:bg-gray-50 disabled:opacity-50"
              >
                Edit
              </button>
            )}
            {!editing && (
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="rounded border border-red-300 px-3 py-1.5 text-sm font-medium text-red-600 hover:bg-red-50 disabled:opacity-50"
              >
                {deleting ? "Deleting…" : "Delete"}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Fields */}
      <dl className="divide-y divide-gray-100">
        {staticFields.map(({ label, value }) => (
          <div key={label} className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-gray-500">{label}</dt>
            <dd className="text-sm text-gray-900 col-span-2 break-words">{value}</dd>
          </div>
        ))}

        {/* Category */}
        <div className="px-6 py-4 grid grid-cols-3 gap-4 items-center">
          <dt className="text-sm font-medium text-gray-500">Category</dt>
          <dd className="col-span-2">
            {editing ? (
              <select
                value={draftCategory}
                onChange={(e) => setDraftCategory(e.target.value)}
                className={inputClass}
                disabled={saving}
              >
                <option value="">— none —</option>
                {categories.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            ) : (
              <span className="text-sm text-gray-900">{category || "—"}</span>
            )}
          </dd>
        </div>

        {/* Rental Property */}
        <div className="px-6 py-4 grid grid-cols-3 gap-4 items-center">
          <dt className="text-sm font-medium text-gray-500">Rental Property</dt>
          <dd className="col-span-2">
            {editing ? (
              <select
                value={draftPropertyId}
                onChange={(e) => setDraftPropertyId(e.target.value)}
                className={inputClass}
                disabled={saving}
              >
                <option value="">— none —</option>
                {properties.map((p) => (
                  <option key={p.id} value={String(p.id)}>{p.alias}</option>
                ))}
              </select>
            ) : propertyId != null ? (
              <span className="inline-block rounded-full bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700">
                {propertyAlias ?? `#${propertyId}`}
              </span>
            ) : (
              <span className="text-sm text-gray-400">—</span>
            )}
          </dd>
        </div>

        {/* Vehicle */}
        <div className="px-6 py-4 grid grid-cols-3 gap-4 items-center">
          <dt className="text-sm font-medium text-gray-500">Vehicle</dt>
          <dd className="col-span-2">
            {editing ? (
              <select
                value={draftVehicleId}
                onChange={(e) => setDraftVehicleId(e.target.value)}
                className={inputClass}
                disabled={saving}
              >
                <option value="">— none —</option>
                {vehicles.map((v) => (
                  <option key={v.id} value={String(v.id)}>{v.alias}</option>
                ))}
              </select>
            ) : vehicleId != null ? (
              <span className="inline-block rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700">
                {vehicleAlias ?? `#${vehicleId}`}
              </span>
            ) : (
              <span className="text-sm text-gray-400">—</span>
            )}
          </dd>
        </div>

        {/* Comments */}
        <div className="px-6 py-4 grid grid-cols-3 gap-4 items-start">
          <dt className="text-sm font-medium text-gray-500">Comments</dt>
          <dd className="col-span-2">
            {editing ? (
              <textarea
                value={draftComments}
                onChange={(e) => setDraftComments(e.target.value)}
                rows={3}
                className={inputClass}
                placeholder="Add a comment…"
                disabled={saving}
              />
            ) : (
              <span className="text-sm text-gray-900 whitespace-pre-wrap">
                {comments || "—"}
              </span>
            )}
          </dd>
        </div>
      </dl>

      {/* Save / Cancel footer */}
      {editing && (
        <div className="flex items-center justify-end gap-3 border-t border-gray-200 px-6 py-4">
          {error && <p className="mr-auto text-sm text-red-600">{error}</p>}
          <button
            onClick={handleCancel}
            disabled={saving}
            className="rounded border border-gray-300 px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? "Saving…" : "Save changes"}
          </button>
        </div>
      )}

      {!editing && error && (
        <div className="border-t border-gray-200 px-6 py-3">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {showAddModal && (
        <AddExpenseModal
          onClose={() => setShowAddModal(false)}
          onSuccess={(created) => {
            setShowAddModal(false);
            router.push(`/expenses/${created.id}`);
          }}
        />
      )}
    </div>
  );
}

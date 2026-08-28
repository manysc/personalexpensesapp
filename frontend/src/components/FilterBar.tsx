"use client";

import type { Category, ExpenseFilters, RentalProperty, Vehicle } from "@/types/expense";
import { useEffect, useState } from "react";

interface Props {
  onApply: (filters: ExpenseFilters) => void;
  initialValues?: ExpenseFilters;
  onExportPdf?: () => void;
  exporting?: boolean;
}

const EMPTY: ExpenseFilters = {
  bank: "",
  category: "",
  date_from: "",
  date_to: "",
  description: "",
  comments: "",
  property_id: "",
  vehicle_id: "",
  overridden_only: false,
};

const inputClass =
  "w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500";

export default function FilterBar({ onApply, initialValues, onExportPdf, exporting }: Props) {
  const [draft, setDraft] = useState<ExpenseFilters>(initialValues ?? EMPTY);
  const [banks, setBanks] = useState<string[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [properties, setProperties] = useState<RentalProperty[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);

  useEffect(() => {
    fetch("/api/banks")
      .then((r) => r.json() as Promise<string[]>)
      .then(setBanks)
      .catch(() => setBanks([]));
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
  }, []);

  const set =
    (field: keyof ExpenseFilters) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
      setDraft((prev) => ({ ...prev, [field]: e.target.value }));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onApply(draft);
  };

  const handleClear = () => {
    setDraft(EMPTY);
    onApply(EMPTY);
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm"
    >
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Row 1 */}
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-600">
            Bank
          </label>
          <select
            value={draft.bank}
            onChange={set("bank")}
            className={inputClass}
          >
            <option value="">All banks</option>
            {banks.map((b) => (
              <option key={b} value={b}>
                {b}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-gray-600">
            Category
          </label>
          <select
            value={draft.category}
            onChange={set("category")}
            className={inputClass}
          >
            <option value="">All categories</option>
            {categories.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
            {!categories.includes("Other") && (
              <option value="Other">Other</option>
            )}
          </select>
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-gray-600">
            From
          </label>
          <input
            type="date"
            value={draft.date_from}
            onChange={set("date_from")}
            className={inputClass}
          />
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-gray-600">
            To
          </label>
          <input
            type="date"
            value={draft.date_to}
            onChange={set("date_to")}
            className={inputClass}
          />
        </div>

        {/* Row 2 */}
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-600">
            Description
          </label>
          <input
            type="text"
            value={draft.description}
            onChange={set("description")}
            placeholder="Search description…"
            className={inputClass}
          />
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-gray-600">
            Comments
          </label>
          <input
            type="text"
            value={draft.comments}
            onChange={set("comments")}
            placeholder="Search comments…"
            className={inputClass}
          />
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-gray-600">
            Property
          </label>
          <select
            value={draft.property_id}
            onChange={set("property_id")}
            className={inputClass}
          >
            <option value="">All properties</option>
            {properties.map((p) => (
              <option key={p.id} value={String(p.id)}>
                {p.alias}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-gray-600">
            Vehicle
          </label>
          <select
            value={draft.vehicle_id}
            onChange={set("vehicle_id")}
            className={inputClass}
          >
            <option value="">All vehicles</option>
            {vehicles.map((v) => (
              <option key={v.id} value={String(v.id)}>
                {v.alias}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2 pt-5">
          <input
            id="overridden_only"
            type="checkbox"
            checked={draft.overridden_only}
            onChange={(e) =>
              setDraft((prev) => ({ ...prev, overridden_only: e.target.checked }))
            }
            className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <label htmlFor="overridden_only" className="text-sm text-gray-700">
            Manually edited only
          </label>
        </div>
      </div>

      <div className="mt-4 flex items-center justify-end gap-3">
        <button
          type="button"
          onClick={handleClear}
          className="text-sm text-gray-500 underline underline-offset-2 hover:text-gray-700"
        >
          Clear
        </button>
        {onExportPdf && (
          <button
            type="button"
            onClick={onExportPdf}
            disabled={exporting}
            className="flex items-center gap-1.5 rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
          >
            {exporting ? (
              <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
              </svg>
            ) : (
              <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3M3 17v3a1 1 0 001 1h16a1 1 0 001-1v-3" />
              </svg>
            )}
            {exporting ? "Exporting…" : "Export PDF"}
          </button>
        )}
        <button
          type="submit"
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        >
          Apply Filters
        </button>
      </div>
    </form>
  );
}

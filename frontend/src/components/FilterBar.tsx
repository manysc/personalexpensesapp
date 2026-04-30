"use client";

import type { ExpenseFilters } from "@/types/expense";
import { useState } from "react";

interface Props {
  onApply: (filters: ExpenseFilters) => void;
}

const EMPTY: ExpenseFilters = {
  bank: "",
  category: "",
  date_from: "",
  date_to: "",
};

const inputClass =
  "w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500";

export default function FilterBar({ onApply }: Props) {
  const [draft, setDraft] = useState<ExpenseFilters>(EMPTY);

  const set =
    (field: keyof ExpenseFilters) =>
    (e: React.ChangeEvent<HTMLInputElement>) =>
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
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-600">
            Bank
          </label>
          <input
            type="text"
            value={draft.bank}
            onChange={set("bank")}
            placeholder="e.g. chase"
            className={inputClass}
          />
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-gray-600">
            Category
          </label>
          <input
            type="text"
            value={draft.category}
            onChange={set("category")}
            placeholder="e.g. groceries"
            className={inputClass}
          />
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
      </div>

      <div className="mt-4 flex items-center justify-end gap-3">
        <button
          type="button"
          onClick={handleClear}
          className="text-sm text-gray-500 underline underline-offset-2 hover:text-gray-700"
        >
          Clear
        </button>
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

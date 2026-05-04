"use client";

import CategoryEditor from "@/components/CategoryEditor";
import CommentsEditor from "@/components/CommentsEditor";
import RentalPropertyEditor from "@/components/RentalPropertyEditor";
import type { Expense } from "@/types/expense";
import { useState } from "react";

interface Props {
  expense: Expense;
  staticFields: { label: string; value: string }[];
}

export default function ExpenseDetailCard({ expense, staticFields }: Props) {
  const [overridden, setOverridden] = useState(expense.overridden);

  function handleSaved(updated: Expense) {
    setOverridden(updated.overridden);
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      <div className="px-6 py-5 border-b border-gray-200">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-semibold text-gray-900">Expense Details</h1>
            <p className="mt-1 text-sm text-gray-500">ID #{expense.id}</p>
          </div>
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
        </div>
      </div>

      <dl className="divide-y divide-gray-100">
        {staticFields.map(({ label, value }) => (
          <div key={label} className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-gray-500">{label}</dt>
            <dd className="text-sm text-gray-900 col-span-2 break-words">{value}</dd>
          </div>
        ))}
        <div className="px-6 py-4 grid grid-cols-3 gap-4 items-center">
          <dt className="text-sm font-medium text-gray-500">Category</dt>
          <dd className="col-span-2">
            <CategoryEditor expense={expense} onSaved={handleSaved} />
          </dd>
        </div>
        <div className="px-6 py-4 grid grid-cols-3 gap-4 items-center">
          <dt className="text-sm font-medium text-gray-500">Rental Property</dt>
          <dd className="col-span-2">
            <RentalPropertyEditor expense={expense} onSaved={handleSaved} />
          </dd>
        </div>
        <div className="px-6 py-4 grid grid-cols-3 gap-4 items-start">
          <dt className="text-sm font-medium text-gray-500">Comments</dt>
          <dd className="col-span-2">
            <CommentsEditor expense={expense} onSaved={handleSaved} />
          </dd>
        </div>
      </dl>
    </div>
  );
}

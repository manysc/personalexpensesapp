"use client";

import type { Expense } from "@/types/expense";
import { useRouter } from "next/navigation";

interface Props {
  items: Expense[];
  loading?: boolean;
  propertyMap?: Record<number, string>;
  vehicleMap?: Record<number, string>;
  selectedIds?: Set<number>;
  onSelectionChange?: (ids: Set<number>) => void;
}

function fmt(value: number | null): string {
  if (value === null) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(value);
}

export default function ExpensesTable({
  items,
  loading = false,
  propertyMap = {},
  vehicleMap = {},
  selectedIds,
  onSelectionChange,
}: Props) {
  const router = useRouter();
  const selectable = selectedIds !== undefined && onSelectionChange !== undefined;

  const allSelected = selectable && items.length > 0 && items.every((e) => selectedIds.has(e.id));
  const someSelected = selectable && !allSelected && items.some((e) => selectedIds.has(e.id));

  function toggleAll() {
    if (!selectable) return;
    if (allSelected) {
      const next = new Set(selectedIds);
      items.forEach((e) => next.delete(e.id));
      onSelectionChange(next);
    } else {
      const next = new Set(selectedIds);
      items.forEach((e) => next.add(e.id));
      onSelectionChange(next);
    }
  }

  function toggleRow(id: number, e: React.MouseEvent) {
    if (!selectable) return;
    e.stopPropagation();
    const next = new Set(selectedIds);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    onSelectionChange(next);
  }

  if (items.length === 0 && !loading) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-12 text-center text-sm text-gray-500">
        No expenses match your filters.
      </div>
    );
  }

  return (
    <div
      className={`overflow-hidden rounded-lg border border-gray-200 bg-white transition-opacity ${
        loading ? "opacity-60 pointer-events-none" : ""
      }`}
    >
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50">
              {selectable && (
                <th className="w-10 px-3 py-3">
                  <input
                    type="checkbox"
                    checked={allSelected}
                    ref={(el) => {
                      if (el) el.indeterminate = someSelected;
                    }}
                    onChange={toggleAll}
                    aria-label="Select all"
                    className="h-4 w-4 rounded border-gray-300 text-blue-600 accent-blue-600"
                    onClick={(e) => e.stopPropagation()}
                  />
                </th>
              )}
              {[
                { label: "Date", align: "left" },
                { label: "Bank", align: "left" },
                { label: "Description", align: "left" },
                { label: "Debit", align: "right" },
                { label: "Credit", align: "right" },
                { label: "Category", align: "left" },
                { label: "Property", align: "left" },
                { label: "Vehicle", align: "left" },
                { label: "Comments", align: "left" },
                { label: "Receipt", align: "left" },
                { label: "Edited", align: "left" },
              ].map(({ label, align }) => (
                <th
                  key={label}
                  className={`px-4 py-3 text-${align} text-xs font-semibold uppercase tracking-wide text-gray-500`}
                >
                  {label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {items.map((expense) => {
              const isSelected = selectable && selectedIds.has(expense.id);
              return (
                <tr
                  key={expense.id}
                  onClick={() => router.push(`/expenses/${expense.id}`)}
                  className={`cursor-pointer transition-colors hover:bg-blue-50 ${isSelected ? "bg-blue-50" : ""}`}
                >
                  {selectable && (
                    <td className="w-10 px-3 py-3" onClick={(e) => toggleRow(expense.id, e)}>
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => {}}
                        aria-label={`Select expense ${expense.id}`}
                        className="h-4 w-4 rounded border-gray-300 text-blue-600 accent-blue-600"
                      />
                    </td>
                  )}
                  <td className={`whitespace-nowrap py-3 text-gray-600 ${
                    expense.overridden
                      ? "border-l-4 border-l-amber-400 pl-3 pr-4"
                      : "px-4"
                  }`}>
                    {expense.date.slice(0, 10)}
                  </td>
                  <td className="px-4 py-3">
                    <span className="inline-block rounded-full bg-indigo-50 px-2 py-0.5 text-xs font-medium capitalize text-indigo-700">
                      {expense.bank}
                    </span>
                  </td>
                  <td className="max-w-xs px-4 py-3 text-gray-900">
                    <span className="block truncate" title={expense.description}>
                      {expense.description}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-right font-medium text-red-600">
                    {fmt(expense.debit)}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-right font-medium text-green-600">
                    {fmt(expense.credit)}
                  </td>
                  <td className="px-4 py-3">
                    {expense.category ? (
                      <span className="inline-block rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-700">
                        {expense.category}
                      </span>
                    ) : (
                      <span className="text-gray-400">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {expense.property_id != null && propertyMap[expense.property_id] ? (
                      <span className="inline-block rounded-full bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700">
                        {propertyMap[expense.property_id]}
                      </span>
                    ) : (
                      <span className="text-gray-400">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {expense.vehicle_id != null && vehicleMap[expense.vehicle_id] ? (
                      <span className="inline-block rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700">
                        {vehicleMap[expense.vehicle_id]}
                      </span>
                    ) : (
                      <span className="text-gray-400">—</span>
                    )}
                  </td>
                  <td className="max-w-[180px] px-4 py-3 text-gray-600">
                    {expense.comments ? (
                      <span className="block truncate text-xs" title={expense.comments}>
                        {expense.comments}
                      </span>
                    ) : (
                      <span className="text-gray-400">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                    {expense.receipt_filename ? (
                      <a
                        href={`/api/expenses/${expense.id}/receipt?inline=true`}
                        target="_blank"
                        rel="noopener noreferrer"
                        title={expense.receipt_filename.replace(/^\d+_/, "")}
                        className="inline-flex items-center gap-1 text-xs text-blue-600 hover:underline"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="h-3.5 w-3.5 shrink-0" aria-hidden="true">
                          <path d="M2 3.5A1.5 1.5 0 0 1 3.5 2h6.879a1.5 1.5 0 0 1 1.06.44l2.122 2.12a1.5 1.5 0 0 1 .439 1.061V12.5A1.5 1.5 0 0 1 12.5 14h-9A1.5 1.5 0 0 1 2 12.5v-9Z" />
                        </svg>
                        View
                      </a>
                    ) : (
                      <span className="text-gray-300">—</span>
                    )}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3">
                    {expense.overridden ? (
                      <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="h-3 w-3" aria-hidden="true">
                          <path d="M13.488 2.513a1.75 1.75 0 0 0-2.475 0L4.75 8.774a2.75 2.75 0 0 0-.596.892l-.79 2.232a.75.75 0 0 0 .95.95l2.233-.79a2.75 2.75 0 0 0 .89-.596l6.262-6.262a1.75 1.75 0 0 0 0-2.475Z" />
                        </svg>
                        Edited
                      </span>
                    ) : (
                      <span className="text-gray-300">—</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

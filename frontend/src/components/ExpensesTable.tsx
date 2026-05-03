"use client";

import type { Expense } from "@/types/expense";
import { useRouter } from "next/navigation";

interface Props {
  items: Expense[];
  loading?: boolean;
  propertyMap?: Record<number, string>;
}

function fmt(value: number | null): string {
  if (value === null) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(value);
}

export default function ExpensesTable({ items, loading = false, propertyMap = {} }: Props) {
  const router = useRouter();

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
              {[
                { label: "Date", align: "left" },
                { label: "Bank", align: "left" },
                { label: "Description", align: "left" },
                { label: "Debit", align: "right" },
                { label: "Credit", align: "right" },
                { label: "Category", align: "left" },
                { label: "Property", align: "left" },
                { label: "Comments", align: "left" },
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
            {items.map((expense) => (
              <tr
                key={expense.id}
                onClick={() => router.push(`/expenses/${expense.id}`)}
                className="cursor-pointer transition-colors hover:bg-blue-50"
              >
                <td className="whitespace-nowrap px-4 py-3 text-gray-600">
                  {expense.date}
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
                  <div className="flex items-center gap-1.5">
                    {expense.category ? (
                      <span className="inline-block rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-700">
                        {expense.category}
                      </span>
                    ) : (
                      <span className="text-gray-400">—</span>
                    )}
                    {expense.overridden && (
                      <span className="inline-block rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700">
                        overridden
                      </span>
                    )}
                  </div>
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
                <td className="max-w-[180px] px-4 py-3 text-gray-600">
                  {expense.comments ? (
                    <span className="block truncate text-xs" title={expense.comments}>
                      {expense.comments}
                    </span>
                  ) : (
                    <span className="text-gray-400">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

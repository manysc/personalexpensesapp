"use client";

import ExpensesTable from "@/components/ExpensesTable";
import FilterBar from "@/components/FilterBar";
import Pagination from "@/components/Pagination";
import type { ExpenseFilters, ExpenseListResponse, RentalProperty } from "@/types/expense";
import { useCallback, useEffect, useState } from "react";

const PAGE_SIZE = 25;
const EMPTY_FILTERS: ExpenseFilters = {
  bank: "",
  category: "",
  date_from: "",
  date_to: "",
};

export default function ExpensesPage() {
  const [appliedFilters, setAppliedFilters] =
    useState<ExpenseFilters>(EMPTY_FILTERS);
  const [page, setPage] = useState(0);
  const [data, setData] = useState<ExpenseListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [propertyMap, setPropertyMap] = useState<Record<number, string>>({});

  useEffect(() => {
    fetch("/api/rental-properties")
      .then((r) => r.json() as Promise<RentalProperty[]>)
      .then((props) => {
        const map: Record<number, string> = {};
        for (const p of props) map[p.id] = p.alias;
        setPropertyMap(map);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    const params = new URLSearchParams();
    if (appliedFilters.bank) params.set("bank", appliedFilters.bank);
    if (appliedFilters.category) params.set("category", appliedFilters.category);
    if (appliedFilters.date_from) params.set("date_from", appliedFilters.date_from);
    if (appliedFilters.date_to) params.set("date_to", appliedFilters.date_to);
    params.set("limit", String(PAGE_SIZE));
    params.set("offset", String(page * PAGE_SIZE));

    fetch(`/api/expenses?${params.toString()}`)
      .then((res) => {
        if (!res.ok) throw new Error(`Error ${res.status}: ${res.statusText}`);
        return res.json() as Promise<ExpenseListResponse>;
      })
      .then((json) => {
        if (!cancelled) {
          setData(json);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Failed to load expenses"
          );
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [appliedFilters, page]);

  const handleApply = useCallback((filters: ExpenseFilters) => {
    setAppliedFilters(filters);
    setPage(0);
  }, []);

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 0;

  return (
    <div className="space-y-4">
      <FilterBar onApply={handleApply} />

      {error && (
        <div className="rounded-md bg-red-50 border border-red-200 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading && !data ? (
        <div className="flex justify-center py-16 text-gray-400 text-sm">
          Loading…
        </div>
      ) : data ? (
        <>
          <p className="text-sm text-gray-500">
            {data.total === 0
              ? "No expenses found"
              : `Showing ${data.offset + 1}–${data.offset + data.items.length} of ${data.total} expenses`}
          </p>
          <ExpensesTable items={data.items} loading={loading} propertyMap={propertyMap} />
          {totalPages > 1 && (
            <Pagination
              page={page}
              totalPages={totalPages}
              onPageChange={setPage}
            />
          )}
        </>
      ) : null}
    </div>
  );
}

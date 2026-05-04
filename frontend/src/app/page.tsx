"use client";

import ExpensesTable from "@/components/ExpensesTable";
import FilterBar from "@/components/FilterBar";
import Pagination from "@/components/Pagination";
import type { ExpenseFilters, ExpenseListResponse, RentalProperty } from "@/types/expense";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

const PAGE_SIZE = 25;
const EMPTY_FILTERS: ExpenseFilters = {
  bank: "",
  category: "",
  date_from: "",
  date_to: "",
};

export default function ExpensesPage() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const filtersFromUrl: ExpenseFilters = {
    bank: searchParams.get("bank") ?? "",
    category: searchParams.get("category") ?? "",
    date_from: searchParams.get("date_from") ?? "",
    date_to: searchParams.get("date_to") ?? "",
  };
  const pageFromUrl = parseInt(searchParams.get("page") ?? "0", 10);

  const [appliedFilters, setAppliedFilters] =
    useState<ExpenseFilters>(filtersFromUrl);
  const [page, setPage] = useState(pageFromUrl);
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

  const pushUrl = useCallback(
    (filters: ExpenseFilters, p: number) => {
      const params = new URLSearchParams();
      if (filters.bank) params.set("bank", filters.bank);
      if (filters.category) params.set("category", filters.category);
      if (filters.date_from) params.set("date_from", filters.date_from);
      if (filters.date_to) params.set("date_to", filters.date_to);
      if (p > 0) params.set("page", String(p));
      const qs = params.toString();
      router.replace(qs ? `/?${qs}` : "/", { scroll: false });
    },
    [router]
  );

  const handleApply = useCallback(
    (filters: ExpenseFilters) => {
      setAppliedFilters(filters);
      setPage(0);
      pushUrl(filters, 0);
    },
    [pushUrl]
  );

  const handlePageChange = useCallback(
    (p: number) => {
      setPage(p);
      pushUrl(appliedFilters, p);
    },
    [appliedFilters, pushUrl]
  );

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 0;

  return (
    <div className="space-y-4">
      <FilterBar onApply={handleApply} initialValues={filtersFromUrl} />

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
              onPageChange={handlePageChange}
            />
          )}
        </>
      ) : null}
    </div>
  );
}

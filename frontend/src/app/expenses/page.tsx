"use client";

import AddExpenseModal from "@/components/AddExpenseModal";
import BulkEditBar from "@/components/BulkEditBar";
import ExpensesTable from "@/components/ExpensesTable";
import FilterBar from "@/components/FilterBar";
import Pagination from "@/components/Pagination";
import type { ExpenseFilters, ExpenseListResponse, RentalProperty, Vehicle } from "@/types/expense";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

const PAGE_SIZE = 25;
const EMPTY_FILTERS: ExpenseFilters = {
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

export default function ExpensesPage() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const filtersFromUrl: ExpenseFilters = {
    bank: searchParams.get("bank") ?? "",
    category: searchParams.get("category") ?? "",
    date_from: searchParams.get("date_from") ?? "",
    date_to: searchParams.get("date_to") ?? "",
    description: searchParams.get("description") ?? "",
    comments: searchParams.get("comments") ?? "",
    property_id: searchParams.get("property_id") ?? "",
    vehicle_id: searchParams.get("vehicle_id") ?? "",
    overridden_only: searchParams.get("overridden_only") === "true",
  };
  const pageFromUrl = parseInt(searchParams.get("page") ?? "0", 10);

  const [appliedFilters, setAppliedFilters] =
    useState<ExpenseFilters>(filtersFromUrl);
  const [page, setPage] = useState(pageFromUrl);
  const [data, setData] = useState<ExpenseListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [propertyMap, setPropertyMap] = useState<Record<number, string>>({});
  const [vehicleMap, setVehicleMap] = useState<Record<number, string>>({});
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [reloadKey, setReloadKey] = useState(0);

  // Restore scroll position when returning from an expense detail page
  useEffect(() => {
    if (!loading && data) {
      const saved = sessionStorage.getItem("expenses-scroll");
      if (saved !== null) {
        sessionStorage.removeItem("expenses-scroll");
        const y = parseInt(saved, 10);
        requestAnimationFrame(() => window.scrollTo(0, y));
      }
    }
  }, [loading, data]);

  useEffect(() => {
    fetch("/api/rental-properties")
      .then((r) => r.json() as Promise<RentalProperty[]>)
      .then((props) => {
        const map: Record<number, string> = {};
        for (const p of props) map[p.id] = p.alias;
        setPropertyMap(map);
      })
      .catch(() => {});
    fetch("/api/vehicles")
      .then((r) => r.json() as Promise<Vehicle[]>)
      .then((vehs) => {
        const map: Record<number, string> = {};
        for (const v of vehs) map[v.id] = v.alias;
        setVehicleMap(map);
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
    if (appliedFilters.description) params.set("description", appliedFilters.description);
    if (appliedFilters.comments) params.set("comments", appliedFilters.comments);
    if (appliedFilters.property_id) params.set("property_id", appliedFilters.property_id);
    if (appliedFilters.vehicle_id) params.set("vehicle_id", appliedFilters.vehicle_id);
    if (appliedFilters.overridden_only) params.set("overridden_only", "true");
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
  }, [appliedFilters, page, reloadKey]);

  const pushUrl = useCallback(
    (filters: ExpenseFilters, p: number) => {
      const params = new URLSearchParams();
      if (filters.bank) params.set("bank", filters.bank);
      if (filters.category) params.set("category", filters.category);
      if (filters.date_from) params.set("date_from", filters.date_from);
      if (filters.date_to) params.set("date_to", filters.date_to);
      if (filters.description) params.set("description", filters.description);
      if (filters.comments) params.set("comments", filters.comments);
      if (filters.property_id) params.set("property_id", filters.property_id);
      if (filters.vehicle_id) params.set("vehicle_id", filters.vehicle_id);
      if (filters.overridden_only) params.set("overridden_only", "true");
      if (p > 0) params.set("page", String(p));
      const qs = params.toString();
      router.replace(qs ? `/expenses?${qs}` : "/expenses", { scroll: false });
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
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-gray-900">Expenses</h1>
        <button
          onClick={() => setShowAddModal(true)}
          className="shrink-0 rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          + Add expense
        </button>
      </div>
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
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-500">
              {data.total === 0
                ? "No expenses found"
                : `Showing ${data.offset + 1}–${data.offset + data.items.length} of ${data.total} expenses`}
            </p>
          </div>
          <BulkEditBar
            selectedIds={selectedIds}
            onClear={() => setSelectedIds(new Set())}
            onApplied={() => {
              setSelectedIds(new Set());
              setReloadKey((k) => k + 1);
            }}
          />
          <ExpensesTable
            items={data.items}
            loading={loading}
            propertyMap={propertyMap}
            vehicleMap={vehicleMap}
            selectedIds={selectedIds}
            onSelectionChange={setSelectedIds}
          />
          {totalPages > 1 && (
            <Pagination
              page={page}
              totalPages={totalPages}
              onPageChange={handlePageChange}
            />
          )}
        </>
      ) : null}

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

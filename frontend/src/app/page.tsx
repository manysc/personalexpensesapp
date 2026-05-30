"use client";

import { useEffect, useState } from "react";
import {
    Bar,
    BarChart,
    CartesianGrid,
    Legend,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";

interface SummaryItem {
  month: string;
  category: string;
  total: number;
}

interface CommentedExpense {
  id: number;
  date: string;
  description: string;
  category: string | null;
  comments: string;
  debit: number | null;
  credit: number | null;
}

interface ChartRow {
  month: string;
  [category: string]: number | string;
}

interface PropertySummaryItem {
  month: string;
  property: string;
  total: number;
}

// Distinct colours for up to 20 categories
const PALETTE = [
  "#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f",
  "#edc948", "#b07aa1", "#ff9da7", "#9c755f", "#bab0ac",
  "#d37295", "#fabfd2", "#8cd17d", "#86bcb6", "#499894",
  "#e49444", "#79706e", "#d4a6c8", "#b6992d", "#a0cbe8",
];

function pivot(items: SummaryItem[]): { rows: ChartRow[]; categories: string[] } {
  const categorySet = new Set<string>();
  const monthMap = new Map<string, ChartRow>();

  for (const item of items) {
    categorySet.add(item.category);
    if (!monthMap.has(item.month)) {
      monthMap.set(item.month, { month: item.month });
    }
    const row = monthMap.get(item.month)!;
    row[item.category] = (row[item.category] as number | undefined ?? 0) + item.total;
  }

  const rows = Array.from(monthMap.values()).sort((a, b) =>
    (a.month as string).localeCompare(b.month as string)
  );
  const categories = Array.from(categorySet).sort();
  return { rows, categories };
}

const INCOME_CATEGORY = "Income";
const TRANSFER_CATEGORY = "Transfers";
const POSITIVE_CATEGORIES = new Set(["Income", "Real State"]);

function fmt(v: number): string {
  return v.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 2 });
}

export default function DashboardPage() {
  const [data, setData] = useState<SummaryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [appliedFrom, setAppliedFrom] = useState("");
  const [appliedTo, setAppliedTo] = useState("");
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [comments, setComments] = useState<CommentedExpense[]>([]);
  const [commentsLoading, setCommentsLoading] = useState(true);
  const [propertyData, setPropertyData] = useState<PropertySummaryItem[]>([]);
  const [propertyLoading, setPropertyLoading] = useState(true);

  // All categories available from the full data set
  const allCategories = Array.from(new Set(data.map((d) => d.category))).sort();

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    const params = new URLSearchParams();
    if (appliedFrom) params.set("date_from", appliedFrom);
    if (appliedTo) params.set("date_to", appliedTo);

    fetch(`/api/expenses/summary?${params.toString()}`)
      .then((res) => {
        if (!res.ok) throw new Error(`Error ${res.status}: ${res.statusText}`);
        return res.json() as Promise<SummaryItem[]>;
      })
      .then((json) => {
        if (!cancelled) {
          setData(json);
          setSelectedCategories([]);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load summary");
          setLoading(false);
        }
      });

    setCommentsLoading(true);
    fetch(`/api/expenses/comments?${params.toString()}`)
      .then((res) => {
        if (!res.ok) throw new Error(`Error ${res.status}: ${res.statusText}`);
        return res.json() as Promise<CommentedExpense[]>;
      })
      .then((json) => { if (!cancelled) { setComments(json); setCommentsLoading(false); } })
      .catch(() => { if (!cancelled) setCommentsLoading(false); });

    setPropertyLoading(true);
    fetch(`/api/expenses/property-summary?${params.toString()}`)
      .then((res) => {
        if (!res.ok) throw new Error(`Error ${res.status}: ${res.statusText}`);
        return res.json() as Promise<PropertySummaryItem[]>;
      })
      .then((json) => { if (!cancelled) { setPropertyData(json); setPropertyLoading(false); } })
      .catch(() => { if (!cancelled) setPropertyLoading(false); });

    return () => { cancelled = true; };
  }, [appliedFrom, appliedTo]);

  const filteredData =
    selectedCategories.length === 0
      ? data
      : data.filter((d) => selectedCategories.includes(d.category));

  const { rows, categories } = pivot(filteredData);

  // Property chart pivot
  const propertyMonthMap = new Map<string, ChartRow>();
  const propertySet = new Set<string>();
  for (const item of propertyData) {
    propertySet.add(item.property);
    if (!propertyMonthMap.has(item.month)) propertyMonthMap.set(item.month, { month: item.month });
    const row = propertyMonthMap.get(item.month)!;
    row[item.property] = (row[item.property] as number | undefined ?? 0) + item.total;
  }
  const propertyRows = Array.from(propertyMonthMap.values()).sort((a, b) =>
    (a.month as string).localeCompare(b.month as string)
  );
  const propertyNames = Array.from(propertySet).sort();

  // Property summary table
  const propTableMonths = Array.from(new Set(propertyData.map((d) => d.month))).sort();
  const propTableProperties = Array.from(new Set(propertyData.map((d) => d.property))).sort();
  const propLookup: Record<string, Record<string, number>> = {};
  for (const item of propertyData) {
    if (!propLookup[item.month]) propLookup[item.month] = {};
    propLookup[item.month][item.property] = item.total;
  }
  const propColTotals: Record<string, number> = {};
  for (const prop of propTableProperties) {
    propColTotals[prop] = propTableMonths.reduce((s, m) => s + (propLookup[m]?.[prop] ?? 0), 0);
  }
  const propRowTotals: Record<string, number> = {};
  for (const m of propTableMonths) {
    propRowTotals[m] = propTableProperties.reduce((s, p) => s + (propLookup[m]?.[p] ?? 0), 0);
  }
  const propGrandTotal = propTableMonths.reduce((s, m) => s + propRowTotals[m], 0);

  // Summary table — uses full (unfiltered) data so category selection doesn't affect it
  const tableMonths = Array.from(new Set(data.map((d) => d.month))).sort();
  const tableCategories = Array.from(new Set(data.map((d) => d.category))).sort();
  const expenseCategories = tableCategories.filter(
    (c) => !POSITIVE_CATEGORIES.has(c) && c !== TRANSFER_CATEGORY
  );
  // lookup[month][category] = total
  const lookup: Record<string, Record<string, number>> = {};
  for (const item of data) {
    if (!lookup[item.month]) lookup[item.month] = {};
    lookup[item.month][item.category] = item.total;
  }
  const colTotals: Record<string, number> = {};
  for (const cat of tableCategories) {
    colTotals[cat] = tableMonths.reduce((s, m) => s + (lookup[m]?.[cat] ?? 0), 0);
  }
  const netByMonth: Record<string, number> = {};
  for (const m of tableMonths) {
    const positiveSum = tableCategories
      .filter((c) => POSITIVE_CATEGORIES.has(c))
      .reduce((s, c) => s - (lookup[m]?.[c] ?? 0), 0);
    const expenseSum = expenseCategories.reduce((s, c) => s + (lookup[m]?.[c] ?? 0), 0);
    netByMonth[m] = positiveSum - expenseSum;
  }
  const grandNet = tableMonths.reduce((s, m) => s + netByMonth[m], 0);

  const toggleCategory = (cat: string) => {
    setSelectedCategories((prev) =>
      prev.includes(cat) ? prev.filter((c) => c !== cat) : [...prev, cat]
    );
  };

  const handleApply = () => {
    setAppliedFrom(dateFrom);
    setAppliedTo(dateTo);
  };

  const handleReset = () => {
    setDateFrom("");
    setDateTo("");
    setAppliedFrom("");
    setAppliedTo("");
    setSelectedCategories([]);
  };

  // Group comments by month (YYYY-MM) or by exact date when a single day is selected
  const singleDay = appliedFrom && appliedTo && appliedFrom === appliedTo;
  const commentGroups: { label: string; items: CommentedExpense[] }[] = (() => {
    if (comments.length === 0) return [];
    if (singleDay) {
      return [{ label: appliedFrom, items: comments }];
    }
    const map = new Map<string, CommentedExpense[]>();
    for (const c of comments) {
      const key = c.date.slice(0, 7);
      if (!map.has(key)) map.set(key, []);
      map.get(key)!.push(c);
    }
    return Array.from(map.entries())
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([label, items]) => ({ label, items }));
  })();

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-gray-900">Dashboard</h1>

      {/* Print-only date range */}
      {(appliedFrom || appliedTo) && (
        <p className="hidden print:block text-sm text-gray-500 -mt-2">
          Period: {appliedFrom || "start"} &mdash; {appliedTo || "present"}
        </p>
      )}

      {/* Filter bar */}
      <div className="print:hidden flex flex-wrap items-end gap-4 rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-gray-600">From</label>
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className="rounded border border-gray-300 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-gray-600">To</label>
          <input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className="rounded border border-gray-300 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
          />
        </div>
        <button
          onClick={handleApply}
          className="rounded bg-blue-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-400"
        >
          Apply
        </button>
        <button
          onClick={handleReset}
          className="rounded border border-gray-300 px-4 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-300"
        >
          Reset
        </button>
        <button
          onClick={() => window.print()}
          className="rounded border border-gray-300 px-4 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-300 ml-auto flex items-center gap-1.5"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M7 10l5 5 5-5M12 15V3" />
          </svg>
          Export PDF
        </button>
      </div>

      {/* Category filter */}
      {allCategories.length > 0 && (
        <div className="print:hidden rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <div className="mb-2 flex items-center justify-between">
            <span className="text-xs font-medium text-gray-600">
              Filter categories
              {selectedCategories.length > 0 && (
                <span className="ml-2 text-blue-600">({selectedCategories.length} selected)</span>
              )}
            </span>
            {selectedCategories.length > 0 && (
              <button
                onClick={() => setSelectedCategories([])}
                className="text-xs text-gray-500 hover:text-gray-700 underline"
              >
                Clear
              </button>
            )}
          </div>
          <div className="flex flex-wrap gap-2">
            {allCategories.map((cat, i) => {
              const active = selectedCategories.length === 0 || selectedCategories.includes(cat);
              return (
                <button
                  key={cat}
                  onClick={() => toggleCategory(cat)}
                  className="flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition-colors"
                  style={{
                    borderColor: PALETTE[i % PALETTE.length],
                    backgroundColor: active ? PALETTE[i % PALETTE.length] : "transparent",
                    color: active ? "#fff" : PALETTE[i % PALETTE.length],
                  }}
                >
                  {cat}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {error && (
        <div className="print:hidden rounded-md bg-red-50 border border-red-200 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-16 text-sm text-gray-500">Loading…</div>
      ) : rows.length === 0 ? (
        <div className="flex justify-center py-16 text-sm text-gray-500">No data available.</div>
      ) : (
        <div className="break-inside-avoid rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <p className="mb-3 text-xs text-gray-400 print:hidden">Click a bar to filter by that month</p>
          <ResponsiveContainer width="100%" height={480}>
            <BarChart
              data={rows}
              margin={{ top: 8, right: 24, left: 16, bottom: 80 }}
              style={{ cursor: "pointer" }}
              onClick={(chartData: { activeLabel?: string }) => {
                if (!chartData?.activeLabel) return;
                const month = chartData.activeLabel;
                const [year, mon] = month.split("-").map(Number);
                const firstDay = `${month}-01`;
                const lastDay = new Date(year, mon, 0).toISOString().split("T")[0];
                setDateFrom(firstDay);
                setDateTo(lastDay);
                setAppliedFrom(firstDay);
                setAppliedTo(lastDay);
              }}
            >
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis
                dataKey="month"
                tick={{ fontSize: 12 }}
                angle={-45}
                textAnchor="end"
                interval={0}
              />
              <YAxis
                tickFormatter={(v: number) =>
                  v >= 1000 ? `$${(v / 1000).toFixed(1)}k` : `$${v}`
                }
                tick={{ fontSize: 12 }}
              />
              <Tooltip
                formatter={(value: number, name: string) => [
                  `$${value.toFixed(2)}`,
                  name,
                ]}
              />
              <Legend verticalAlign="bottom" wrapperStyle={{ paddingTop: 16 }} />
              {categories.map((cat) => {
                const i = allCategories.indexOf(cat);
                return (
                  <Bar
                    key={cat}
                    dataKey={cat}
                    stackId="a"
                    fill={PALETTE[i % PALETTE.length]}
                  />
                );
              })}
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Summary table */}
      {!loading && tableMonths.length > 0 && (
        <div className="break-inside-avoid rounded-lg border border-gray-200 bg-white shadow-sm overflow-hidden">
          <h2 className="px-6 pt-5 pb-3 text-base font-semibold text-gray-800">Monthly Summary</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full text-xs">
              <thead>
                <tr className="bg-gray-50 border-y border-gray-200">
                  <th className="sticky left-0 z-10 bg-gray-50 px-4 py-2 text-left font-semibold text-gray-600">Month</th>
                  {tableCategories.map((cat) => (
                    <th key={cat} className="px-4 py-2 text-right font-semibold text-gray-600 whitespace-nowrap">{cat}</th>
                  ))}
                  <th className="px-4 py-2 text-right font-semibold text-gray-900 whitespace-nowrap border-l border-gray-200">Net</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {tableMonths.map((month) => {
                  const net = netByMonth[month];
                  return (
                    <tr key={month} className="hover:bg-gray-50">
                      <td className="sticky left-0 z-10 bg-white hover:bg-gray-50 px-4 py-2 font-medium text-gray-700 whitespace-nowrap">{month}</td>
                      {tableCategories.map((cat) => {
                        const v = lookup[month]?.[cat];
                        const isPositive = POSITIVE_CATEGORIES.has(cat) && v !== undefined && v < 0;
                        return (
                          <td key={cat} className={`px-4 py-2 text-right whitespace-nowrap tabular-nums ${isPositive ? "text-green-700" : "text-gray-700"}`}>
                            {v !== undefined ? fmt(isPositive ? -v : v) : ""}
                          </td>
                        );
                      })}
                      <td className={`px-4 py-2 text-right font-semibold whitespace-nowrap tabular-nums border-l border-gray-200 ${
                        net >= 0 ? "text-green-700" : "text-red-600"
                      }`}>
                        {fmt(net)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
              <tfoot>
                <tr className="bg-gray-50 border-t-2 border-gray-300 font-semibold">
                  <td className="sticky left-0 z-10 bg-gray-50 px-4 py-2 text-gray-700">Total</td>
                  {tableCategories.map((cat) => {
                    const v = colTotals[cat] ?? 0;
                    const isPositive = POSITIVE_CATEGORIES.has(cat) && v < 0;
                    return (
                      <td key={cat} className={`px-4 py-2 text-right whitespace-nowrap tabular-nums ${isPositive ? "text-green-700" : "text-gray-800"}`}>
                        {fmt(isPositive ? -v : v)}
                      </td>
                    );
                  })}
                  <td className={`px-4 py-2 text-right whitespace-nowrap tabular-nums border-l border-gray-200 ${
                    grandNet >= 0 ? "text-green-700" : "text-red-600"
                  }`}>
                    {fmt(grandNet)}
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      )}

      {/* Property chart */}
      <div className="break-inside-avoid rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-base font-semibold text-gray-800">Expenses by Property</h2>
        {propertyLoading ? (
          <div className="flex justify-center py-10 text-sm text-gray-500">Loading…</div>
        ) : propertyRows.length === 0 ? (
          <div className="flex justify-center py-10 text-sm text-gray-500">No property data available.</div>
        ) : (
          <ResponsiveContainer width="100%" height={360}>
            <BarChart data={propertyRows} margin={{ top: 8, right: 24, left: 16, bottom: 80 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis
                dataKey="month"
                tick={{ fontSize: 12 }}
                angle={-45}
                textAnchor="end"
                interval={0}
              />
              <YAxis
                tickFormatter={(v: number) =>
                  v >= 1000 ? `$${(v / 1000).toFixed(1)}k` : `$${v}`
                }
                tick={{ fontSize: 12 }}
              />
              <Tooltip
                formatter={(value: number, name: string) => [`$${value.toFixed(2)}`, name]}
              />
              <Legend verticalAlign="bottom" wrapperStyle={{ paddingTop: 16 }} />
              {propertyNames.map((prop, i) => (
                <Bar
                  key={prop}
                  dataKey={prop}
                  stackId="p"
                  fill={PALETTE[(i + 5) % PALETTE.length]}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Property summary table */}
      {!propertyLoading && propTableMonths.length > 0 && (
        <div className="break-inside-avoid rounded-lg border border-gray-200 bg-white shadow-sm overflow-hidden">
          <h2 className="px-6 pt-5 pb-3 text-base font-semibold text-gray-800">Monthly Property Summary</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full text-xs">
              <thead>
                <tr className="bg-gray-50 border-y border-gray-200">
                  <th className="sticky left-0 z-10 bg-gray-50 px-4 py-2 text-left font-semibold text-gray-600">Month</th>
                  {propTableProperties.map((prop) => (
                    <th key={prop} className="px-4 py-2 text-right font-semibold text-gray-600 whitespace-nowrap">{prop}</th>
                  ))}
                  <th className="px-4 py-2 text-right font-semibold text-gray-900 whitespace-nowrap border-l border-gray-200">Total</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {propTableMonths.map((month) => {
                  const rowTotal = propRowTotals[month];
                  const isRowPositive = rowTotal < 0;
                  return (
                    <tr key={month} className="hover:bg-gray-50">
                      <td className="sticky left-0 z-10 bg-white hover:bg-gray-50 px-4 py-2 font-medium text-gray-700 whitespace-nowrap">{month}</td>
                      {propTableProperties.map((prop) => {
                        const v = propLookup[month]?.[prop];
                        const isPositive = v !== undefined && v < 0;
                        return (
                          <td key={prop} className={`px-4 py-2 text-right whitespace-nowrap tabular-nums ${isPositive ? "text-green-700" : "text-gray-700"}`}>
                            {v !== undefined ? fmt(isPositive ? -v : v) : ""}
                          </td>
                        );
                      })}
                      <td className={`px-4 py-2 text-right font-semibold whitespace-nowrap tabular-nums border-l border-gray-200 ${isRowPositive ? "text-green-700" : "text-red-600"}`}>
                        {fmt(isRowPositive ? -rowTotal : rowTotal)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
              <tfoot>
                <tr className="bg-gray-50 border-t-2 border-gray-300 font-semibold">
                  <td className="sticky left-0 z-10 bg-gray-50 px-4 py-2 text-gray-700">Total</td>
                  {propTableProperties.map((prop) => {
                    const v = propColTotals[prop] ?? 0;
                    const isPositive = v < 0;
                    return (
                      <td key={prop} className={`px-4 py-2 text-right whitespace-nowrap tabular-nums ${isPositive ? "text-green-700" : "text-gray-800"}`}>
                        {fmt(isPositive ? -v : v)}
                      </td>
                    );
                  })}
                  <td className={`px-4 py-2 text-right whitespace-nowrap tabular-nums border-l border-gray-200 ${propGrandTotal < 0 ? "text-green-700" : "text-red-600"}`}>
                    {fmt(propGrandTotal < 0 ? -propGrandTotal : propGrandTotal)}
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      )}

      {/* Comments section */}
      <div className="break-inside-avoid rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-base font-semibold text-gray-800">Expense Comments</h2>
        {commentsLoading ? (
          <p className="text-sm text-gray-500">Loading…</p>
        ) : commentGroups.length === 0 ? (
          <p className="text-sm text-gray-500">No comments found for this period.</p>
        ) : (
          <div className="space-y-6">
            {commentGroups.map(({ label, items }) => (
              <div key={label}>
                <h3 className="mb-2 text-sm font-medium text-gray-600 border-b border-gray-100 pb-1">{label}</h3>
                <ul className="divide-y divide-gray-100">
                  {items.map((c) => (
                    <li key={c.id} className="py-2 flex flex-col gap-0.5">
                      <div className="flex items-center justify-between gap-4">
                        <span className="text-sm font-medium text-gray-800 truncate">{c.description}</span>
                        <div className="shrink-0 flex items-center gap-3">
                          {c.credit != null && c.credit > 0 && (c.debit == null || c.credit > c.debit) ? (
                            <span className="text-sm font-semibold text-green-700">{fmt(c.credit)}</span>
                          ) : c.debit != null && c.debit > 0 ? (
                            <span className="text-sm font-semibold text-gray-800">{fmt(c.debit)}</span>
                          ) : null}
                          <span className="text-xs text-gray-400">{c.date}</span>
                        </div>
                      </div>
                      {c.category && (
                        <span className="text-xs text-gray-500">{c.category}</span>
                      )}
                      <p className="text-sm text-gray-700 mt-0.5">{c.comments}</p>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

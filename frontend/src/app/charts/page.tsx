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

interface ChartRow {
  month: string;
  [category: string]: number | string;
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

export default function ChartsPage() {
  const [data, setData] = useState<SummaryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [appliedFrom, setAppliedFrom] = useState("");
  const [appliedTo, setAppliedTo] = useState("");

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
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load summary");
          setLoading(false);
        }
      });

    return () => { cancelled = true; };
  }, [appliedFrom, appliedTo]);

  const { rows, categories } = pivot(data);

  const handleApply = () => {
    setAppliedFrom(dateFrom);
    setAppliedTo(dateTo);
  };

  const handleReset = () => {
    setDateFrom("");
    setDateTo("");
    setAppliedFrom("");
    setAppliedTo("");
  };

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-gray-900">Expenses by Month &amp; Category</h1>

      {/* Filter bar */}
      <div className="flex flex-wrap items-end gap-4 rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
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
      </div>

      {error && (
        <div className="rounded-md bg-red-50 border border-red-200 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-16 text-sm text-gray-500">Loading…</div>
      ) : rows.length === 0 ? (
        <div className="flex justify-center py-16 text-sm text-gray-500">No data available.</div>
      ) : (
        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <ResponsiveContainer width="100%" height={480}>
            <BarChart data={rows} margin={{ top: 8, right: 24, left: 16, bottom: 80 }}>
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
              {categories.map((cat, i) => (
                <Bar
                  key={cat}
                  dataKey={cat}
                  stackId="a"
                  fill={PALETTE[i % PALETTE.length]}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

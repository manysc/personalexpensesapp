"use client";

import { useEffect, useRef, useState } from "react";

const MONTHS = [
  "jan", "feb", "mar", "apr", "may", "jun",
  "jul", "aug", "sep", "oct", "nov", "dec",
];

const MONTH_LABELS: Record<string, string> = {
  jan: "Jan", feb: "Feb", mar: "Mar", apr: "Apr",
  may: "May", jun: "Jun", jul: "Jul", aug: "Aug",
  sep: "Sep", oct: "Oct", nov: "Nov", dec: "Dec",
};

const BANKS = [
  { key: "citi",       label: "Citi"        },
  { key: "wellsfargo", label: "Wells Fargo" },
  { key: "chase",      label: "Chase"       },
  { key: "banamex",    label: "Banamex"     },
] as const;

type BankKey = (typeof BANKS)[number]["key"];
type SelectedMonths = Record<BankKey, Set<string>>;

function emptySelection(): SelectedMonths {
  return { citi: new Set(), wellsfargo: new Set(), chase: new Set(), banamex: new Set() };
}

export default function ImportPage() {
  const [year, setYear] = useState("2026");
  const [selectedMonths, setSelectedMonths] = useState<SelectedMonths>(emptySelection);
  const [running, setRunning] = useState(false);
  const [output, setOutput] = useState<string | null>(null);
  const [hasError, setHasError] = useState(false);
  const outputRef = useRef<HTMLPreElement>(null);

  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [output]);

  function toggleMonth(bank: BankKey, month: string) {
    setSelectedMonths((prev) => {
      const next = new Set(prev[bank]);
      if (next.has(month)) next.delete(month);
      else next.add(month);
      return { ...prev, [bank]: next };
    });
  }

  function toggleBank(bank: BankKey, checked: boolean) {
    setSelectedMonths((prev) => ({
      ...prev,
      [bank]: checked ? new Set(MONTHS) : new Set<string>(),
    }));
  }

  async function handleRun() {
    setRunning(true);
    setOutput("");
    setHasError(false);

    const body = {
      year,
      citi_months: Array.from(selectedMonths.citi),
      wellsfargo_months: Array.from(selectedMonths.wellsfargo),
      chase_months: Array.from(selectedMonths.chase),
      banamex_months: Array.from(selectedMonths.banamex),
    };

    try {
      const response = await fetch("/api/pipeline/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!response.ok || !response.body) {
        setOutput(`HTTP error: ${response.status}`);
        setHasError(true);
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        setOutput((prev) => (prev ?? "") + chunk);
        if (chunk.includes("ERROR:")) setHasError(true);
      }
    } catch (err) {
      setOutput(`Error: ${String(err)}`);
      setHasError(true);
    } finally {
      setRunning(false);
    }
  }

  const anySelected = BANKS.some((b) => selectedMonths[b.key].size > 0);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h1 className="text-2xl font-semibold text-gray-800">Import Expenses</h1>

      {/* Year */}
      <div className="flex items-center gap-3">
        <label className="text-sm font-medium text-gray-700 w-16">Year</label>
        <input
          type="text"
          value={year}
          onChange={(e) => setYear(e.target.value)}
          disabled={running}
          className="border border-gray-300 rounded px-3 py-1.5 text-sm w-28 focus:outline-none focus:ring-2 focus:ring-blue-400 disabled:bg-gray-100"
        />
      </div>

      {/* Bank sections */}
      <div className="space-y-3">
        {BANKS.map(({ key, label }) => {
          const selected = selectedMonths[key];
          const allChecked = selected.size === MONTHS.length;
          const someChecked = selected.size > 0 && !allChecked;

          return (
            <div key={key} className="border border-gray-200 rounded-lg p-4 bg-white">
              <div className="flex items-center gap-2 mb-3">
                <input
                  type="checkbox"
                  id={`bank-${key}`}
                  checked={allChecked}
                  ref={(el) => { if (el) el.indeterminate = someChecked; }}
                  onChange={(e) => toggleBank(key, e.target.checked)}
                  disabled={running}
                  className="w-4 h-4 accent-blue-600"
                />
                <label
                  htmlFor={`bank-${key}`}
                  className="text-sm font-semibold text-gray-700 cursor-pointer select-none"
                >
                  {label}
                </label>
                {selected.size > 0 && (
                  <span className="text-xs text-gray-400">
                    ({selected.size} month{selected.size !== 1 ? "s" : ""})
                  </span>
                )}
              </div>
              <div className="flex flex-wrap gap-x-4 gap-y-1.5">
                {MONTHS.map((month) => (
                  <label key={month} className="flex items-center gap-1.5 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={selected.has(month)}
                      onChange={() => toggleMonth(key, month)}
                      disabled={running}
                      className="w-3.5 h-3.5 accent-blue-600"
                    />
                    <span className="text-xs text-gray-600">{MONTH_LABELS[month]}</span>
                  </label>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Run button */}
      <button
        onClick={handleRun}
        disabled={running || !anySelected || !year.trim()}
        className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white text-sm font-medium px-5 py-2 rounded transition-colors"
      >
        {running && (
          <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
        )}
        {running ? "Running…" : "Run Pipeline"}
      </button>

      {/* Streaming output */}
      {output !== null && (
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-gray-700">Output</span>
            {!running && (
              <span
                className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                  hasError
                    ? "bg-red-100 text-red-700"
                    : "bg-green-100 text-green-700"
                }`}
              >
                {hasError ? "Completed with errors" : "Completed"}
              </span>
            )}
            {running && (
              <span className="text-xs text-gray-400 animate-pulse">live</span>
            )}
          </div>
          <pre
            ref={outputRef}
            className={`text-xs font-mono p-4 rounded border overflow-auto max-h-[32rem] whitespace-pre-wrap break-words ${
              hasError
                ? "border-red-300 bg-red-50 text-red-900"
                : "border-gray-200 bg-gray-50 text-gray-800"
            }`}
          >
            {output || " "}
          </pre>
        </div>
      )}
    </div>
  );
}

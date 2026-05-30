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
type MonthSet = Record<BankKey, Set<string>>;

function emptyMonthSets(): MonthSet {
  return { citi: new Set(), wellsfargo: new Set(), chase: new Set(), banamex: new Set() };
}

export default function ImportPage() {
  const [year, setYear] = useState("2026");
  const [selectedMonths, setSelectedMonths] = useState<MonthSet>(emptyMonthSets);
  const [availableFiles, setAvailableFiles] = useState<MonthSet>(emptyMonthSets);
  const [loadingFiles, setLoadingFiles] = useState(false);
  const [uploading, setUploading] = useState<Record<string, boolean>>({});
  const [running, setRunning] = useState(false);
  const [output, setOutput] = useState<string | null>(null);
  const [hasError, setHasError] = useState(false);
  const outputRef = useRef<HTMLPreElement>(null);

  // Load available statement files whenever year changes
  useEffect(() => {
    if (!year.trim() || !/^\d{4}$/.test(year)) return;
    setLoadingFiles(true);
    Promise.all(
      BANKS.map(async ({ key }) => {
        try {
          const res = await fetch(`/api/statements/${key}/${year}`);
          return [key, res.ok ? (await res.json() as string[]) : []] as const;
        } catch {
          return [key, [] as string[]] as const;
        }
      })
    ).then((results) => {
      const files = emptyMonthSets();
      for (const [k, months] of results) files[k as BankKey] = new Set(months);
      setAvailableFiles(files);
      setLoadingFiles(false);
    });
  }, [year]);

  // Auto-scroll output
  useEffect(() => {
    if (outputRef.current) outputRef.current.scrollTop = outputRef.current.scrollHeight;
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

  function selectAvailable(bank: BankKey) {
    setSelectedMonths((prev) => ({ ...prev, [bank]: new Set(availableFiles[bank]) }));
  }

  async function handleUpload(bank: BankKey, month: string, file: File) {
    const uploadKey = `${bank}-${month}`;
    setUploading((prev) => ({ ...prev, [uploadKey]: true }));
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await fetch(`/api/statements/${bank}/${year}/${month}`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) throw new Error(String(res.status));
      // Mark file as available and auto-select the month for the run
      setAvailableFiles((prev) => ({ ...prev, [bank]: new Set([...prev[bank], month]) }));
      setSelectedMonths((prev) => ({ ...prev, [bank]: new Set([...prev[bank], month]) }));
    } catch (err) {
      alert(`Upload failed for ${bank} ${month}: ${String(err)}`);
    } finally {
      setUploading((prev) => ({ ...prev, [uploadKey]: false }));
    }
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
        {loadingFiles && (
          <span className="text-xs text-gray-400 animate-pulse">Loading statements…</span>
        )}
      </div>

      {/* Bank sections */}
      <div className="space-y-3">
        {BANKS.map(({ key, label }) => {
          const selected = selectedMonths[key];
          const available = availableFiles[key];
          const allChecked = selected.size === MONTHS.length;
          const someChecked = selected.size > 0 && !allChecked;

          return (
            <div key={key} className="border border-gray-200 rounded-lg p-4 bg-white">
              {/* Bank header */}
              <div className="flex items-center gap-2 mb-3 flex-wrap">
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
                  <span className="text-xs text-gray-400">({selected.size} selected)</span>
                )}
                {available.size > 0 && (
                  <>
                    <span className="text-xs text-gray-300">·</span>
                    <span className="text-xs text-gray-400">
                      {available.size} file{available.size !== 1 ? "s" : ""} available
                    </span>
                    <button
                      onClick={() => selectAvailable(key)}
                      disabled={running}
                      className="text-xs text-blue-500 hover:text-blue-700 disabled:text-gray-300"
                    >
                      Select available
                    </button>
                  </>
                )}
              </div>

              {/* Month grid: 6 columns × 2 rows */}
              <div className="grid grid-cols-6 gap-1.5">
                {MONTHS.map((month) => {
                  const isAvailable = available.has(month);
                  const isUploading = !!uploading[`${key}-${month}`];
                  const isSelected = selected.has(month);

                  return (
                    <div
                      key={month}
                      className={`border rounded p-2 text-xs flex flex-col gap-1.5 ${
                        isAvailable
                          ? "border-green-200 bg-green-50"
                          : "border-gray-100 bg-gray-50"
                      }`}
                    >
                      {/* Checkbox + month label */}
                      <label className="flex items-center gap-1 cursor-pointer select-none">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => toggleMonth(key, month)}
                          disabled={running}
                          className="w-3 h-3 accent-blue-600 flex-shrink-0"
                        />
                        <span className="font-medium text-gray-700">{MONTH_LABELS[month]}</span>
                      </label>

                      {/* Status + action buttons */}
                      <div className="flex items-center gap-1">
                        {isAvailable ? (
                          <span className="text-green-500 leading-none" title="Statement available">●</span>
                        ) : (
                          <span className="text-gray-300 leading-none" title="No statement">○</span>
                        )}

                        {/* Upload */}
                        <label
                          title={`Upload ${label} ${MONTH_LABELS[month]} statement`}
                          className={`ml-auto cursor-pointer ${
                            isUploading ? "opacity-50 pointer-events-none" : "text-gray-400 hover:text-blue-500"
                          }`}
                        >
                          <input
                            type="file"
                            accept=".pdf"
                            className="sr-only"
                            disabled={running || isUploading}
                            onChange={(e) => {
                              const file = e.target.files?.[0];
                              if (file) handleUpload(key, month, file);
                              e.currentTarget.value = "";
                            }}
                          />
                          {isUploading ? (
                            <svg className="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                            </svg>
                          ) : (
                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                            </svg>
                          )}
                        </label>

                        {/* View / Download (only when file exists) */}
                        {isAvailable && (
                          <>
                            <a
                              href={`/api/statements/${key}/${year}/${month}?view=1`}
                              target="_blank"
                              rel="noopener noreferrer"
                              title={`View ${label} ${MONTH_LABELS[month]} statement`}
                              className="text-gray-400 hover:text-blue-500"
                            >
                              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.477 0 8.268 2.943 9.542 7-1.274 4.057-5.065 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                              </svg>
                            </a>
                            <a
                              href={`/api/statements/${key}/${year}/${month}`}
                              download
                              title={`Download ${label} ${MONTH_LABELS[month]} statement`}
                              className="text-gray-400 hover:text-blue-500"
                            >
                              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                              </svg>
                            </a>
                          </>
                        )}
                      </div>
                    </div>
                  );
                })}
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
                  hasError ? "bg-red-100 text-red-700" : "bg-green-100 text-green-700"
                }`}
              >
                {hasError ? "Completed with errors" : "Completed"}
              </span>
            )}
            {running && <span className="text-xs text-gray-400 animate-pulse">live</span>}
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

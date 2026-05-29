"use client";

import type { Category, Expense, RentalProperty } from "@/types/expense";
import { useEffect, useRef, useState } from "react";

interface Props {
  onClose: () => void;
  onSuccess: (expense: Expense) => void;
}

const BANKS = ["banamex", "cash", "chase", "citi", "wellsfargo"];

const inputClass =
  "w-full rounded border border-gray-300 px-2 py-1 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50";

export default function AddExpenseModal({ onClose, onSuccess }: Props) {
  const [date, setDate] = useState("");
  const [bank, setBank] = useState("");
  const [description, setDescription] = useState("");
  const [debit, setDebit] = useState("");
  const [credit, setCredit] = useState("");
  const [category, setCategory] = useState("");
  const [propertyId, setPropertyId] = useState("");
  const [comments, setComments] = useState("");

  const [categories, setCategories] = useState<string[]>([]);
  const [properties, setProperties] = useState<RentalProperty[]>([]);

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [receiptFile, setReceiptFile] = useState<File | null>(null);
  const [receiptPreview, setReceiptPreview] = useState<string | null>(null);
  const receiptInputRef = useRef<HTMLInputElement>(null);

  const backdropRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch("/api/categories")
      .then((r) => r.json() as Promise<Category[]>)
      .then((data) => setCategories(data.map((c) => c.name)))
      .catch(() => setCategories([]));
    fetch("/api/rental-properties")
      .then((r) => r.json() as Promise<RentalProperty[]>)
      .then(setProperties)
      .catch(() => setProperties([]));
  }, []);

  function handleBackdropClick(e: React.MouseEvent) {
    if (e.target === backdropRef.current) onClose();
  }

  function handleReceiptChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0] ?? null;
    setReceiptFile(file);
    if (receiptPreview) URL.revokeObjectURL(receiptPreview);
    setReceiptPreview(file && file.type.startsWith("image/") ? URL.createObjectURL(file) : null);
  }

  function handleReceiptClear() {
    setReceiptFile(null);
    if (receiptPreview) URL.revokeObjectURL(receiptPreview);
    setReceiptPreview(null);
    if (receiptInputRef.current) receiptInputRef.current.value = "";
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!date || !bank || !description) {
      setError("Date, bank, and description are required.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const body: Record<string, unknown> = {
        date,
        bank,
        description,
        debit: debit !== "" ? Number(debit) : null,
        credit: credit !== "" ? Number(credit) : null,
        category: category || null,
        property_id: propertyId ? Number(propertyId) : null,
        comments: comments || null,
      };
      const res = await fetch("/api/expenses", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data?.detail ?? `Error ${res.status}: ${res.statusText}`);
      }
      const created: Expense = await res.json();
      let finalExpense = created;
      if (receiptFile) {
        const formData = new FormData();
        formData.append("receipt", receiptFile);
        const uploadRes = await fetch(`/api/expenses/${created.id}/receipt`, {
          method: "POST",
          body: formData,
        });
        if (uploadRes.ok) finalExpense = await uploadRes.json();
      }
      onSuccess(finalExpense);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create expense");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div
      ref={backdropRef}
      onClick={handleBackdropClick}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
    >
      <div className="w-full max-w-lg rounded-lg bg-white shadow-xl">
        {/* Modal header */}
        <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
          <h2 className="text-base font-semibold text-gray-900">Add Expense</h2>
          <button
            onClick={onClose}
            aria-label="Close"
            className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5">
              <path d="M6.28 5.22a.75.75 0 0 0-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 1 0 1.06 1.06L10 11.06l3.72 3.72a.75.75 0 1 0 1.06-1.06L11.06 10l3.72-3.72a.75.75 0 0 0-1.06-1.06L10 8.94 6.28 5.22Z" />
            </svg>
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="divide-y divide-gray-100">
          <div className="grid grid-cols-2 gap-4 px-6 py-4">
            {/* Date */}
            <div className="col-span-1 flex flex-col gap-1">
              <label className="text-xs font-medium text-gray-500">Date *</label>
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className={inputClass}
                disabled={saving}
                required
              />
            </div>

            {/* Bank */}
            <div className="col-span-1 flex flex-col gap-1">
              <label className="text-xs font-medium text-gray-500">Bank *</label>
              <select
                value={bank}
                onChange={(e) => setBank(e.target.value)}
                className={inputClass}
                disabled={saving}
                required
              >
                <option value="">— select —</option>
                {BANKS.map((b) => (
                  <option key={b} value={b}>{b}</option>
                ))}
              </select>
            </div>

            {/* Description */}
            <div className="col-span-2 flex flex-col gap-1">
              <label className="text-xs font-medium text-gray-500">Description *</label>
              <input
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className={inputClass}
                disabled={saving}
                placeholder="Expense description"
                required
              />
            </div>

            {/* Debit */}
            <div className="col-span-1 flex flex-col gap-1">
              <label className="text-xs font-medium text-gray-500">Debit (USD)</label>
              <input
                type="number"
                min="0"
                step="0.01"
                value={debit}
                onChange={(e) => setDebit(e.target.value)}
                className={inputClass}
                disabled={saving}
                placeholder="0.00"
              />
            </div>

            {/* Credit */}
            <div className="col-span-1 flex flex-col gap-1">
              <label className="text-xs font-medium text-gray-500">Credit (USD)</label>
              <input
                type="number"
                min="0"
                step="0.01"
                value={credit}
                onChange={(e) => setCredit(e.target.value)}
                className={inputClass}
                disabled={saving}
                placeholder="0.00"
              />
            </div>

            {/* Category */}
            <div className="col-span-1 flex flex-col gap-1">
              <label className="text-xs font-medium text-gray-500">Category</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className={inputClass}
                disabled={saving}
              >
                <option value="">— none —</option>
                {categories.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>

            {/* Rental Property */}
            <div className="col-span-1 flex flex-col gap-1">
              <label className="text-xs font-medium text-gray-500">Rental Property</label>
              <select
                value={propertyId}
                onChange={(e) => setPropertyId(e.target.value)}
                className={inputClass}
                disabled={saving}
              >
                <option value="">— none —</option>
                {properties.map((p) => (
                  <option key={p.id} value={String(p.id)}>{p.alias}</option>
                ))}
              </select>
            </div>

            {/* Comments */}
            <div className="col-span-2 flex flex-col gap-1">
              <label className="text-xs font-medium text-gray-500">Comments</label>
              <textarea
                value={comments}
                onChange={(e) => setComments(e.target.value)}
                rows={2}
                className={inputClass}
                placeholder="Optional notes…"
                disabled={saving}
              />
            </div>
            {/* Receipt */}
            <div className="col-span-2 flex flex-col gap-1">
              <label className="text-xs font-medium text-gray-500">Receipt (optional)</label>
              {receiptFile ? (
                <div className="flex items-center gap-3 rounded border border-gray-200 bg-gray-50 px-3 py-2">
                  {receiptPreview ? (
                    <img src={receiptPreview} alt="preview" className="h-10 w-10 rounded object-cover shrink-0" />
                  ) : (
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="h-8 w-8 shrink-0 text-gray-400" aria-hidden="true">
                      <path d="M2 3.5A1.5 1.5 0 0 1 3.5 2h6.879a1.5 1.5 0 0 1 1.06.44l2.122 2.12a1.5 1.5 0 0 1 .439 1.061V12.5A1.5 1.5 0 0 1 12.5 14h-9A1.5 1.5 0 0 1 2 12.5v-9Z" />
                    </svg>
                  )}
                  <span className="flex-1 truncate text-sm text-gray-700" title={receiptFile.name}>
                    {receiptFile.name}
                  </span>
                  {receiptPreview && (
                    <a
                      href={receiptPreview}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="shrink-0 text-xs text-blue-600 hover:underline"
                    >
                      View
                    </a>
                  )}
                  <button
                    type="button"
                    onClick={handleReceiptClear}
                    disabled={saving}
                    aria-label="Remove receipt"
                    className="shrink-0 rounded p-0.5 text-gray-400 hover:bg-gray-200 hover:text-gray-600 disabled:opacity-50"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
                      <path d="M6.28 5.22a.75.75 0 0 0-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 1 0 1.06 1.06L10 11.06l3.72 3.72a.75.75 0 1 0 1.06-1.06L11.06 10l3.72-3.72a.75.75 0 0 0-1.06-1.06L10 8.94 6.28 5.22Z" />
                    </svg>
                  </button>
                </div>
              ) : (
                <label className="flex cursor-pointer items-center gap-2 rounded border border-dashed border-gray-300 px-3 py-2 text-sm text-gray-500 hover:border-blue-400 hover:text-blue-600">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="h-4 w-4 shrink-0" aria-hidden="true">
                    <path d="M8.75 3.75a.75.75 0 0 0-1.5 0v3.5h-3.5a.75.75 0 0 0 0 1.5h3.5v3.5a.75.75 0 0 0 1.5 0v-3.5h3.5a.75.75 0 0 0 0-1.5h-3.5v-3.5Z" />
                  </svg>
                  Attach receipt
                  <input
                    ref={receiptInputRef}
                    type="file"
                    className="hidden"
                    accept="image/*,.pdf"
                    onChange={handleReceiptChange}
                    disabled={saving}
                  />
                </label>
              )}
            </div>
          </div>
          <div className="flex items-center justify-end gap-3 px-6 py-4">
            {error && <p className="mr-auto text-sm text-red-600">{error}</p>}
            <button
              type="button"
              onClick={onClose}
              disabled={saving}
              className="rounded border border-gray-300 px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {saving ? "Saving…" : "Add expense"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

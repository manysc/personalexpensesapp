"use client";

import type { Category } from "@/types/expense";
import { useEffect, useState } from "react";

const EMPTY_FORM = { name: "", keywords: "" };

export default function CategoriesPage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Category | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null);
  const [seeding, setSeeding] = useState(false);
  const [seedResult, setSeedResult] = useState<string | null>(null);

  function loadCategories() {
    setLoading(true);
    setError(null);
    fetch("/api/categories")
      .then((res) => {
        if (!res.ok) throw new Error(`Error ${res.status}: ${res.statusText}`);
        return res.json() as Promise<Category[]>;
      })
      .then((data) => {
        setCategories(data);
        setLoading(false);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Failed to load categories");
        setLoading(false);
      });
  }

  useEffect(() => {
    loadCategories();
  }, []);

  function openCreate() {
    setEditing(null);
    setForm(EMPTY_FORM);
    setFormError(null);
    setShowForm(true);
  }

  function openEdit(cat: Category) {
    setEditing(cat);
    setForm({ name: cat.name, keywords: cat.keywords.join("\n") });
    setFormError(null);
    setShowForm(true);
  }

  function closeForm() {
    setShowForm(false);
    setEditing(null);
    setForm(EMPTY_FORM);
    setFormError(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.name.trim()) {
      setFormError("Category name is required.");
      return;
    }
    setSaving(true);
    setFormError(null);
    try {
      const keywords = form.keywords
        .split("\n")
        .map((k) => k.trim())
        .filter(Boolean);
      const payload = { name: form.name.trim(), keywords };
      const url = editing ? `/api/categories/${editing.id}` : "/api/categories";
      const method = editing ? "PUT" : "POST";
      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error((data as { detail?: string }).detail ?? `Error ${res.status}`);
      }
      closeForm();
      loadCategories();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Failed to save category");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: number) {
    try {
      const res = await fetch(`/api/categories/${id}`, { method: "DELETE" });
      if (!res.ok && res.status !== 204) {
        const data = await res.json().catch(() => ({}));
        throw new Error((data as { detail?: string }).detail ?? `Error ${res.status}`);
      }
      setConfirmDeleteId(null);
      loadCategories();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to delete category");
    }
  }

  async function handleSeed() {
    setSeeding(true);
    setSeedResult(null);
    setError(null);
    try {
      const res = await fetch("/api/categories/seed", { method: "POST" });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error((data as { detail?: string }).detail ?? `Error ${res.status}`);
      }
      const data = (await res.json()) as { inserted: number; skipped: number };
      setSeedResult(`Seeded: ${data.inserted} inserted, ${data.skipped} already existed.`);
      loadCategories();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to seed categories");
    } finally {
      setSeeding(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-gray-900">Categories</h1>
        <div className="flex items-center gap-3">
          <button
            onClick={handleSeed}
            disabled={seeding}
            className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors disabled:opacity-50"
          >
            {seeding ? "Seeding…" : "Seed from rules"}
          </button>
          <button
            onClick={openCreate}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
          >
            + Add Category
          </button>
        </div>
      </div>

      {seedResult && (
        <div className="rounded-md bg-green-50 border border-green-200 p-3 text-sm text-green-700">
          {seedResult}
        </div>
      )}

      {error && (
        <div className="rounded-md bg-red-50 border border-red-200 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-sm text-gray-500">Loading…</div>
      ) : categories.length === 0 ? (
        <div className="rounded-md border border-dashed border-gray-300 p-10 text-center text-sm text-gray-500">
          No categories yet. Click &ldquo;Seed from rules&rdquo; to import the built-in categories, or &ldquo;Add Category&rdquo; to create one manually.
        </div>
      ) : (
        <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-gray-600 w-48">Name</th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Keywords</th>
                <th className="px-4 py-3 text-right font-medium text-gray-600 w-32">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {categories.map((cat) => (
                <tr key={cat.id} className="hover:bg-gray-50 transition-colors align-top">
                  <td className="px-4 py-3 font-medium text-gray-900">{cat.name}</td>
                  <td className="px-4 py-3 text-gray-600">
                    <div className="flex flex-wrap gap-1">
                      {cat.keywords.map((kw) => (
                        <span
                          key={kw}
                          className="inline-block rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-700"
                        >
                          {kw}
                        </span>
                      ))}
                      {cat.keywords.length === 0 && (
                        <span className="text-gray-400 italic text-xs">—</span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right space-x-2">
                    <button
                      onClick={() => openEdit(cat)}
                      className="rounded px-3 py-1 text-xs font-medium text-blue-600 border border-blue-200 hover:bg-blue-50 transition-colors"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => setConfirmDeleteId(cat.id)}
                      className="rounded px-3 py-1 text-xs font-medium text-red-600 border border-red-200 hover:bg-red-50 transition-colors"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Add / Edit modal */}
      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-lg rounded-lg bg-white shadow-xl p-6 space-y-4">
            <h2 className="text-lg font-semibold text-gray-900">
              {editing ? "Edit Category" : "New Category"}
            </h2>
            {formError && (
              <div className="rounded-md bg-red-50 border border-red-200 p-3 text-sm text-red-700">
                {formError}
              </div>
            )}
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder="e.g. Groceries"
                  disabled={saving}
                  autoFocus
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Keywords{" "}
                  <span className="font-normal text-gray-400">(one per line)</span>
                </label>
                <textarea
                  value={form.keywords}
                  onChange={(e) => setForm((f) => ({ ...f, keywords: e.target.value }))}
                  rows={10}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm font-mono focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder={"WALMART\nHEB\nGROCERY"}
                  disabled={saving}
                />
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={closeForm}
                  disabled={saving}
                  className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                >
                  {saving ? "Saving…" : editing ? "Save Changes" : "Create"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Confirm delete modal */}
      {confirmDeleteId !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-sm rounded-lg bg-white shadow-xl p-6 space-y-4">
            <h2 className="text-lg font-semibold text-gray-900">Delete Category</h2>
            <p className="text-sm text-gray-600">
              Are you sure you want to delete &ldquo;
              {categories.find((c) => c.id === confirmDeleteId)?.name}&rdquo;? This cannot be undone.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setConfirmDeleteId(null)}
                className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDelete(confirmDeleteId)}
                className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

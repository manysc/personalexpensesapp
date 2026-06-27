"use client";

import type { RentalProperty, RentalPropertyRequest } from "@/types/expense";
import { useEffect, useState } from "react";

const EMPTY_FORM: RentalPropertyRequest = { alias: "", address: "", tenant: null, lease_renewal_date: null, payment_day: null };

export default function RentalPropertiesPage() {
  const [properties, setProperties] = useState<RentalProperty[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<RentalProperty | null>(null);
  const [form, setForm] = useState<RentalPropertyRequest>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);

  function loadProperties() {
    setLoading(true);
    setError(null);
    fetch("/api/rental-properties")
      .then((res) => {
        if (!res.ok) throw new Error(`Error ${res.status}: ${res.statusText}`);
        return res.json() as Promise<RentalProperty[]>;
      })
      .then((data) => {
        setProperties(data);
        setLoading(false);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Failed to load properties");
        setLoading(false);
      });
  }

  useEffect(() => {
    loadProperties();
  }, []);

  function openCreate() {
    setEditing(null);
    setForm(EMPTY_FORM);
    setFormError(null);
    setShowForm(true);
  }

  function openEdit(prop: RentalProperty) {
    setEditing(prop);
    setForm({ alias: prop.alias, address: prop.address, tenant: prop.tenant, lease_renewal_date: prop.lease_renewal_date, payment_day: prop.payment_day });
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
    if (!form.alias.trim() || !form.address.trim()) {
      setFormError("Alias and address are required.");
      return;
    }
    setSaving(true);
    setFormError(null);
    const previousTenant = editing?.tenant ?? null;
    try {
      const payload: RentalPropertyRequest = {
        alias: form.alias.trim(),
        address: form.address.trim(),
        tenant: form.tenant?.trim() || null,
        lease_renewal_date: form.lease_renewal_date || null,
        payment_day: form.payment_day,
      };
      const url = editing
        ? `/api/rental-properties/${editing.id}`
        : "/api/rental-properties";
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
      const saved: RentalProperty = await res.json();

      // After a PUT where the tenant changed (or a new tenant was set), sync expenses
      const tenantChanged = editing !== null && payload.tenant && payload.tenant !== previousTenant;
      if (tenantChanged) {
        try {
          const syncRes = await fetch(`/api/rental-properties/${saved.id}/sync-expenses`, { method: "POST" });
          if (syncRes.ok) {
            const syncData = await syncRes.json() as { updated: number };
            setSyncMessage(`${syncData.updated} expense${syncData.updated === 1 ? "" : "s"} linked to "${saved.alias}".`);
          }
        } catch {
          // sync failure is non-fatal
        }
      }

      closeForm();
      loadProperties();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Failed to save property");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: number) {
    try {
      const res = await fetch(`/api/rental-properties/${id}`, { method: "DELETE" });
      if (!res.ok && res.status !== 204) {
        const data = await res.json().catch(() => ({}));
        throw new Error((data as { detail?: string }).detail ?? `Error ${res.status}`);
      }
      setConfirmDeleteId(null);
      loadProperties();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to delete property");
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-gray-900">Rental Properties</h1>
        <button
          onClick={openCreate}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
        >
          + Add Property
        </button>
      </div>

      {error && (
        <div className="rounded-md bg-red-50 border border-red-200 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {syncMessage && (
        <div className="rounded-md bg-green-50 border border-green-200 p-4 text-sm text-green-700 flex items-center justify-between">
          <span>{syncMessage}</span>
          <button onClick={() => setSyncMessage(null)} className="ml-4 text-green-500 hover:text-green-700 font-medium">✕</button>
        </div>
      )}

      {loading ? (
        <div className="text-sm text-gray-500">Loading…</div>
      ) : properties.length === 0 ? (
        <div className="rounded-md border border-dashed border-gray-300 p-10 text-center text-sm text-gray-500">
          No rental properties yet. Click &ldquo;Add Property&rdquo; to create one.
        </div>
      ) : (
        <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Alias</th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Address</th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Tenant</th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Lease Renewal</th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Payment Day</th>
                <th className="px-4 py-3 text-right font-medium text-gray-600">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {properties.map((prop) => (
                <tr key={prop.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 font-medium text-gray-900">{prop.alias}</td>
                  <td className="px-4 py-3 text-gray-700">{prop.address}</td>
                  <td className="px-4 py-3 text-gray-700">{prop.tenant ?? <span className="text-gray-400 italic">—</span>}</td>
                  <td className="px-4 py-3 text-gray-700">{prop.lease_renewal_date ?? <span className="text-gray-400 italic">—</span>}</td>
                  <td className="px-4 py-3 text-gray-700">{prop.payment_day != null ? `Day ${prop.payment_day}` : <span className="text-gray-400 italic">—</span>}</td>
                  <td className="px-4 py-3 text-right space-x-2">
                    <button
                      onClick={() => openEdit(prop)}
                      className="rounded px-3 py-1 text-xs font-medium text-blue-600 border border-blue-200 hover:bg-blue-50 transition-colors"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => setConfirmDeleteId(prop.id)}
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
          <div className="w-full max-w-md rounded-lg bg-white shadow-xl p-6 space-y-4">
            <h2 className="text-lg font-semibold text-gray-900">
              {editing ? "Edit Property" : "New Property"}
            </h2>
            {formError && (
              <div className="rounded-md bg-red-50 border border-red-200 p-3 text-sm text-red-700">
                {formError}
              </div>
            )}
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Alias <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={form.alias}
                  onChange={(e) => setForm({ ...form, alias: e.target.value })}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g. Downtown Apt"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Address <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={form.address}
                  onChange={(e) => setForm({ ...form, address: e.target.value })}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g. 123 Main St, City, State"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tenant
                </label>
                <input
                  type="text"
                  value={form.tenant ?? ""}
                  onChange={(e) =>
                    setForm({ ...form, tenant: e.target.value || null })
                  }
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g. John Doe"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Lease Renewal Date
                </label>
                <input
                  type="date"
                  value={form.lease_renewal_date ?? ""}
                  onChange={(e) =>
                    setForm({ ...form, lease_renewal_date: e.target.value || null })
                  }
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Monthly Payment Day
                </label>
                <input
                  type="number"
                  min={1}
                  max={31}
                  value={form.payment_day ?? ""}
                  onChange={(e) =>
                    setForm({ ...form, payment_day: e.target.value ? Number(e.target.value) : null })
                  }
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g. 1"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={closeForm}
                  className="rounded-md px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
                >
                  {saving ? "Saving…" : "Save"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete confirmation modal */}
      {confirmDeleteId !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-sm rounded-lg bg-white shadow-xl p-6 space-y-4">
            <h2 className="text-lg font-semibold text-gray-900">Delete Property</h2>
            <p className="text-sm text-gray-600">
              Are you sure you want to delete this property? This action cannot be undone.
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setConfirmDeleteId(null)}
                className="rounded-md px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDelete(confirmDeleteId)}
                className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 transition-colors"
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

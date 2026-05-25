"use client";

import type { Vehicle, VehicleRequest, VehicleService, VehicleServiceRequest } from "@/types/expense";
import { useEffect, useState } from "react";

const EMPTY_VEHICLE: VehicleRequest = { alias: "", make: "", model: "", year: new Date().getFullYear(), registration_due_date: null };
const EMPTY_SERVICE: VehicleServiceRequest = { date: "", description: "", mileage: null };

export default function VehiclesPage() {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Vehicle form state
  const [showVehicleForm, setShowVehicleForm] = useState(false);
  const [editingVehicle, setEditingVehicle] = useState<Vehicle | null>(null);
  const [vehicleForm, setVehicleForm] = useState<VehicleRequest>(EMPTY_VEHICLE);
  const [savingVehicle, setSavingVehicle] = useState(false);
  const [vehicleFormError, setVehicleFormError] = useState<string | null>(null);
  const [confirmDeleteVehicleId, setConfirmDeleteVehicleId] = useState<number | null>(null);

  // Services state
  const [expandedVehicleId, setExpandedVehicleId] = useState<number | null>(null);
  const [services, setServices] = useState<Record<number, VehicleService[]>>({});
  const [servicesLoading, setServicesLoading] = useState<Record<number, boolean>>({});

  // Service form state
  const [showServiceForm, setShowServiceForm] = useState(false);
  const [editingService, setEditingService] = useState<VehicleService | null>(null);
  const [serviceForm, setServiceForm] = useState<VehicleServiceRequest>(EMPTY_SERVICE);
  const [savingService, setSavingService] = useState(false);
  const [serviceFormError, setServiceFormError] = useState<string | null>(null);
  const [confirmDeleteService, setConfirmDeleteService] = useState<{ vehicleId: number; serviceId: number } | null>(null);

  function loadVehicles() {
    setLoading(true);
    setError(null);
    fetch("/api/vehicles")
      .then((res) => {
        if (!res.ok) throw new Error(`Error ${res.status}: ${res.statusText}`);
        return res.json() as Promise<Vehicle[]>;
      })
      .then((data) => {
        setVehicles(data);
        setLoading(false);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Failed to load vehicles");
        setLoading(false);
      });
  }

  function loadServices(vehicleId: number) {
    setServicesLoading((prev) => ({ ...prev, [vehicleId]: true }));
    fetch(`/api/vehicles/${vehicleId}/services`)
      .then((res) => {
        if (!res.ok) throw new Error(`Error ${res.status}: ${res.statusText}`);
        return res.json() as Promise<VehicleService[]>;
      })
      .then((data) => {
        setServices((prev) => ({ ...prev, [vehicleId]: data }));
        setServicesLoading((prev) => ({ ...prev, [vehicleId]: false }));
      })
      .catch(() => {
        setServicesLoading((prev) => ({ ...prev, [vehicleId]: false }));
      });
  }

  useEffect(() => {
    loadVehicles();
  }, []);

  function toggleServices(vehicleId: number) {
    if (expandedVehicleId === vehicleId) {
      setExpandedVehicleId(null);
    } else {
      setExpandedVehicleId(vehicleId);
      if (!services[vehicleId]) {
        loadServices(vehicleId);
      }
    }
  }

  // --- Vehicle CRUD ---
  function openCreateVehicle() {
    setEditingVehicle(null);
    setVehicleForm(EMPTY_VEHICLE);
    setVehicleFormError(null);
    setShowVehicleForm(true);
  }

  function openEditVehicle(v: Vehicle) {
    setEditingVehicle(v);
    setVehicleForm({ alias: v.alias, make: v.make, model: v.model, year: v.year, registration_due_date: v.registration_due_date });
    setVehicleFormError(null);
    setShowVehicleForm(true);
  }

  function closeVehicleForm() {
    setShowVehicleForm(false);
    setEditingVehicle(null);
    setVehicleForm(EMPTY_VEHICLE);
    setVehicleFormError(null);
  }

  async function handleVehicleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!vehicleForm.alias.trim()) {
      setVehicleFormError("Alias is required.");
      return;
    }
    if (!vehicleForm.make.trim() || !vehicleForm.model.trim()) {
      setVehicleFormError("Make and model are required.");
      return;
    }
    if (!vehicleForm.year || vehicleForm.year < 1900 || vehicleForm.year > 2100) {
      setVehicleFormError("Please enter a valid year.");
      return;
    }
    setSavingVehicle(true);
    setVehicleFormError(null);
    try {
      const payload: VehicleRequest = {
        alias: vehicleForm.alias.trim(),
        make: vehicleForm.make.trim(),
        model: vehicleForm.model.trim(),
        year: vehicleForm.year,
        registration_due_date: vehicleForm.registration_due_date || null,
      };
      const url = editingVehicle ? `/api/vehicles/${editingVehicle.id}` : "/api/vehicles";
      const method = editingVehicle ? "PUT" : "POST";
      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error((data as { detail?: string }).detail ?? `Error ${res.status}`);
      }
      closeVehicleForm();
      loadVehicles();
    } catch (err: unknown) {
      setVehicleFormError(err instanceof Error ? err.message : "Failed to save vehicle");
    } finally {
      setSavingVehicle(false);
    }
  }

  async function handleDeleteVehicle(id: number) {
    try {
      const res = await fetch(`/api/vehicles/${id}`, { method: "DELETE" });
      if (!res.ok && res.status !== 204) {
        const data = await res.json().catch(() => ({}));
        throw new Error((data as { detail?: string }).detail ?? `Error ${res.status}`);
      }
      setConfirmDeleteVehicleId(null);
      if (expandedVehicleId === id) setExpandedVehicleId(null);
      loadVehicles();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to delete vehicle");
    }
  }

  // --- Service CRUD ---
  function openCreateService(vehicleId: number) {
    setEditingService(null);
    setServiceForm({ ...EMPTY_SERVICE, _vehicleId: vehicleId } as VehicleServiceRequest & { _vehicleId: number });
    setServiceFormError(null);
    setShowServiceForm(true);
  }

  function openEditService(svc: VehicleService) {
    setEditingService(svc);
    setServiceForm({ date: svc.date, description: svc.description, mileage: svc.mileage });
    setServiceFormError(null);
    setShowServiceForm(true);
  }

  function closeServiceForm() {
    setShowServiceForm(false);
    setEditingService(null);
    setServiceForm(EMPTY_SERVICE);
    setServiceFormError(null);
  }

  async function handleServiceSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!serviceForm.date) {
      setServiceFormError("Date is required.");
      return;
    }
    if (!serviceForm.description.trim()) {
      setServiceFormError("Description is required.");
      return;
    }
    setSavingService(true);
    setServiceFormError(null);
    try {
      const payload: VehicleServiceRequest = {
        date: serviceForm.date,
        description: serviceForm.description.trim(),
        mileage: serviceForm.mileage,
      };
      let url: string;
      let method: string;
      let vehicleId: number;
      if (editingService) {
        url = `/api/vehicles/${editingService.vehicle_id}/services/${editingService.id}`;
        method = "PUT";
        vehicleId = editingService.vehicle_id;
      } else {
        vehicleId = (serviceForm as VehicleServiceRequest & { _vehicleId: number })._vehicleId;
        url = `/api/vehicles/${vehicleId}/services`;
        method = "POST";
      }
      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error((data as { detail?: string }).detail ?? `Error ${res.status}`);
      }
      closeServiceForm();
      loadServices(vehicleId);
    } catch (err: unknown) {
      setServiceFormError(err instanceof Error ? err.message : "Failed to save service");
    } finally {
      setSavingService(false);
    }
  }

  async function handleDeleteService(vehicleId: number, serviceId: number) {
    try {
      const res = await fetch(`/api/vehicles/${vehicleId}/services/${serviceId}`, { method: "DELETE" });
      if (!res.ok && res.status !== 204) {
        const data = await res.json().catch(() => ({}));
        throw new Error((data as { detail?: string }).detail ?? `Error ${res.status}`);
      }
      setConfirmDeleteService(null);
      loadServices(vehicleId);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to delete service");
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-gray-900">Vehicles</h1>
        <button
          onClick={openCreateVehicle}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
        >
          + Add Vehicle
        </button>
      </div>

      {error && (
        <div className="rounded-md bg-red-50 border border-red-200 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-sm text-gray-500">Loading…</div>
      ) : vehicles.length === 0 ? (
        <div className="rounded-md border border-dashed border-gray-300 p-10 text-center text-sm text-gray-500">
          No vehicles yet. Click &ldquo;Add Vehicle&rdquo; to create one.
        </div>
      ) : (
        <div className="space-y-3">
          {vehicles.map((vehicle) => (
            <div key={vehicle.id} className="rounded-lg border border-gray-200 bg-white shadow-sm overflow-hidden">
              {/* Vehicle row */}
              <div className="flex items-center justify-between px-4 py-3">
                <div className="flex items-center gap-6 min-w-0">
                  <div className="min-w-0">
                    <span className="font-semibold text-gray-900">{vehicle.alias}</span>
                    <span className="ml-2 text-sm text-gray-500">{vehicle.year} {vehicle.make} {vehicle.model}</span>
                  </div>
                  <div className="text-sm text-gray-500">
                    {vehicle.registration_due_date ? (
                      <span>
                        Registration due:{" "}
                        <span className="font-medium text-gray-700">{vehicle.registration_due_date}</span>
                      </span>
                    ) : (
                      <span className="italic text-gray-400">No registration date</span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={() => toggleServices(vehicle.id)}
                    className="rounded px-3 py-1 text-xs font-medium text-gray-600 border border-gray-200 hover:bg-gray-50 transition-colors"
                  >
                    {expandedVehicleId === vehicle.id ? "Hide Services" : "Services"}
                  </button>
                  <button
                    onClick={() => openEditVehicle(vehicle)}
                    className="rounded px-3 py-1 text-xs font-medium text-blue-600 border border-blue-200 hover:bg-blue-50 transition-colors"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => setConfirmDeleteVehicleId(vehicle.id)}
                    className="rounded px-3 py-1 text-xs font-medium text-red-600 border border-red-200 hover:bg-red-50 transition-colors"
                  >
                    Delete
                  </button>
                </div>
              </div>

              {/* Maintenance services panel */}
              {expandedVehicleId === vehicle.id && (
                <div className="border-t border-gray-100 bg-gray-50 px-4 py-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-gray-700">Maintenance Services</h3>
                    <button
                      onClick={() => openCreateService(vehicle.id)}
                      className="rounded px-3 py-1 text-xs font-medium text-blue-600 border border-blue-200 bg-white hover:bg-blue-50 transition-colors"
                    >
                      + Add Service
                    </button>
                  </div>

                  {servicesLoading[vehicle.id] ? (
                    <div className="text-sm text-gray-400">Loading…</div>
                  ) : !services[vehicle.id] || services[vehicle.id].length === 0 ? (
                    <div className="rounded border border-dashed border-gray-200 p-6 text-center text-xs text-gray-400">
                      No maintenance records yet.
                    </div>
                  ) : (
                    <div className="overflow-hidden rounded-md border border-gray-200 bg-white">
                      <table className="min-w-full divide-y divide-gray-100 text-sm">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Date</th>
                            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Description</th>
                            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Mileage</th>
                            <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">Actions</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-50">
                          {services[vehicle.id].map((svc) => (
                            <tr key={svc.id} className="hover:bg-gray-50 transition-colors">
                              <td className="px-3 py-2 text-gray-700 whitespace-nowrap">{svc.date}</td>
                              <td className="px-3 py-2 text-gray-700">{svc.description}</td>
                              <td className="px-3 py-2 text-gray-700 whitespace-nowrap">
                                {svc.mileage != null ? svc.mileage.toLocaleString() : <span className="text-gray-400 italic">—</span>}
                              </td>
                              <td className="px-3 py-2 text-right space-x-2 whitespace-nowrap">
                                <button
                                  onClick={() => openEditService(svc)}
                                  className="rounded px-2 py-0.5 text-xs font-medium text-blue-600 border border-blue-200 hover:bg-blue-50 transition-colors"
                                >
                                  Edit
                                </button>
                                <button
                                  onClick={() => setConfirmDeleteService({ vehicleId: vehicle.id, serviceId: svc.id })}
                                  className="rounded px-2 py-0.5 text-xs font-medium text-red-600 border border-red-200 hover:bg-red-50 transition-colors"
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
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Add / Edit Vehicle modal */}
      {showVehicleForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-md rounded-lg bg-white shadow-xl p-6 space-y-4">
            <h2 className="text-lg font-semibold text-gray-900">
              {editingVehicle ? "Edit Vehicle" : "New Vehicle"}
            </h2>
            {vehicleFormError && (
              <div className="rounded-md bg-red-50 border border-red-200 p-3 text-sm text-red-700">
                {vehicleFormError}
              </div>
            )}
            <form onSubmit={handleVehicleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Alias <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={vehicleForm.alias}
                  onChange={(e) => setVehicleForm({ ...vehicleForm, alias: e.target.value })}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g. My Car"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Make <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={vehicleForm.make}
                    onChange={(e) => setVehicleForm({ ...vehicleForm, make: e.target.value })}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g. Toyota"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Model <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={vehicleForm.model}
                    onChange={(e) => setVehicleForm({ ...vehicleForm, model: e.target.value })}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g. Camry"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Year <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="number"
                    min={1900}
                    max={2100}
                    value={vehicleForm.year}
                    onChange={(e) => setVehicleForm({ ...vehicleForm, year: Number(e.target.value) })}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g. 2022"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Registration Due Date
                  </label>
                  <input
                    type="date"
                    value={vehicleForm.registration_due_date ?? ""}
                    onChange={(e) =>
                      setVehicleForm({ ...vehicleForm, registration_due_date: e.target.value || null })
                    }
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={closeVehicleForm}
                  className="rounded-md px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={savingVehicle}
                  className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
                >
                  {savingVehicle ? "Saving…" : "Save"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add / Edit Service modal */}
      {showServiceForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-md rounded-lg bg-white shadow-xl p-6 space-y-4">
            <h2 className="text-lg font-semibold text-gray-900">
              {editingService ? "Edit Service" : "New Service"}
            </h2>
            {serviceFormError && (
              <div className="rounded-md bg-red-50 border border-red-200 p-3 text-sm text-red-700">
                {serviceFormError}
              </div>
            )}
            <form onSubmit={handleServiceSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Date <span className="text-red-500">*</span>
                </label>
                <input
                  type="date"
                  value={serviceForm.date}
                  onChange={(e) => setServiceForm({ ...serviceForm, date: e.target.value })}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={serviceForm.description}
                  onChange={(e) => setServiceForm({ ...serviceForm, description: e.target.value })}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g. Oil change, Tire rotation"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Mileage
                </label>
                <input
                  type="number"
                  min={0}
                  value={serviceForm.mileage ?? ""}
                  onChange={(e) =>
                    setServiceForm({ ...serviceForm, mileage: e.target.value ? Number(e.target.value) : null })
                  }
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g. 45000"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={closeServiceForm}
                  className="rounded-md px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={savingService}
                  className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
                >
                  {savingService ? "Saving…" : "Save"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Vehicle confirmation modal */}
      {confirmDeleteVehicleId !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-sm rounded-lg bg-white shadow-xl p-6 space-y-4">
            <h2 className="text-lg font-semibold text-gray-900">Delete Vehicle</h2>
            <p className="text-sm text-gray-600">
              Are you sure you want to delete this vehicle? All associated maintenance records will also be deleted.
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setConfirmDeleteVehicleId(null)}
                className="rounded-md px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDeleteVehicle(confirmDeleteVehicleId)}
                className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Service confirmation modal */}
      {confirmDeleteService !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-sm rounded-lg bg-white shadow-xl p-6 space-y-4">
            <h2 className="text-lg font-semibold text-gray-900">Delete Service Record</h2>
            <p className="text-sm text-gray-600">
              Are you sure you want to delete this maintenance record? This action cannot be undone.
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setConfirmDeleteService(null)}
                className="rounded-md px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDeleteService(confirmDeleteService.vehicleId, confirmDeleteService.serviceId)}
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

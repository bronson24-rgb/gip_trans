import { clearSession, getAccessToken, refreshAccessToken } from "./auth";
import type { RouteReportCreatePayload, RouteReportInput, Vehicle } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export function toPayload(input: RouteReportInput): RouteReportCreatePayload {
  return {
    vehicle_id: input.vehicleId,
    report_date: input.reportDate,
    route_from: input.routeFrom.trim(),
    route_to: input.routeTo.trim(),
    odometer_start: Number(input.odometerStart),
    odometer_end: Number(input.odometerEnd),
    fuel_end: Number(input.fuelEnd),
    departure_time: input.departureTime,
    arrival_time: input.arrivalTime,
    comment: input.comment.trim() ? input.comment.trim() : null,
    fuel_refills: input.fuelRefills.map((refill) => ({
      refill_datetime: new Date(refill.refillDatetime).toISOString(),
      station_name: refill.stationName.trim(),
      liters: Number(refill.liters),
      total_cost: Number(refill.totalCost),
      receipt_photo_key: refill.receiptPhotoKey ?? null,
    })),
  };
}

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function doFetch(path: string, options: RequestInit): Promise<Response> {
  const token = getAccessToken();
  return fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
}

async function authenticatedFetch(path: string, options: RequestInit = {}): Promise<Response> {
  let response = await doFetch(path, options);

  if (response.status === 401) {
    // Access-токен просрочений — пробуємо оновити його через refresh і повторити запит один раз.
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      response = await doFetch(path, options);
    }
  }

  if (response.status === 401) {
    // Refresh теж не спрацював (відкликаний/протермінований) — сесія дійсно закінчилась.
    clearSession();
    window.location.reload();
  }

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(body?.detail ? JSON.stringify(body.detail) : `Помилка ${response.status}`, response.status);
  }

  return response;
}

export async function createRouteReport(input: RouteReportInput) {
  const response = await authenticatedFetch("/api/route-reports", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(toPayload(input)),
  });
  return response.json();
}

export async function uploadReceiptPhoto(file: File): Promise<string> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await authenticatedFetch("/api/uploads/receipt", {
    method: "POST",
    body: formData,
  });
  const data = await response.json();
  return data.key as string;
}

export async function fetchActiveVehicles(): Promise<Vehicle[]> {
  const response = await authenticatedFetch("/api/vehicles");
  const vehicles: Vehicle[] = await response.json();
  return vehicles.filter((v) => v.is_active);
}

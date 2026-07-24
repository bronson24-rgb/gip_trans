import type { RouteReportCreatePayload, RouteReportInput } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export function toPayload(input: RouteReportInput): RouteReportCreatePayload {
  return {
    vehicle_plate: input.vehiclePlate.trim(),
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
      receipt_photo_url: refill.receiptPhotoUrl ?? null,
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

// TODO(auth): в дев-окружении личность водителя передаётся заголовком
// X-User-Email (см. app-backend/app/api/deps.py). Заменить на реальную Google
// OAuth-сессию, когда авторизация будет реализована.
export async function createRouteReport(input: RouteReportInput, driverEmail: string) {
  const response = await fetch(`${API_BASE_URL}/api/route-reports`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-User-Email": driverEmail,
    },
    body: JSON.stringify(toPayload(input)),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(body?.detail ? JSON.stringify(body.detail) : `Помилка ${response.status}`, response.status);
  }

  return response.json();
}

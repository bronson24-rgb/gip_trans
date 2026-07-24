import { describe, expect, it } from "vitest";
import { toPayload } from "./api";
import type { RouteReportInput } from "./types";

function baseInput(overrides: Partial<RouteReportInput> = {}): RouteReportInput {
  return {
    vehicleId: "veh-1",
    reportDate: "2026-07-24",
    routeFrom: "  Москва  ",
    routeTo: "Тверь",
    odometerStart: "1000",
    odometerEnd: "1180",
    fuelEnd: "30.5",
    departureTime: "08:00",
    arrivalTime: "12:00",
    comment: "  ",
    fuelRefills: [],
    ...overrides,
  };
}

describe("toPayload", () => {
  it("trims whitespace and converts numeric strings to numbers", () => {
    const payload = toPayload(baseInput());

    expect(payload.route_from).toBe("Москва");
    expect(payload.odometer_start).toBe(1000);
    expect(payload.odometer_end).toBe(1180);
    expect(payload.fuel_end).toBe(30.5);
  });

  it("converts blank comment to null instead of sending an empty string", () => {
    const payload = toPayload(baseInput({ comment: "   " }));
    expect(payload.comment).toBeNull();
  });

  it("keeps a real comment", () => {
    const payload = toPayload(baseInput({ comment: "Все нормально" }));
    expect(payload.comment).toBe("Все нормально");
  });

  it("maps fuel refills, defaulting missing photo key to null", () => {
    const payload = toPayload(
      baseInput({
        fuelRefills: [
          {
            refillDatetime: "2026-07-24T08:30",
            stationName: "  Лукойл  ",
            liters: "50",
            totalCost: "3500",
          },
        ],
      }),
    );

    expect(payload.fuel_refills).toHaveLength(1);
    expect(payload.fuel_refills[0].station_name).toBe("Лукойл");
    expect(payload.fuel_refills[0].liters).toBe(50);
    expect(payload.fuel_refills[0].receipt_photo_key).toBeNull();
  });

  it("passes through an uploaded receipt photo key", () => {
    const payload = toPayload(
      baseInput({
        fuelRefills: [
          {
            refillDatetime: "2026-07-24T08:30",
            stationName: "АЗС",
            liters: "10",
            totalCost: "700",
            receiptPhotoKey: "receipts/1.png",
          },
        ],
      }),
    );

    expect(payload.fuel_refills[0].receipt_photo_key).toBe("receipts/1.png");
  });
});

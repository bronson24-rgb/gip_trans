import { beforeEach, describe, expect, it } from "vitest";
import { clearDraft, loadDraft, saveDraft } from "./draft";
import type { RouteReportInput } from "./types";

// Тестовое окружение vitest здесь — "node", без DOM/localStorage по умолчанию.
// Ставим лёгкий in-memory стаб вместо подключения jsdom ради одного файла.
class MemoryStorage implements Storage {
  private store = new Map<string, string>();
  get length() {
    return this.store.size;
  }
  clear(): void {
    this.store.clear();
  }
  getItem(key: string): string | null {
    return this.store.has(key) ? this.store.get(key)! : null;
  }
  key(index: number): string | null {
    return Array.from(this.store.keys())[index] ?? null;
  }
  removeItem(key: string): void {
    this.store.delete(key);
  }
  setItem(key: string, value: string): void {
    this.store.set(key, value);
  }
}

beforeEach(() => {
  globalThis.localStorage = new MemoryStorage();
});

function sampleReport(): RouteReportInput {
  return {
    vehicleId: "veh-1",
    reportDate: "2026-07-24",
    routeFrom: "Москва",
    routeTo: "Тверь",
    odometerStart: "1000",
    odometerEnd: "1180",
    fuelEnd: "30",
    departureTime: "08:00",
    arrivalTime: "12:00",
    comment: "",
    fuelRefills: [],
  };
}

describe("draft", () => {
  it("returns null when nothing was saved", () => {
    expect(loadDraft()).toBeNull();
  });

  it("round-trips a saved draft", () => {
    const report = sampleReport();
    saveDraft(report);

    expect(loadDraft()).toEqual(report);
  });

  it("clearDraft removes the saved draft", () => {
    saveDraft(sampleReport());
    clearDraft();

    expect(loadDraft()).toBeNull();
  });

  it("returns null instead of throwing on corrupted JSON", () => {
    localStorage.setItem("gip_driver_report_draft", "{not valid json");

    expect(loadDraft()).toBeNull();
  });
});

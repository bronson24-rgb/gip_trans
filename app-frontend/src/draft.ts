import type { RouteReportInput } from "./types";

const DRAFT_KEY = "gip_driver_report_draft";

export function saveDraft(report: RouteReportInput): void {
  localStorage.setItem(DRAFT_KEY, JSON.stringify(report));
}

export function loadDraft(): RouteReportInput | null {
  const raw = localStorage.getItem(DRAFT_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as RouteReportInput;
  } catch {
    return null;
  }
}

export function clearDraft(): void {
  localStorage.removeItem(DRAFT_KEY);
}

import { useEffect, useState } from "react";
import type { ChangeEvent, FormEvent } from "react";
import { ApiError, createRouteReport, fetchActiveVehicles, uploadReceiptPhoto } from "./api";
import { clearDraft, loadDraft, saveDraft } from "./draft";
import type { FuelRefillInput, RouteReportInput, Vehicle } from "./types";

type PhotoUploadStatus = "idle" | "uploading" | "uploaded" | "error";

function generateLocalId(): string {
  return typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

const emptyRefill = (): FuelRefillInput => ({
  id: generateLocalId(),
  refillDatetime: "",
  stationName: "",
  liters: "",
  totalCost: "",
});

const emptyReport = (): RouteReportInput => ({
  vehicleId: "",
  reportDate: new Date().toISOString().slice(0, 10),
  routeFrom: "",
  routeTo: "",
  odometerStart: "",
  odometerEnd: "",
  fuelEnd: "",
  departureTime: "",
  arrivalTime: "",
  comment: "",
  fuelRefills: [],
});

// Черновик, только что загруженный со старта, ещё непусто заполнен, но не
// содержит фото в статусе "uploading" (файлы не переживают localStorage) —
// такие статусы при восстановлении выводятся как "uploaded", если ключ уже
// есть, иначе просто не отображаются.
function photoStatusFromDraft(draft: RouteReportInput): Record<string, PhotoUploadStatus> {
  const status: Record<string, PhotoUploadStatus> = {};
  for (const refill of draft.fuelRefills) {
    if (refill.receiptPhotoKey) status[refill.id] = "uploaded";
  }
  return status;
}

function isReportEmpty(report: RouteReportInput): boolean {
  return (
    !report.vehicleId &&
    !report.routeFrom &&
    !report.routeTo &&
    !report.odometerStart &&
    !report.odometerEnd &&
    !report.fuelEnd &&
    !report.departureTime &&
    !report.arrivalTime &&
    !report.comment &&
    report.fuelRefills.length === 0
  );
}

type Status = "idle" | "submitting" | "success" | "error";

export function DriverReportForm() {
  const [report, setReport] = useState<RouteReportInput>(emptyReport);
  const [status, setStatus] = useState<Status>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [photoStatus, setPhotoStatus] = useState<Record<string, PhotoUploadStatus>>({});
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [vehiclesError, setVehiclesError] = useState<string | null>(null);

  // Черновик, ожидающий решения пользователя (відновити/почати заново) —
  // поки не вирішено, поточну (порожню) форму в localStorage не пишемо, щоб
  // не затерти ще не переглянутий чернетку.
  const [pendingDraft, setPendingDraft] = useState<RouteReportInput | null>(null);
  const [draftResolved, setDraftResolved] = useState(false);

  useEffect(() => {
    fetchActiveVehicles()
      .then(setVehicles)
      .catch(() => setVehiclesError("Не вдалося завантажити список автомобілів"));
  }, []);

  useEffect(() => {
    const draft = loadDraft();
    if (draft && !isReportEmpty(draft)) {
      setPendingDraft(draft);
    } else {
      setDraftResolved(true);
    }
  }, []);

  useEffect(() => {
    if (!draftResolved) return; // ждём решения по найденному черновику
    if (isReportEmpty(report)) {
      clearDraft();
    } else {
      saveDraft(report);
    }
  }, [report, draftResolved]);

  const handleRestoreDraft = () => {
    if (pendingDraft) {
      setReport(pendingDraft);
      setPhotoStatus(photoStatusFromDraft(pendingDraft));
    }
    setPendingDraft(null);
    setDraftResolved(true);
  };

  const handleDiscardDraft = () => {
    clearDraft();
    setPendingDraft(null);
    setDraftResolved(true);
  };

  const updateField = <K extends keyof RouteReportInput>(field: K, value: RouteReportInput[K]) => {
    setReport((prev) => ({ ...prev, [field]: value }));
  };

  const updateRefill = <K extends keyof FuelRefillInput>(id: string, field: K, value: FuelRefillInput[K]) => {
    setReport((prev) => ({
      ...prev,
      fuelRefills: prev.fuelRefills.map((refill) => (refill.id === id ? { ...refill, [field]: value } : refill)),
    }));
  };

  const addRefill = () => {
    setReport((prev) => ({ ...prev, fuelRefills: [...prev.fuelRefills, emptyRefill()] }));
  };

  const removeRefill = (id: string) => {
    setReport((prev) => ({ ...prev, fuelRefills: prev.fuelRefills.filter((refill) => refill.id !== id) }));
    setPhotoStatus((prev) => {
      const next = { ...prev };
      delete next[id];
      return next;
    });
  };

  const handlePhotoSelect = async (id: string, event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setPhotoStatus((prev) => ({ ...prev, [id]: "uploading" }));
    try {
      const key = await uploadReceiptPhoto(file);
      updateRefill(id, "receiptPhotoKey", key);
      setPhotoStatus((prev) => ({ ...prev, [id]: "uploaded" }));
    } catch {
      setPhotoStatus((prev) => ({ ...prev, [id]: "error" }));
    }
  };

  const odometerInvalid =
    report.odometerStart !== "" &&
    report.odometerEnd !== "" &&
    Number(report.odometerEnd) < Number(report.odometerStart);

  const photosUploading = Object.values(photoStatus).includes("uploading");

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (odometerInvalid || photosUploading) return;

    setStatus("submitting");
    setErrorMessage(null);

    try {
      await createRouteReport(report);
      setStatus("success");
      setReport(emptyReport());
      setPhotoStatus({});
      clearDraft();
    } catch (err) {
      setStatus("error");
      setErrorMessage(err instanceof ApiError ? err.message : "Не вдалося надіслати звіт. Перевірте з'єднання.");
    }
  };

  if (pendingDraft) {
    return (
      <div className="draft-prompt">
        <h1>Знайдено незавершений звіт</h1>
        <p>Схоже, ви не встигли надіслати попередній звіт. Відновити його чи почати заново?</p>
        <div className="draft-prompt-actions">
          <button type="button" onClick={handleRestoreDraft}>
            Відновити
          </button>
          <button type="button" onClick={handleDiscardDraft}>
            Почати заново
          </button>
        </div>
      </div>
    );
  }

  return (
    <form className="report-form" onSubmit={handleSubmit}>
      <h1>Звіт по маршруту</h1>

      <fieldset>
        <legend>Рейс</legend>
        <label>
          Автомобіль
          <select
            required
            value={report.vehicleId}
            onChange={(e) => updateField("vehicleId", e.target.value)}
          >
            <option value="" disabled>
              Оберіть автомобіль
            </option>
            {vehicles.map((vehicle) => (
              <option key={vehicle.id} value={vehicle.id}>
                {vehicle.plate_number}
                {vehicle.make || vehicle.model ? ` — ${[vehicle.make, vehicle.model].filter(Boolean).join(" ")}` : ""}
              </option>
            ))}
          </select>
          {vehiclesError && <span className="field-error">{vehiclesError}</span>}
        </label>
        <label>
          Дата
          <input
            type="date"
            required
            value={report.reportDate}
            onChange={(e) => updateField("reportDate", e.target.value)}
          />
        </label>
        <label>
          Звідки
          <input required value={report.routeFrom} onChange={(e) => updateField("routeFrom", e.target.value)} />
        </label>
        <label>
          Куди
          <input required value={report.routeTo} onChange={(e) => updateField("routeTo", e.target.value)} />
        </label>
        <label>
          Час виїзду
          <input
            type="time"
            required
            value={report.departureTime}
            onChange={(e) => updateField("departureTime", e.target.value)}
          />
        </label>
        <label>
          Час прибуття
          <input
            type="time"
            required
            value={report.arrivalTime}
            onChange={(e) => updateField("arrivalTime", e.target.value)}
          />
        </label>
      </fieldset>

      <fieldset>
        <legend>Пробіг і пальне</legend>
        <label>
          Одометр на початок (км)
          <input
            type="number"
            required
            min={0}
            value={report.odometerStart}
            onChange={(e) => updateField("odometerStart", e.target.value)}
          />
        </label>
        <label>
          Одометр на кінець (км)
          <input
            type="number"
            required
            min={0}
            value={report.odometerEnd}
            onChange={(e) => updateField("odometerEnd", e.target.value)}
          />
        </label>
        {odometerInvalid && <p className="field-error">Одометр на кінець не може бути меншим за одометр на початок</p>}
        <label>
          Залишок пального на кінець (л)
          <input
            type="number"
            required
            min={0}
            step="0.1"
            value={report.fuelEnd}
            onChange={(e) => updateField("fuelEnd", e.target.value)}
          />
        </label>
      </fieldset>

      <fieldset>
        <legend>Заправки</legend>
        {report.fuelRefills.map((refill) => (
          <div className="refill-row" key={refill.id}>
            <label>
              Дата і час
              <input
                type="datetime-local"
                required
                value={refill.refillDatetime}
                onChange={(e) => updateRefill(refill.id, "refillDatetime", e.target.value)}
              />
            </label>
            <label>
              АЗС
              <input
                required
                value={refill.stationName}
                onChange={(e) => updateRefill(refill.id, "stationName", e.target.value)}
              />
            </label>
            <label>
              Літри
              <input
                type="number"
                required
                min={0}
                step="0.1"
                value={refill.liters}
                onChange={(e) => updateRefill(refill.id, "liters", e.target.value)}
              />
            </label>
            <label>
              Сума (₽)
              <input
                type="number"
                required
                min={0}
                step="0.01"
                value={refill.totalCost}
                onChange={(e) => updateRefill(refill.id, "totalCost", e.target.value)}
              />
            </label>
            <label>
              Фото чека (необов'язково)
              <input
                type="file"
                accept="image/*"
                capture="environment"
                onChange={(e) => handlePhotoSelect(refill.id, e)}
              />
            </label>
            {photoStatus[refill.id] === "uploading" && <p className="photo-status">Завантаження фото...</p>}
            {photoStatus[refill.id] === "uploaded" && <p className="photo-status photo-status-ok">Фото завантажено.</p>}
            {photoStatus[refill.id] === "error" && (
              <p className="photo-status photo-status-error">Не вдалося завантажити фото. Спробуйте ще раз.</p>
            )}
            <button type="button" onClick={() => removeRefill(refill.id)}>
              Видалити заправку
            </button>
          </div>
        ))}
        <button type="button" onClick={addRefill}>
          + Додати заправку
        </button>
      </fieldset>

      <fieldset>
        <legend>Коментар</legend>
        <label>
          Коментар (необов'язково)
          <textarea value={report.comment} onChange={(e) => updateField("comment", e.target.value)} />
        </label>
      </fieldset>

      <button type="submit" disabled={status === "submitting" || photosUploading}>
        {status === "submitting" ? "Надсилання..." : photosUploading ? "Зачекайте, фото завантажується..." : "Надіслати звіт"}
      </button>

      {status === "success" && <p className="status-success">Звіт надіслано.</p>}
      {status === "error" && <p className="status-error">{errorMessage}</p>}
    </form>
  );
}

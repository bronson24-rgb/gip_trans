import { useState } from "react";
import type { FormEvent } from "react";
import { ApiError, createRouteReport } from "./api";
import type { FuelRefillInput, RouteReportInput } from "./types";

const emptyRefill = (): FuelRefillInput => ({
  refillDatetime: "",
  stationName: "",
  liters: "",
  totalCost: "",
});

const emptyReport = (): RouteReportInput => ({
  vehiclePlate: "",
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

type Status = "idle" | "submitting" | "success" | "error";

export function DriverReportForm() {
  // TODO(auth): временный ввод email вместо реальной Google OAuth-сессии.
  // Убрать, когда авторизация будет реализована — email будет браться из сессии.
  const [driverEmail, setDriverEmail] = useState(() => localStorage.getItem("dev_driver_email") ?? "");
  const [report, setReport] = useState<RouteReportInput>(emptyReport);
  const [status, setStatus] = useState<Status>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const updateField = <K extends keyof RouteReportInput>(field: K, value: RouteReportInput[K]) => {
    setReport((prev) => ({ ...prev, [field]: value }));
  };

  const updateRefill = <K extends keyof FuelRefillInput>(index: number, field: K, value: FuelRefillInput[K]) => {
    setReport((prev) => ({
      ...prev,
      fuelRefills: prev.fuelRefills.map((refill, i) => (i === index ? { ...refill, [field]: value } : refill)),
    }));
  };

  const addRefill = () => {
    setReport((prev) => ({ ...prev, fuelRefills: [...prev.fuelRefills, emptyRefill()] }));
  };

  const removeRefill = (index: number) => {
    setReport((prev) => ({ ...prev, fuelRefills: prev.fuelRefills.filter((_, i) => i !== index) }));
  };

  const odometerInvalid =
    report.odometerStart !== "" &&
    report.odometerEnd !== "" &&
    Number(report.odometerEnd) < Number(report.odometerStart);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (odometerInvalid) return;

    localStorage.setItem("dev_driver_email", driverEmail);
    setStatus("submitting");
    setErrorMessage(null);

    try {
      await createRouteReport(report, driverEmail);
      setStatus("success");
      setReport(emptyReport());
    } catch (err) {
      setStatus("error");
      setErrorMessage(err instanceof ApiError ? err.message : "Не удалось отправить отчёт. Проверьте связь.");
    }
  };

  return (
    <form className="report-form" onSubmit={handleSubmit}>
      <h1>Отчёт по маршруту</h1>

      <fieldset>
        <legend>Вход (временно, до Google OAuth)</legend>
        <label>
          Email водителя
          <input
            type="email"
            required
            value={driverEmail}
            onChange={(e) => setDriverEmail(e.target.value)}
          />
        </label>
      </fieldset>

      <fieldset>
        <legend>Рейс</legend>
        <label>
          Гос.номер автомобиля
          <input
            required
            value={report.vehiclePlate}
            onChange={(e) => updateField("vehiclePlate", e.target.value)}
          />
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
          Откуда
          <input required value={report.routeFrom} onChange={(e) => updateField("routeFrom", e.target.value)} />
        </label>
        <label>
          Куда
          <input required value={report.routeTo} onChange={(e) => updateField("routeTo", e.target.value)} />
        </label>
        <label>
          Время выезда
          <input
            type="time"
            required
            value={report.departureTime}
            onChange={(e) => updateField("departureTime", e.target.value)}
          />
        </label>
        <label>
          Время прибытия
          <input
            type="time"
            required
            value={report.arrivalTime}
            onChange={(e) => updateField("arrivalTime", e.target.value)}
          />
        </label>
      </fieldset>

      <fieldset>
        <legend>Пробег и топливо</legend>
        <label>
          Одометр на начало (км)
          <input
            type="number"
            required
            min={0}
            value={report.odometerStart}
            onChange={(e) => updateField("odometerStart", e.target.value)}
          />
        </label>
        <label>
          Одометр на конец (км)
          <input
            type="number"
            required
            min={0}
            value={report.odometerEnd}
            onChange={(e) => updateField("odometerEnd", e.target.value)}
          />
        </label>
        {odometerInvalid && <p className="field-error">Одометр на конец не может быть меньше одометра на начало</p>}
        <label>
          Остаток топлива на конец (л)
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
        {report.fuelRefills.map((refill, index) => (
          <div className="refill-row" key={index}>
            <label>
              Дата и время
              <input
                type="datetime-local"
                required
                value={refill.refillDatetime}
                onChange={(e) => updateRefill(index, "refillDatetime", e.target.value)}
              />
            </label>
            <label>
              АЗС
              <input
                required
                value={refill.stationName}
                onChange={(e) => updateRefill(index, "stationName", e.target.value)}
              />
            </label>
            <label>
              Литры
              <input
                type="number"
                required
                min={0}
                step="0.1"
                value={refill.liters}
                onChange={(e) => updateRefill(index, "liters", e.target.value)}
              />
            </label>
            <label>
              Сумма (₽)
              <input
                type="number"
                required
                min={0}
                step="0.01"
                value={refill.totalCost}
                onChange={(e) => updateRefill(index, "totalCost", e.target.value)}
              />
            </label>
            <label>
              Фото чека (необязательно)
              {/* TODO(storage): реальная загрузка в S3 — отдельная задача.
                  Пока поле только для выбора файла на клиенте, на backend не отправляется. */}
              <input type="file" accept="image/*" capture="environment" />
            </label>
            <button type="button" onClick={() => removeRefill(index)}>
              Удалить заправку
            </button>
          </div>
        ))}
        <button type="button" onClick={addRefill}>
          + Добавить заправку
        </button>
      </fieldset>

      <fieldset>
        <legend>Комментарий</legend>
        <label>
          Комментарий (необязательно)
          <textarea value={report.comment} onChange={(e) => updateField("comment", e.target.value)} />
        </label>
      </fieldset>

      <button type="submit" disabled={status === "submitting"}>
        {status === "submitting" ? "Отправка..." : "Отправить отчёт"}
      </button>

      {status === "success" && <p className="status-success">Отчёт отправлен.</p>}
      {status === "error" && <p className="status-error">{errorMessage}</p>}
    </form>
  );
}

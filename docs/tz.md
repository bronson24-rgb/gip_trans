# ТЗ — Онлайн-форма отчёта водителя по маршруту

Детализирует раздел 1 `architecture.md` («форма отчёта водителя (состав полей, валидация, логика)»).

## Версии

| № | Дата | Резюме |
|---|---|---|
| 1.0 | 2026-07-23 | Согласован состав полей MVP, реализованы backend (модели/миграции/API) и форма |

## Состав данных

Один рейс = отчёт (`route_reports`) + 0..N заправок (`fuel_refills`). Расходы, номер ТТН и справочник машин — намеренно не входят в MVP (см. «Отложено» ниже).

### `route_reports`

| Поле | Тип | Обяз. | Источник | Комментарий |
|---|---|---|---|---|
| driver_id | FK → users | да | сессия (заглушка авторизации) | не вводится вручную |
| vehicle_plate | текст | да | ввод водителя | MVP: свободный текст вместо справочника машин |
| report_date | дата | да | ввод водителя | |
| route_from / route_to | текст | да | ввод водителя | |
| odometer_start / odometer_end | целое, км | да | ввод водителя | odometer_end ≥ odometer_start (валидация) |
| mileage | целое, км | — | вычисляется backend | хранится, не пересчитывается «на лету» |
| fuel_end | число, л | да | ввод водителя | остаток топлива на конец рейса |
| departure_time / arrival_time | время | да | ввод водителя | нужно для учёта часов работы |
| comment | текст | нет | ввод водителя | |
| status | enum (draft/submitted/approved/rejected) | — | backend | заготовка под workflow подтверждения |

### `fuel_refills` (1:N к отчёту)

| Поле | Тип | Обяз. | Комментарий |
|---|---|---|---|
| refill_datetime | дата+время | да | |
| station_name | текст | да | |
| liters | число | да | |
| total_cost | число | да | |
| receipt_photo_url | текст (URL) | нет | опционально — форма отправляется и без фото |

## Отложено (сознательно не в MVP)

- **Справочник автомобилей** (`vehicles`, `vehicle_id` FK) — вместо него `vehicle_plate` текстом. Модель `route_reports.vehicle_plate` спроектирована так, чтобы при появлении справочника добавить nullable `vehicle_id`, перенести данные и только потом сделать его обязательным (см. TODO в `app/models/route_report.py`).
- **Номер ТТН/накладной** — добавится на этапе управленческого блока (баланс, финрез).
- **Прочие расходы** (платные дороги, парковки, мойка и т.д.) — добавляются позже отдельной таблицей `expenses` (report_id FK), по той же схеме, что и `fuel_refills`, без изменения `route_reports`.
- **Реальная загрузка фото чеков в S3** — сейчас поле `receipt_photo_url` есть в модели/API, но во frontend это только выбор файла на клиенте без загрузки (см. TODO в `DriverReportForm.tsx`).
- **Google OAuth** — доступ к API временно защищён по заголовку `X-User-Email` (см. `app/api/deps.py`), сверяется с таблицей `users` (allow-list через `is_allowed`). Замена на реальную проверку Google id_token не меняет сигнатуру зависимости `get_current_driver`.

## Реализация

- Backend: `app-backend/` — FastAPI + SQLAlchemy (sync, psycopg) + Alembic + PostgreSQL. Эндпоинты: `POST/GET /api/route-reports`, `GET /api/route-reports/{id}`.
- Frontend: `app-frontend/` — React + TypeScript + Vite, mobile-first, компонент `DriverReportForm`.
- Локальный запуск: `cd infra && cp .env.example .env && docker compose up --build` (backend + Postgres), фронтенд — `cd app-frontend && npm install && npm run dev`.

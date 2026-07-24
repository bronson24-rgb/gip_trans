# GIP Trans — Учётная система

Учётная система для компании автотранспортных перевозок. Архитектура — `docs/architecture.md`, ТЗ на форму отчёта водителя — `docs/tz.md`.

## Структура репозитория

- `/app-frontend` — React + TypeScript + Vite, форма отчёта водителя
- `/app-backend` — FastAPI + SQLAlchemy + Alembic + PostgreSQL
- `/infra` — docker-compose.yml, .env.example
- `/docs` — ТЗ, документация проекта

## Как поднять окружение с нуля

Backend + Postgres через Docker Compose (миграции применяются автоматически при старте контейнера):

```bash
cd infra
cp .env.example .env
docker compose up --build
```

Backend будет на `http://localhost:8000` (`/health` — проверка живости).

Frontend — локально через Vite dev server:

```bash
cd app-frontend
npm install
cp .env.example .env
npm run dev
```

Откроется на `http://localhost:5173`.

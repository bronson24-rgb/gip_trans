import type { DataProvider } from "react-admin";
import { getSessionToken, refreshAccessToken } from "./authProvider";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function rawFetch(path: string, options: RequestInit): Promise<Response> {
  const token = getSessionToken();
  return fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
}

// Backend не поддерживает пагинацию/сортировку на сервере (см. app-backend/app/api/*.py —
// GET-эндпоинты всегда отдают полный список). Для MVP-объёмов (десятки-сотни записей)
// этого достаточно: применяем пагинацию/сортировку на клиенте.
async function apiFetch(path: string, options: RequestInit = {}) {
  let response = await rawFetch(path, options);

  if (response.status === 401) {
    // Access-токен прострочений — пробуємо оновити й повторити запит один раз.
    // Якщо refresh теж поверне 401 — authProvider.checkError підхопить це і зробить logout.
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      response = await rawFetch(path, options);
    }
  }

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const error: { message: string; status: number } = {
      message: body?.detail ? JSON.stringify(body.detail) : `Помилка ${response.status}`,
      status: response.status,
    };
    throw error;
  }

  if (response.status === 204) return null;
  return response.json();
}

const RESOURCE_PATH: Record<string, string> = {
  "route-reports": "/api/route-reports",
  expenses: "/api/expenses",
  users: "/api/users",
  vehicles: "/api/vehicles",
};

export const dataProvider: DataProvider = {
  async getList(resource, params) {
    const path = RESOURCE_PATH[resource];
    const data: Record<string, unknown>[] = await apiFetch(path);

    const { field, order } = params.sort ?? { field: "id", order: "ASC" };
    const sorted = [...data].sort((a, b) => {
      const av = a[field];
      const bv = b[field];
      if (av === bv) return 0;
      const cmp = (av as string | number) < (bv as string | number) ? -1 : 1;
      return order === "ASC" ? cmp : -cmp;
    });

    const { page, perPage } = params.pagination ?? { page: 1, perPage: 25 };
    const start = (page - 1) * perPage;
    const pageData = sorted.slice(start, start + perPage);

    return { data: pageData as never, total: data.length };
  },

  async getOne(resource, params) {
    const path = RESOURCE_PATH[resource];
    const data = await apiFetch(`${path}/${params.id}`);
    return { data };
  },

  async getMany(resource, params) {
    const path = RESOURCE_PATH[resource];
    const all: Record<string, unknown>[] = await apiFetch(path);
    return { data: all.filter((item) => params.ids.includes(item.id as never)) as never };
  },

  async getManyReference() {
    throw new Error("getManyReference не используется");
  },

  async create(resource, params) {
    const path = RESOURCE_PATH[resource];
    const data = await apiFetch(path, { method: "POST", body: JSON.stringify(params.data) });
    return { data };
  },

  async update(resource, params) {
    const path = RESOURCE_PATH[resource];
    const data = await apiFetch(`${path}/${params.id}`, {
      method: "PATCH",
      body: JSON.stringify(params.data),
    });
    return { data };
  },

  async updateMany() {
    throw new Error("updateMany не используется");
  },

  async delete(resource, params) {
    const path = RESOURCE_PATH[resource];
    await apiFetch(`${path}/${params.id}`, { method: "DELETE" });
    return { data: params.previousData as never };
  },

  async deleteMany() {
    throw new Error("deleteMany не используется");
  },
};

import type { DataProvider } from "react-admin";
import { getCurrentUserEmail } from "./authProvider";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

// Backend не поддерживает пагинацию/сортировку на сервере (см. app-backend/app/api/*.py —
// GET-эндпоинты всегда отдают полный список). Для MVP-объёмов (десятки-сотни записей)
// этого достаточно: применяем пагинацию/сортировку на клиенте.
async function apiFetch(path: string, options: RequestInit = {}) {
  const email = getCurrentUserEmail();
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(email ? { "X-User-Email": email } : {}),
      ...options.headers,
    },
  });

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

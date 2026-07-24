import { createAuthenticatedFetch } from "./authenticatedFetch";
import { getSessionToken, refreshAccessToken } from "./authProvider";

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

// Единая точка входа для "запрос -> 401 -> refresh -> повтор" во всём app-admin
// (dataProvider, Summary, ReceiptButton) — раньше эта логика была продублирована
// в каждом из этих мест по отдельности и уже начала расходиться в поведении.
//
// onAuthFailure намеренно не задан: если и после refresh пришёл 401/403, ошибка
// просто долетает до react-admin, а его authProvider.checkError сам решает,
// что делать (обычно — разлогинить и показать экран входа). Явный редирект/reload
// здесь был бы лишним и конфликтовал бы с тем, как react-admin управляет своей
// навигацией.
const rawAuthenticatedFetch = createAuthenticatedFetch({
  getAccessToken: getSessionToken,
  refreshAccessToken,
});

/** Уже привязан к API_BASE_URL — вызывать как authenticatedFetch(path, options). */
export function authenticatedFetch(path: string, options: RequestInit = {}): Promise<Response> {
  return rawAuthenticatedFetch(API_BASE_URL, path, options);
}

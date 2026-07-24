import type { AuthProvider } from "react-admin";

const ACCESS_TOKEN_KEY = "gip_admin_access_token";
const REFRESH_TOKEN_KEY = "gip_admin_refresh_token";
const EMAIL_KEY = "gip_admin_email";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

function clearTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(EMAIL_KEY);
}

export const authProvider: AuthProvider = {
  // Вызывается кастомной LoginPage с id_token, полученным от Google (см. LoginPage.tsx).
  async login({ googleIdToken }: { googleIdToken: string }) {
    const response = await fetch(`${API_BASE_URL}/api/auth/google`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id_token: googleIdToken }),
    });

    if (!response.ok) {
      const body = await response.json().catch(() => null);
      throw new Error(body?.detail ?? "Не вдалося увійти");
    }

    const data = await response.json();
    localStorage.setItem(ACCESS_TOKEN_KEY, data.access_token);
    localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh_token);
    localStorage.setItem(EMAIL_KEY, data.email);
  },
  async logout() {
    const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
    if (refreshToken) {
      try {
        await fetch(`${API_BASE_URL}/api/auth/logout`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
      } catch {
        // локальну сесію все одно очищаємо нижче
      }
    }
    clearTokens();
  },
  async checkAuth() {
    if (!localStorage.getItem(ACCESS_TOKEN_KEY)) {
      throw new Error("Не авторизовано");
    }
  },
  async checkError(error) {
    if (error?.status === 401 || error?.status === 403) {
      clearTokens();
      throw error;
    }
  },
  async getIdentity() {
    const email = localStorage.getItem(EMAIL_KEY) ?? "";
    return { id: email, fullName: email };
  },
  async getPermissions() {
    return undefined;
  },
};

export function getSessionToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

// Дедуплікація одночасних 401 — лише один реальний запит на оновлення токена.
let refreshPromise: Promise<boolean> | null = null;

export function refreshAccessToken(): Promise<boolean> {
  if (!refreshPromise) {
    refreshPromise = performRefresh().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

async function performRefresh(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;

  const response = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!response.ok) return false;

  const data = await response.json();
  localStorage.setItem(ACCESS_TOKEN_KEY, data.access_token);
  localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh_token);
  return true;
}

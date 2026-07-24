import type { AuthProvider } from "react-admin";

// ВРЕМЕННАЯ заглушка авторизации — см. app-backend/app/api/deps.py.
// "Логин" здесь не проверяет пароль, только сохраняет email, которым дальше
// подписывается каждый запрос к API (заголовок X-User-Email). Если email не
// в allow-list — backend ответит 401/403, и это увидит пользователь.
// TODO(auth): заменить на реальный Google OAuth, не меняя интерфейс AuthProvider.
const STORAGE_KEY = "gip_admin_email";

export const authProvider: AuthProvider = {
  async login({ username }: { username: string }) {
    if (!username || !username.includes("@")) {
      throw new Error("Введіть email");
    }
    localStorage.setItem(STORAGE_KEY, username);
  },
  async logout() {
    localStorage.removeItem(STORAGE_KEY);
  },
  async checkAuth() {
    if (!localStorage.getItem(STORAGE_KEY)) {
      throw new Error("Не авторизовано");
    }
  },
  async checkError(error) {
    if (error?.status === 401 || error?.status === 403) {
      localStorage.removeItem(STORAGE_KEY);
      throw error;
    }
  },
  async getIdentity() {
    const email = localStorage.getItem(STORAGE_KEY) ?? "";
    return { id: email, fullName: email };
  },
  async getPermissions() {
    return undefined;
  },
};

export function getCurrentUserEmail(): string | null {
  return localStorage.getItem(STORAGE_KEY);
}

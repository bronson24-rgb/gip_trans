// Общая логика "запрос -> 401 -> refresh -> повтор", используемая и в
// app-frontend, и в app-admin. Проекты — два независимых Vite-приложения без
// общего build-тулинга (не monorepo/workspaces), поэтому шарить это как
// настоящий общий npm-пакет означало бы менять build context в Dockerfile
// обоих приложений (см. infra/docker-compose.yml, этап 1) — сознательно этого
// не делаем, чтобы не трогать уже проверенную продовую сборку. Вместо этого
// файл держим ИДЕНТИЧНЫМ в обоих приложениях: app-frontend/src/authenticatedFetch.ts
// и app-admin/src/authenticatedFetch.ts. При правке — правь оба сразу.

export interface AuthenticatedFetchConfig {
  getAccessToken: () => string | null;
  refreshAccessToken: () => Promise<boolean>;
  /** Вызывается, если запрос вернул 401 и после refresh — тоже 401 (сессия реально мертва). */
  onAuthFailure?: () => void;
}

export function createAuthenticatedFetch(config: AuthenticatedFetchConfig) {
  async function doFetch(baseUrl: string, path: string, options: RequestInit): Promise<Response> {
    const token = config.getAccessToken();
    return fetch(`${baseUrl}${path}`, {
      ...options,
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options.headers,
      },
    });
  }

  return async function authenticatedFetch(baseUrl: string, path: string, options: RequestInit = {}): Promise<Response> {
    let response = await doFetch(baseUrl, path, options);

    if (response.status === 401) {
      const refreshed = await config.refreshAccessToken();
      if (refreshed) {
        response = await doFetch(baseUrl, path, options);
      }
    }

    if (response.status === 401) {
      config.onAuthFailure?.();
    }

    return response;
  };
}

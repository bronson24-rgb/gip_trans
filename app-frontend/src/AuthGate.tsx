import { useState } from "react";
import type { ReactNode } from "react";
import { GoogleLogin } from "@react-oauth/google";
import { getAccessToken, getSessionEmail, loginWithGoogle, logout } from "./auth";

export function AuthGate({ children }: { children: ReactNode }) {
  const [token, setToken] = useState(getAccessToken());
  const [error, setError] = useState<string | null>(null);

  if (!token) {
    return (
      <div className="login-screen">
        <h1>Звіт водія — GIP Trans</h1>
        <p>Увійдіть через Google, щоб надіслати звіт.</p>
        <GoogleLogin
          onSuccess={async (credential) => {
            if (!credential.credential) return;
            setError(null);
            try {
              await loginWithGoogle(credential.credential);
              setToken(getAccessToken());
            } catch (err) {
              setError(err instanceof Error ? err.message : "Не вдалося увійти");
            }
          }}
          onError={() => setError("Не вдалося увійти через Google")}
        />
        {error && <p className="status-error">{error}</p>}
      </div>
    );
  }

  return (
    <div>
      <div className="session-bar">
        <span>{getSessionEmail()}</span>
        <button
          type="button"
          onClick={async () => {
            await logout();
            setToken(null);
          }}
        >
          Вийти
        </button>
      </div>
      {children}
    </div>
  );
}

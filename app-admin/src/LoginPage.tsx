import { GoogleLogin } from "@react-oauth/google";
import { useState } from "react";
import { useLogin, useNotify } from "react-admin";
import { Card, CardContent, Typography, Box } from "@mui/material";

export function LoginPage() {
  const login = useLogin();
  const notify = useNotify();
  const [loading, setLoading] = useState(false);

  return (
    <Box sx={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "100vh" }}>
      <Card sx={{ p: 3, minWidth: 320 }}>
        <CardContent sx={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 2 }}>
          <Typography variant="h6">GIP Trans — Керування</Typography>
          <Typography variant="body2" color="text.secondary">
            Увійдіть через Google
          </Typography>
          <GoogleLogin
            onSuccess={async (credential) => {
              if (!credential.credential) return;
              setLoading(true);
              try {
                await login({ googleIdToken: credential.credential });
              } catch (err) {
                notify(err instanceof Error ? err.message : "Не вдалося увійти", { type: "error" });
              } finally {
                setLoading(false);
              }
            }}
            onError={() => notify("Не вдалося увійти через Google", { type: "error" })}
          />
          {loading && <Typography variant="body2">Вхід...</Typography>}
        </CardContent>
      </Card>
    </Box>
  );
}

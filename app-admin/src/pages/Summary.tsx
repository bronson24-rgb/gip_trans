import { useState } from "react";
import { Card, CardContent, Typography, TextField, Button, Box, Alert } from "@mui/material";
import { Title } from "react-admin";
import { getSessionToken, refreshAccessToken } from "../authProvider";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

interface SummaryData {
  date_from: string;
  date_to: string;
  revenue: string;
  fuel_cost: string;
  other_expenses: string;
  profit: string;
}

function firstDayOfMonth(): string {
  const now = new Date();
  return new Date(now.getFullYear(), now.getMonth(), 1).toISOString().slice(0, 10);
}

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

export function Summary() {
  const [dateFrom, setDateFrom] = useState(firstDayOfMonth());
  const [dateTo, setDateTo] = useState(today());
  const [data, setData] = useState<SummaryData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchSummary = async () => {
    setLoading(true);
    setError(null);
    try {
      const url = `${API_BASE_URL}/api/summary?date_from=${dateFrom}&date_to=${dateTo}`;
      const authHeader = (): Record<string, string> => {
        const token = getSessionToken();
        return token ? { Authorization: `Bearer ${token}` } : {};
      };

      let response = await fetch(url, { headers: authHeader() });
      if (response.status === 401 && (await refreshAccessToken())) {
        response = await fetch(url, { headers: authHeader() });
      }
      if (!response.ok) throw new Error(`Помилка ${response.status}`);
      setData(await response.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не вдалося завантажити зведення");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <Title title="Зведення P&L" />
      <CardContent>
        <Box sx={{ display: "flex", flexDirection: "row", gap: 2, alignItems: "center", mb: 3 }}>
          <TextField
            label="З"
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            slotProps={{ inputLabel: { shrink: true } }}
          />
          <TextField
            label="По"
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            slotProps={{ inputLabel: { shrink: true } }}
          />
          <Button variant="contained" onClick={fetchSummary} disabled={loading}>
            {loading ? "Рахую..." : "Порахувати"}
          </Button>
        </Box>

        {error && <Alert severity="error">{error}</Alert>}

        {data && (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
            <Typography>Виручка: {data.revenue}</Typography>
            <Typography>Пальне: {data.fuel_cost}</Typography>
            <Typography>Інші витрати: {data.other_expenses}</Typography>
            <Typography variant="h6">Прибуток: {data.profit}</Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
}

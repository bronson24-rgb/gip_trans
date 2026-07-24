from slowapi import Limiter
from slowapi.util import get_remote_address

# In-memory хранилище (по умолчанию у slowapi) — достаточно для одного инстанса
# backend (текущая архитектура). При горизонтальном масштабировании потребуется
# storage_uri="redis://..." — тогда лимиты будут общими для всех реплик.
limiter = Limiter(key_func=get_remote_address)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.expenses import router as expenses_router
from app.api.route_reports import router as route_reports_router
from app.api.summary import router as summary_router
from app.core.config import settings

app = FastAPI(title="GIP Trans API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(route_reports_router)
app.include_router(expenses_router)
app.include_router(summary_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.database import get_db
from app.models.expense import Expense
from app.models.fuel_refill import FuelRefill
from app.models.route_report import RouteReport
from app.models.user import UserRole
from app.schemas.summary import SummaryResponse

# P&L — управленческая отчётность, водителю не нужна и не должна быть видна.
router = APIRouter(
    prefix="/api/summary",
    tags=["summary"],
    dependencies=[Depends(require_roles(UserRole.accountant, UserRole.admin))],
)


@router.get("", response_model=SummaryResponse)
def get_summary(
    date_from: date = Query(...),
    date_to: date = Query(...),
    db: Session = Depends(get_db),
) -> SummaryResponse:
    revenue = db.scalar(
        select(func.coalesce(func.sum(RouteReport.revenue_amount), 0)).where(
            RouteReport.report_date >= date_from, RouteReport.report_date <= date_to
        )
    )

    fuel_cost = db.scalar(
        select(func.coalesce(func.sum(FuelRefill.total_cost), 0))
        .join(RouteReport, FuelRefill.report_id == RouteReport.id)
        .where(RouteReport.report_date >= date_from, RouteReport.report_date <= date_to)
    )

    other_expenses = db.scalar(
        select(func.coalesce(func.sum(Expense.amount), 0)).where(
            Expense.expense_date >= date_from, Expense.expense_date <= date_to
        )
    )

    revenue = Decimal(revenue)
    fuel_cost = Decimal(fuel_cost)
    other_expenses = Decimal(other_expenses)

    return SummaryResponse(
        date_from=date_from,
        date_to=date_to,
        revenue=revenue,
        fuel_cost=fuel_cost,
        other_expenses=other_expenses,
        profit=revenue - fuel_cost - other_expenses,
    )

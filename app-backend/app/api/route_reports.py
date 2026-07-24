import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, require_roles
from app.database import get_db
from app.models.fuel_refill import FuelRefill
from app.models.route_report import RouteReport
from app.models.user import User, UserRole
from app.schemas.route_report import RouteReportAdminUpdate, RouteReportCreate, RouteReportRead

router = APIRouter(prefix="/api/route-reports", tags=["route-reports"])

manage_reports = require_roles(UserRole.accountant, UserRole.admin)


@router.post("", response_model=RouteReportRead, status_code=status.HTTP_201_CREATED)
def create_route_report(
    payload: RouteReportCreate,
    db: Session = Depends(get_db),
    driver: User = Depends(get_current_user),
) -> RouteReport:
    report = RouteReport(
        driver_id=driver.id,
        vehicle_id=payload.vehicle_id,
        report_date=payload.report_date,
        route_from=payload.route_from,
        route_to=payload.route_to,
        odometer_start=payload.odometer_start,
        odometer_end=payload.odometer_end,
        mileage=payload.odometer_end - payload.odometer_start,
        fuel_end=payload.fuel_end,
        departure_time=payload.departure_time,
        arrival_time=payload.arrival_time,
        comment=payload.comment,
        fuel_refills=[FuelRefill(**fr.model_dump()) for fr in payload.fuel_refills],
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("", response_model=list[RouteReportRead])
def list_route_reports(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[RouteReport]:
    # Бухгалтер/админ видят рейсы всех водителей (нужно для P&L и подтверждения
    # рейсов); водитель — только свои (иначе видел бы чужие расходы/маршруты).
    query = db.query(RouteReport).options(selectinload(RouteReport.fuel_refills), selectinload(RouteReport.vehicle))
    if user.role == UserRole.driver:
        query = query.filter(RouteReport.driver_id == user.id)
    return query.order_by(RouteReport.report_date.desc()).all()


@router.get("/{report_id}", response_model=RouteReportRead)
def get_route_report(
    report_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RouteReport:
    query = (
        db.query(RouteReport)
        .options(selectinload(RouteReport.fuel_refills), selectinload(RouteReport.vehicle))
        .filter(RouteReport.id == report_id)
    )
    if user.role == UserRole.driver:
        query = query.filter(RouteReport.driver_id == user.id)
    report = query.first()
    # 404, а не 403 — чтобы водитель не мог даже узнать по коду ответа, что
    # чужой рейс с таким id вообще существует.
    if report is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Отчёт не найден")
    return report


@router.patch("/{report_id}", response_model=RouteReportRead)
def update_route_report(
    report_id: uuid.UUID,
    payload: RouteReportAdminUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(manage_reports),
) -> RouteReport:
    """Проставляет ТТН/клиента/выручку и статус — используется app-admin (бухгалтер/админ)."""
    report = (
        db.query(RouteReport)
        .options(selectinload(RouteReport.fuel_refills), selectinload(RouteReport.vehicle))
        .filter(RouteReport.id == report_id)
        .first()
    )
    if report is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Отчёт не найден")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(report, field, value)

    db.commit()
    db.refresh(report)
    return report

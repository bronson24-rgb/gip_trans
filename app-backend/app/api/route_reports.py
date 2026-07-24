import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_driver
from app.database import get_db
from app.models.fuel_refill import FuelRefill
from app.models.route_report import RouteReport
from app.models.user import User
from app.schemas.route_report import RouteReportCreate, RouteReportRead

router = APIRouter(prefix="/api/route-reports", tags=["route-reports"])


@router.post("", response_model=RouteReportRead, status_code=status.HTTP_201_CREATED)
def create_route_report(
    payload: RouteReportCreate,
    db: Session = Depends(get_db),
    driver: User = Depends(get_current_driver),
) -> RouteReport:
    report = RouteReport(
        driver_id=driver.id,
        vehicle_plate=payload.vehicle_plate,
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
    driver: User = Depends(get_current_driver),
) -> list[RouteReport]:
    return (
        db.query(RouteReport)
        .options(selectinload(RouteReport.fuel_refills))
        .filter(RouteReport.driver_id == driver.id)
        .order_by(RouteReport.report_date.desc())
        .all()
    )


@router.get("/{report_id}", response_model=RouteReportRead)
def get_route_report(
    report_id: uuid.UUID,
    db: Session = Depends(get_db),
    driver: User = Depends(get_current_driver),
) -> RouteReport:
    report = (
        db.query(RouteReport)
        .options(selectinload(RouteReport.fuel_refills))
        .filter(RouteReport.id == report_id, RouteReport.driver_id == driver.id)
        .first()
    )
    if report is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Отчёт не найден")
    return report

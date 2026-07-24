import uuid
from datetime import date, datetime, time
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.route_report import ReportStatus
from app.schemas.vehicle import VehicleRead


class FuelRefillCreate(BaseModel):
    refill_datetime: datetime
    station_name: str = Field(min_length=1, max_length=255)
    liters: Decimal = Field(gt=0)
    total_cost: Decimal = Field(gt=0)
    receipt_photo_key: str | None = None


class FuelRefillRead(FuelRefillCreate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


class RouteReportCreate(BaseModel):
    vehicle_id: uuid.UUID
    report_date: date
    route_from: str = Field(min_length=1, max_length=255)
    route_to: str = Field(min_length=1, max_length=255)
    odometer_start: int = Field(ge=0)
    odometer_end: int = Field(ge=0)
    fuel_end: Decimal = Field(ge=0)
    departure_time: time
    arrival_time: time
    comment: str | None = None
    fuel_refills: list[FuelRefillCreate] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_odometer(self) -> "RouteReportCreate":
        if self.odometer_end < self.odometer_start:
            raise ValueError("odometer_end не может быть меньше odometer_start")
        return self


class RouteReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    driver_id: uuid.UUID
    vehicle_id: uuid.UUID
    vehicle: VehicleRead
    report_date: date
    route_from: str
    route_to: str
    odometer_start: int
    odometer_end: int
    mileage: int
    fuel_end: Decimal
    departure_time: time
    arrival_time: time
    comment: str | None
    waybill_number: str | None
    client_name: str | None
    revenue_amount: Decimal | None
    status: ReportStatus
    created_at: datetime
    fuel_refills: list[FuelRefillRead] = []


class RouteReportAdminUpdate(BaseModel):
    """Поля, которые проставляет PO/бухгалтер через app-admin — не водитель."""

    waybill_number: str | None = Field(default=None, max_length=50)
    client_name: str | None = Field(default=None, max_length=255)
    revenue_amount: Decimal | None = Field(default=None, ge=0)
    status: ReportStatus | None = None

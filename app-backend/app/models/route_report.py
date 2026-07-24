import enum
import uuid
from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, Time, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ReportStatus(str, enum.Enum):
    draft = "draft"
    submitted = "submitted"
    approved = "approved"
    rejected = "rejected"


class RouteReport(Base):
    """Отчёт водителя по рейсу. Состав полей — docs/tz-driver-report.md."""

    __tablename__ = "route_reports"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    driver_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    # MVP: свободный текст, без справочника машин (согласовано).
    # TODO(vehicle-registry): при появлении таблицы vehicles — добавить nullable
    # vehicle_id FK, перенести значения из vehicle_plate, затем сделать vehicle_id
    # обязательным и вывести vehicle_plate в read-only/legacy.
    vehicle_plate: Mapped[str] = mapped_column(String(20), nullable=False)

    report_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    route_from: Mapped[str] = mapped_column(String(255), nullable=False)
    route_to: Mapped[str] = mapped_column(String(255), nullable=False)

    odometer_start: Mapped[int] = mapped_column(Integer, nullable=False)
    odometer_end: Mapped[int] = mapped_column(Integer, nullable=False)
    # Храним, а не вычисляем on-the-fly: пробег рейса не должен "плыть", если
    # одометр машины позже скорректируют записью в другом отчёте.
    mileage: Mapped[int] = mapped_column(Integer, nullable=False)

    fuel_end: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)

    departure_time: Mapped[time] = mapped_column(Time, nullable=False)
    arrival_time: Mapped[time] = mapped_column(Time, nullable=False)

    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Заполняются не водителем, а PO/бухгалтером через app-admin — после того как
    # рейс отправлен. MVP: client_name текстом, без справочника клиентов (тот же
    # паттерн, что и vehicle_plate).
    waybill_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    client_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    revenue_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    status: Mapped[ReportStatus] = mapped_column(
        SAEnum(ReportStatus, name="report_status"),
        default=ReportStatus.submitted,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    driver: Mapped["User"] = relationship()
    fuel_refills: Mapped[list["FuelRefill"]] = relationship(
        back_populates="report", cascade="all, delete-orphan", order_by="FuelRefill.refill_datetime"
    )

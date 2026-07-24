import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class FuelRefill(Base):
    """Заправка в рамках рейса. Один отчёт — много заправок (1:N).

    Расширяемость: расходы другого рода (платные дороги, парковки — не входят
    в MVP) добавляются по этой же схеме — отдельной таблицей с report_id FK,
    без изменения route_reports.
    """

    __tablename__ = "fuel_refills"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("route_reports.id", ondelete="CASCADE"), nullable=False, index=True
    )

    refill_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    station_name: Mapped[str] = mapped_column(String(255), nullable=False)
    liters: Mapped[Decimal] = mapped_column(Numeric(7, 2), nullable=False)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # Опционально (согласовано): форма должна успешно отправляться без фото.
    # Хранится КЛЮЧ объекта в S3 (например "receipts/<uuid>.jpg"), не URL — так
    # доступ к файлу не завязан на конкретный домен/публичность bucket'а; для
    # получения используется GET /api/uploads/receipt/{key} (presigned URL).
    receipt_photo_key: Mapped[str | None] = mapped_column(String(500), nullable=True)

    report: Mapped["RouteReport"] = relationship(back_populates="fuel_refills")

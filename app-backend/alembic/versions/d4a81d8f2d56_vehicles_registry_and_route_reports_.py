"""vehicles registry and route_reports.vehicle_id

Revision ID: d4a81d8f2d56
Revises: afcd031107b8
Create Date: 2026-07-24 02:03:15.447131

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd4a81d8f2d56'
down_revision: Union[str, None] = 'afcd031107b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "vehicles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("plate_number", sa.String(length=20), nullable=False),
        sa.Column("make", sa.String(length=100), nullable=True),
        sa.Column("model", sa.String(length=100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_vehicles_plate_number"), "vehicles", ["plate_number"], unique=True)

    # Бэкофилл: по одной записи vehicles на каждый уникальный vehicle_plate,
    # уже встречавшийся в route_reports.
    op.execute(
        """
        INSERT INTO vehicles (id, plate_number, is_active, created_at)
        SELECT gen_random_uuid(), vehicle_plate, true, now()
        FROM (SELECT DISTINCT vehicle_plate FROM route_reports) AS distinct_plates
        """
    )

    op.add_column("route_reports", sa.Column("vehicle_id", sa.Uuid(), nullable=True))
    op.execute(
        """
        UPDATE route_reports
        SET vehicle_id = vehicles.id
        FROM vehicles
        WHERE vehicles.plate_number = route_reports.vehicle_plate
        """
    )
    op.alter_column("route_reports", "vehicle_id", nullable=False)
    op.create_index(op.f("ix_route_reports_vehicle_id"), "route_reports", ["vehicle_id"], unique=False)
    op.create_foreign_key(
        "route_reports_vehicle_id_fkey", "route_reports", "vehicles", ["vehicle_id"], ["id"], ondelete="RESTRICT"
    )

    op.drop_column("route_reports", "vehicle_plate")


def downgrade() -> None:
    op.add_column("route_reports", sa.Column("vehicle_plate", sa.String(length=20), nullable=True))
    op.execute(
        """
        UPDATE route_reports
        SET vehicle_plate = vehicles.plate_number
        FROM vehicles
        WHERE vehicles.id = route_reports.vehicle_id
        """
    )
    op.alter_column("route_reports", "vehicle_plate", nullable=False)

    op.drop_constraint("route_reports_vehicle_id_fkey", "route_reports", type_="foreignkey")
    op.drop_index(op.f("ix_route_reports_vehicle_id"), table_name="route_reports")
    op.drop_column("route_reports", "vehicle_id")

    op.drop_index(op.f("ix_vehicles_plate_number"), table_name="vehicles")
    op.drop_table("vehicles")

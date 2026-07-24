"""add financial fields to route reports

Revision ID: 4dc25553105b
Revises: 6844573dc0ef
Create Date: 2026-07-23 21:06:14.749500

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '4dc25553105b'
down_revision: Union[str, None] = '6844573dc0ef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("route_reports", sa.Column("waybill_number", sa.String(length=50), nullable=True))
    op.add_column("route_reports", sa.Column("client_name", sa.String(length=255), nullable=True))
    op.add_column("route_reports", sa.Column("revenue_amount", sa.Numeric(precision=10, scale=2), nullable=True))


def downgrade() -> None:
    op.drop_column("route_reports", "revenue_amount")
    op.drop_column("route_reports", "client_name")
    op.drop_column("route_reports", "waybill_number")

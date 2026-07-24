"""create expenses table

Revision ID: afcd031107b8
Revises: 4dc25553105b
Create Date: 2026-07-23 21:06:15.357207

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'afcd031107b8'
down_revision: Union[str, None] = '4dc25553105b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "expenses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("expense_date", sa.Date(), nullable=False),
        sa.Column(
            "category",
            sa.Enum("salary", "rent", "insurance", "tax", "maintenance", "other", name="expense_category"),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_expenses_expense_date"), "expenses", ["expense_date"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_expenses_expense_date"), table_name="expenses")
    op.drop_table("expenses")
    sa.Enum(name="expense_category").drop(op.get_bind(), checkfirst=True)

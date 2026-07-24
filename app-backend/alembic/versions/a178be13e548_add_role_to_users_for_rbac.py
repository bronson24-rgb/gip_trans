"""add role to users for RBAC

Revision ID: a178be13e548
Revises: cc7d92d06a57
Create Date: 2026-07-24 13:51:44.285186

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a178be13e548'
down_revision: Union[str, None] = 'cc7d92d06a57'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    user_role = sa.Enum("driver", "accountant", "admin", name="user_role")
    user_role.create(op.get_bind())
    op.add_column(
        "users",
        sa.Column("role", user_role, nullable=False, server_default="driver"),
    )
    # server_default нужен только чтобы проставить существующие строки безопасным
    # значением по умолчанию; дальше приложение всегда передаёт role явно.
    op.alter_column("users", "role", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "role")
    sa.Enum(name="user_role").drop(op.get_bind(), checkfirst=True)

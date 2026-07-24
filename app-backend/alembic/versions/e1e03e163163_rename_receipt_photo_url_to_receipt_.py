"""rename receipt_photo_url to receipt_photo_key

Revision ID: e1e03e163163
Revises: d4a81d8f2d56
Create Date: 2026-07-24 02:23:36.787094

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e1e03e163163'
down_revision: Union[str, None] = 'd4a81d8f2d56'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("fuel_refills", "receipt_photo_url", new_column_name="receipt_photo_key")
    # Раньше хранился полный публичный URL — теперь только ключ объекта
    # (сам файл всегда "receipts/<имя>", без вложенных "/" — берём последний
    # такой сегмент от конца строки. Раньше здесь стоял паттерн 'receipts/.*'
    # без якоря $, и он по ошибке матчился на хвост имени бакета
    # "gip-trans-RECEIPTS/", а не на настоящий префикс ключа).
    op.execute(
        r"""
        UPDATE fuel_refills
        SET receipt_photo_key = substring(receipt_photo_key from 'receipts/[^/]+$')
        WHERE receipt_photo_key IS NOT NULL
        """
    )


def downgrade() -> None:
    op.alter_column("fuel_refills", "receipt_photo_key", new_column_name="receipt_photo_url")

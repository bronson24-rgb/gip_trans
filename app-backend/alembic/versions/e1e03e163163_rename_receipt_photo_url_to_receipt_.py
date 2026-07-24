"""rename receipt_photo_url to receipt_photo_key

Revision ID: e1e03e163163
Revises: d4a81d8f2d56
Create Date: 2026-07-24 02:23:36.787094

⚠️ LOSSY DOWNGRADE — необратима по данным (хотя формально выполняется без ошибок).

upgrade() меняет не только имя колонки, но и ФОРМАТ значений: было — полный
публичный URL ("{s3_public_base_url}/{key}"), стало — только ключ объекта
("receipts/<uuid>.jpg"). downgrade() возвращает исходное ИМЯ колонки
(receipt_photo_url), но не может восстановить исходный ФОРМАТ значений:
- настройка s3_public_base_url, из которой раньше строился полный URL, в
  текущей кодовой базе уже удалена (см. последующую миграцию, добавившую
  вместо неё s3_endpoint_url/s3_public_endpoint_url для presigned-ссылок);
- даже если бы она была доступна, мы не храним, какой именно bucket/host
  использовался в момент исходной загрузки каждого файла.

Практическое следствие: если накатить upgrade(), затем downgrade() на БД,
где уже появились новые (post-upgrade) строки — колонка снова будет
называться receipt_photo_url, но содержать голые ключи вместо URL. Старый
код, ожидающий там полный URL, получит нерабочие ссылки на фото без явной
ошибки на уровне БД/миграции — это нужно учитывать вручную, если такой
откат когда-либо понадобится на проде.
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
    # LOSSY: возвращает только имя колонки. Значения остаются в новом формате
    # (голый ключ, не URL) — см. предупреждение в докстринге модуля выше.
    op.alter_column("fuel_refills", "receipt_photo_key", new_column_name="receipt_photo_url")

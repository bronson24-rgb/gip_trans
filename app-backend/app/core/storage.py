import uuid

import boto3
from botocore.client import Config as BotoConfig

from app.core.config import settings

_s3_client = None
_s3_presign_client = None


def get_s3_client():
    """Клиент для реальных операций с хранилищем (put/head) — внутренний адрес хранилища."""
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
            config=BotoConfig(signature_version="s3v4"),
        )
    return _s3_client


def get_s3_presign_client():
    """Отдельный клиент только для generate_presigned_url — публичный адрес хранилища,
    иначе подписанная ссылка ведёт на хост, недоступный из браузера пользователя
    (например "minio" — внутреннее имя контейнера в docker-сети)."""
    global _s3_presign_client
    if _s3_presign_client is None:
        _s3_presign_client = boto3.client(
            "s3",
            endpoint_url=settings.s3_public_endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
            config=BotoConfig(signature_version="s3v4"),
        )
    return _s3_presign_client


ALLOWED_CONTENT_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/heic": "heic",
}

MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024  # 10 МБ — с запасом под фото с телефона

PRESIGNED_URL_EXPIRE_SECONDS = 300


class UnsupportedFileTypeError(Exception):
    pass


class FileTooLargeError(Exception):
    pass


class ObjectNotFoundError(Exception):
    pass


def upload_receipt_photo(content: bytes, content_type: str) -> str:
    """Загружает фото чека в S3-совместимое хранилище, возвращает ключ объекта (не URL)."""
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise UnsupportedFileTypeError(content_type)
    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        raise FileTooLargeError(len(content))

    extension = ALLOWED_CONTENT_TYPES[content_type]
    key = f"receipts/{uuid.uuid4()}.{extension}"

    get_s3_client().put_object(
        Bucket=settings.s3_bucket,
        Key=key,
        Body=content,
        ContentType=content_type,
    )

    return key


def get_receipt_photo_url(key: str) -> str:
    """Временная (недолгоживущая) ссылка на объект — bucket приватный, публичного URL нет."""
    # head_object бросает ClientError (404), если ключа нет — не даём presigned-ссылку в никуда.
    try:
        get_s3_client().head_object(Bucket=settings.s3_bucket, Key=key)
    except Exception as exc:  # noqa: BLE001 — botocore кидает ClientError с деталями внутри
        raise ObjectNotFoundError(key) from exc

    return get_s3_presign_client().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.s3_bucket, "Key": key},
        ExpiresIn=PRESIGNED_URL_EXPIRE_SECONDS,
    )

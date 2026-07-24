import logging

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status
from fastapi.responses import RedirectResponse

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.limiter import limiter
from app.core.storage import (
    FileTooLargeError,
    MAX_UPLOAD_SIZE_BYTES,
    ObjectNotFoundError,
    UnsupportedFileTypeError,
    get_receipt_photo_url,
    upload_receipt_photo,
)
from app.models.user import User

logger = logging.getLogger("app.uploads")

router = APIRouter(prefix="/api/uploads", tags=["uploads"])


@router.post("/receipt")
@limiter.limit(lambda: settings.rate_limit_uploads)
async def upload_receipt(
    request: Request,
    file: UploadFile,
    _user: User = Depends(get_current_user),
) -> dict[str, str]:
    content = await file.read()

    try:
        key = upload_receipt_photo(content, file.content_type or "")
    except UnsupportedFileTypeError:
        logger.warning("Загрузка отклонена: неподдерживаемый тип файла %s", file.content_type)
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Дозволені формати: JPEG, PNG, WEBP, HEIC"
        )
    except FileTooLargeError:
        logger.warning("Загрузка отклонена: файл слишком большой (%d байт)", len(content))
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            f"Файл завеликий (максимум {MAX_UPLOAD_SIZE_BYTES // 1024 // 1024} МБ)",
        )
    except Exception:
        logger.exception("Не удалось загрузить файл в S3-хранилище")
        raise

    return {"key": key}


@router.get("/receipt/{key:path}")
@limiter.limit(lambda: settings.rate_limit_uploads)
def get_receipt(
    request: Request,
    key: str,
    _user: User = Depends(get_current_user),
) -> RedirectResponse:
    # Только ключи из-под upload_receipt_photo — не даём использовать этот эндпоинт
    # как проброс к произвольным объектам bucket'а.
    if not key.startswith("receipts/"):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Файл не знайдено")

    try:
        url = get_receipt_photo_url(key)
    except ObjectNotFoundError:
        logger.warning("Запрошен несуществующий объект: %s", key)
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Файл не знайдено")

    return RedirectResponse(url)

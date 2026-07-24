import io

from fastapi.testclient import TestClient

from app.api import uploads as uploads_module
from app.main import app


def test_unexpected_error_returns_clean_500_not_a_traceback(client, auth_headers, monkeypatch):
    """upload_receipt_photo падает с чем-то неожиданным (не Unsupported/TooLarge) —
    глобальный exception handler должен превратить это в чистый JSON 500, а не
    уронить процесс/утечь трейсбеком наружу.

    TestClient по умолчанию (raise_server_exceptions=True) сам перевыбрасывает
    исключение, пойманное ServerErrorMiddleware, — это фича для отладки тестов,
    а не признак того, что наш handler не сработал. Здесь явно отключаем это
    поведение, чтобы проверить именно то, что реально уйдёт клиенту по сети.
    """
    headers, _user = auth_headers

    def _boom(*args, **kwargs):
        raise RuntimeError("S3 недоступен")

    monkeypatch.setattr(uploads_module, "upload_receipt_photo", _boom)

    no_raise_client = TestClient(app, raise_server_exceptions=False)
    response = no_raise_client.post(
        "/api/uploads/receipt",
        files={"file": ("receipt.png", io.BytesIO(b"fake"), "image/png")},
        headers=headers,
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "Внутренняя ошибка сервера"}

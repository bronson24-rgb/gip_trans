import io
import struct
import zlib

from app.core import storage


def _make_1px_png() -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))

    raw = b"\x00\xff\x00\x00"  # 1 пиксель RGB + filter byte
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw))
    png += chunk(b"IEND", b"")
    return png


PNG_1PX = _make_1px_png()


def test_upload_receipt_requires_auth(client):
    response = client.post(
        "/api/uploads/receipt", files={"file": ("receipt.png", io.BytesIO(PNG_1PX), "image/png")}
    )
    assert response.status_code == 401


def test_upload_receipt_success(client, auth_headers):
    headers, _user = auth_headers

    response = client.post(
        "/api/uploads/receipt",
        files={"file": ("receipt.png", io.BytesIO(PNG_1PX), "image/png")},
        headers=headers,
    )

    assert response.status_code == 200
    key = response.json()["key"]
    assert key.startswith("receipts/")
    assert key.endswith(".png")


def test_get_receipt_redirects_to_presigned_url(client, auth_headers):
    headers, _user = auth_headers
    upload = client.post(
        "/api/uploads/receipt",
        files={"file": ("receipt.png", io.BytesIO(PNG_1PX), "image/png")},
        headers=headers,
    ).json()

    response = client.get(f"/api/uploads/receipt/{upload['key']}", headers=headers, follow_redirects=False)

    assert response.status_code == 307
    location = response.headers["location"]
    assert location.startswith(storage.settings.s3_public_endpoint_url)
    assert "X-Amz-Signature" in location


def test_get_receipt_requires_auth(client, auth_headers):
    headers, _user = auth_headers
    upload = client.post(
        "/api/uploads/receipt",
        files={"file": ("receipt.png", io.BytesIO(PNG_1PX), "image/png")},
        headers=headers,
    ).json()

    response = client.get(f"/api/uploads/receipt/{upload['key']}")

    assert response.status_code == 401


def test_get_receipt_unknown_key_is_404(client, auth_headers):
    headers, _user = auth_headers
    response = client.get("/api/uploads/receipt/receipts/does-not-exist.png", headers=headers)
    assert response.status_code == 404


def test_get_receipt_rejects_keys_outside_receipts_prefix(client, auth_headers):
    headers, _user = auth_headers
    response = client.get("/api/uploads/receipt/other/secret.txt", headers=headers)
    assert response.status_code == 404


def test_upload_receipt_rejects_unsupported_type(client, auth_headers):
    headers, _user = auth_headers

    response = client.post(
        "/api/uploads/receipt",
        files={"file": ("notes.txt", io.BytesIO(b"just text"), "text/plain")},
        headers=headers,
    )

    assert response.status_code == 415


def test_upload_receipt_rejects_oversized_file(client, auth_headers, monkeypatch):
    headers, _user = auth_headers
    monkeypatch.setattr(storage, "MAX_UPLOAD_SIZE_BYTES", 10)

    response = client.post(
        "/api/uploads/receipt",
        files={"file": ("receipt.png", io.BytesIO(PNG_1PX), "image/png")},
        headers=headers,
    )

    assert response.status_code == 413

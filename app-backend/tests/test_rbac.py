"""Проверки прав доступа (RBAC) для ресурсов, не покрытых в их собственных
test_*.py — там уже используется auth_headers (admin) и тестируется бизнес-логика,
здесь — именно разграничение driver / accountant / admin.
"""

from app.models.user import UserRole


def test_driver_cannot_list_expenses(client, headers_for):
    headers, _user = headers_for(UserRole.driver)
    response = client.get("/api/expenses", headers=headers)
    assert response.status_code == 403


def test_accountant_can_list_expenses(client, headers_for):
    headers, _user = headers_for(UserRole.accountant)
    response = client.get("/api/expenses", headers=headers)
    assert response.status_code == 200


def test_driver_can_list_vehicles(client, headers_for):
    """Список машин нужен водителю для выбора авто в форме отчёта — читать можно всем."""
    headers, _user = headers_for(UserRole.driver)
    response = client.get("/api/vehicles", headers=headers)
    assert response.status_code == 200


def test_driver_cannot_create_vehicle(client, headers_for):
    headers, _user = headers_for(UserRole.driver)
    response = client.post("/api/vehicles", json={"plate_number": "X999XX99"}, headers=headers)
    assert response.status_code == 403


def test_accountant_can_create_vehicle(client, headers_for):
    headers, _user = headers_for(UserRole.accountant)
    response = client.post("/api/vehicles", json={"plate_number": "X999XX99"}, headers=headers)
    assert response.status_code == 201


def test_driver_cannot_list_users(client, headers_for):
    headers, _user = headers_for(UserRole.driver)
    response = client.get("/api/users", headers=headers)
    assert response.status_code == 403


def test_accountant_cannot_manage_users(client, headers_for):
    """Управление доступом — только admin, даже бухгалтеру нельзя."""
    headers, _user = headers_for(UserRole.accountant)
    response = client.get("/api/users", headers=headers)
    assert response.status_code == 403


def test_admin_can_manage_users(client, headers_for):
    headers, _user = headers_for(UserRole.admin)
    response = client.post("/api/users", json={"email": "new-hire@example.com"}, headers=headers)
    assert response.status_code == 201
    assert response.json()["role"] == "driver"  # дефолтная роль новой записи


def test_driver_cannot_view_summary(client, headers_for):
    headers, _user = headers_for(UserRole.driver)
    response = client.get("/api/summary", params={"date_from": "2026-01-01", "date_to": "2026-01-31"}, headers=headers)
    assert response.status_code == 403


def test_accountant_can_view_summary(client, headers_for):
    headers, _user = headers_for(UserRole.accountant)
    response = client.get("/api/summary", params={"date_from": "2026-01-01", "date_to": "2026-01-31"}, headers=headers)
    assert response.status_code == 200


def test_any_allowed_role_can_upload_and_create_route_report(client, headers_for, make_vehicle):
    """POST /route-reports не ограничен ролью — создать рейс может любой допущенный пользователь."""
    vehicle = make_vehicle(plate_number="Y777YY77")
    headers, _user = headers_for(UserRole.driver)

    response = client.post(
        "/api/route-reports",
        json={
            "vehicle_id": str(vehicle.id),
            "report_date": "2026-07-24",
            "route_from": "А",
            "route_to": "Б",
            "odometer_start": 1,
            "odometer_end": 2,
            "fuel_end": "1.00",
            "departure_time": "08:00:00",
            "arrival_time": "09:00:00",
            "fuel_refills": [],
        },
        headers=headers,
    )

    assert response.status_code == 201

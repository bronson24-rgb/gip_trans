def test_create_route_report_requires_auth(client, valid_route_report_payload):
    response = client.post("/api/route-reports", json=valid_route_report_payload)
    assert response.status_code == 401


def test_create_route_report_success(client, auth_headers, valid_route_report_payload):
    headers, _user = auth_headers

    response = client.post("/api/route-reports", json=valid_route_report_payload, headers=headers)

    assert response.status_code == 201
    body = response.json()
    assert body["mileage"] == 180  # odometer_end - odometer_start
    assert body["status"] == "submitted"
    assert body["waybill_number"] is None
    assert body["vehicle"]["plate_number"] == "A123BC77"


def test_create_route_report_with_unknown_vehicle_returns_404_not_500(client, auth_headers, valid_route_report_payload):
    headers, _user = auth_headers
    valid_route_report_payload["vehicle_id"] = "00000000-0000-0000-0000-000000000000"

    response = client.post("/api/route-reports", json=valid_route_report_payload, headers=headers)

    assert response.status_code == 404


def test_create_route_report_rejects_odometer_end_before_start(client, auth_headers, valid_route_report_payload):
    headers, _user = auth_headers
    valid_route_report_payload["odometer_end"] = valid_route_report_payload["odometer_start"] - 1

    response = client.post("/api/route-reports", json=valid_route_report_payload, headers=headers)

    assert response.status_code == 422


def test_create_route_report_with_fuel_refills(client, auth_headers, valid_route_report_payload):
    headers, _user = auth_headers
    valid_route_report_payload["fuel_refills"] = [
        {
            "refill_datetime": "2026-07-24T08:30:00Z",
            "station_name": "Лукойл",
            "liters": "50.5",
            "total_cost": "3500.00",
        }
    ]

    response = client.post("/api/route-reports", json=valid_route_report_payload, headers=headers)

    assert response.status_code == 201
    refills = response.json()["fuel_refills"]
    assert len(refills) == 1
    assert refills[0]["station_name"] == "Лукойл"
    assert refills[0]["receipt_photo_key"] is None


def test_driver_sees_only_own_route_reports(client, headers_for, valid_route_report_payload):
    from app.models.user import UserRole

    driver1_headers, _driver1 = headers_for(UserRole.driver, email="driver1@example.com")
    driver2_headers, _driver2 = headers_for(UserRole.driver, email="driver2@example.com")

    client.post("/api/route-reports", json=valid_route_report_payload, headers=driver1_headers)

    response = client.get("/api/route-reports", headers=driver2_headers)

    assert response.status_code == 200
    assert response.json() == []  # чужой рейс driver2 не видит


def test_driver_cannot_open_someone_elses_report_by_id(client, headers_for, valid_route_report_payload):
    from app.models.user import UserRole

    driver1_headers, _driver1 = headers_for(UserRole.driver, email="driver1@example.com")
    driver2_headers, _driver2 = headers_for(UserRole.driver, email="driver2@example.com")

    created = client.post("/api/route-reports", json=valid_route_report_payload, headers=driver1_headers).json()

    response = client.get(f"/api/route-reports/{created['id']}", headers=driver2_headers)

    assert response.status_code == 404  # не 403 — не палим сам факт существования чужого рейса


def test_accountant_and_admin_see_reports_from_all_drivers(client, headers_for, valid_route_report_payload):
    from app.models.user import UserRole

    driver_headers, _driver = headers_for(UserRole.driver, email="driver1@example.com")
    accountant_headers, _accountant = headers_for(UserRole.accountant, email="accountant@example.com")

    client.post("/api/route-reports", json=valid_route_report_payload, headers=driver_headers)

    response = client.get("/api/route-reports", headers=accountant_headers)

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_driver_cannot_patch_financial_fields(client, headers_for, valid_route_report_payload):
    from app.models.user import UserRole

    driver_headers, _driver = headers_for(UserRole.driver, email="driver1@example.com")
    created = client.post("/api/route-reports", json=valid_route_report_payload, headers=driver_headers).json()

    response = client.patch(
        f"/api/route-reports/{created['id']}",
        json={"revenue_amount": "99999.00"},
        headers=driver_headers,
    )

    assert response.status_code == 403


def test_accountant_can_patch_financial_fields(client, headers_for, valid_route_report_payload):
    from app.models.user import UserRole

    driver_headers, _driver = headers_for(UserRole.driver, email="driver1@example.com")
    accountant_headers, _accountant = headers_for(UserRole.accountant, email="accountant@example.com")
    created = client.post("/api/route-reports", json=valid_route_report_payload, headers=driver_headers).json()

    response = client.patch(
        f"/api/route-reports/{created['id']}",
        json={"revenue_amount": "5000.00"},
        headers=accountant_headers,
    )

    assert response.status_code == 200
    assert response.json()["revenue_amount"] == "5000.00"


def test_patch_route_report_sets_financial_fields(client, auth_headers, valid_route_report_payload):
    headers, _user = auth_headers
    created = client.post("/api/route-reports", json=valid_route_report_payload, headers=headers).json()

    response = client.patch(
        f"/api/route-reports/{created['id']}",
        json={"waybill_number": "TTN-42", "client_name": "ООО Ромашка", "revenue_amount": "15000.00", "status": "approved"},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["waybill_number"] == "TTN-42"
    assert body["revenue_amount"] == "15000.00"
    assert body["status"] == "approved"


def test_patch_route_report_partial_update_does_not_clear_other_fields(client, auth_headers, valid_route_report_payload):
    headers, _user = auth_headers
    created = client.post("/api/route-reports", json=valid_route_report_payload, headers=headers).json()
    client.patch(f"/api/route-reports/{created['id']}", json={"waybill_number": "TTN-1"}, headers=headers)

    response = client.patch(f"/api/route-reports/{created['id']}", json={"client_name": "Клиент"}, headers=headers)

    body = response.json()
    assert body["waybill_number"] == "TTN-1"  # не затёрлось предыдущим PATCH
    assert body["client_name"] == "Клиент"


def test_get_route_report_not_found(client, auth_headers):
    headers, _user = auth_headers
    response = client.get("/api/route-reports/00000000-0000-0000-0000-000000000000", headers=headers)
    assert response.status_code == 404

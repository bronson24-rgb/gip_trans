def test_create_and_list_vehicle(client, auth_headers):
    headers, _user = auth_headers

    response = client.post("/api/vehicles", json={"plate_number": "X001XX77", "make": "Volvo"}, headers=headers)
    assert response.status_code == 201

    listed = client.get("/api/vehicles", headers=headers)
    assert listed.status_code == 200
    assert any(v["plate_number"] == "X001XX77" for v in listed.json())


def test_create_vehicle_duplicate_plate_conflicts(client, auth_headers, make_vehicle):
    headers, _user = auth_headers
    make_vehicle(plate_number="DUP001")

    response = client.post("/api/vehicles", json={"plate_number": "DUP001"}, headers=headers)

    assert response.status_code == 409


def test_deactivate_vehicle(client, auth_headers, make_vehicle):
    headers, _user = auth_headers
    vehicle = make_vehicle(plate_number="Y002YY77")

    response = client.patch(f"/api/vehicles/{vehicle.id}", json={"is_active": False}, headers=headers)

    assert response.status_code == 200
    assert response.json()["is_active"] is False

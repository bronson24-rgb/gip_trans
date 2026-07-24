def test_create_and_list_expense(client, auth_headers):
    headers, _user = auth_headers

    create_response = client.post(
        "/api/expenses",
        json={"expense_date": "2026-07-24", "category": "rent", "amount": "15000.00", "comment": "Оренда"},
        headers=headers,
    )
    assert create_response.status_code == 201
    expense = create_response.json()
    assert expense["category"] == "rent"

    list_response = client.get("/api/expenses", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


def test_expense_requires_auth(client):
    response = client.get("/api/expenses")
    assert response.status_code == 401


def test_update_and_delete_expense(client, auth_headers):
    headers, _user = auth_headers
    expense = client.post(
        "/api/expenses",
        json={"expense_date": "2026-07-24", "category": "tax", "amount": "1000.00"},
        headers=headers,
    ).json()

    patched = client.patch(f"/api/expenses/{expense['id']}", json={"amount": "1200.00"}, headers=headers)
    assert patched.status_code == 200
    assert patched.json()["amount"] == "1200.00"

    deleted = client.delete(f"/api/expenses/{expense['id']}", headers=headers)
    assert deleted.status_code == 204

    missing = client.get(f"/api/expenses/{expense['id']}", headers=headers)
    assert missing.status_code == 404


def test_create_expense_rejects_non_positive_amount(client, auth_headers):
    headers, _user = auth_headers
    response = client.post(
        "/api/expenses",
        json={"expense_date": "2026-07-24", "category": "other", "amount": "0"},
        headers=headers,
    )
    assert response.status_code == 422

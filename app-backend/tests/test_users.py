def test_create_user_and_duplicate_conflicts(client, auth_headers):
    headers, _user = auth_headers

    first = client.post("/api/users", json={"email": "new@example.com"}, headers=headers)
    assert first.status_code == 201
    assert first.json()["is_allowed"] is True  # значение по умолчанию

    duplicate = client.post("/api/users", json={"email": "new@example.com"}, headers=headers)
    assert duplicate.status_code == 409


def test_revoke_user_access(client, auth_headers, make_user):
    headers, _user = auth_headers
    target = make_user(email="revoke-me@example.com")

    response = client.patch(f"/api/users/{target.id}", json={"is_allowed": False}, headers=headers)

    assert response.status_code == 200
    assert response.json()["is_allowed"] is False


def test_revoked_user_cannot_use_existing_token(client, auth_headers):
    """Токен ещё не истёк, но is_allowed уже False — get_current_user должен перепроверять по БД, а не только по подписи токена."""
    headers, user = auth_headers

    client.patch(f"/api/users/{user.id}", json={"is_allowed": False}, headers=headers)

    response = client.get("/api/route-reports", headers=headers)

    assert response.status_code == 403

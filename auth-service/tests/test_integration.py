def test_registration(client):
    payload = {
        "username": "new_user",
        "email": "new_user@example.com",
        "password": "strong_password_123",
    }
    response = client.post("/registration", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_authorization(client):
    registration_payload = {
        "username": "auth_user",
        "email": "auth_user@example.com",
        "password": "strong_password_123",
    }
    client.post("/registration", json=registration_payload)

    response = client.post(
        "/authorization",
        json={"email": "auth_user@example.com", "password": "strong_password_123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_get_current_user(client):
    payload = {
        "username": "me_user",
        "email": "me_user@example.com",
        "password": "strong_password_123",
    }
    reg_response = client.post("/registration", json=payload)
    token = reg_response.json()["access_token"]

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "me_user@example.com"

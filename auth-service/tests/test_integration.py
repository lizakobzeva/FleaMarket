import uuid


def _unique_suffix() -> str:
    return uuid.uuid4().hex[:12]


def test_registration(client):
    suffix = _unique_suffix()
    payload = {
        "username": f"new_user_{suffix}",
        "email": f"new_user_{suffix}@example.com",
        "password": "strong_password_123",
    }
    response = client.post("/registration", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_authorization(client):
    suffix = _unique_suffix()
    registration_payload = {
        "username": f"auth_user_{suffix}",
        "email": f"auth_user_{suffix}@example.com",
        "password": "strong_password_123",
    }
    reg = client.post("/registration", json=registration_payload)
    assert reg.status_code == 201

    response = client.post(
        "/authorization",
        json={
            "email": registration_payload["email"],
            "password": registration_payload["password"],
        },
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "running"


def test_metrics_endpoint(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text


def test_correlation_id_in_response_header(client):
    response = client.get("/", headers={"X-Request-ID": "test-correlation-123"})
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == "test-correlation-123"


def test_correlation_id_generated_when_missing(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID")


def test_error_endpoint_returns_500(client):
    response = client.get("/test/error")
    assert response.status_code == 500


def test_get_current_user(client):
    suffix = _unique_suffix()
    email = f"me_user_{suffix}@example.com"
    payload = {
        "username": f"me_user_{suffix}",
        "email": email,
        "password": "strong_password_123",
    }
    reg_response = client.post("/registration", json=payload)
    assert reg_response.status_code == 201
    token = reg_response.json()["access_token"]

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == email

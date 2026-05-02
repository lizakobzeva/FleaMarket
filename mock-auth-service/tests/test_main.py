from fastapi.testclient import TestClient

from main import app


def test_get_user_id_returns_uuid():
    client = TestClient(app)
    response = client.post("/auth/get_user_id", json={"token": "test-token"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 36
    assert data.count("-") == 4

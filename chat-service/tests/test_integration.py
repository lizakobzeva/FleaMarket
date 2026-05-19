from unittest.mock import patch


class _MockResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


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


def test_create_chat(client):
    with patch("app.main.httpx.get", return_value=_MockResponse(200, {"seller_id": 700})):
        response = client.post(
            "/chats",
            headers={"Authorization": "Bearer test-token"},
            json={"product_id": "00000000-0000-0000-0000-000000000101", "initial_message": "Hi"},
        )
    assert response.status_code == 201
    data = response.json()
    assert data["buyer_id"] == 500
    assert data["seller_id"] == 700


def test_get_chat_and_chats_list(client):
    with patch("app.main.httpx.get", return_value=_MockResponse(200, {"seller_id": 700})):
        created = client.post(
            "/chats",
            headers={"Authorization": "Bearer test-token"},
            json={"product_id": "00000000-0000-0000-0000-000000000102", "initial_message": "Start"},
        )

    chat_id = created.json()["id"]
    single = client.get(f"/chats/{chat_id}")
    all_chats = client.get("/chats")
    assert single.status_code == 200
    assert all_chats.status_code == 200
    assert any(chat["id"] == chat_id for chat in all_chats.json())


def test_create_and_read_messages(client):
    with patch("app.main.httpx.get", return_value=_MockResponse(200, {"seller_id": 700})):
        created = client.post(
            "/chats",
            headers={"Authorization": "Bearer test-token"},
            json={"product_id": "00000000-0000-0000-0000-000000000103", "initial_message": "Start"},
        )

    chat_id = created.json()["id"]
    msg = client.post(f"/chats/{chat_id}/messages", json={"sender_id": 500, "text": "new message", "is_read": False})
    assert msg.status_code == 201

    messages = client.get(f"/chats/{chat_id}/messages")
    assert messages.status_code == 200
    assert len(messages.json()) == 1


def test_complete_chat(client):
    with patch("app.main.httpx.get", return_value=_MockResponse(200, {"seller_id": 700})):
        created = client.post(
            "/chats",
            headers={"Authorization": "Bearer test-token"},
            json={"product_id": "00000000-0000-0000-0000-000000000104", "initial_message": "Start"},
        )

    chat_id = created.json()["id"]
    response = client.post(f"/chats/{chat_id}/complete")
    assert response.status_code == 200
    assert response.json()["message"] == "Chat completed successfully"

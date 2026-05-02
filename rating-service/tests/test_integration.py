from unittest.mock import AsyncMock, patch


class _MockResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def test_create_review(client):
    with (
        patch("app.main.send_notification", new=AsyncMock(return_value=None)),
        patch("app.main.write_log", return_value=None),
        patch("app.main.httpx.AsyncClient") as mock_client,
    ):
        ctx = AsyncMock()
        ctx.get.return_value = _MockResponse(200, {"status": "complet", "buyer_id": 10, "seller_id": 20})
        mock_client.return_value.__aenter__.return_value = ctx

        response = client.post("/reviews", json={"order_id": 1, "user_id": 20, "rating": 5, "comment": "ok"})

    assert response.status_code == 201
    data = response.json()
    assert data["order_id"] == 1
    assert data["author_id"] == 10


def test_get_review(client):
    with (
        patch("app.main.send_notification", new=AsyncMock(return_value=None)),
        patch("app.main.write_log", return_value=None),
        patch("app.main.httpx.AsyncClient") as mock_client,
    ):
        ctx = AsyncMock()
        ctx.get.return_value = _MockResponse(200, {"status": "complet", "buyer_id": 10, "seller_id": 20})
        mock_client.return_value.__aenter__.return_value = ctx
        created = client.post("/reviews", json={"order_id": 2, "user_id": 20, "rating": 4, "comment": "good"})

    review_id = created.json()["id"]
    response = client.get(f"/reviews/{review_id}")
    assert response.status_code == 200
    assert response.json()["id"] == review_id


def test_update_review(client):
    with (
        patch("app.main.send_notification", new=AsyncMock(return_value=None)),
        patch("app.main.write_log", return_value=None),
        patch("app.main.httpx.AsyncClient") as mock_client,
    ):
        ctx = AsyncMock()
        ctx.get.return_value = _MockResponse(200, {"status": "complet", "buyer_id": 10, "seller_id": 20})
        mock_client.return_value.__aenter__.return_value = ctx
        created = client.post("/reviews", json={"order_id": 3, "user_id": 20, "rating": 3, "comment": "middle"})

    review_id = created.json()["id"]
    updated = client.put(f"/reviews/{review_id}", json={"rating": 5, "comment": "updated"})
    assert updated.status_code == 200
    assert updated.json()["rating"] == 5


def test_delete_review(client):
    with (
        patch("app.main.send_notification", new=AsyncMock(return_value=None)),
        patch("app.main.write_log", return_value=None),
        patch("app.main.httpx.AsyncClient") as mock_client,
    ):
        ctx = AsyncMock()
        ctx.get.return_value = _MockResponse(200, {"status": "complet", "buyer_id": 10, "seller_id": 20})
        mock_client.return_value.__aenter__.return_value = ctx
        created = client.post("/reviews", json={"order_id": 4, "user_id": 20, "rating": 2, "comment": "bad"})

    review_id = created.json()["id"]
    response = client.delete(f"/reviews/{review_id}")
    assert response.status_code == 200

    missing = client.get(f"/reviews/{review_id}")
    assert missing.status_code == 404


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body.get("status") == "running with PostgreSQL"


def test_get_user_reviews(client):
    with (
        patch("app.main.send_notification", new=AsyncMock(return_value=None)),
        patch("app.main.write_log", return_value=None),
        patch("app.main.httpx.AsyncClient") as mock_client,
    ):
        ctx = AsyncMock()
        ctx.get.return_value = _MockResponse(200, {"status": "complet", "buyer_id": 10, "seller_id": 20})
        mock_client.return_value.__aenter__.return_value = ctx
        client.post("/reviews", json={"order_id": 10, "user_id": 20, "rating": 5, "comment": "ok"})

    response = client.get("/reviews", params={"user_id": 20})
    assert response.status_code == 200
    reviews = response.json()
    assert len(reviews) >= 1
    assert any(r["user_id"] == 20 for r in reviews)


def test_get_user_rating(client):
    with (
        patch("app.main.send_notification", new=AsyncMock(return_value=None)),
        patch("app.main.write_log", return_value=None),
        patch("app.main.httpx.AsyncClient") as mock_client,
    ):
        ctx = AsyncMock()
        ctx.get.return_value = _MockResponse(200, {"status": "complet", "buyer_id": 10, "seller_id": 20})
        mock_client.return_value.__aenter__.return_value = ctx
        client.post("/reviews", json={"order_id": 11, "user_id": 20, "rating": 4, "comment": "good"})
        client.post("/reviews", json={"order_id": 12, "user_id": 20, "rating": 2, "comment": "meh"})

    response = client.get("/ratings/users/20")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == 20
    assert data["total_reviews"] == 2
    assert data["average_rating"] == 3.0


def test_get_user_rating_not_found(client):
    response = client.get("/ratings/users/999999")
    assert response.status_code == 404


def test_get_review_not_found(client):
    response = client.get("/reviews/999999")
    assert response.status_code == 404


def test_delete_review_not_found(client):
    response = client.delete("/reviews/999999")
    assert response.status_code == 404

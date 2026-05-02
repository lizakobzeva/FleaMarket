from unittest.mock import AsyncMock, patch


class _MockResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def test_create_order(client):
    with patch("main.httpx.AsyncClient") as mock_client:
        ctx = AsyncMock()
        ctx.get.return_value = _MockResponse(
            200,
            {"id": "00000000-0000-0000-0000-000000000001", "title": "Phone", "seller_id": 200, "price": 15000},
        )
        ctx.post.return_value = _MockResponse(200, {"ok": True})
        mock_client.return_value.__aenter__.return_value = ctx

        response = client.post(
            "/orders",
            headers={"Authorization": "Bearer test-token"},
            json={"product_id": "00000000-0000-0000-0000-000000000001", "seller_id": 200},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["seller_id"] == 200
    assert data["buyer_id"] == 101
    assert data["status"] == "active"


def test_get_order_by_id(client):
    create_resp = client.post(
        "/orders",
        headers={"Authorization": "Bearer test-token"},
        json={"product_id": "00000000-0000-0000-0000-000000000010", "seller_id": 300, "price": 100.5},
    )
    if create_resp.status_code != 201:
        with patch("main.httpx.AsyncClient") as mock_client:
            ctx = AsyncMock()
            ctx.get.return_value = _MockResponse(
                200,
                {"id": "00000000-0000-0000-0000-000000000010", "title": "Laptop", "seller_id": 300, "price": 100.5},
            )
            ctx.post.return_value = _MockResponse(200, {"ok": True})
            mock_client.return_value.__aenter__.return_value = ctx
            create_resp = client.post(
                "/orders",
                headers={"Authorization": "Bearer test-token"},
                json={"product_id": "00000000-0000-0000-0000-000000000010", "seller_id": 300, "price": 100.5},
            )

    order_id = create_resp.json()["id"]
    response = client.get(f"/orders/{order_id}")
    assert response.status_code == 200
    assert response.json()["id"] == order_id


def test_update_order_status(client):
    with patch("main.httpx.AsyncClient") as mock_client:
        ctx = AsyncMock()
        ctx.get.return_value = _MockResponse(
            200,
            {"id": "00000000-0000-0000-0000-000000000020", "title": "Tablet", "seller_id": 301, "price": 5000},
        )
        ctx.post.return_value = _MockResponse(200, {"ok": True})
        mock_client.return_value.__aenter__.return_value = ctx
        created = client.post(
            "/orders",
            headers={"Authorization": "Bearer test-token"},
            json={"product_id": "00000000-0000-0000-0000-000000000020", "seller_id": 301},
        )

    order_id = created.json()["id"]
    response = client.patch(f"/orders/{order_id}/status", json={"status": "complet"})
    assert response.status_code == 200
    assert response.json()["status"] == "complet"


def test_cancel_order(client):
    with patch("main.httpx.AsyncClient") as mock_client:
        ctx = AsyncMock()
        ctx.get.return_value = _MockResponse(
            200,
            {"id": "00000000-0000-0000-0000-000000000030", "title": "Book", "seller_id": 302, "price": 200},
        )
        ctx.post.return_value = _MockResponse(200, {"ok": True})
        mock_client.return_value.__aenter__.return_value = ctx
        created = client.post(
            "/orders",
            headers={"Authorization": "Bearer test-token"},
            json={"product_id": "00000000-0000-0000-0000-000000000030", "seller_id": 302},
        )

    order_id = created.json()["id"]
    response = client.post(f"/orders/{order_id}/cancel", json={"reason": "changed mind"})
    assert response.status_code == 200
    assert response.json()["status"] == "canceled"

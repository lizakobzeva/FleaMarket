def test_create_product(client):
    payload = {
        "title": "Gaming PC",
        "description": "Ryzen",
        "category": "computers",
        "price": 45000.0,
        "address": "Moscow",
    }
    response = client.post("/products/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Gaming PC"
    assert data["seller_id"] == 777


def test_get_products(client):
    client.post(
        "/products/",
        json={"title": "Book", "category": "books", "price": 250.0, "description": "Sci-fi"},
    )
    response = client.get("/products/")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_update_product(client):
    created = client.post(
        "/products/",
        json={"title": "Mouse", "category": "electronics", "price": 500.0, "description": "wireless"},
    )
    product_id = created.json()["id"]
    response = client.put(
        f"/products/{product_id}",
        json={"title": "Mouse 2", "category": "electronics", "price": 700.0, "description": "updated"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Mouse 2"


def test_delete_product(client):
    created = client.post(
        "/products/",
        json={"title": "Chair", "category": "home", "price": 1200.0, "description": "wood"},
    )
    product_id = created.json()["id"]
    response = client.delete(f"/products/{product_id}")
    assert response.status_code == 204

    missing = client.get(f"/products/{product_id}")
    assert missing.status_code == 404

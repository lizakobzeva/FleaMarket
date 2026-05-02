import pytest
from pydantic import ValidationError

from app.schemas import ProductCreate, ProductResponse


def test_product_create_valid():
    product = ProductCreate(title="iPhone", category="phones", price=1000.0)
    assert product.title == "iPhone"
    assert product.description is None


def test_product_create_requires_title():
    with pytest.raises(ValidationError):
        ProductCreate(category="phones", price=1000.0)


def test_product_response_contains_required_fields():
    with pytest.raises(ValidationError):
        ProductResponse(title="x", category="y", price=1.0)

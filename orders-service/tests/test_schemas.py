import pytest
from pydantic import ValidationError

from main import CancelOrderRequest, OrderCreate, OrderStatusUpdate


def test_order_create_valid():
    payload = {"product_id": "00000000-0000-0000-0000-000000000001", "seller_id": 77}
    order = OrderCreate(**payload)
    assert order.seller_id == 77
    assert order.price is None


def test_order_create_requires_product_id():
    with pytest.raises(ValidationError):
        OrderCreate(seller_id=77)


def test_order_status_update_valid():
    status = OrderStatusUpdate(status="active")
    assert status.status == "active"


def test_cancel_order_request_default_reason():
    payload = CancelOrderRequest()
    assert payload.reason is None

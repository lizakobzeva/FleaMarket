import pytest
from pydantic import ValidationError

from app.schemas import ChatCreate, MessageCreate


def test_chat_create_valid():
    chat = ChatCreate(product_id="00000000-0000-0000-0000-000000000001", initial_message="hello")
    assert chat.initial_message == "hello"


def test_chat_create_requires_product_id():
    with pytest.raises(ValidationError):
        ChatCreate(initial_message="hello")


def test_message_create_defaults_is_read_false():
    message = MessageCreate(sender_id=1, text="text")
    assert message.is_read is False

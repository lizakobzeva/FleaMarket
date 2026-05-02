import pytest
from pydantic import ValidationError

from app.schemas import UserCreate, UserLogin


def test_user_create_valid():
    user = UserCreate(username="tester", email="tester@example.com", password="password123")
    assert user.username == "tester"
    assert user.phone is None


def test_user_create_short_password_invalid():
    with pytest.raises(ValidationError):
        UserCreate(username="tester", email="tester@example.com", password="short")


def test_user_login_requires_email():
    with pytest.raises(ValidationError):
        UserLogin(password="password123")

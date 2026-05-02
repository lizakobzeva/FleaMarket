import pytest
from pydantic import ValidationError

from app.schemas import ReviewCreate, ReviewUpdate


def test_review_create_valid():
    review = ReviewCreate(order_id=1, user_id=2, rating=5, comment="great")
    assert review.rating == 5
    assert review.comment == "great"


def test_review_create_invalid_rating():
    with pytest.raises(ValidationError):
        ReviewCreate(order_id=1, user_id=2, rating=7)


def test_review_update_all_optional():
    review = ReviewUpdate()
    assert review.rating is None
    assert review.comment is None

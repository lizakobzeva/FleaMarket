from pydantic import BaseModel
from datetime import datetime
from typing import Optional


# Базовая модель с общими полями
class ReviewBase(BaseModel):
    order_id: int
    user_id: int
    rating: int
    comment: Optional[str] = None


# Модель для создания (без id и служебных полей)
class ReviewCreate(ReviewBase):
    pass


# Модель для обновления (все поля опциональны)
class ReviewUpdate(BaseModel):
    order_id: Optional[int] = None
    user_id: Optional[int] = None
    rating: Optional[int] = None
    comment: Optional[str] = None


# Модель для ответа (со всеми полями)
class ReviewResponse(ReviewBase):
    id: int
    author_id: int
    created_at: datetime

    class Config:
        from_attributes = True  # позволяет создавать Pydantic-модель из ORM-объекта


# Модель для рейтинга пользователя
class UserRating(BaseModel):
    user_id: int
    average_rating: float
    total_reviews: int

    class Config:
        from_attributes = True

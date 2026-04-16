from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


# Базовая модель с общими полями
class ProductBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: str
    price: float
    address: Optional[str] = None


# Модель для создания (без id и служебных полей)
class ProductCreate(ProductBase):
    pass


# Модель для ответа (со всеми полями)
class ProductResponse(ProductBase):
    id: UUID
    # user_id: UUID
    created_at: datetime
    updated_at: datetime

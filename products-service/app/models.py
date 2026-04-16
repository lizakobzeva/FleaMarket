from typing import Optional
from uuid import UUID, uuid4

from app.database import Base
from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


# Модель продукта в базе данных
class Product(Base):
    __tablename__ = 'products'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    # user_id: Mapped[UUID] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    title: Mapped[str]
    description: Mapped[Optional[str]]
    category: Mapped[str]
    price: Mapped[float]
    address: Mapped[Optional[str]]
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

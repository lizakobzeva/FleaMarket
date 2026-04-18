import sqlalchemy as sa
from sqlalchemy import Column, Integer, String, Float
from database import Base


class OrderModel(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(sa.Uuid(), nullable=False, index=True)
    product_title = Column(String, nullable=True)
    buyer_id = Column(Integer, nullable=False)
    buyer_name = Column(String, nullable=True)
    seller_id = Column(Integer, nullable=False)
    seller_name = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    status = Column(String, default="active")

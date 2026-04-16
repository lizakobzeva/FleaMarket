from sqlalchemy import Column, Integer, String, Float
from database import Base


class OrderModel(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, nullable=False)
    item_name = Column(String, nullable=True)
    buyer_id = Column(Integer, nullable=False)
    buyer_name = Column(String, nullable=True)
    seller_id = Column(Integer, nullable=False)
    seller_name = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    status = Column(String, default="active")

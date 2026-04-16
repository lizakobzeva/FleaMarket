from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, nullable=False)
    buyer_id = Column(Integer, nullable=False)
    seller_id = Column(Integer, nullable=False)
    last_message = Column(String, nullable=True)
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    unread_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False)
    sender_id = Column(Integer, nullable=False)
    text = Column(String, nullable=False)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    is_read = Column(Boolean, default=False)
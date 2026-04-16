from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ChatBase(BaseModel):
    item_id: int
    seller_id: int
    last_message: Optional[str] = None
    unread_count: int = 0

class ChatCreate(BaseModel):
    item_id: int
    seller_id: int
    initial_message: str

class ChatUpdate(BaseModel):
    last_message: Optional[str] = None
    unread_count: Optional[int] = None

class ChatResponse(ChatBase):
    id: int
    buyer_id: int
    last_message_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class MessageBase(BaseModel):
    sender_id: int
    text: str
    is_read: bool = False

class MessageCreate(MessageBase):
    pass

class MessageResponse(MessageBase):
    id: int
    chat_id: int
    sent_at: datetime
    
    class Config:
        from_attributes = True
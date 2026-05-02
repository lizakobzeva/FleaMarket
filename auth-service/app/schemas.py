# schemas.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Имя пользователя")
    email: EmailStr = Field(..., description="Электронная почта")
    phone: Optional[str] = Field(None, max_length=20, description="Номер телефона")


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128, description="Пароль (минимум 8 символов)")


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None
    rating: Optional[float] = Field(None, ge=0, le=5)


class UserResponse(UserBase):
    id: int
    rating: float = Field(default=0.0, ge=0, le=5, description="Рейтинг пользователя")
    is_active: bool = True
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LogCreate(BaseModel):
    message: str = Field(..., description="Текст лога")
    endpoint: Optional[str] = Field(None, description="Эндпоинт, который вызвали")
    user_id: Optional[int] = Field(None, description="ID пользователя")


class LogResponse(BaseModel):
    id: int
    message: str
    endpoint: Optional[str] = None
    user_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
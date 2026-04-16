"""
Notification Service — сервис уведомлений для барахолки.
Получает уведомления от других сервисов и логирует их.
"""

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import logging
from datetime import datetime

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Notification Service", description="Отправка уведомлений")


class Notification(BaseModel):
    user_id: int
    message: str
    type: str  # "welcome", "post_created", "post_deleted" и т.д.


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    message: str
    type: str
    timestamp: str


# Хранилище уведомлений в памяти
notifications_db: List[dict] = []
next_id = 1


@app.get("/")
def root():
    return {
        "service": "notification-service",
        "status": "running",
        "notifications_count": len(notifications_db)
    }


@app.post("/notify", response_model=NotificationResponse)
def send_notification(notification: Notification):
    """
    Получить уведомление и сохранить его.
    В реальном проекте здесь была бы отправка email/push.
    """
    global next_id

    # Логируем
    logger.info(
        f"NOTIFICATION: user_id={notification.user_id}, "
        f"type={notification.type}, "
        f"message={notification.message}"
    )

    # Сохраняем
    saved = {
        "id": next_id,
        "user_id": notification.user_id,
        "message": notification.message,
        "type": notification.type,
        "timestamp": datetime.now().isoformat()
    }
    notifications_db.append(saved)
    next_id += 1

    return saved


@app.get("/notifications", response_model=List[NotificationResponse])
def get_notifications():
    """Получить все уведомления"""
    return notifications_db


@app.get("/notifications/user/{user_id}", response_model=List[NotificationResponse])
def get_user_notifications(user_id: int):
    """Получить уведомления для конкретного пользователя"""
    return [n for n in notifications_db if n["user_id"] == user_id]

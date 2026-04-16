"""
Core Service — сервис объявлений барахолки.
Управляет постами (объявлениями) и проверяет пользователей через Auth API.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import httpx
import os

app = FastAPI(title="Core Service", description="Управление объявлениями барахолки")

# URL Auth-сервиса берется из переменных окружения
# В Docker Compose это будет http://auth-service:8000
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8000")

# URL Notification-сервиса
NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8003")

# Модели данных
class Post(BaseModel):
    id: int
    title: str
    content: str
    author_id: int
    author_username: str = ""
    published: bool = False

class PostCreate(BaseModel):
    title: str
    content: str
    author_id: int
    published: bool = False

# "База данных" в памяти
posts_db = {
    1: Post(id=1, title="Продам велосипед", content="Б/у, в хорошем состоянии", author_id=1, author_username="alice", published=True),
    2: Post(id=2, title="Куплю монитор", content="Ищу 27 дюймов, 4K", author_id=2, author_username="bob", published=True),
}
next_id = 3


@app.get("/")
def root():
    return {
        "service": "core-service",
        "status": "running",
        "auth_service_url": AUTH_SERVICE_URL,
        "notification_service_url": NOTIFICATION_SERVICE_URL
    }


@app.get("/posts", response_model=List[Post])
def get_posts():
    """Получить все объявления"""
    return list(posts_db.values())


@app.get("/posts/{post_id}", response_model=Post)
def get_post(post_id: int):
    """Получить объявление по ID"""
    if post_id not in posts_db:
        raise HTTPException(status_code=404, detail="Post not found")
    return posts_db[post_id]


@app.post("/posts", response_model=Post, status_code=201)
async def create_post(post: PostCreate):
    """
    Создать новое объявление.
    Перед созданием проверяем, существует ли пользователь в Auth-сервисе.
    После создания отправляем уведомление автору.
    """
    global next_id

    # 1. Проверяем существование автора через Auth-сервис
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{AUTH_SERVICE_URL}/users/{post.author_id}")
            if response.status_code == 404:
                raise HTTPException(
                    status_code=400,
                    detail=f"User with id {post.author_id} not found in Auth service"
                )
            response.raise_for_status()
            author_data = response.json()
            author_username = author_data.get("username", f"user_{post.author_id}")
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Auth service unavailable: {str(e)}"
            )

    # 2. Создаём пост
    new_post = Post(
        id=next_id,
        title=post.title,
        content=post.content,
        author_id=post.author_id,
        author_username=author_username,
        published=post.published
    )
    posts_db[next_id] = new_post
    next_id += 1

    # 3. Отправляем уведомление автору (средний уровень)
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{NOTIFICATION_SERVICE_URL}/notify",
                json={
                    "user_id": post.author_id,
                    "message": f"Ваше объявление '{post.title}' успешно создано!",
                    "type": "post_created"
                },
                timeout=5.0
            )
    except Exception as e:
        # Не прерываем создание поста, если уведомление не отправилось
        print(f"Warning: Failed to send notification: {e}")

    return new_post


@app.delete("/posts/{post_id}")
def delete_post(post_id: int):
    """Удалить объявление"""
    if post_id not in posts_db:
        raise HTTPException(status_code=404, detail="Post not found")
    del posts_db[post_id]
    return {"message": "Post deleted"}

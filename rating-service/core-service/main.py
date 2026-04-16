"""
Core Service — заглушка для демонстрации взаимодействия с Auth-сервисом.
Управляет постами и проверяет пользователей через Auth API.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import httpx
import os

app = FastAPI(title="Core Service", description="Управление постами")

# URL Auth-сервиса берется из переменных окружения
# В Docker Compose это будет http://auth-service:8000
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")

# Модели данных
class Post(BaseModel):
    id: int
    title: str
    content: str
    author_id: int
    published: bool = False

class PostCreate(BaseModel):
    title: str
    content: str
    author_id: int
    published: bool = False

# "База данных" в памяти
posts_db = {
    1: Post(id=1, title="Первый пост", content="Привет, мир!", author_id=1, published=True),
    2: Post(id=2, title="Второй пост", content="Docker — это круто", author_id=2, published=True),
}
next_id = 3

@app.get("/")
def root():
    return {
        "service": "core-service",
        "status": "running",
        "auth_service_url": AUTH_SERVICE_URL
    }

@app.get("/posts", response_model=List[Post])
def get_posts():
    """Получить все посты"""
    return list(posts_db.values())

@app.get("/posts/{post_id}", response_model=Post)
def get_post(post_id: int):
    """Получить пост по ID"""
    if post_id not in posts_db:
        raise HTTPException(status_code=404, detail="Post not found")
    return posts_db[post_id]

@app.post("/posts", response_model=Post, status_code=201)
async def create_post(post: PostCreate):
    """
    Создать новый пост.
    Перед созданием проверяем, существует ли пользователь в Auth-сервисе.
    """
    global next_id

    # ВАЖНО: Вызов другого микросервиса!
    # Проверяем, есть ли пользователь с author_id в Auth-сервисе
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{AUTH_SERVICE_URL}/users/{post.author_id}")
            if response.status_code == 404:
                raise HTTPException(status_code=400, detail=f"User with id {post.author_id} not found")
            response.raise_for_status()
        except httpx.RequestError as e:
            # Если Auth-сервис недоступен, возвращаем 503
            raise HTTPException(status_code=503, detail=f"Auth service unavailable: {str(e)}")

    # Если пользователь существует, создаём пост
    new_post = Post(id=next_id, **post.dict())
    posts_db[next_id] = new_post
    next_id += 1
    return new_post

@app.delete("/posts/{post_id}")
def delete_post(post_id: int):
    """Удалить пост"""
    if post_id not in posts_db:
        raise HTTPException(status_code=404, detail="Post not found")
    del posts_db[post_id]
    return {"message": "Post deleted"}

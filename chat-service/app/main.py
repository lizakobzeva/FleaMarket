from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import httpx
import asyncio
import time
import os
from app import schemas, models
from app.auth import get_current_user_id
from app.database import SessionLocal, engine, get_db

app = FastAPI(
    title="Chat Service API",
    description="Сервис чатов для онлайн-барахолки",
    version="1.0.0"
)


def write_log(message: str):
    """
    Фоновая задача — запись в лог-файл.
    Выполняется ПОСЛЕ того, как ответ уже ушёл клиенту.
    """
    time.sleep(0.5)  # Имитируем задержку (как будто пишем на диск)
    with open("app.log", "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")



@app.get("/")
def root():
    return {
        "message": "Chat Service API",
        "docs": "/docs",
        "status": "running with PostgreSQL"
    }

# GET /chats - список всех чатов
@app.get("/chats", response_model=List[schemas.ChatResponse])
def read_chats(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Получить список чатов текущего пользователя"""
    chats = (
        db.query(models.Chat)
        .filter((models.Chat.buyer_id == user_id) | (models.Chat.seller_id == user_id))
        .all()
    )
    return chats

# GET /chats/{chat_id} - один чат
@app.get("/chats/{chat_id}", response_model=schemas.ChatResponse)
def read_chat(
    chat_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Получить чат по ID"""
    chat = db.get(models.Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    if chat.buyer_id != user_id and chat.seller_id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return chat

# POST /chats - создать чат
@app.post("/chats", response_model=schemas.ChatResponse, status_code=201)
def create_chat(
    chat: schemas.ChatCreate,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
    user_id: int = Depends(get_current_user_id),
):
    """Создать новый чат"""
    products_url = os.getenv("PRODUCTS_SERVICE_URL", "http://products-service:8000").rstrip("/")
    try:
        resp = httpx.get(f"{products_url}/products/{chat.product_id}", timeout=5.0)
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Products service unavailable")
    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="Product not found")
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Products service error")

    product = resp.json()
    seller_id = product.get("seller_id")
    if not isinstance(seller_id, int):
        raise HTTPException(status_code=502, detail="Products payload missing seller_id")
    if seller_id == user_id:
        raise HTTPException(status_code=400, detail="Cannot create chat with yourself")

    existing = (
        db.query(models.Chat)
        .filter(
            models.Chat.product_id == chat.product_id,
            models.Chat.buyer_id == user_id,
            models.Chat.seller_id == seller_id,
        )
        .first()
    )
    if existing:
        return existing

    db_chat = models.Chat(
        product_id=chat.product_id,
        buyer_id=user_id,
        seller_id=seller_id,
        last_message=chat.initial_message,
        last_message_at=None
    )
    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)
    
    # Добавила фоновую задачу логирования
    if background_tasks:
        background_tasks.add_task(
            write_log,
            f"Chat created: id={db_chat.id}, product_id={db_chat.product_id}, seller_id={db_chat.seller_id}"
        )
    
    return db_chat

# GET /chats/{chat_id}/messages - сообщения чата
@app.get("/chats/{chat_id}/messages", response_model=List[schemas.MessageResponse])
def read_messages(
    chat_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Получить все сообщения чата"""
    chat = db.get(models.Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    if chat.buyer_id != user_id and chat.seller_id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    messages = db.query(models.Message).filter(models.Message.chat_id == chat_id).all()
    return messages

# POST /chats/{chat_id}/messages - отправить сообщение
@app.post("/chats/{chat_id}/messages", response_model=schemas.MessageResponse, status_code=201)
def create_message(
    chat_id: int,
    message: schemas.MessageCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Отправить сообщение в чат"""
    chat = db.get(models.Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    if chat.buyer_id != user_id and chat.seller_id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    db_message = models.Message(
        chat_id=chat_id,
        sender_id=user_id,
        text=message.text,
        is_read=False
    )
    db.add(db_message)
    
    chat.last_message = message.text
    chat.last_message_at = db_message.sent_at
    chat.unread_count += 1
    
    db.commit()
    db.refresh(db_message)
    return db_message

# POST /chats/{chat_id}/complete - завершить сделку
@app.post("/chats/{chat_id}/complete")
def complete_chat(
    chat_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    chat = db.get(models.Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    if chat.buyer_id != user_id and chat.seller_id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return {"message": "Chat completed successfully"}


# ===== Асинхронные эндпоинты =====

@app.get("/external/posts")
async def get_external_posts():
    """
    Асинхронно получает данные из внешнего API (JSONPlaceholder)
    """
    async with httpx.AsyncClient() as client:
        response = await client.get("https://jsonplaceholder.typicode.com/posts")
        return response.json()[:5]


@app.get("/external/combined")
async def get_combined_data():
    """
    Параллельно получает данные из трёх внешних API
    """
    async with httpx.AsyncClient() as client:
        posts_task = client.get("https://jsonplaceholder.typicode.com/posts")
        users_task = client.get("https://jsonplaceholder.typicode.com/users")
        comments_task = client.get("https://jsonplaceholder.typicode.com/comments")
        
        posts_resp, users_resp, comments_resp = await asyncio.gather(
            posts_task, users_task, comments_task
        )
        
        return {
            "posts": posts_resp.json()[:3],
            "users": users_resp.json()[:3],
            "comments": comments_resp.json()[:3]
        }


@app.get("/external/posts-with-log")
async def get_external_posts_with_log(background_tasks: BackgroundTasks):
    """
    Получает внешние данные и логирует факт обращения
    """
    async with httpx.AsyncClient() as client:
        response = await client.get("https://jsonplaceholder.typicode.com/posts")
        data = response.json()[:5]
    
    background_tasks.add_task(
        write_log,
        f"External posts requested, returned {len(data)} items"
    )
    return data
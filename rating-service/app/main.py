from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from statistics import mean
import httpx
import asyncio
import time
import os

from app import schemas, models
from app.auth import get_current_user_id
from app.database import SessionLocal, engine, get_db

# URL Notification-сервиса берется из переменных окружения
# В Docker Compose это будет http://notification-service:8000
NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8003")

# Создаём таблицы (только для разработки, в продакшене используем миграции!)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Rating Service API",
    description="Сервис для управления комментариями, оценками и рейтингами продавцов и покупателей",
    version="1.0.0"
)


def write_log(message: str):
    """
    Фоновая задача — запись в лог-файл.

    Особенности:
    - Это обычная синхронная функция, не async
    - Она выполняется ПОСЛЕ того, как ответ уже ушёл клиенту
    - Клиент НЕ ЖДЁТ завершения этой функции
    """
    # Имитируем небольшую задержку (как будто пишем на диск)
    time.sleep(0.5)

    # Открываем файл и дописываем строку
    with open("app.log", "a") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

    # Функция завершается, клиент об этом уже не узнает


# Асинхронный эндпоинт для внешних данных
@app.get("/external/posts")
async def get_external_posts():
    """
    Асинхронно получает данные из внешнего API (JSONPlaceholder)

    - async def создаёт корутину, а не обычную функцию
    - async with httpx.AsyncClient() создаёт асинхронный HTTP-клиент
    - await client.get() отправляет запрос и ОТДАЁТ УПРАВЛЕНИЕ event loop'у
    - Пока запрос выполняется, сервер может обрабатывать других клиентов
    """
    # Создаём асинхронный клиент (он сам закроется после выполнения)
    async with httpx.AsyncClient() as client:
        # await - точка приостановки корутины
        # В этот момент сервер может заниматься другими задачами
        response = await client.get("https://jsonplaceholder.typicode.com/posts")

        # Вернём только первые 5 записей, чтобы ответ не был слишком большим
        return response.json()[:5]


# Параллельные запросы с asyncio.gather() -----
async def fetch_posts(client):
    response = await client.get("https://jsonplaceholder.typicode.com/posts")
    return response.json()[:3]

async def fetch_users(client):
    response = await client.get("https://jsonplaceholder.typicode.com/users")
    return response.json()[:3]

async def fetch_comments(client):
    response = await client.get("https://jsonplaceholder.typicode.com/comments")
    return response.json()[:3]

@app.get("/external/combined")
async def get_combined_data():
    """
    Параллельно получает данные из трёх внешних API

    Здесь мы демонстрируем мощь asyncio.gather():
    - Запросы выполняются ОДНОВРЕМЕННО, а не последовательно
    - Общее время = максимальное время самого долгого запроса, а не сумма
    """
    async with httpx.AsyncClient() as client:
        # ЖДЁМ ВСЕ ЗАДАЧИ ОДНОВРЕМЕННО
        # gather() приостанавливает выполнение, пока ВСЕ задачи не завершатся
        # Но пока мы ждём, сервер может обрабатывать других клиентов!
        posts, users, comments = await asyncio.gather(
            fetch_posts(client),
            fetch_users(client),
            fetch_comments(client)
        )

        # Возвращаем объединённые данные
        return {
            "posts": posts,
            "users": users,
            "comments": comments
        }


# Комбинируем асинхронный запрос с фоновой задачей -----
@app.get("/external/posts-with-log")
async def get_external_posts_with_log(background_tasks: BackgroundTasks):
    """
    Получает внешние данные и логирует факт обращения

    Демонстрирует комбинацию асинхронного запроса и фоновой задачи
    """

    # Асинхронный запрос к внешнему API
    async with httpx.AsyncClient() as client:
        response = await client.get("https://jsonplaceholder.typicode.com/posts")
        data = response.json()[:5]

    # Логируем ПОСЛЕ ответа
    background_tasks.add_task(
        write_log,
        f"External posts requested, returned {len(data)} items"
    )

    # Ответ уходит сразу, логирование выполнится позже
    return data


# ----- GET /reviews - список всех отзывов пользователя -----
@app.get("/reviews", response_model=List[schemas.ReviewResponse])
def get_user_reviews(
    user_id: int = Query(..., description="ID пользователя, для которого ищем отзывы"),
    db: Session = Depends(get_db)
):
    """
    Получить список всех отзывов для конкретного пользователя (продавца или покупателя).
    """
    if not user_id:
        raise HTTPException(
            status_code=400,
            detail={"error": "Не указан user_id", "code": 400}
        )

    reviews = db.query(models.Review).filter(models.Review.user_id == user_id).all()
    return reviews


# ----- POST /reviews - создать отзыв -----
@app.post("/reviews", response_model=schemas.ReviewResponse, status_code=201)
async def create_review(
    review: schemas.ReviewCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    author_id: int = Depends(get_current_user_id),
):
    """
    Добавляет новый отзыв о пользователе после завершения сделки.
    """
    # Проверяем, что автор и получатель отзыва - разные пользователи
    if author_id == review.user_id:
        raise HTTPException(
            status_code=400,
            detail={"error": "Нельзя оставить отзыв самому себе", "code": 400}
        )

    orders_url = os.getenv("ORDERS_SERVICE_URL", "http://orders-service:8000").rstrip("/")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{orders_url}/orders/{review.order_id}", timeout=5.0)
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail={"error": "Orders service unavailable", "code": 503})
    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail={"error": "Заказ не найден", "code": 404})
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail={"error": "Orders service error", "code": 502})

    order = resp.json()
    if order.get("status") != "complet":
        raise HTTPException(status_code=400, detail={"error": "Заказ не завершен", "code": 400})

    buyer_id = order.get("buyer_id")
    seller_id = order.get("seller_id")
    if author_id not in [buyer_id, seller_id]:
        raise HTTPException(status_code=403, detail={"error": "Вы не участник сделки", "code": 403})
    if review.user_id not in [buyer_id, seller_id] or review.user_id == author_id:
        raise HTTPException(status_code=400, detail={"error": "user_id должен быть другой стороной сделки", "code": 400})

    # Преобразуем Pydantic модель в словарь и создаём SQLAlchemy объект
    payload = review.model_dump()
    payload["author_id"] = author_id
    db_review = models.Review(**payload)

    # Добавляем в сессию и сохраняем
    db.add(db_review)
    db.commit()
    db.refresh(db_review)

    # Отправляем уведомление автору отзыва об успешном создании
    background_tasks.add_task(
        send_notification,
        user_id=author_id,
        message=f"Ваш отзыв для пользователя {review.user_id} успешно создан!",
        notification_type="review_created"
    )

    # Фоновая задача — логирование создания отзыва
    background_tasks.add_task(
        write_log,
        f"Review created: id={db_review.id}, author={db_review.author_id}, user={db_review.user_id}, rating={db_review.rating}"
    )

    return db_review


async def send_notification(user_id: int, message: str, notification_type: str):
    """
    Отправляет уведомление в notification-service.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{NOTIFICATION_SERVICE_URL}/notify",
                json={
                    "user_id": user_id,
                    "message": message,
                    "type": notification_type
                }
            )
            if response.status_code == 200:
                print(f"Notification sent to user {user_id}")
        except httpx.RequestError as e:
            print(f"Failed to send notification: {str(e)}")


# ----- GET /reviews/{review_id} - получить один отзыв -----
@app.get("/reviews/{review_id}", response_model=schemas.ReviewResponse)
def get_review(review_id: int, db: Session = Depends(get_db)):
    """
    Возвращает конкретный отзыв по его идентификатору.
    """
    review = db.get(models.Review, review_id)
    if not review:
        raise HTTPException(
            status_code=404,
            detail={"error": "Отзыв не найден", "code": 404}
        )
    return review


# ----- PUT /reviews/{review_id} - обновить отзыв -----
@app.put("/reviews/{review_id}", response_model=schemas.ReviewResponse)
def update_review(review_id: int, review_update: schemas.ReviewUpdate, db: Session = Depends(get_db)):
    """
    Обновить существующий отзыв.
    """
    # Ищем отзыв
    db_review = db.get(models.Review, review_id)
    if not db_review:
        raise HTTPException(
            status_code=404,
            detail={"error": "Отзыв не найден", "code": 404}
        )

    # Обновляем только переданные поля
    update_data = review_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_review, field, value)

    # Сохраняем изменения
    db.commit()
    db.refresh(db_review)

    return db_review


# ----- DELETE /reviews/{review_id} - удалить отзыв -----
@app.delete("/reviews/{review_id}", status_code=200)
def delete_review(review_id: int, db: Session = Depends(get_db)):
    """
    Удаляет существующий отзыв.
    """
    review = db.get(models.Review, review_id)
    if not review:
        raise HTTPException(
            status_code=404,
            detail={"error": "Отзыв не найден", "code": 404}
        )

    db.delete(review)
    db.commit()

    return {"message": "Отзыв успешно удалён", "code": 200}


# ----- GET /ratings/users/{user_id} - получить рейтинг пользователя -----
@app.get("/ratings/users/{user_id}", response_model=schemas.UserRating)
def get_user_rating(user_id: int, db: Session = Depends(get_db)):
    """
    Возвращает среднюю оценку и общее количество отзывов для конкретного пользователя.
    """
    # Получаем все отзывы для пользователя
    reviews = db.query(models.Review).filter(models.Review.user_id == user_id).all()

    if not reviews:
        raise HTTPException(
            status_code=404,
            detail={"error": "Пользователь не найден или у него нет отзывов", "code": 404}
        )

    # Вычисляем средний рейтинг
    ratings = [review.rating for review in reviews]
    average_rating = round(mean(ratings), 2)

    return schemas.UserRating(
        user_id=user_id,
        average_rating=average_rating,
        total_reviews=len(reviews)
    )


# ----- Корневой эндпоинт -----
@app.get("/")
def root():
    return {
        "message": "Rating Service API",
        "status": "running with PostgreSQL",
        "docs": "/docs",
        "notification_service_url": NOTIFICATION_SERVICE_URL,
        "endpoints": [
            "GET /reviews?user_id= - список отзывов пользователя",
            "POST /reviews - создать отзыв",
            "GET /reviews/{reviewId} - получить отзыв по ID",
            "DELETE /reviews/{reviewId} - удалить отзыв",
            "GET /ratings/users/{userId} - получить рейтинг пользователя"
        ]
    }

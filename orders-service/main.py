from fastapi import FastAPI, HTTPException, status, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
import httpx
import asyncio
from datetime import datetime
from database import engine, get_db, Base
from models import OrderModel

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Orders Service API",
    description="Микросервис для управления заказами на онлайн барахолке.",
    version="1.0.0"
)


class OrderResponse(BaseModel):
    id: int
    item_id: int
    item_name: Optional[str]
    buyer_id: int
    buyer_name: Optional[str]
    seller_id: int
    seller_name: Optional[str]
    price: float
    status: str

    class Config:
        from_attributes = True


class OrderCreate(BaseModel):
    item_id: int
    buyer_id: int
    seller_id: int
    price: float


class OrderStatusUpdate(BaseModel):
    status: str


class CancelOrderRequest(BaseModel):
    reason: Optional[str] = None


AUTH_SERVICE_URL = "http://auth-service:8000"
NOTIFICATION_SERVICE_URL = "http://notification-service:8000"


def write_log(message: str):
    with open("app.log", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} - {message}\n")


async def fetch_user_info(user_id: int):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{AUTH_SERVICE_URL}/users/{user_id}", timeout=5.0)
        if resp.status_code == 200:
            return resp.json()
        return {"id": user_id, "username": f"Пользователь #{user_id}"}


@app.get("/")
def root():
    return {
        "message": "Orders Service API",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    auth_health = False
    notification_health = False
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{AUTH_SERVICE_URL}/", timeout=5.0)
            auth_health = resp.status_code == 200
    except Exception:
        pass
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{NOTIFICATION_SERVICE_URL}/", timeout=5.0)
            notification_health = resp.status_code == 200
    except Exception:
        pass
    return {
        "orders_service": "healthy",
        "auth_service": "healthy" if auth_health else "unavailable",
        "notification_service": "healthy" if notification_health else "unavailable",
    }


@app.get("/orders", response_model=List[OrderResponse])
def get_orders(db: Session = Depends(get_db)):
    orders = db.query(OrderModel).all()
    return orders


@app.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    return order


@app.patch("/orders/{order_id}/status", response_model=OrderResponse)
def update_order_status(order_id: int, status_update: OrderStatusUpdate, db: Session = Depends(get_db)):
    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    if status_update.status not in ["active", "complet", "canceled"]:
        raise HTTPException(status_code=400, detail="Некорректный статус. Допустимо: active, complet, canceled")

    if order.status == "canceled":
        raise HTTPException(status_code=400, detail="Нельзя изменить статус отмененного заказа")

    order.status = status_update.status
    db.commit()
    db.refresh(order)
    return order


@app.on_event("startup")
def startup_event():
    db = next(get_db())
    if db.query(OrderModel).count() == 0:
        order1 = OrderModel(
            item_id=1, item_name="Смартфон", buyer_id=55, buyer_name="Евгений Попов",
            seller_id=12, seller_name="Петр Сидоров", price=30000.00, status="active"
        )
        order2 = OrderModel(
            item_id=2, item_name="Ноутбук", buyer_id=56, buyer_name="Иван Иванов",
            seller_id=13, seller_name="Анна Петрова", price=75000.00, status="complet"
        )
        db.add_all([order1, order2])
        db.commit()
        print("Тестовые заказы добавлены в базу данных.")
    db.close()


@app.get("/external/user-info")
async def get_external_user_info(buyer_id: int, seller_id: int):
    buyer_info, seller_info = await asyncio.gather(
        fetch_user_info(buyer_id),
        fetch_user_info(seller_id)
    )
    return {
        "buyer": buyer_info,
        "seller": seller_info
    }


@app.post("/orders/{order_id}/cancel", response_model=OrderResponse)
def cancel_order(order_id: int, background_tasks: BackgroundTasks, cancel_request: Optional[CancelOrderRequest] = None, db: Session = Depends(get_db)):
    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    if order.status == "canceled":
        raise HTTPException(status_code=400, detail="Заказ уже отменен")
    if order.status == "complet":
        raise HTTPException(status_code=400, detail="Нельзя отменить завершенный заказ")

    reason = cancel_request.reason if cancel_request and cancel_request.reason else "Без причины"
    order.status = "canceled"
    db.commit()
    db.refresh(order)

    background_tasks.add_task(write_log, f"Заказ #{order_id} отменён. Причина: {reason}")

    return order


@app.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(order: OrderCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    buyer_name = f"Покупатель #{order.buyer_id}"
    seller_name = f"Продавец #{order.seller_id}"

    try:
        async with httpx.AsyncClient() as client:
            resp_buyer = await client.post(f"{AUTH_SERVICE_URL}/verify/{order.buyer_id}", timeout=5.0)
            if resp_buyer.status_code == 200:
                buyer_data = resp_buyer.json()
                buyer_name = buyer_data.get("username", buyer_name)
    except Exception:
        pass

    try:
        async with httpx.AsyncClient() as client:
            resp_seller = await client.post(f"{AUTH_SERVICE_URL}/verify/{order.seller_id}", timeout=5.0)
            if resp_seller.status_code == 200:
                seller_data = resp_seller.json()
                seller_name = seller_data.get("username", seller_name)
    except Exception:
        pass

    db_order = OrderModel(
        item_id=order.item_id,
        item_name=f"Товар #{order.item_id}",
        buyer_id=order.buyer_id,
        buyer_name=buyer_name,
        seller_id=order.seller_id,
        seller_name=seller_name,
        price=order.price,
        status="active"
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)

    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{NOTIFICATION_SERVICE_URL}/send",
                json={
                    "user_id": order.buyer_id,
                    "order_id": db_order.id,
                    "message": f"Ваш заказ #{db_order.id} на '{db_order.item_name}' создан."
                },
                timeout=5.0
            )
    except Exception:
        pass

    background_tasks.add_task(write_log, f"Создан заказ #{db_order.id} на сумму {db_order.price}")

    return db_order

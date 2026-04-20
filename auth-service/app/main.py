# main.py
import asyncio
import os
import hashlib
from datetime import datetime, timedelta
from typing import List, Optional

import jwt
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Base, User, Log, engine, AsyncSessionLocal, init_db, get_db
from app.schemas import (
    UserCreate, UserResponse, UserLogin, TokenResponse,
    LogResponse
)

# 1. ЗАГРУЗКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 2. FASTAPI ПРИЛОЖЕНИЕ
app = FastAPI(
    title="Auth Service API",
    description="Сервис регистрации и аутентификации пользователей онлайн-барахолки",
    version="1.0.0"
)

bearer_scheme = HTTPBearer()


# 3. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None


# 4. CRUD-ФУНКЦИИ
async def get_user(db: AsyncSession, user_id: int) -> Optional[User]:
    return await db.get(User, user_id)


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user: UserCreate) -> User:
    db_user = User(
        username=user.username,
        email=user.email,
        password_hash=hash_password(user.password),
        phone=user.phone,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    if not user.is_active:
        return None
    return user


def build_token_response_for_user(user: User) -> TokenResponse:
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return TokenResponse(access_token=access_token, token_type="bearer")


async def create_log(db: AsyncSession, message: str, endpoint: Optional[str] = None,
                     user_id: Optional[int] = None) -> Log:
    db_log = Log(message=message, endpoint=endpoint, user_id=user_id)
    db.add(db_log)
    await db.commit()
    await db.refresh(db_log)
    return db_log


async def get_all_logs(db: AsyncSession) -> List[Log]:
    stmt = select(Log).order_by(Log.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_logs_by_user(db: AsyncSession, user_id: int) -> List[Log]:
    stmt = select(Log).where(Log.user_id == user_id).order_by(Log.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


# 5. ЗАВИСИМОСТИ FASTAPI
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception
    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    user = await get_user(db, int(user_id))
    if user is None:
        raise credentials_exception
    return user


async def write_log_to_db(message: str, endpoint: str = None, user_id: int = None):
    async with AsyncSessionLocal() as db:
        log = Log(message=message, endpoint=endpoint, user_id=user_id)
        db.add(log)
        await db.commit()
        print(f"Log written: {message}")


# 6. ИНИЦИАЛИЗАЦИЯ БД ПРИ ЗАПУСКЕ
@app.on_event("startup")
async def startup_event() -> None:
    # Для docker/dev гарантируем, что таблицы auth-service существуют.
    await init_db()


# 7. ЭНДПОИНТЫ
@app.get("/")
async def root():
    return {
        "message": "Auth Service Microservice",
        "docs": "/docs",
        "status": "running with PostgreSQL"
    }


@app.post("/authorization", response_model=TokenResponse)
async def authorization(user_login: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    Упрощенный endpoint авторизации для UI/Swagger:
    принимает JSON `{email, password}` и возвращает bearer token.
    """
    user = await authenticate_user(db, user_login.email, user_login.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return build_token_response_for_user(user)


@app.post("/registration", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def registration(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Упрощенный endpoint регистрации:
    создает пользователя и сразу возвращает bearer token.
    """
    existing_user = await get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with this email already exists")

    existing_username = await get_user_by_username(db, user.username)
    if existing_username:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with this username already exists")

    db_user = await create_user(db, user)
    return build_token_response_for_user(db_user)


@app.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Получить информацию о текущем авторизованном пользователе"""
    return current_user


@app.get("/external/posts")
async def get_external_posts():
    """Асинхронно получает данные из внешнего API (JSONPlaceholder)"""
    async with httpx.AsyncClient() as client:
        response = await client.get("https://jsonplaceholder.typicode.com/posts")
        return response.json()[:5]


@app.get("/external/combined")
async def get_combined_data():
    """Параллельно получает данные из трёх внешних API"""
    async def fetch_data(url: str):
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            return response.json()

    posts, users, albums = await asyncio.gather(
        fetch_data("https://jsonplaceholder.typicode.com/posts"),
        fetch_data("https://jsonplaceholder.typicode.com/users"),
        fetch_data("https://jsonplaceholder.typicode.com/albums")
    )

    return {"posts": posts[:3], "users": users[:3], "albums": albums[:3]}


@app.get("/external/posts-with-log")
async def get_external_posts_with_log(background_tasks: BackgroundTasks):
    """Получает внешние данные и логирует факт обращения в БД"""
    async with httpx.AsyncClient() as client:
        response = await client.get("https://jsonplaceholder.typicode.com/posts")
        data = response.json()[:5]

    background_tasks.add_task(
        write_log_to_db,
        message=f"External posts requested, returned {len(data)} items",
        endpoint="/external/posts-with-log"
    )

    return data


@app.get("/logs", response_model=List[LogResponse])
async def get_logs(db: AsyncSession = Depends(get_db)):
    """Получить все логи из БД"""
    return await get_all_logs(db)
import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# Загружаем переменные окружения из .env
load_dotenv()

# Формируем строку подключения
POSTGRES_URL = os.getenv("DATABASE_URL")
if not POSTGRES_URL:
    POSTGRES_URL = (
        f'postgresql+asyncpg://{os.getenv("POSTGRES_USER")}:{os.getenv("POSTGRES_PASSWORD")}'
        f'@{os.getenv("POSTGRES_HOST")}:{os.getenv("POSTGRES_PORT")}/{os.getenv("POSTGRES_DB")}'
    )

# Создаём engine (двигатель) - фабрика соединений
engine = create_async_engine(POSTGRES_URL)

# Создаём SessionLocal - фабрика сессий
async_session_maker = async_sessionmaker(engine, autoflush=False, expire_on_commit=False)

# Базовый класс для моделей
class Base(DeclarativeBase):
    pass

# Зависимость для получения сессии БД в эндпоинтах
async def get_db():
    async with async_session_maker() as session:
        yield session

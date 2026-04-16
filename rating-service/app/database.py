from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env
load_dotenv()

# Формируем строку подключения
# Используем HOST из переменных окружения (в Docker это rating-db, локально localhost)
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST", "localhost")  # По умолчанию localhost для локальной разработки
DB_PORT = os.getenv("DB_PORT", "5435")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Создаём engine (двигатель) - фабрика соединений
engine = create_engine(DATABASE_URL, echo=True)  # echo=True для отладки SQL-запросов

# Создаём SessionLocal - фабрика сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()

# Зависимость для получения сессии БД в эндпоинтах
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
